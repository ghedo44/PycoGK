from __future__ import annotations

import ctypes
import io
import math
import threading
import time
import zipfile
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Optional, Protocol, Sequence, cast

import numpy as np
import vedo
from vedo import Mesh as VedoMesh

from ._base import HandleOwner
from ._config import STRING_LENGTH
from ._errors import PicoGKInvalidHandleError
from ._native import CallbackImplicitDistance, CallbackScalarFieldTraverse, CallbackVectorFieldTraverse, native
from ._types import BBox3, ColorFloat, Triangle, Vec3, VoxelDimensions, as_bbox3, as_vec3, vec3_tuple

Vector3Like = Sequence[float]


class Library:
    _lock = threading.Lock()
    _running = False
    _app_exit = False
    _continue_task = True
    voxel_size_mm: float = 0.5

    @staticmethod
    def _lib() -> ctypes.CDLL:
        return native().lib

    @classmethod
    def init(cls, voxel_size_mm: float) -> None:
        with cls._lock:
            if cls._running:
                raise RuntimeError("PicoGK is already running")
            cls._lib().Library_Init(ctypes.c_float(voxel_size_mm))
            cls._running = True
            cls._app_exit = False
            cls._continue_task = True
            cls.voxel_size_mm = voxel_size_mm

    @classmethod
    def destroy(cls) -> None:
        with cls._lock:
            if not cls._running:
                return
            cls._app_exit = True
            cls._lib().Library_Destroy()
            cls._running = False

    @classmethod
    def _string_fn(cls, fn_name: str) -> str:
        buffer = ctypes.create_string_buffer(STRING_LENGTH)
        getattr(cls._lib(), fn_name)(buffer)
        return buffer.value.decode("utf-8")

    @classmethod
    def name(cls) -> str:
        return cls._string_fn("Library_GetName")

    strName = name

    @classmethod
    def version(cls) -> str:
        return cls._string_fn("Library_GetVersion")

    strVersion = version

    @classmethod
    def build_info(cls) -> str:
        return cls._string_fn("Library_GetBuildInfo")

    strBuildInfo = build_info

    @classmethod
    def voxels_to_mm(cls, xyz: Vector3Like) -> tuple[float, float, float]:
        src = as_vec3(xyz)
        dst = Vec3()
        cls._lib().Library_VoxelsToMm(ctypes.byref(src), ctypes.byref(dst))
        return vec3_tuple(dst)

    vecVoxelsToMm = voxels_to_mm

    @classmethod
    def mm_to_voxels(cls, xyz: Vector3Like) -> tuple[float, float, float]:
        src = as_vec3(xyz)
        dst = Vec3()
        cls._lib().Library_MmToVoxels(ctypes.byref(src), ctypes.byref(dst))
        return vec3_tuple(dst)

    MmToVoxels = mm_to_voxels

    @classmethod
    def bContinueTask(cls, app_exit_only: bool = False) -> bool:
        return (not cls._app_exit) and (app_exit_only or cls._continue_task)

    @classmethod
    def EndTask(cls) -> None:
        cls._continue_task = False

    @classmethod
    def CancelEndTaskRequest(cls) -> None:
        cls._continue_task = True

    @classmethod
    def Log(cls, message: str, *args: object) -> None:
        if args:
            message = message.format(*args)
        print(message)


class FieldMetadata(HandleOwner):
    class Type(IntEnum):
        UNKNOWN = -1
        STRING = 0
        FLOAT = 1
        VECTOR = 2

    @classmethod
    def from_voxels(cls, voxels: "Voxels") -> "FieldMetadata":
        h = Library._lib().Metadata_hFromVoxels(voxels.handle)
        if not h:
            raise PicoGKInvalidHandleError("Metadata_hFromVoxels returned null")
        return cls(h)

    @classmethod
    def from_scalar_field(cls, field: "ScalarField") -> "FieldMetadata":
        h = Library._lib().Metadata_hFromScalarField(field.handle)
        if not h:
            raise PicoGKInvalidHandleError("Metadata_hFromScalarField returned null")
        return cls(h)

    @classmethod
    def from_vector_field(cls, field: "VectorField") -> "FieldMetadata":
        h = Library._lib().Metadata_hFromVectorField(field.handle)
        if not h:
            raise PicoGKInvalidHandleError("Metadata_hFromVectorField returned null")
        return cls(h)

    def _destroy_native(self) -> None:
        Library._lib().Metadata_Destroy(self._handle)

    def count(self) -> int:
        self._ensure_open()
        return int(Library._lib().Metadata_nCount(self.handle))

    nCount = count

    def name_at(self, index: int) -> str:
        self._ensure_open()
        n = int(Library._lib().Metadata_nNameLengthAt(self.handle, int(index))) + 1
        buf = ctypes.create_string_buffer(n)
        ok = bool(Library._lib().Metadata_bGetNameAt(self.handle, int(index), buf, int(n)))
        if not ok:
            raise IndexError(index)
        return buf.value.decode("utf-8")

    def bGetNameAt(self, index: int) -> tuple[bool, str]:
        try:
            return True, self.name_at(index)
        except IndexError:
            return False, ""

    def type_at(self, name: str) -> "FieldMetadata.Type":
        self._ensure_open()
        return FieldMetadata.Type(int(Library._lib().Metadata_nTypeAt(self.handle, name.encode("utf-8"))))

    eTypeAt = type_at

    @classmethod
    def strTypeName(cls, value_type: "FieldMetadata.Type") -> str:
        mapping = {
            cls.Type.UNKNOWN: "unknown",
            cls.Type.STRING: "string",
            cls.Type.FLOAT: "float",
            cls.Type.VECTOR: "vector",
        }
        return mapping.get(value_type, "undefined")

    def strTypeAt(self, name: str) -> str:
        return self.strTypeName(self.type_at(name))

    def get_string(self, name: str) -> str:
        self._ensure_open()
        name_b = name.encode("utf-8")
        n = int(Library._lib().Metadata_nStringLengthAt(self.handle, name_b)) + 1
        buf = ctypes.create_string_buffer(n)
        ok = bool(Library._lib().Metadata_bGetStringAt(self.handle, name_b, buf, int(n)))
        if not ok:
            raise KeyError(name)
        return buf.value.decode("utf-8")

    def bGetValueAt(self, name: str) -> tuple[bool, object]:
        value_type = self.type_at(name)
        try:
            if value_type == self.Type.STRING:
                return True, self.get_string(name)
            if value_type == self.Type.FLOAT:
                return True, self.get_float(name)
            if value_type == self.Type.VECTOR:
                return True, self.get_vector(name)
        except KeyError:
            return False, ""
        return False, ""

    def get_float(self, name: str) -> float:
        self._ensure_open()
        out = ctypes.c_float()
        ok = bool(Library._lib().Metadata_bGetFloatAt(self.handle, name.encode("utf-8"), ctypes.byref(out)))
        if not ok:
            raise KeyError(name)
        return float(out.value)

    def get_vector(self, name: str) -> tuple[float, float, float]:
        self._ensure_open()
        out = Vec3()
        ok = bool(Library._lib().Metadata_bGetVectorAt(self.handle, name.encode("utf-8"), ctypes.byref(out)))
        if not ok:
            raise KeyError(name)
        return vec3_tuple(out)

    def set_string(self, name: str, value: str) -> "FieldMetadata":
        self._ensure_open()
        Library._lib().Metadata_SetStringValue(self.handle, name.encode("utf-8"), value.encode("utf-8"))
        return self

    def set_float(self, name: str, value: float) -> "FieldMetadata":
        self._ensure_open()
        Library._lib().Metadata_SetFloatValue(self.handle, name.encode("utf-8"), ctypes.c_float(value))
        return self

    def set_vector(self, name: str, value: Vector3Like) -> "FieldMetadata":
        self._ensure_open()
        v = as_vec3(value)
        Library._lib().Metadata_SetVectorValue(self.handle, name.encode("utf-8"), ctypes.byref(v))
        return self

    def SetValue(self, name: str, value: object) -> "FieldMetadata":
        if isinstance(value, str):
            return self.set_string(name, value)
        if isinstance(value, (int, float)):
            return self.set_float(name, float(value))
        return self.set_vector(name, cast(Vector3Like, value))

    def remove(self, name: str) -> "FieldMetadata":
        self._ensure_open()
        Library._lib().MetaData_RemoveValue(self.handle, name.encode("utf-8"))
        return self

    RemoveValue = remove

    def __str__(self) -> str:
        rows: list[str] = [f"Metadata table with {self.count()} items"]
        for index in range(self.count()):
            ok, name = self.bGetNameAt(index)
            if not ok:
                continue
            value_ok, value = self.bGetValueAt(name)
            rows.append(f"  {name} ({self.strTypeAt(name)}): {value if value_ok else ''}")
        return "\n".join(rows)


