from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fields import ScalarField

import ctypes
from typing import Any, Callable, Protocol, Sequence, cast

import numpy as np

from _common.types import Vector3Like

from .._base import HandleOwner
from .._errors import PicoGKInvalidHandleError
from .._native import CallbackImplicitDistance
from .._types import BBox3, Vec3, VoxelDimensions, as_bbox3, as_vec3, vec3_tuple

from .lattice import Lattice
from .library import Library
from .mesh import Mesh
from .metadata import FieldMetadata


class SupportsSignedDistance(Protocol):
    def fSignedDistance(self, vecPt: tuple[float, float, float]) -> float: ...


SignedDistanceInput = Callable[[tuple[float, float, float]], float] | SupportsSignedDistance


def _coerce_signed_distance_fn(fn_or_implicit: SignedDistanceInput) -> Callable[[tuple[float, float, float]], float]:
    if callable(fn_or_implicit):
        return cast(Callable[[tuple[float, float, float]], float], fn_or_implicit)

    signed_distance = getattr(fn_or_implicit, "fSignedDistance", None)
    if callable(signed_distance):
        method = cast(Callable[[tuple[float, float, float]], float], signed_distance)

        def _wrapped(vec: tuple[float, float, float]) -> float:
            return float(method(vec))

        return _wrapped

    raise TypeError("Expected a callable signed-distance function or an object exposing fSignedDistance(vecPt)")

class ESliceMode(IntEnum):
    SignedDistance = 0
    Antialiased = 1
    BlackWhite = 2

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

    def intersect_implicit(self, fn: SignedDistanceInput) -> "Voxels":
        self._ensure_open()
        sd_fn = _coerce_signed_distance_fn(fn)

        def _wrapped(vec_ptr: Any) -> float:
            v = vec_ptr.contents
            return float(sd_fn((float(v.x), float(v.y), float(v.z))))

        cb = CallbackImplicitDistance(_wrapped)
        self._implicit_callback_ref = cb
        Library._lib().Voxels_IntersectImplicit(self.handle, cb)
        return self

    IntersectImplicit = intersect_implicit

    def voxIntersectImplicit(self, fn: SignedDistanceInput) -> "Voxels":
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
        lib = Library._lib()
        if hasattr(lib, "Voxels_bIsInside"):
            return bool(lib.Voxels_bIsInside(self.handle, ctypes.byref(p)))

        # Compatibility fallback for older runtimes that predate Voxels_bIsInside.
        # Sample signed distance from a scalar field built from this voxel set.
        from .fields import ScalarField
        with ScalarField.from_voxels(self) as field:
            return field.signed_distance(point) < 0.0

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

    def trim(self, oBox: tuple[Vector3Like, Vector3Like]) -> "Voxels":
        from .utils import Utils

        with Utils.mshCreateCube(oBox) as msh_trim:
            with Voxels.from_mesh(msh_trim) as vox_trim:
                self.bool_intersect(vox_trim)
        return self

    Trim = trim

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

    def GetVoxelSlice(self, z_slice: int, mode: ESliceMode = ESliceMode.SignedDistance) -> np.ndarray:
        arr, background = self.slice(z_slice)
        if mode == ESliceMode.SignedDistance:
            return arr
        if mode == ESliceMode.BlackWhite:
            return np.where(arr <= 0, 0.0, 1.0).astype(np.float32)
        if mode == ESliceMode.Antialiased:
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

    def GetInterpolatedVoxelSlice(self, z_slice: float, mode: ESliceMode = ESliceMode.SignedDistance) -> np.ndarray:
        arr, background = self.interpolated_slice(z_slice)
        if mode == ESliceMode.SignedDistance:
            return arr
        if mode == ESliceMode.BlackWhite:
            return np.where(arr <= 0, 0.0, 1.0).astype(np.float32)
        if mode == ESliceMode.Antialiased:
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
        from .openvdb import OpenVdbFile

        with OpenVdbFile(strFileName) as oFile:
            if oFile.nFieldCount() == 0:
                raise OSError(f"No fields contained in OpenVDB file {strFileName}")
            for n in range(oFile.nFieldCount()):
                if oFile.eFieldType(n) == OpenVdbFile.FieldType.VOXELS:
                    return oFile.voxGet(n)
        raise OSError(f"No voxel field (openvdb::GRID_LEVEL_SET) found in VDB file {strFileName}")

    def SaveToVdbFile(self, strFileName: str) -> None:
        from .openvdb import OpenVdbFile

        with OpenVdbFile() as oFile:
            oFile.nAdd(self)
            oFile.SaveToFile(strFileName)

    def voxVoxelizeHollow(self, fThickness: float) -> "Voxels":
        from .triangle_voxelization import TriangleVoxelization

        with self.mshAsMesh() as msh:
            return TriangleVoxelization.voxVoxelizeHollow(msh, fThickness)

    def oVectorize(self, fLayerHeight: float = 0.0, bUseAbsXYOrigin: bool = False) -> Any:
        from .image import ImageGrayScale
        from .slice import PolySlice, PolySliceStack

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
            arr = self.GetInterpolatedVoxelSlice(f_z, ESliceMode.SignedDistance)
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
        from .cli import Cli

        use_format = Cli.EFormat.FirstLayerWithContent if eFormat is None else eFormat
        oStack = self.oVectorize(fLayerHeight, bUseAbsXYOrigin)
        Cli.WriteSlicesToCliFile(cast(Any, oStack), strFileName, cast(Any, use_format))



