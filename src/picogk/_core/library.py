from __future__ import annotations

import ctypes
import threading

from _common.types import Vector3Like

from .._config import STRING_LENGTH
from .._native import native
from .._types import Vec3, as_vec3, vec3_tuple
from .._viewer_protocol import IViewer

class Library:
    _lock = threading.Lock()
    _running = False
    _app_exit = False
    _continue_task = True
    _viewer: IViewer | None = None
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

    @classmethod
    def SetViewer(cls, viewer: IViewer | None) -> None:
        cls._viewer = viewer

    @classmethod
    def oViewer(cls) -> IViewer | None:
        return cls._viewer

    @classmethod
    def ClearViewer(cls) -> None:
        cls._viewer = None

    @classmethod
    def Dispose(cls) -> None:
        cls.destroy()



