from __future__ import annotations

import ctypes
from enum import IntEnum
from typing import Any, cast

from .._base import HandleOwner
from .._config import STRING_LENGTH
from .._errors import PicoGKInvalidHandleError
from .fields import ScalarField, VectorField
from .library import Library
from .._core.voxels import Voxels

VdbField = Voxels | ScalarField | VectorField

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

    def nAdd(self, field: VdbField, field_name: str = "") -> int:
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

    def xField(self, index: int) -> VdbField:
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



