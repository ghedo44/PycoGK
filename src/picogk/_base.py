from __future__ import annotations

import ctypes
from typing import Optional

from ._errors import PicoGKDisposedError


class HandleOwner:
    """Base class for wrappers that own a native handle."""

    _destroy_func_name: Optional[str] = None

    def __init__(self, handle: int | ctypes.c_void_p, *, owns_handle: bool = True) -> None:
        self._handle = ctypes.c_void_p(int(handle) if not isinstance(handle, ctypes.c_void_p) else handle.value)
        self._owns_handle = owns_handle
        self._closed = False

    @property
    def handle(self) -> ctypes.c_void_p:
        self._ensure_open()
        return self._handle

    @property
    def is_closed(self) -> bool:
        return self._closed or not bool(self._handle.value)

    def _ensure_open(self) -> None:
        if self.is_closed:
            raise PicoGKDisposedError(f"{self.__class__.__name__} is closed")

    def _destroy_native(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        if self.is_closed:
            self._closed = True
            return
        try:
            if self._owns_handle:
                self._destroy_native()
        finally:
            self._handle = ctypes.c_void_p()
            self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
