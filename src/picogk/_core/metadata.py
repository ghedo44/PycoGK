from __future__ import annotations

import ctypes
from enum import IntEnum
from typing import TYPE_CHECKING, cast

from _common.types import Vector3Like

from .._base import HandleOwner
from .._errors import PicoGKInvalidHandleError
from .._types import Vec3, as_vec3, vec3_tuple

from .library import Library

if TYPE_CHECKING:
    from .fields import ScalarField, VectorField
    from .._core.voxels import Voxels

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

    def Dispose(self) -> None:
        self.close()



