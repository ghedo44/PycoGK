from __future__ import annotations

import ctypes
from typing import Any, Callable
import numpy as np

from _common.types import Vector3Like

from .._base import HandleOwner
from .._errors import PicoGKInvalidHandleError
from .._native import CallbackScalarFieldTraverse, CallbackVectorFieldTraverse
from .._types import Vec3, VoxelDimensions, as_vec3, vec3_tuple

from .library import Library
from .metadata import FieldMetadata
from .._core.voxels import IImplicit, Voxels

class ScalarField(HandleOwner, IImplicit):
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

    def signed_distance(self, vecPt: Vector3Like) -> float:
        ok, value = self.get_value(vecPt)
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



