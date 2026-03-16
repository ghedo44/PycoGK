from __future__ import annotations

import ctypes
import math
from typing import TYPE_CHECKING, Any, Sequence, cast

import numpy as np

from _common.types import Vector3Like
from picogk._core.mesh_io import EStlUnit, MeshIo
from picogk._core.mesh_mat import MeshMath

from .._base import HandleOwner
from .._errors import PicoGKInvalidHandleError
from .._types import BBox3, Triangle, Vec3, as_vec3, vec3_tuple

from .library import Library

if TYPE_CHECKING:
    from .._core.voxels import Voxels

class Mesh(HandleOwner):
    def __init__(self, handle: int | ctypes.c_void_p | None = None, *, owns_handle: bool = True) -> None:
        if handle is None:
            handle = Library._lib().Mesh_hCreate()
        if not handle:
            raise PicoGKInvalidHandleError("Mesh_hCreate returned null")
        super().__init__(handle, owns_handle=owns_handle)
        # C# parity fields used by STL IO helpers.
        self.m_strLoadHeaderData: str = ""
        self.m_eLoadUnits: EStlUnit = EStlUnit.AUTO

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
        return MeshMath.bPointLiesOnTriangle(vecP, vecA, vecB, vecC)

    def bFindTriangleFromSurfacePoint(self, vecSurfacePoint: Vector3Like) -> tuple[bool, int]:
        return MeshMath.bFindTriangleFromSurfacePoint(self, vecSurfacePoint)

    def voxVoxelizeHollow(self, fThickness: float) -> "Voxels":
        from .triangle_voxelization import TriangleVoxelization

        return TriangleVoxelization.voxVoxelizeHollow(self, float(fThickness))

    @staticmethod
    def mshFromStlFile(
        strFilePath: str,
        eLoadUnit: Any = None,
        fPostScale: float = 1.0,
        vecPostOffsetMM: Vector3Like | None = None,
    ) -> "Mesh":

        load_unit = EStlUnit.AUTO if eLoadUnit is None else eLoadUnit
        return MeshIo.mshFromStlFile(strFilePath, cast(Any, load_unit), fPostScale, vecPostOffsetMM)

    def SaveToStlFile(
        self,
        strFilePath: str,
        eUnit: Any = None,
        vecOffsetMM: Vector3Like | None = None,
        fScale: float = 1.0,
    ) -> None:

        unit = EStlUnit.AUTO if eUnit is None else eUnit
        MeshIo.SaveToStlFile(self, strFilePath, cast(Any, unit), vecOffsetMM, fScale)

