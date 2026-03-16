from __future__ import annotations


import ctypes

from _common.types import Vector3Like

from .._base import HandleOwner
from .._errors import PicoGKInvalidHandleError
from .._types import as_vec3

from .library import Library

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