class Mesh(HandleOwner):
    def __init__(self, handle: int | ctypes.c_void_p | None = None, *, owns_handle: bool = True) -> None:
        if handle is None:
            handle = Library._lib().Mesh_hCreate()
        if not handle:
            raise PicoGKInvalidHandleError("Mesh_hCreate returned null")
        super().__init__(handle, owns_handle=owns_handle)

    @classmethod
    def from_voxels(cls, voxels: "Voxels") -> "Mesh":
        h = Library._lib().Mesh_hCreateFromVoxels(voxels.handle)
        if not h:
            raise PicoGKInvalidHandleError("Mesh_hCreateFromVoxels returned null")
        return cls(h)

    def _destroy_native(self) -> None:
        Library._lib().Mesh_Destroy(self._handle)

    def is_valid(self) -> bool:
        return bool(Library._lib().Mesh_bIsValid(self.handle))

    def add_vertex(self, xyz: Vector3Like) -> int:
        self._ensure_open()
        v = as_vec3(xyz)
        return int(Library._lib().Mesh_nAddVertex(self.handle, ctypes.byref(v)))

    nAddVertex = add_vertex

    def vertex_count(self) -> int:
        self._ensure_open()
        return int(Library._lib().Mesh_nVertexCount(self.handle))

    nVertexCount = vertex_count

    def get_vertex(self, index: int) -> tuple[float, float, float]:
        self._ensure_open()
        v = Vec3()
        Library._lib().Mesh_GetVertex(self.handle, int(index), ctypes.byref(v))
        return vec3_tuple(v)

    vecVertexAt = get_vertex

    def add_vertices(self, vertices: Sequence[Vector3Like]) -> list[int]:
        return [self.add_vertex(vertex) for vertex in vertices]

    AddVertices = add_vertices

    def add_triangle_indices(self, a: int, b: int, c: int) -> int:
        self._ensure_open()
        tri = Triangle(int(a), int(b), int(c))
        return int(Library._lib().Mesh_nAddTriangle(self.handle, ctypes.byref(tri)))

    def add_triangle(self, a_xyz: Vector3Like, b_xyz: Vector3Like, c_xyz: Vector3Like) -> int:
        ai = self.add_vertex(a_xyz)
        bi = self.add_vertex(b_xyz)
        ci = self.add_vertex(c_xyz)
        return self.add_triangle_indices(ai, bi, ci)

    def nAddTriangle(self, *args: object) -> int:
        if len(args) == 1 and isinstance(args[0], Triangle):
            tri = cast(Triangle, args[0])
            return self.add_triangle_indices(tri.a, tri.b, tri.c)
        if len(args) == 3 and all(isinstance(arg, int) for arg in args):
            return self.add_triangle_indices(cast(int, args[0]), cast(int, args[1]), cast(int, args[2]))
        if len(args) == 3:
            return self.add_triangle(cast(Vector3Like, args[0]), cast(Vector3Like, args[1]), cast(Vector3Like, args[2]))
        raise TypeError("nAddTriangle expects a Triangle, 3 ints, or 3 xyz vectors")

    def triangle_count(self) -> int:
        self._ensure_open()
        return int(Library._lib().Mesh_nTriangleCount(self.handle))

    nTriangleCount = triangle_count

    def get_triangle(self, index: int) -> tuple[int, int, int]:
        self._ensure_open()
        tri = Triangle()
        Library._lib().Mesh_GetTriangle(self.handle, int(index), ctypes.byref(tri))
        return (int(tri.a), int(tri.b), int(tri.c))

    oTriangleAt = get_triangle

    def get_triangle_vertices(self, index: int) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
        self._ensure_open()
        a = Vec3()
        b = Vec3()
        c = Vec3()
        Library._lib().Mesh_GetTriangleV(self.handle, int(index), ctypes.byref(a), ctypes.byref(b), ctypes.byref(c))
        return vec3_tuple(a), vec3_tuple(b), vec3_tuple(c)

    GetTriangle = get_triangle_vertices

    def bounding_box(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        self._ensure_open()
        box = BBox3()
        Library._lib().Mesh_GetBoundingBox(self.handle, ctypes.byref(box))
        return vec3_tuple(box.min), vec3_tuple(box.max)

    oBoundingBox = bounding_box

    def add_quad_indices(self, n0: int, n1: int, n2: int, n3: int, flipped: bool = False) -> "Mesh":
        if flipped:
            self.add_triangle_indices(n0, n2, n1)
            self.add_triangle_indices(n0, n3, n2)
        else:
            self.add_triangle_indices(n0, n1, n2)
            self.add_triangle_indices(n0, n2, n3)
        return self

    def add_quad(self, v0: Vector3Like, v1: Vector3Like, v2: Vector3Like, v3: Vector3Like, flipped: bool = False) -> "Mesh":
        n0 = self.add_vertex(v0)
        n1 = self.add_vertex(v1)
        n2 = self.add_vertex(v2)
        n3 = self.add_vertex(v3)
        return self.add_quad_indices(n0, n1, n2, n3, flipped)

    def AddQuad(self, *args: object, bFlipped: bool = False) -> "Mesh":
        if len(args) == 4 and all(isinstance(arg, int) for arg in args):
            return self.add_quad_indices(cast(int, args[0]), cast(int, args[1]), cast(int, args[2]), cast(int, args[3]), bFlipped)
        if len(args) == 4:
            return self.add_quad(cast(Vector3Like, args[0]), cast(Vector3Like, args[1]), cast(Vector3Like, args[2]), cast(Vector3Like, args[3]), bFlipped)
        raise TypeError("AddQuad expects 4 indices or 4 xyz vectors")

    def append(self, other: "Mesh") -> "Mesh":
        for index in range(other.triangle_count()):
            a, b, c = other.get_triangle_vertices(index)
            self.add_triangle(a, b, c)
        return self

    Append = append

    def create_transformed(self, scale: Vector3Like = (1.0, 1.0, 1.0), offset: Vector3Like = (0.0, 0.0, 0.0)) -> "Mesh":
        scale_v = scale
        offset_v = offset
        out = Mesh()
        for index in range(self.triangle_count()):
            a, b, c = self.get_triangle_vertices(index)
            out.add_triangle(
                (a[0] * scale_v[0] + offset_v[0], a[1] * scale_v[1] + offset_v[1], a[2] * scale_v[2] + offset_v[2]),
                (b[0] * scale_v[0] + offset_v[0], b[1] * scale_v[1] + offset_v[1], b[2] * scale_v[2] + offset_v[2]),
                (c[0] * scale_v[0] + offset_v[0], c[1] * scale_v[1] + offset_v[1], c[2] * scale_v[2] + offset_v[2]),
            )
        return out

    mshCreateTransformed = create_transformed

    def create_mirrored(self, plane_point: Vector3Like, plane_normal: Vector3Like) -> "Mesh":
        px, py, pz = plane_point
        nx, ny, nz = plane_normal
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length <= 1e-12:
            raise ValueError("plane_normal must be non-zero")
        nx /= length
        ny /= length
        nz /= length

        def mirror(v: tuple[float, float, float]) -> tuple[float, float, float]:
            vx, vy, vz = v
            dx = vx - px
            dy = vy - py
            dz = vz - pz
            dist = dx * nx + dy * ny + dz * nz
            return (vx - 2 * dist * nx, vy - 2 * dist * ny, vz - 2 * dist * nz)

        out = Mesh()
        for index in range(self.triangle_count()):
            a, b, c = self.get_triangle_vertices(index)
            out.add_triangle(mirror(a), mirror(b), mirror(c))
        return out

    mshCreateMirrored = create_mirrored

    def to_numpy(self) -> tuple[np.ndarray, np.ndarray]:
        self._ensure_open()
        vertices = np.zeros((self.vertex_count(), 3), dtype=np.float32)
        for i in range(vertices.shape[0]):
            vertices[i, :] = np.array(self.get_vertex(i), dtype=np.float32)

        triangles = np.zeros((self.triangle_count(), 3), dtype=np.int32)
        for i in range(triangles.shape[0]):
            triangles[i, :] = np.array(self.get_triangle(i), dtype=np.int32)

        return vertices, triangles

    @staticmethod
    def bPointLiesOnTriangle(vecP: Vector3Like, vecA: Vector3Like, vecB: Vector3Like, vecC: Vector3Like) -> bool:
        from ._extras import MeshMath

        return MeshMath.bPointLiesOnTriangle(vecP, vecA, vecB, vecC)

    def bFindTriangleFromSurfacePoint(self, vecSurfacePoint: Vector3Like) -> tuple[bool, int]:
        from ._extras import MeshMath

        return MeshMath.bFindTriangleFromSurfacePoint(self, vecSurfacePoint)

    @staticmethod
    def mshFromStlFile(
        strFilePath: str,
        eLoadUnit: Any = None,
        fPostScale: float = 1.0,
        vecPostOffsetMM: Vector3Like | None = None,
    ) -> "Mesh":
        from ._extras import EStlUnit, MeshIo

        load_unit = EStlUnit.AUTO if eLoadUnit is None else eLoadUnit
        return MeshIo.mshFromStlFile(strFilePath, cast(Any, load_unit), fPostScale, vecPostOffsetMM)

    def SaveToStlFile(
        self,
        strFilePath: str,
        eUnit: Any = None,
        vecOffsetMM: Vector3Like | None = None,
        fScale: float = 1.0,
    ) -> None:
        from ._extras import EStlUnit, MeshIo

        unit = EStlUnit.AUTO if eUnit is None else eUnit
        MeshIo.SaveToStlFile(self, strFilePath, cast(Any, unit), vecOffsetMM, fScale)


class Lattice(HandleOwner):
    def __init__(self, handle: int | ctypes.c_void_p | None = None, *, owns_handle: bool = True) -> None:
        if handle is None:
            handle = Library._lib().Lattice_hCreate()
        if not handle:
            raise PicoGKInvalidHandleError("Lattice_hCreate returned null")
        super().__init__(handle, owns_handle=owns_handle)

    def _destroy_native(self) -> None:
        Library._lib().Lattice_Destroy(self._handle)

    def is_valid(self) -> bool:
        return bool(Library._lib().Lattice_bIsValid(self.handle))

    def add_sphere(self, center: Vector3Like, radius: float) -> "Lattice":
        self._ensure_open()
        c = as_vec3(center)
        Library._lib().Lattice_AddSphere(self.handle, ctypes.byref(c), ctypes.c_float(radius))
        return self

    AddSphere = add_sphere

    def add_beam(
        self,
        a: Vector3Like,
        b: Vector3Like,
        radius_a: float,
        radius_b: float,
        round_cap: bool = True,
    ) -> "Lattice":
        self._ensure_open()
        va = as_vec3(a)
        vb = as_vec3(b)
        Library._lib().Lattice_AddBeam(
            self.handle,
            ctypes.byref(va),
            ctypes.byref(vb),
            ctypes.c_float(radius_a),
            ctypes.c_float(radius_b),
            ctypes.c_bool(round_cap),
        )
        return self

    AddBeam = add_beam


class Voxels(HandleOwner):
    def __init__(self, handle: int | ctypes.c_void_p | None = None, *, copy_from: "Voxels | None" = None, owns_handle: bool = True) -> None:
        if handle is None and copy_from is not None:
            handle = Library._lib().Voxels_hCreateCopy(copy_from.handle)
        elif handle is None:
            handle = Library._lib().Voxels_hCreate()
        if not handle:
            raise PicoGKInvalidHandleError("Voxels handle creation returned null")
        super().__init__(handle, owns_handle=owns_handle)
        self.metadata = FieldMetadata.from_voxels(self)
        self.metadata.set_string("PicoGK.Class", "Voxels")
        self._implicit_callback_ref: Any = None

    def _destroy_native(self) -> None:
        try:
            self.metadata.close()
        finally:
            Library._lib().Voxels_Destroy(self._handle)

    @classmethod
    def from_lattice(cls, lattice: Lattice) -> "Voxels":
        vox = cls()
        vox.render_lattice(lattice)
        return vox

    @classmethod
    def from_scalar_field(cls, field: "ScalarField") -> "Voxels":
        vox = cls()
        box_min, box_max = field.bounding_box()
        vox.render_implicit(box_min, box_max, field.signed_distance)
        return vox

    @classmethod
    def sphere(cls, center: Vector3Like, radius: float) -> "Voxels":
        with Lattice() as lattice:
            lattice.add_sphere(center, radius)
            return cls.from_lattice(lattice)

    voxSphere = sphere

    @classmethod
    def from_mesh(cls, mesh: Mesh) -> "Voxels":
        vox = cls()
        vox.render_mesh(mesh)
        return vox

    def duplicate(self) -> "Voxels":
        self._ensure_open()
        return Voxels(copy_from=self)

    voxDuplicate = duplicate

    def is_valid(self) -> bool:
        return bool(Library._lib().Voxels_bIsValid(self.handle))

    def bool_add(self, other: "Voxels") -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_BoolAdd(self.handle, other.handle)
        return self

    BoolAdd = bool_add

    def bool_add_all(self, items: Sequence["Voxels"]) -> "Voxels":
        for item in items:
            self.bool_add(item)
        return self

    BoolAddAll = bool_add_all

    def vox_bool_add(self, other: "Voxels") -> "Voxels":
        return self.duplicate().bool_add(other)

    voxBoolAdd = vox_bool_add

    def vox_bool_add_all(self, items: Sequence["Voxels"]) -> "Voxels":
        return self.duplicate().bool_add_all(items)

    voxBoolAddAll = vox_bool_add_all

    @staticmethod
    def voxCombine(vox1: "Voxels", vox2: "Voxels") -> "Voxels":
        return vox1.vox_bool_add(vox2)

    @staticmethod
    def voxCombineAll(items: Sequence["Voxels"]) -> "Voxels":
        vox = Voxels()
        return vox.bool_add_all(items)

    def bool_subtract(self, other: "Voxels") -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_BoolSubtract(self.handle, other.handle)
        return self

    BoolSubtract = bool_subtract

    def bool_subtract_all(self, items: Sequence["Voxels"]) -> "Voxels":
        for item in items:
            self.bool_subtract(item)
        return self

    BoolSubtractAll = bool_subtract_all

    def vox_bool_subtract(self, other: "Voxels") -> "Voxels":
        return self.duplicate().bool_subtract(other)

    voxBoolSubtract = vox_bool_subtract

    def vox_bool_subtract_all(self, items: Sequence["Voxels"]) -> "Voxels":
        return self.duplicate().bool_subtract_all(items)

    voxBoolSubtractAll = vox_bool_subtract_all

    def bool_intersect(self, other: "Voxels") -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_BoolIntersect(self.handle, other.handle)
        return self

    BoolIntersect = bool_intersect

    def vox_bool_intersect(self, other: "Voxels") -> "Voxels":
        return self.duplicate().bool_intersect(other)

    voxBoolIntersect = vox_bool_intersect

    def bool_add_smooth(self, other: "Voxels", smooth_distance: float) -> "Voxels":
        self._ensure_open()
        if not hasattr(Library._lib(), "Voxels_BoolAddSmooth"):
            raise NotImplementedError("Voxels_BoolAddSmooth is not available in this PicoGK runtime")
        Library._lib().Voxels_BoolAddSmooth(self.handle, other.handle, ctypes.c_float(smooth_distance))
        return self

    def offset(self, distance_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_Offset(self.handle, ctypes.c_float(distance_mm))
        return self

    Offset = offset

    def voxOffset(self, distance_mm: float) -> "Voxels":
        return self.duplicate().offset(distance_mm)

    def double_offset(self, first_mm: float, second_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_DoubleOffset(self.handle, ctypes.c_float(first_mm), ctypes.c_float(second_mm))
        return self

    DoubleOffset = double_offset

    def voxDoubleOffset(self, first_mm: float, second_mm: float) -> "Voxels":
        return self.duplicate().double_offset(first_mm, second_mm)

    def triple_offset(self, distance_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_TripleOffset(self.handle, ctypes.c_float(distance_mm))
        return self

    TripleOffset = triple_offset

    def voxTripleOffset(self, distance_mm: float) -> "Voxels":
        return self.duplicate().triple_offset(distance_mm)

    def Smoothen(self, distance_mm: float) -> "Voxels":
        return self.triple_offset(distance_mm)

    def voxSmoothen(self, distance_mm: float) -> "Voxels":
        return self.voxTripleOffset(distance_mm)

    def OverOffset(self, first_mm: float, final_surface_dist_mm: float = 0.0) -> "Voxels":
        return self.double_offset(first_mm, -(first_mm - final_surface_dist_mm))

    def voxOverOffset(self, first_mm: float, final_surface_dist_mm: float = 0.0) -> "Voxels":
        return self.duplicate().OverOffset(first_mm, final_surface_dist_mm)

    def Fillet(self, rounding_mm: float) -> "Voxels":
        return self.OverOffset(rounding_mm)

    def voxFillet(self, rounding_mm: float) -> "Voxels":
        return self.voxOverOffset(rounding_mm)

    def voxShell(self, neg_offset_mm: float, pos_offset_mm: float | None = None, smooth_inner_mm: float = 0.0) -> "Voxels":
        if pos_offset_mm is None:
            if neg_offset_mm < 0:
                return self.vox_bool_subtract(self.voxOffset(neg_offset_mm))
            return self.voxOffset(neg_offset_mm).vox_bool_subtract(self)
        if neg_offset_mm > pos_offset_mm:
            neg_offset_mm, pos_offset_mm = pos_offset_mm, neg_offset_mm
        inner = self.voxOffset(neg_offset_mm)
        if smooth_inner_mm > 0:
            inner = inner.voxTripleOffset(smooth_inner_mm)
        outer = self.voxOffset(pos_offset_mm)
        return outer.vox_bool_subtract(inner)

    def gaussian(self, size_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_Gaussian(self.handle, ctypes.c_float(size_mm))
        return self

    Gaussian = gaussian

    def median(self, size_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_Median(self.handle, ctypes.c_float(size_mm))
        return self

    Median = median

    def mean(self, size_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_Mean(self.handle, ctypes.c_float(size_mm))
        return self

    Mean = mean

    def render_mesh(self, mesh: Mesh) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_RenderMesh(self.handle, mesh.handle)
        return self

    RenderMesh = render_mesh

    def render_lattice(self, lattice: Lattice) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_RenderLattice(self.handle, lattice.handle)
        return self

    RenderLattice = render_lattice

    def render_implicit(
        self,
        bounds_min: Vector3Like,
        bounds_max: Vector3Like,
        fn: Callable[[tuple[float, float, float]], float],
    ) -> "Voxels":
        self._ensure_open()
        bbox = as_bbox3(bounds_min, bounds_max)

        def _wrapped(vec_ptr: Any) -> float:
            v = vec_ptr.contents
            return float(fn((float(v.x), float(v.y), float(v.z))))

        cb = CallbackImplicitDistance(_wrapped)
        self._implicit_callback_ref = cb
        Library._lib().Voxels_RenderImplicit(self.handle, ctypes.byref(bbox), cb)
        return self

    RenderImplicit = render_implicit

    def intersect_implicit(self, fn: Callable[[tuple[float, float, float]], float]) -> "Voxels":
        self._ensure_open()

        def _wrapped(vec_ptr: Any) -> float:
            v = vec_ptr.contents
            return float(fn((float(v.x), float(v.y), float(v.z))))

        cb = CallbackImplicitDistance(_wrapped)
        self._implicit_callback_ref = cb
        Library._lib().Voxels_IntersectImplicit(self.handle, cb)
        return self

    IntersectImplicit = intersect_implicit

    def voxIntersectImplicit(self, fn: Callable[[tuple[float, float, float]], float]) -> "Voxels":
        return self.duplicate().intersect_implicit(fn)

    def project_z_slice(self, start_mm: float, end_mm: float) -> "Voxels":
        self._ensure_open()
        Library._lib().Voxels_ProjectZSlice(self.handle, ctypes.c_float(start_mm), ctypes.c_float(end_mm))
        return self

    ProjectZSlice = project_z_slice

    def voxProjectZSlice(self, start_mm: float, end_mm: float) -> "Voxels":
        return self.duplicate().project_z_slice(start_mm, end_mm)

    def is_inside(self, point: Vector3Like) -> bool:
        self._ensure_open()
        p = as_vec3(point)
        return bool(Library._lib().Voxels_bIsInside(self.handle, ctypes.byref(p)))

    bIsInside = is_inside

    def is_equal(self, other: "Voxels") -> bool:
        self._ensure_open()
        return bool(Library._lib().Voxels_bIsEqual(self.handle, other.handle))

    bIsEqual = is_equal

    def calculate_properties(self) -> tuple[float, tuple[tuple[float, float, float], tuple[float, float, float]]]:
        self._ensure_open()
        volume = ctypes.c_float(0.0)
        box = BBox3()
        Library._lib().Voxels_CalculateProperties(self.handle, ctypes.byref(volume), ctypes.byref(box))
        return float(volume.value), (vec3_tuple(box.min), vec3_tuple(box.max))

    CalculateProperties = calculate_properties

    def oCalculateBoundingBox(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        with Mesh.from_voxels(self) as mesh:
            return mesh.bounding_box()

    def get_surface_normal(self, point: Vector3Like) -> tuple[float, float, float]:
        self._ensure_open()
        p = as_vec3(point)
        out = Vec3()
        Library._lib().Voxels_GetSurfaceNormal(self.handle, ctypes.byref(p), ctypes.byref(out))
        return vec3_tuple(out)

    vecSurfaceNormal = get_surface_normal

    def closest_point_on_surface(self, search: Vector3Like) -> tuple[bool, tuple[float, float, float]]:
        self._ensure_open()
        s = as_vec3(search)
        out = Vec3()
        ok = bool(Library._lib().Voxels_bClosestPointOnSurface(self.handle, ctypes.byref(s), ctypes.byref(out)))
        return ok, vec3_tuple(out)

    bClosestPointOnSurface = closest_point_on_surface

    def vecClosestPointOnSurface(self, search: Vector3Like) -> tuple[float, float, float]:
        ok, point = self.closest_point_on_surface(search)
        if not ok:
            raise ValueError("Empty voxel field used in ClosestPointOnSurface")
        return point

    def ray_cast_to_surface(self, search: Vector3Like, direction: Vector3Like) -> tuple[bool, tuple[float, float, float]]:
        self._ensure_open()
        s = as_vec3(search)
        d = as_vec3(direction)
        out = Vec3()
        ok = bool(Library._lib().Voxels_bRayCastToSurface(self.handle, ctypes.byref(s), ctypes.byref(d), ctypes.byref(out)))
        return ok, vec3_tuple(out)

    bRayCastToSurface = ray_cast_to_surface

    def vecRayCastToSurface(self, search: Vector3Like, direction: Vector3Like) -> tuple[float, float, float]:
        ok, point = self.ray_cast_to_surface(search, direction)
        if not ok:
            raise ValueError("No intersection with surface in RayCastToSurface")
        return point

    def voxel_dimensions(self) -> VoxelDimensions:
        self._ensure_open()
        xo = ctypes.c_int()
        yo = ctypes.c_int()
        zo = ctypes.c_int()
        xs = ctypes.c_int()
        ys = ctypes.c_int()
        zs = ctypes.c_int()
        Library._lib().Voxels_GetVoxelDimensions(
            self.handle,
            ctypes.byref(xo),
            ctypes.byref(yo),
            ctypes.byref(zo),
            ctypes.byref(xs),
            ctypes.byref(ys),
            ctypes.byref(zs),
        )
        return VoxelDimensions(xo.value, yo.value, zo.value, xs.value, ys.value, zs.value)

    GetVoxelDimensions = voxel_dimensions

    def vecZSliceOrigin(self, z_slice: int = 0) -> tuple[float, float, float]:
        dims = self.voxel_dimensions()
        return Library.voxels_to_mm((dims.x_origin, dims.y_origin, dims.z_origin + z_slice))

    def nSliceCount(self) -> int:
        return self.voxel_dimensions().z_size

    def slice(self, z_slice: int) -> tuple[np.ndarray, float]:
        self._ensure_open()
        dims = self.voxel_dimensions()
        count = dims.x_size * dims.y_size
        buf = (ctypes.c_float * count)()
        background = ctypes.c_float(0.0)
        Library._lib().Voxels_GetSlice(self.handle, int(z_slice), ctypes.cast(buf, ctypes.c_void_p), ctypes.byref(background))
        arr = np.frombuffer(buf, dtype=np.float32).reshape((dims.y_size, dims.x_size))
        return arr.copy(), float(background.value)

    def GetVoxelSlice(self, z_slice: int, mode: str = "signed_distance") -> np.ndarray:
        arr, background = self.slice(z_slice)
        if mode == "signed_distance":
            return arr
        if mode == "black_white":
            return np.where(arr <= 0, 0.0, 1.0).astype(np.float32)
        if mode == "antialiased":
            if background <= 0:
                return np.where(arr <= 0, 0.0, 1.0).astype(np.float32)
            clipped = np.where(arr <= 0, 0.0, np.where(arr > background, 1.0, arr / background))
            return clipped.astype(np.float32)
        raise ValueError("mode must be 'signed_distance', 'black_white', or 'antialiased'")

    def interpolated_slice(self, z_slice: float) -> tuple[np.ndarray, float]:
        self._ensure_open()
        dims = self.voxel_dimensions()
        count = dims.x_size * dims.y_size
        buf = (ctypes.c_float * count)()
        background = ctypes.c_float(0.0)
        Library._lib().Voxels_GetInterpolatedSlice(self.handle, ctypes.c_float(z_slice), ctypes.cast(buf, ctypes.c_void_p), ctypes.byref(background))
        arr = np.frombuffer(buf, dtype=np.float32).reshape((dims.y_size, dims.x_size))
        return arr.copy(), float(background.value)

    def GetInterpolatedVoxelSlice(self, z_slice: float, mode: str = "signed_distance") -> np.ndarray:
        arr, background = self.interpolated_slice(z_slice)
        if mode == "signed_distance":
            return arr
        if mode == "black_white":
            return np.where(arr <= 0, 0.0, 1.0).astype(np.float32)
        if mode == "antialiased":
            if background <= 0:
                return np.where(arr <= 0, 0.0, 1.0).astype(np.float32)
            clipped = np.where(arr <= 0, 0.0, np.where(arr > background, 1.0, arr / background))
            return clipped.astype(np.float32)
        raise ValueError("mode must be 'signed_distance', 'black_white', or 'antialiased'")

    def as_mesh(self) -> Mesh:
        self._ensure_open()
        return Mesh.from_voxels(self)

    mshAsMesh = as_mesh

    def oMetaData(self) -> FieldMetadata:
        return self.metadata

    @staticmethod
    def voxFromVdbFile(strFileName: str) -> "Voxels":
        with OpenVdbFile(strFileName) as oFile:
            if oFile.nFieldCount() == 0:
                raise OSError(f"No fields contained in OpenVDB file {strFileName}")
            for n in range(oFile.nFieldCount()):
                if oFile.eFieldType(n) == OpenVdbFile.FieldType.VOXELS:
                    return oFile.voxGet(n)
        raise OSError(f"No voxel field (openvdb::GRID_LEVEL_SET) found in VDB file {strFileName}")

    def SaveToVdbFile(self, strFileName: str) -> None:
        with OpenVdbFile() as oFile:
            oFile.nAdd(self)
            oFile.SaveToFile(strFileName)

    def voxVoxelizeHollow(self, fThickness: float) -> "Voxels":
        from ._extras import TriangleVoxelization

        with self.mshAsMesh() as msh:
            return TriangleVoxelization.voxVoxelizeHollow(msh, fThickness)

    def oVectorize(self, fLayerHeight: float = 0.0, bUseAbsXYOrigin: bool = False) -> Any:
        from ._extras import ImageGrayScale, PolySlice, PolySliceStack

        voxel_size = float(getattr(Library, "voxel_size_mm", 0.5))
        if fLayerHeight == 0.0:
            fLayerHeight = voxel_size

        f_z_step = float(fLayerHeight) / voxel_size
        dims = self.GetVoxelDimensions()
        origin = (0.0, 0.0)
        if bUseAbsXYOrigin:
            origin = (dims.x_origin * voxel_size, dims.y_origin * voxel_size)

        slices: list[Any] = []
        started = False
        f_last_layer = float(dims.z_size - 1)
        f_z = 0.0
        f_layer_z = float(fLayerHeight)

        while f_z <= f_last_layer:
            arr = self.GetInterpolatedVoxelSlice(f_z, "signed_distance")
            img = ImageGrayScale(dims.x_size, dims.y_size)
            img._data[:, :] = arr[:, :]

            poly_slice = PolySlice.oFromSdf(img, f_layer_z, origin, voxel_size)
            if not started and poly_slice.bIsEmpty():
                f_z += f_z_step
                f_layer_z += fLayerHeight
                continue

            started = True

            poly_slice.Close()
            slices.append(poly_slice)
            f_z += f_z_step
            f_layer_z += fLayerHeight

        if not slices:
            raise ValueError("Voxel field is empty - cannot write .CLI file")

        while slices and slices[-1].bIsEmpty():
            slices.pop()

        if not slices:
            raise ValueError("Voxel field is empty - cannot write .CLI file")

        return PolySliceStack(cast(Sequence[Any], slices))

    def SaveToCliFile(
        self,
        strFileName: str,
        fLayerHeight: float = 0.0,
        eFormat: Any = None,
        bUseAbsXYOrigin: bool = False,
    ) -> None:
        from ._extras import Cli

        use_format = Cli.EFormat.FirstLayerWithContent if eFormat is None else eFormat
        oStack = self.oVectorize(fLayerHeight, bUseAbsXYOrigin)
        Cli.WriteSlicesToCliFile(cast(Any, oStack), strFileName, cast(Any, use_format))


class ScalarField(HandleOwner):
    def __init__(
        self,
        handle: int | ctypes.c_void_p | None = None,
        *,
        copy_from: "ScalarField | None" = None,
        from_voxels: Voxels | None = None,
        fill_value: float | None = None,
        sd_threshold: float = 0.5,
        owns_handle: bool = True,
    ) -> None:
        if handle is None and copy_from is not None:
            handle = Library._lib().ScalarField_hCreateCopy(copy_from.handle)
        elif handle is None and from_voxels is not None and fill_value is None:
            handle = Library._lib().ScalarField_hCreateFromVoxels(from_voxels.handle)
        elif handle is None and from_voxels is not None and fill_value is not None:
            handle = Library._lib().ScalarField_hBuildFromVoxels(from_voxels.handle, ctypes.c_float(fill_value), ctypes.c_float(sd_threshold))
        elif handle is None:
            handle = Library._lib().ScalarField_hCreate()

        if not handle:
            raise PicoGKInvalidHandleError("ScalarField handle creation returned null")
        super().__init__(handle, owns_handle=owns_handle)
        self.metadata = FieldMetadata.from_scalar_field(self)
        self.metadata.set_string("PicoGK.Class", "ScalarField")
        self._traverse_callback_ref: Any = None

    @classmethod
    def from_voxels(cls, voxels: Voxels) -> "ScalarField":
        return cls(from_voxels=voxels)

    @classmethod
    def build_from_voxels(cls, voxels: Voxels, value: float, sd_threshold: float = 0.5) -> "ScalarField":
        return cls(from_voxels=voxels, fill_value=value, sd_threshold=sd_threshold)

    def duplicate(self) -> "ScalarField":
        return ScalarField(copy_from=self)

    def _destroy_native(self) -> None:
        try:
            self.metadata.close()
        finally:
            Library._lib().ScalarField_Destroy(self._handle)

    def is_valid(self) -> bool:
        return bool(Library._lib().ScalarField_bIsValid(self.handle))

    def set_value(self, position: Vector3Like, value: float) -> "ScalarField":
        self._ensure_open()
        p = as_vec3(position)
        Library._lib().ScalarField_SetValue(self.handle, ctypes.byref(p), ctypes.c_float(value))
        return self

    SetValue = set_value

    def get_value(self, position: Vector3Like) -> tuple[bool, float]:
        self._ensure_open()
        p = as_vec3(position)
        out = ctypes.c_float(0.0)
        ok = bool(Library._lib().ScalarField_bGetValue(self.handle, ctypes.byref(p), ctypes.byref(out)))
        return ok, float(out.value)

    bGetValue = get_value

    def remove_value(self, position: Vector3Like) -> bool:
        self._ensure_open()
        p = as_vec3(position)
        return bool(Library._lib().ScalarField_RemoveValue(self.handle, ctypes.byref(p)))

    RemoveValue = remove_value

    def voxel_dimensions(self) -> VoxelDimensions:
        xo = ctypes.c_int()
        yo = ctypes.c_int()
        zo = ctypes.c_int()
        xs = ctypes.c_int()
        ys = ctypes.c_int()
        zs = ctypes.c_int()
        Library._lib().ScalarField_GetVoxelDimensions(self.handle, ctypes.byref(xo), ctypes.byref(yo), ctypes.byref(zo), ctypes.byref(xs), ctypes.byref(ys), ctypes.byref(zs))
        return VoxelDimensions(xo.value, yo.value, zo.value, xs.value, ys.value, zs.value)

    GetVoxelDimensions = voxel_dimensions

    def slice(self, z_slice: int) -> np.ndarray:
        dims = self.voxel_dimensions()
        count = dims.x_size * dims.y_size
        buf = (ctypes.c_float * count)()
        Library._lib().ScalarField_GetSlice(self.handle, int(z_slice), ctypes.cast(buf, ctypes.c_void_p))
        return np.frombuffer(buf, dtype=np.float32).reshape((dims.y_size, dims.x_size)).copy()

    GetVoxelSlice = slice

    def traverse_active(self, callback: Callable[[tuple[float, float, float], float], None]) -> "ScalarField":
        def _wrapped(vec_ptr: Any, value: float) -> None:
            vec = vec_ptr.contents
            callback((float(vec.x), float(vec.y), float(vec.z)), float(value))
        self._traverse_callback_ref = CallbackScalarFieldTraverse(_wrapped)
        Library._lib().ScalarField_TraverseActive(self.handle, self._traverse_callback_ref)
        return self

    TraverseActive = traverse_active

    def signed_distance(self, position: Vector3Like) -> float:
        ok, value = self.get_value(position)
        return float(value if ok else 0.0) * Library.voxel_size_mm

    fSignedDistance = signed_distance

    def bounding_box(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        dims = self.voxel_dimensions()
        return (
            Library.voxels_to_mm((dims.x_origin, dims.y_origin, dims.z_origin)),
            Library.voxels_to_mm((dims.x_origin + dims.x_size, dims.y_origin + dims.y_size, dims.z_origin + dims.z_size)),
        )

    oBoundingBox = bounding_box

    def oMetaData(self) -> FieldMetadata:
        return self.metadata


class VectorField(HandleOwner):
    def __init__(
        self,
        handle: int | ctypes.c_void_p | None = None,
        *,
        copy_from: "VectorField | None" = None,
        from_voxels: Voxels | None = None,
        fill_value: Vector3Like | None = None,
        sd_threshold: float = 0.5,
        owns_handle: bool = True,
    ) -> None:
        if handle is None and copy_from is not None:
            handle = Library._lib().VectorField_hCreateCopy(copy_from.handle)
        elif handle is None and from_voxels is not None and fill_value is None:
            handle = Library._lib().VectorField_hCreateFromVoxels(from_voxels.handle)
        elif handle is None and from_voxels is not None and fill_value is not None:
            fill = as_vec3(fill_value)
            handle = Library._lib().VectorField_hBuildFromVoxels(from_voxels.handle, ctypes.byref(fill), ctypes.c_float(sd_threshold))
        elif handle is None:
            handle = Library._lib().VectorField_hCreate()

        if not handle:
            raise PicoGKInvalidHandleError("VectorField handle creation returned null")
        super().__init__(handle, owns_handle=owns_handle)
        self.metadata = FieldMetadata.from_vector_field(self)
        self.metadata.set_string("PicoGK.Class", "VectorField")
        self._traverse_callback_ref: Any = None

    @classmethod
    def from_voxels(cls, voxels: Voxels) -> "VectorField":
        return cls(from_voxels=voxels)

    @classmethod
    def build_from_voxels(cls, voxels: Voxels, value: Vector3Like, sd_threshold: float = 0.5) -> "VectorField":
        return cls(from_voxels=voxels, fill_value=value, sd_threshold=sd_threshold)

    def duplicate(self) -> "VectorField":
        return VectorField(copy_from=self)

    def _destroy_native(self) -> None:
        try:
            self.metadata.close()
        finally:
            Library._lib().VectorField_Destroy(self._handle)

    def is_valid(self) -> bool:
        return bool(Library._lib().VectorField_bIsValid(self.handle))

    def set_value(self, position: Vector3Like, value: Vector3Like) -> "VectorField":
        self._ensure_open()
        p = as_vec3(position)
        v = as_vec3(value)
        Library._lib().VectorField_SetValue(self.handle, ctypes.byref(p), ctypes.byref(v))
        return self

    SetValue = set_value

    def get_value(self, position: Vector3Like) -> tuple[bool, tuple[float, float, float]]:
        self._ensure_open()
        p = as_vec3(position)
        out = Vec3()
        ok = bool(Library._lib().VectorField_bGetValue(self.handle, ctypes.byref(p), ctypes.byref(out)))
        return ok, vec3_tuple(out)

    bGetValue = get_value

    def remove_value(self, position: Vector3Like) -> bool:
        self._ensure_open()
        p = as_vec3(position)
        return bool(Library._lib().VectorField_RemoveValue(self.handle, ctypes.byref(p)))

    RemoveValue = remove_value

    def traverse_active(self, callback: Callable[[tuple[float, float, float], tuple[float, float, float]], None]) -> "VectorField":
        def _wrapped(pos_ptr: Any, val_ptr: Any) -> None:
            pos = pos_ptr.contents
            val = val_ptr.contents
            callback((float(pos.x), float(pos.y), float(pos.z)), (float(val.x), float(val.y), float(val.z)))
        self._traverse_callback_ref = CallbackVectorFieldTraverse(_wrapped)
        Library._lib().VectorField_TraverseActive(self.handle, self._traverse_callback_ref)
        return self

    TraverseActive = traverse_active

    def oMetaData(self) -> FieldMetadata:
        return self.metadata


class OpenVdbFile(HandleOwner):
    class FieldType(IntEnum):
        UNSUPPORTED = -1
        VOXELS = 0
        SCALAR_FIELD = 1
        VECTOR_FIELD = 2

    def __init__(self, path: str | None = None, handle: int | ctypes.c_void_p | None = None, *, owns_handle: bool = True) -> None:
        if handle is None and path is None:
            handle = Library._lib().VdbFile_hCreate()
        elif handle is None and path is not None:
            handle = Library._lib().VdbFile_hCreateFromFile(path.encode("utf-8"))
        if not handle:
            raise PicoGKInvalidHandleError("VdbFile creation returned null")
        super().__init__(handle, owns_handle=owns_handle)

    def _destroy_native(self) -> None:
        Library._lib().VdbFile_Destroy(self._handle)

    def save(self, path: str) -> None:
        self._ensure_open()
        for index in range(self.field_count()):
            field = cast(Any, self.xField(index))
            field.oMetaData().SetValue("PicoGK.Library", Library.name())
            field.oMetaData().SetValue("PicoGK.Version", Library.version())
            field.oMetaData().SetValue("PicoGK.VoxelSize", Library.voxel_size_mm / 1000.0)
        ok = bool(Library._lib().VdbFile_bSaveToFile(self.handle, path.encode("utf-8")))
        if not ok:
            raise IOError(f"Failed to save VDB: {path}")

    SaveToFile = save

    def field_count(self) -> int:
        self._ensure_open()
        return int(Library._lib().VdbFile_nFieldCount(self.handle))

    nFieldCount = field_count

    def field_name(self, index: int) -> str:
        self._ensure_open()
        buf = ctypes.create_string_buffer(STRING_LENGTH)
        Library._lib().VdbFile_GetFieldName(self.handle, int(index), buf)
        return buf.value.decode("utf-8")

    strFieldName = field_name

    def field_type(self, index: int) -> "OpenVdbFile.FieldType":
        self._ensure_open()
        return OpenVdbFile.FieldType(int(Library._lib().VdbFile_nFieldType(self.handle, int(index))))

    eFieldType = field_type

    def strFieldType(self, index: int) -> str:
        mapping = {
            self.FieldType.UNSUPPORTED: "Unsupported",
            self.FieldType.VOXELS: "Voxels",
            self.FieldType.SCALAR_FIELD: "ScalarField",
            self.FieldType.VECTOR_FIELD: "VectorField",
        }
        return mapping.get(self.field_type(index), f"Unknown #{self.field_type(index).value}")

    def add_voxels(self, voxels: Voxels, field_name: str = "") -> int:
        self._ensure_open()
        if not field_name:
            field_name = f"PicoGK.Voxels.{self.field_count()}"
        return int(Library._lib().VdbFile_nAddVoxels(self.handle, field_name.encode("utf-8"), voxels.handle))

    def add_scalar_field(self, field: ScalarField, field_name: str = "") -> int:
        self._ensure_open()
        if not field_name:
            field_name = f"PicoGK.ScalarField.{self.field_count()}"
        return int(Library._lib().VdbFile_nAddScalarField(self.handle, field_name.encode("utf-8"), field.handle))

    def add_vector_field(self, field: VectorField, field_name: str = "") -> int:
        self._ensure_open()
        if not field_name:
            field_name = f"PicoGK.VectorField.{self.field_count()}"
        return int(Library._lib().VdbFile_nAddVectorField(self.handle, field_name.encode("utf-8"), field.handle))

    def nAdd(self, field: object, field_name: str = "") -> int:
        if isinstance(field, Voxels):
            return self.add_voxels(field, field_name)
        if isinstance(field, ScalarField):
            return self.add_scalar_field(field, field_name)
        if isinstance(field, VectorField):
            return self.add_vector_field(field, field_name)
        raise TypeError("nAdd expects Voxels, ScalarField, or VectorField")

    def get_voxels(self, index: int) -> Voxels:
        self._ensure_open()
        h = Library._lib().VdbFile_hGetVoxels(self.handle, int(index))
        if not h:
            raise PicoGKInvalidHandleError(f"No voxel field at index {index}")
        return Voxels(handle=h)

    def voxGet(self, index_or_name: int | str) -> Voxels:
        if isinstance(index_or_name, int):
            return self.get_voxels(index_or_name)
        for index in range(self.field_count()):
            if self.field_name(index).lower() == index_or_name.lower():
                return self.get_voxels(index)
        raise KeyError(index_or_name)

    def get_scalar_field(self, index: int) -> ScalarField:
        self._ensure_open()
        h = Library._lib().VdbFile_hGetScalarField(self.handle, int(index))
        if not h:
            raise PicoGKInvalidHandleError(f"No scalar field at index {index}")
        return ScalarField(handle=h)

    def oGetScalarField(self, index_or_name: int | str) -> ScalarField:
        if isinstance(index_or_name, int):
            return self.get_scalar_field(index_or_name)
        for index in range(self.field_count()):
            if self.field_name(index).lower() == index_or_name.lower():
                return self.get_scalar_field(index)
        raise KeyError(index_or_name)

    def get_vector_field(self, index: int) -> VectorField:
        self._ensure_open()
        h = Library._lib().VdbFile_hGetVectorField(self.handle, int(index))
        if not h:
            raise PicoGKInvalidHandleError(f"No vector field at index {index}")
        return VectorField(handle=h)

    def oGetVectorField(self, index_or_name: int | str) -> VectorField:
        if isinstance(index_or_name, int):
            return self.get_vector_field(index_or_name)
        for index in range(self.field_count()):
            if self.field_name(index).lower() == index_or_name.lower():
                return self.get_vector_field(index)
        raise KeyError(index_or_name)

    def xField(self, index: int) -> object:
        field_type = self.field_type(index)
        if field_type == self.FieldType.VOXELS:
            return self.get_voxels(index)
        if field_type == self.FieldType.SCALAR_FIELD:
            return self.get_scalar_field(index)
        if field_type == self.FieldType.VECTOR_FIELD:
            return self.get_vector_field(index)
        raise ValueError(f"Unsupported field at index {index}")

    def bIsPicoGKCompatible(self) -> bool:
        if self.field_count() < 1:
            return False
        field = cast(Any, self.xField(0))
        ok, _ = field.oMetaData().bGetValueAt("PicoGK.VoxelSize")
        return ok

    def fPicoGKVoxelSizeMM(self) -> float:
        if self.field_count() < 1:
            return 0.0
        field = cast(Any, self.xField(0))
        ok, value = field.oMetaData().bGetValueAt("PicoGK.VoxelSize")
        if ok and isinstance(value, (float, int)) and float(value) > 0:
            return float(value) * 1000.0
        return 0.0


class PolyLine(HandleOwner):
    def __init__(self, color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)) -> None:
        clr = ColorFloat(*[float(c) for c in color])
        h = Library._lib().PolyLine_hCreate(ctypes.byref(clr))
        if not h:
            raise PicoGKInvalidHandleError("PolyLine_hCreate returned null")
        super().__init__(h)
        self._bbox_min = [float("inf"), float("inf"), float("inf")]
        self._bbox_max = [float("-inf"), float("-inf"), float("-inf")]

    def _destroy_native(self) -> None:
        Library._lib().PolyLine_Destroy(self._handle)

    def add_vertex(self, xyz: Vector3Like) -> int:
        self._ensure_open()
        v = as_vec3(xyz)
        self._bbox_min[0] = min(self._bbox_min[0], float(v.x))
        self._bbox_min[1] = min(self._bbox_min[1], float(v.y))
        self._bbox_min[2] = min(self._bbox_min[2], float(v.z))
        self._bbox_max[0] = max(self._bbox_max[0], float(v.x))
        self._bbox_max[1] = max(self._bbox_max[1], float(v.y))
        self._bbox_max[2] = max(self._bbox_max[2], float(v.z))
        return int(Library._lib().PolyLine_nAddVertex(self.handle, ctypes.byref(v)))

    nAddVertex = add_vertex

    def Add(self, vertices: Sequence[Vector3Like]) -> "PolyLine":
        for vertex in vertices:
            self.add_vertex(vertex)
        return self

    def vertex_count(self) -> int:
        self._ensure_open()
        return int(Library._lib().PolyLine_nVertexCount(self.handle))

    nVertexCount = vertex_count

    def get_vertex(self, index: int) -> tuple[float, float, float]:
        self._ensure_open()
        v = Vec3()
        Library._lib().PolyLine_GetVertex(self.handle, int(index), ctypes.byref(v))
        return vec3_tuple(v)

    vecVertexAt = get_vertex

    def get_color(self) -> tuple[float, float, float, float]:
        clr = ColorFloat()
        Library._lib().PolyLine_GetColor(self.handle, ctypes.byref(clr))
        return (float(clr.r), float(clr.g), float(clr.b), float(clr.a))

    GetColor = get_color

    def bounding_box(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        if self.vertex_count() == 0:
            return ((float("inf"), float("inf"), float("inf")), (float("-inf"), float("-inf"), float("-inf")))
        return (
            (self._bbox_min[0], self._bbox_min[1], self._bbox_min[2]),
            (self._bbox_max[0], self._bbox_max[1], self._bbox_max[2]),
        )

    oBoundingBox = bounding_box

    def AddArrow(self, size_mm: float = 1.0, direction: Vector3Like | None = None) -> "PolyLine":
        if self.vertex_count() < 1:
            return self
        if direction is None:
            if self.vertex_count() < 2:
                return self
            start = self.get_vertex(self.vertex_count() - 2)
            end = self.get_vertex(self.vertex_count() - 1)
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            dz = end[2] - start[2]
        else:
            dx, dy, dz = direction
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length <= 1e-12:
            return self
        dx /= length
        dy /= length
        dz /= length
        init = (1.0, 0.0, 0.0) if abs(dx) < 0.999 else (0.0, 1.0, 0.0)
        ux = dy * init[2] - dz * init[1]
        uy = dz * init[0] - dx * init[2]
        uz = dx * init[1] - dy * init[0]
        ul = math.sqrt(ux * ux + uy * uy + uz * uz)
        ux, uy, uz = ux / ul, uy / ul, uz / ul
        vx = dy * uz - dz * uy
        vy = dz * ux - dx * uz
        vz = dx * uy - dy * ux
        tip = self.get_vertex(self.vertex_count() - 1)
        base = (tip[0] - dx * size_mm, tip[1] - dy * size_mm, tip[2] - dz * size_mm)
        self.add_vertex((base[0] + ux * size_mm / 2, base[1] + uy * size_mm / 2, base[2] + uz * size_mm / 2))
        self.add_vertex((base[0] - ux * size_mm / 2, base[1] - uy * size_mm / 2, base[2] - uz * size_mm / 2))
        self.add_vertex(tip)
        self.add_vertex((base[0] + vx * size_mm / 2, base[1] + vy * size_mm / 2, base[2] + vz * size_mm / 2))
        self.add_vertex((base[0] - vx * size_mm / 2, base[1] - vy * size_mm / 2, base[2] - vz * size_mm / 2))
        self.add_vertex(tip)
        return self

    def AddCross(self, size_mm: float = 1.0) -> "PolyLine":
        if self.vertex_count() < 1:
            return self
        cx, cy, cz = self.get_vertex(self.vertex_count() - 1)
        self.add_vertex((cx + size_mm, cy, cz))
        self.add_vertex((cx - size_mm, cy, cz))
        self.add_vertex((cx, cy, cz))
        self.add_vertex((cx, cy + size_mm, cz))
        self.add_vertex((cx, cy - size_mm, cz))
        self.add_vertex((cx, cy, cz))
        self.add_vertex((cx, cy, cz + size_mm))
        self.add_vertex((cx, cy, cz - size_mm))
        self.add_vertex((cx, cy, cz))
        return self


class IViewerAction(Protocol):
    def Do(self, viewer: "VedoViewer") -> None:
        ...


class IKeyHandler(Protocol):
    def bHandleEvent(
        self,
        viewer: "VedoViewer",
        eKey: str,
        bPressed: bool,
        bShift: bool,
        bCtrl: bool,
        bAlt: bool,
        bCmd: bool,
    ) -> bool:
        ...


class KeyAction:
    def __init__(
        self,
        xAction: IViewerAction,
        eKey: str,
        bPressed: bool = False,
        bShift: bool = False,
        bCtrl: bool = False,
        bAlt: bool = False,
        bCmd: bool = False,
    ) -> None:
        self._action = xAction
        self._key = str(eKey).lower()
        self._pressed = bool(bPressed)
        self._shift = bool(bShift)
        self._ctrl = bool(bCtrl)
        self._alt = bool(bAlt)
        self._cmd = bool(bCmd)

    def bKeyEquals(
        self,
        eKey: str,
        bPressed: bool,
        bShift: bool,
        bCtrl: bool,
        bAlt: bool,
        bCmd: bool,
    ) -> bool:
        return (
            self._key == str(eKey).lower()
            and self._pressed == bool(bPressed)
            and self._shift == bool(bShift)
            and self._ctrl == bool(bCtrl)
            and self._alt == bool(bAlt)
            and self._cmd == bool(bCmd)
        )

    def Do(self, viewer: "VedoViewer") -> None:
        self._action.Do(viewer)


class KeyHandler:
    def __init__(self) -> None:
        self._actions: list[KeyAction] = []

    def AddAction(self, action: KeyAction) -> None:
        self._actions.insert(0, action)

    def bHandleEvent(
        self,
        viewer: "VedoViewer",
        eKey: str,
        bPressed: bool,
        bShift: bool,
        bCtrl: bool,
        bAlt: bool,
        bCmd: bool,
    ) -> bool:
        for action in self._actions:
            if action.bKeyEquals(eKey, bPressed, bShift, bCtrl, bAlt, bCmd):
                action.Do(viewer)
                return True
        return False


class RotateToNextRoundAngleAction:
    class EDir(IntEnum):
        Dir_Down = 0
        Dir_Up = 1
        Dir_Left = 2
        Dir_Right = 3

    def __init__(self, eDir: "RotateToNextRoundAngleAction.EDir") -> None:
        self._dir = eDir

    def Do(self, viewer: "VedoViewer") -> None:
        step = 15.0
        if self._dir == self.EDir.Dir_Left:
            viewer.AdjustViewAngles(-step, 0.0)
        elif self._dir == self.EDir.Dir_Right:
            viewer.AdjustViewAngles(step, 0.0)
        elif self._dir == self.EDir.Dir_Up:
            viewer.AdjustViewAngles(0.0, step)
        else:
            viewer.AdjustViewAngles(0.0, -step)


class AnimGroupMatrixRotate:
    def __init__(
        self,
        oViewer: "VedoViewer",
        nGroup: int,
        matInit: Sequence[float],
        vecAxis: Sequence[float],
        fDegrees: float,
    ) -> None:
        if len(matInit) != 16:
            raise ValueError("matInit must contain 16 values")
        self._viewer = oViewer
        self._group = int(nGroup)
        self._mat_init = np.array(matInit, dtype=np.float64).reshape((4, 4))
        axis = np.array(vecAxis, dtype=np.float64)
        n = float(np.linalg.norm(axis))
        if n <= 1e-12:
            raise ValueError("vecAxis must be non-zero")
        self._axis = axis / n
        self._degrees = float(fDegrees)

    def Do(self, fFactor: float) -> None:
        theta = math.radians(float(fFactor) * self._degrees)
        x, y, z = self._axis.tolist()
        c = math.cos(theta)
        s = math.sin(theta)
        t = 1.0 - c
        rot = np.array(
            [
                [t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0.0],
                [t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0.0],
                [t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        mat = self._mat_init @ rot
        self._viewer.SetGroupMatrix(self._group, tuple(float(v) for v in mat.reshape(-1)))


class AnimViewRotate:
    def __init__(self, oViewer: "VedoViewer", vecFrom: Sequence[float], vecTo: Sequence[float]) -> None:
        if len(vecFrom) < 2 or len(vecTo) < 2:
            raise ValueError("vecFrom and vecTo must contain at least 2 values")
        self._viewer = oViewer
        self._from = (float(vecFrom[0]), float(vecFrom[1]))
        self._to = (float(vecTo[0]), float(vecTo[1]))

    def Do(self, fFactor: float) -> None:
        factor = float(fFactor)
        orbit = self._from[0] + ((self._to[0] - self._from[0]) * factor)
        elevation = self._from[1] + ((self._to[1] - self._from[1]) * factor)
        self._viewer.SetViewAngles(orbit, elevation)


@dataclass
class _TimeLapseState:
    interval_ms: float
    path: Path
    file_name: str
    current_frame: int
    paused: bool
    next_due_ms: float

    @classmethod
    def create(
        cls,
        fIntervalInMilliseconds: float,
        strPath: str,
        strFileName: str,
        nStartFrame: int,
        bPaused: bool,
    ) -> "_TimeLapseState":
        now = time.perf_counter() * 1000.0
        path = Path(strPath)
        path.mkdir(parents=True, exist_ok=True)
        return cls(
            interval_ms=float(fIntervalInMilliseconds),
            path=path,
            file_name=strFileName,
            current_frame=int(nStartFrame),
            paused=bool(bPaused),
            next_due_ms=now + float(fIntervalInMilliseconds),
        )

    def Pause(self) -> None:
        self.paused = True

    def Resume(self) -> None:
        self.paused = False
        self.next_due_ms = (time.perf_counter() * 1000.0) + self.interval_ms

    def bDue(self) -> tuple[bool, str]:
        if self.paused:
            return False, ""
        now = time.perf_counter() * 1000.0
        if now < self.next_due_ms:
            return False, ""
        frame_path = self.path / f"{self.file_name}{self.current_frame:05d}.png"
        self.current_frame += 1
        self.next_due_ms = now + self.interval_ms
        return True, str(frame_path)


class VedoViewer:
    """C#-style viewer facade adapted to vedo with a thread-safe command queue."""

    def __init__(self, title: str = "PicoGK", offscreen: bool = False) -> None:
        self._plotter = vedo.Plotter(title=title, interactive=False, offscreen=offscreen)
        self._queue: Queue[tuple[str, object]] = Queue()
        self._running = False
        self._closed = False
        self._thread: Optional[threading.Thread] = None
        self._actors: dict[int, object] = {}
        self._groups: dict[int, set[int]] = {}
        self._object_to_actor: dict[int, int] = {}
        self._group_visible: dict[int, bool] = {}
        self._group_static: dict[int, bool] = {}
        self._group_material: dict[int, tuple[tuple[float, float, float, float], float, float]] = {}
        self._group_matrix: dict[int, tuple[float, ...]] = {}
        self._next_actor_id = 1
        self._idle = True
        self._light_setup_raw: tuple[bytes, bytes] | None = None
        self._timelapse: _TimeLapseState | None = None
        self._animations: list[Any] = []
        self._key_handlers: list[IKeyHandler] = []
        self._key_callback_handle: object | None = None

        self.m_fElevation = 30.0
        self.m_fOrbit = 45.0
        self.m_fFov = 45.0
        self.m_fZoom = 1.0
        self.m_bPerspective = True

        self._default_key_handler = KeyHandler()
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Down), "Down"))
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Up), "Up"))
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Left), "Left"))
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Right), "Right"))
        self.AddKeyHandler(self._default_key_handler)

    def _enqueue(self, cmd: str, payload: object = None) -> None:
        self._idle = False
        self._queue.put((cmd, payload))

    def _stop_loop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _is_visible(self, actor: object) -> bool:
        visible_fn = getattr(actor, "is_visible", None)
        if callable(visible_fn):
            try:
                return bool(visible_fn())
            except Exception:
                return True
        return True

    def _set_actor_visible(self, actor: object, visible: bool) -> None:
        if visible:
            on_fn = getattr(actor, "on", None)
            if callable(on_fn):
                on_fn()
                return
        else:
            off_fn = getattr(actor, "off", None)
            if callable(off_fn):
                off_fn()
                return

        set_vis = getattr(actor, "SetVisibility", None)
        if callable(set_vis):
            set_vis(bool(visible))

    def _set_actor_pickable(self, actor: object, pickable: bool) -> None:
        pickable_fn = getattr(actor, "pickable", None)
        if callable(pickable_fn):
            try:
                pickable_fn(bool(pickable))
                return
            except Exception:
                pass
        set_pickable = getattr(actor, "SetPickable", None)
        if callable(set_pickable):
            set_pickable(bool(pickable))

    def _apply_matrix_points(self, actor: object, mat: tuple[float, ...]) -> None:
        if len(mat) != 16:
            raise ValueError("mat must contain 16 values")
        pts_fn = getattr(actor, "points", None)
        if not callable(pts_fn):
            return
        try:
            points = np.asarray(pts_fn(), dtype=np.float64)
        except Exception:
            return
        if points.ndim != 2 or points.shape[0] == 0 or points.shape[1] != 3:
            return
        m = np.array(mat, dtype=np.float64).reshape((4, 4))
        homo = np.hstack([points, np.ones((points.shape[0], 1), dtype=np.float64)])
        transformed = (homo @ m.T)[:, :3]
        pts_fn(transformed.astype(np.float32))

    def _apply_group_style_to_actor(self, actor_id: int) -> None:
        actor = self._actors.get(actor_id)
        if actor is None:
            return
        group_id = None
        for gid, members in self._groups.items():
            if actor_id in members:
                group_id = gid
                break
        if group_id is None:
            return

        visible = self._group_visible.get(group_id)
        if visible is not None:
            self._set_actor_visible(actor, visible)

        static = self._group_static.get(group_id)
        if static is not None:
            self._set_actor_pickable(actor, not static)

        material = self._group_material.get(group_id)
        if material is not None:
            clr, _metallic, _roughness = material
            color_fn = getattr(actor, "c", None)
            if callable(color_fn):
                color_fn((clr[0], clr[1], clr[2]))
            alpha_fn = getattr(actor, "alpha", None)
            if callable(alpha_fn):
                alpha_fn(clr[3])

        matrix = self._group_matrix.get(group_id)
        if matrix is not None:
            self._apply_matrix_points(actor, matrix)

    def _active_bounds(self) -> tuple[float, float, float, float, float, float] | None:
        items: list[tuple[float, float, float, float, float, float]] = []
        for actor in self._actors.values():
            if not self._is_visible(actor):
                continue
            bounds_fn = getattr(actor, "bounds", None)
            if not callable(bounds_fn):
                continue
            try:
                raw_bounds = cast(Sequence[object], bounds_fn())
                b = tuple(float(cast(Any, v)) for v in raw_bounds)
            except Exception:
                continue
            if len(b) == 6:
                items.append(cast(tuple[float, float, float, float, float, float], b))
        if not items:
            return None
        xmin = min(v[0] for v in items)
        xmax = max(v[1] for v in items)
        ymin = min(v[2] for v in items)
        ymax = max(v[3] for v in items)
        zmin = min(v[4] for v in items)
        zmax = max(v[5] for v in items)
        return (xmin, xmax, ymin, ymax, zmin, zmax)

    def _update_camera(self) -> None:
        bounds = self._active_bounds()
        if bounds is None:
            return
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        cx = (xmin + xmax) * 0.5
        cy = (ymin + ymax) * 0.5
        cz = (zmin + zmax) * 0.5
        rx = max(1e-3, xmax - xmin)
        ry = max(1e-3, ymax - ymin)
        rz = max(1e-3, zmax - zmin)
        radius = max(rx, ry, rz) * 1.5 * max(1e-3, self.m_fZoom)

        orbit = math.radians(self.m_fOrbit)
        elev = math.radians(self.m_fElevation)
        cos_e = math.cos(elev)
        ex = cx + (math.cos(orbit) * cos_e * radius)
        ey = cy + (math.sin(orbit) * cos_e * radius)
        ez = cz + (math.sin(elev) * radius)

        cam = self._plotter.camera
        cam.SetPosition(ex, ey, ez)
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetViewUp(0.0, 0.0, 1.0)
        cam.SetViewAngle(float(self.m_fFov))
        if self.m_bPerspective:
            cam.ParallelProjectionOff()
        else:
            cam.ParallelProjectionOn()

    def _pulse_animations(self) -> bool:
        if not self._animations:
            return False
        current = time.perf_counter() - self._anim_start
        keep: list[Any] = []
        changed = False
        for anim in self._animations:
            try:
                alive = bool(anim.bAnimate(float(current)))
            except Exception:
                alive = False
            changed = True
            if alive:
                keep.append(anim)
        self._animations = keep
        return changed

    def _capture_timelapse_if_due(self) -> bool:
        if self._timelapse is None:
            return False
        due, path = self._timelapse.bDue()
        if not due:
            return False
        self._plotter.screenshot(path)
        return True

    def _render(self) -> None:
        self._update_camera()
        self._plotter.render(resetcam=False)

    def _next_id(self) -> int:
        out = self._next_actor_id
        self._next_actor_id += 1
        return out

    def _process_command(self, cmd: str, payload: object) -> None:
        if cmd == "close":
            self._running = False
            self._closed = True
            return

        if cmd == "add_actor":
            actor_id, actor, group_id, object_key = cast(tuple[int, object, int, int], payload)
            self._actors[actor_id] = self._plotter.add(actor)
            self._groups.setdefault(group_id, set()).add(actor_id)
            if object_key >= 0:
                self._object_to_actor[object_key] = actor_id
            self._apply_group_style_to_actor(actor_id)
            self._render()
            return

        if cmd == "remove_actor":
            actor_id = int(cast(int, payload))
            actor = self._actors.pop(actor_id, None)
            if actor is not None:
                self._plotter.remove(actor)
            for members in self._groups.values():
                members.discard(actor_id)
            keys = [k for k, v in self._object_to_actor.items() if v == actor_id]
            for k in keys:
                self._object_to_actor.pop(k, None)
            self._render()
            return

        if cmd == "remove_object":
            object_key = int(cast(int, payload))
            actor_id = self._object_to_actor.pop(object_key, None)
            if actor_id is not None:
                self._process_command("remove_actor", actor_id)
            return

        if cmd == "remove_all":
            for actor in list(self._actors.values()):
                self._plotter.remove(actor)
            self._actors.clear()
            self._groups.clear()
            self._object_to_actor.clear()
            self._render()
            return

        if cmd == "render":
            self._render()
            return

        if cmd == "set_group_visible":
            group_id, visible = cast(tuple[int, bool], payload)
            self._group_visible[group_id] = bool(visible)
            for actor_id in self._groups.get(group_id, set()):
                actor = self._actors.get(actor_id)
                if actor is not None:
                    self._set_actor_visible(actor, visible)
            self._render()
            return

        if cmd == "set_group_static":
            group_id, static = cast(tuple[int, bool], payload)
            self._group_static[group_id] = bool(static)
            for actor_id in self._groups.get(group_id, set()):
                actor = self._actors.get(actor_id)
                if actor is not None:
                    self._set_actor_pickable(actor, not static)
            return

        if cmd == "set_group_material":
            group_id, clr, metallic, roughness = cast(tuple[int, tuple[float, float, float, float], float, float], payload)
            self._group_material[group_id] = (clr, metallic, roughness)
            for actor_id in self._groups.get(group_id, set()):
                self._apply_group_style_to_actor(actor_id)
            self._render()
            return

        if cmd == "set_group_matrix":
            group_id, mat = cast(tuple[int, tuple[float, ...]], payload)
            self._group_matrix[group_id] = mat
            for actor_id in self._groups.get(group_id, set()):
                self._apply_group_style_to_actor(actor_id)
            self._render()
            return

        if cmd == "set_background":
            r, g, b = cast(tuple[float, float, float], payload)
            self._plotter.background((r, g, b))
            self._render()
            return

        if cmd == "set_view":
            orbit, elevation = cast(tuple[float, float], payload)
            self.m_fOrbit = float(orbit)
            self.m_fElevation = float(max(-89.9, min(89.9, elevation)))
            self._render()
            return

        if cmd == "set_fov":
            self.m_fFov = float(cast(float, payload))
            self._render()
            return

        if cmd == "set_zoom":
            self.m_fZoom = float(max(0.05, cast(float, payload)))
            self._render()
            return

        if cmd == "set_perspective":
            self.m_bPerspective = bool(cast(bool, payload))
            self._render()
            return

        if cmd == "screenshot":
            path = str(cast(str, payload))
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._plotter.screenshot(path)
            return

        if cmd == "log_stats":
            bounds = self._active_bounds()
            print(f"Viewer stats: actors={len(self._actors)} groups={len(self._groups)} queue={self._queue.qsize()} idle={self._idle}")
            if bounds is not None:
                print(f"Bounds: x[{bounds[0]:.3f},{bounds[1]:.3f}] y[{bounds[2]:.3f},{bounds[3]:.3f}] z[{bounds[4]:.3f},{bounds[5]:.3f}]")
            return

        if cmd == "light_setup":
            self._light_setup_raw = cast(tuple[bytes, bytes], payload)
            return

    def _drain_queue(self) -> None:
        drained = False
        while True:
            try:
                cmd, payload = self._queue.get_nowait()
            except Empty:
                break
            drained = True
            self._process_command(cmd, payload)
        if drained:
            self._idle = self._queue.empty()

    def _loop(self) -> None:
        while self._running:
            updated = False
            try:
                cmd, payload = self._queue.get(timeout=0.03)
                self._process_command(cmd, payload)
                updated = True
            except Empty:
                pass
            if self._pulse_animations():
                updated = True
            if self._capture_timelapse_if_due():
                updated = True
            if updated:
                self._render()
            self._idle = self._queue.empty()

    def _color_tuple(self, clr: ColorFloat | Sequence[float]) -> tuple[float, float, float, float]:
        if isinstance(clr, ColorFloat):
            return (float(clr.r), float(clr.g), float(clr.b), float(clr.a))
        if len(clr) == 3:
            return (float(clr[0]), float(clr[1]), float(clr[2]), 1.0)
        if len(clr) == 4:
            return (float(clr[0]), float(clr[1]), float(clr[2]), float(clr[3]))
        raise ValueError("Color must be (r,g,b) or (r,g,b,a)")

    def _make_mesh_actor(self, mesh: Mesh, color: str | Sequence[float] = "lightgray") -> object:
        vertices, triangles = mesh.to_numpy()
        faces = np.hstack([np.full((triangles.shape[0], 1), 3, dtype=np.int32), triangles]).astype(np.int32)
        actor = VedoMesh([vertices, faces])
        if isinstance(color, str):
            actor = actor.c(color)
        else:
            clr = self._color_tuple(cast(Sequence[float], color))
            actor = actor.c((clr[0], clr[1], clr[2])).alpha(clr[3])
        return actor

    def _make_polyline_actor(self, poly: PolyLine) -> object:
        n = poly.vertex_count()
        color = poly.get_color()
        if n <= 0:
            actor = vedo.Points(np.array([[0.0, 0.0, 0.0]], dtype=np.float32), c=(color[0], color[1], color[2]), r=1)
            alpha_fn = getattr(actor, "alpha", None)
            if callable(alpha_fn):
                alpha_fn(color[3])
            return actor
        pts = np.array([poly.get_vertex(i) for i in range(n)], dtype=np.float32)
        if n == 1:
            actor = vedo.Points(pts, c=(color[0], color[1], color[2]), r=8)
            alpha_fn = getattr(actor, "alpha", None)
            if callable(alpha_fn):
                alpha_fn(color[3])
            return actor
        actor = vedo.Line(pts, lw=2)
        color_fn = getattr(actor, "c", None)
        if callable(color_fn):
            color_fn((color[0], color[1], color[2]))
        alpha_fn = getattr(actor, "alpha", None)
        if callable(alpha_fn):
            alpha_fn(color[3])
        return actor

    def Add(self, xObject: object, nGroupID: int = 0) -> int:
        if isinstance(xObject, Mesh):
            return self.add_mesh(xObject, nGroupID=nGroupID)
        if isinstance(xObject, Voxels):
            return self.add_voxels(xObject, nGroupID=nGroupID)
        if isinstance(xObject, PolyLine):
            return self.add_polyline(xObject, nGroupID=nGroupID)
        raise TypeError("Add expects Mesh, Voxels, or PolyLine")

    def add_mesh(self, mesh: Mesh, color: str | Sequence[float] = "lightgray", nGroupID: int = 0) -> int:
        actor_id = self._next_id()
        actor = self._make_mesh_actor(mesh, color)
        self._enqueue("add_actor", (actor_id, actor, int(nGroupID), id(mesh)))
        return actor_id

    def add_voxels(self, vox: Voxels, nGroupID: int = 0, color: str | Sequence[float] = "lightgray") -> int:
        with Mesh.from_voxels(vox) as mesh:
            actor = self._make_mesh_actor(mesh, color)
        actor_id = self._next_id()
        self._enqueue("add_actor", (actor_id, actor, int(nGroupID), id(vox)))
        return actor_id

    def add_polyline(self, poly: PolyLine, nGroupID: int = 0) -> int:
        actor_id = self._next_id()
        actor = self._make_polyline_actor(poly)
        self._enqueue("add_actor", (actor_id, actor, int(nGroupID), id(poly)))
        return actor_id

    def Remove(self, xObject: object) -> None:
        if isinstance(xObject, int):
            self._enqueue("remove_actor", int(xObject))
            return
        self._enqueue("remove_object", id(xObject))

    def remove(self, actor_id: int) -> None:
        self.Remove(actor_id)

    def RemoveAllObjects(self) -> None:
        self._enqueue("remove_all")

    def RequestUpdate(self) -> None:
        self._enqueue("render")

    def request_render(self) -> None:
        self.RequestUpdate()

    def RequestScreenShot(self, strScreenShotPath: str) -> None:
        self._enqueue("screenshot", str(strScreenShotPath))

    def SetGroupVisible(self, nGroupID: int, bVisible: bool) -> None:
        self._enqueue("set_group_visible", (int(nGroupID), bool(bVisible)))

    def SetGroupStatic(self, nGroupID: int, bStatic: bool) -> None:
        self._enqueue("set_group_static", (int(nGroupID), bool(bStatic)))

    def SetGroupMaterial(self, nGroupID: int, clr: ColorFloat | Sequence[float], fMetallic: float, fRoughness: float) -> None:
        self._enqueue("set_group_material", (int(nGroupID), self._color_tuple(clr), float(fMetallic), float(fRoughness)))

    def SetGroupMatrix(self, nGroupID: int, mat: Sequence[float]) -> None:
        if len(mat) != 16:
            raise ValueError("mat must contain 16 values (row-major 4x4)")
        self._enqueue("set_group_matrix", (int(nGroupID), tuple(float(v) for v in mat)))

    def SetBackgroundColor(self, clr: ColorFloat | Sequence[float]) -> None:
        rgba = self._color_tuple(clr)
        self._enqueue("set_background", (rgba[0], rgba[1], rgba[2]))

    def AdjustViewAngles(self, fOrbitRelative: float, fElevationRelative: float) -> None:
        self.SetViewAngles(self.m_fOrbit + float(fOrbitRelative), self.m_fElevation + float(fElevationRelative))

    def SetViewAngles(self, fOrbit: float, fElevation: float) -> None:
        orbit = float(fOrbit)
        while orbit >= 360.0:
            orbit -= 360.0
        while orbit < 0.0:
            orbit += 360.0
        elev = max(-89.9, min(89.9, float(fElevation)))
        self._enqueue("set_view", (orbit, elev))

    def SetFov(self, fAngle: float) -> None:
        self._enqueue("set_fov", float(fAngle))

    def SetZoom(self, fZoom: float) -> None:
        self._enqueue("set_zoom", float(fZoom))

    def SetPerspective(self, bPerspective: bool) -> None:
        self._enqueue("set_perspective", bool(bPerspective))

    def LogStatistics(self) -> None:
        self._enqueue("log_stats")

    def LoadLightSetup(self, source: str | bytes | io.BytesIO) -> None:
        if isinstance(source, str):
            blob = Path(source).read_bytes()
        elif isinstance(source, io.BytesIO):
            blob = source.getvalue()
        else:
            blob = bytes(source)

        with zipfile.ZipFile(io.BytesIO(blob), "r") as zf:
            diffuse = zf.read("Diffuse.dds")
            specular = zf.read("Specular.dds")
        self._enqueue("light_setup", (diffuse, specular))

    def AddKeyHandler(self, xKeyHandler: IKeyHandler) -> None:
        self._key_handlers.insert(0, xKeyHandler)

    def _ensure_key_callback(self) -> None:
        if self._key_callback_handle is not None:
            return

        def _on_key(event: object) -> None:
            key = str(getattr(event, "keypress", getattr(event, "keyPressed", "")))
            if not key:
                return
            shift = bool(getattr(event, "shift", False))
            ctrl = bool(getattr(event, "ctrl", False))
            alt = bool(getattr(event, "alt", False))
            cmd = bool(getattr(event, "cmd", False))
            for handler in self._key_handlers:
                if handler.bHandleEvent(self, key, False, shift, ctrl, alt, cmd):
                    self.RequestUpdate()
                    break

        self._key_callback_handle = self._plotter.add_callback("KeyPress", _on_key)

    def AddAnimation(self, oAnim: Any) -> None:
        if not hasattr(self, "_anim_start"):
            self._anim_start = time.perf_counter()
        self._animations.append(oAnim)
        self.RequestUpdate()

    def RemoveAllAnimations(self) -> None:
        for anim in self._animations:
            end_fn = getattr(anim, "End", None)
            if callable(end_fn):
                end_fn()
        self._animations.clear()

    def StartTimeLapse(
        self,
        fIntervalInMilliseconds: float,
        strPath: str,
        strFileName: str = "frame_",
        nStartFrame: int = 0,
        bPaused: bool = False,
    ) -> None:
        self._timelapse = _TimeLapseState.create(
            fIntervalInMilliseconds,
            strPath,
            strFileName,
            nStartFrame,
            bPaused,
        )

    def PauseTimeLapse(self) -> None:
        if self._timelapse is not None:
            self._timelapse.Pause()

    def ResumeTimeLapse(self) -> None:
        if self._timelapse is not None:
            self._timelapse.Resume()

    def StopTimeLapse(self) -> None:
        self._timelapse = None

    def bPoll(self) -> bool:
        self._drain_queue()
        changed = self._pulse_animations()
        changed = self._capture_timelapse_if_due() or changed
        if changed:
            self._render()
        self._idle = self._queue.empty()
        return not self._closed

    def bIsIdle(self) -> bool:
        self._idle = self._idle and self._queue.empty()
        return self._idle

    def interact(self) -> None:
        self._stop_loop()
        self._drain_queue()
        self._ensure_key_callback()
        # Phase 1: open the VTK window non-interactively so the render window
        # and camera object actually exist.  resetcam=True lets vedo fit the
        # scene so the object is always visible before we reposition.
        self._plotter.show(interactive=False, resetcam=True)
        # Phase 2: now that the window is live, apply our computed camera
        # position (respecting m_fZoom, m_fOrbit, m_fElevation, m_fFov) on
        # the real VTK camera, then re-render without resetting.
        self._update_camera()
        self._plotter.render(resetcam=False)
        # Phase 3: hand off to the VTK interactive event loop.
        if getattr(self._plotter, "interactor", None) is not None:
            self._plotter.interactor.Start()
        else:
            self._plotter.show(interactive=True, resetcam=False)

    def close(self) -> None:
        if self._closed:
            return
        self._enqueue("close")
        self._stop_loop()
        self._drain_queue()
        self._plotter.close()


def go(
    voxel_size_mm: float,
    task: Callable[[], None],
    *,
    end_on_task_completion: bool = False,
    viewer: VedoViewer | None = None,
) -> None:
    """Initialize runtime, execute task in worker thread, then clean up."""

    errors: list[BaseException] = []

    def _runner() -> None:
        try:
            task()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    Library.init(float(voxel_size_mm))
    try:
        # For interactive viewer mode we render on the main thread after task completion.
        # Starting the background loop in that mode can race window lifetime on some backends.
        if viewer is not None and end_on_task_completion:
            viewer.start()

        worker = threading.Thread(target=_runner, daemon=True)
        worker.start()

        worker.join()

        if errors:
            raise errors[0]

        if viewer is not None and not end_on_task_completion:
            viewer.interact()
    finally:
        if viewer is not None:
            viewer.close()
        Library.destroy()
