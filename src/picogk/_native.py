from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any

from ._config import candidate_library_paths
from ._errors import PicoGKLoadError
from ._types import BBox3, ColorFloat, Mat4, Triangle, Vec2, Vec3


CallbackImplicitDistance = ctypes.CFUNCTYPE(ctypes.c_float, ctypes.POINTER(Vec3))
CallbackScalarFieldTraverse = ctypes.CFUNCTYPE(None, ctypes.POINTER(Vec3), ctypes.c_float)
CallbackVectorFieldTraverse = ctypes.CFUNCTYPE(None, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3))

InfoCallback = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_bool)
UpdateCallback = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(Vec2),
    ctypes.POINTER(ColorFloat),
    ctypes.POINTER(Mat4),
    ctypes.POINTER(Mat4),
    ctypes.POINTER(Mat4),
    ctypes.POINTER(Vec3),
    ctypes.POINTER(Vec3),
)
KeyPressedCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
MouseMovedCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(Vec2))
MouseButtonCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(Vec2))
ScrollWheelCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(Vec2), ctypes.POINTER(Vec2))
WindowSizeCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(Vec2))


@dataclass
class Native:
    lib: ctypes.CDLL


def _bind(lib: ctypes.CDLL, name: str, restype: Any, argtypes: list[Any]) -> None:
    fn = getattr(lib, name)
    fn.restype = restype
    fn.argtypes = argtypes


def _bind_if_exists(lib: ctypes.CDLL, name: str, restype: Any, argtypes: list[Any]) -> None:
    if hasattr(lib, name):
        _bind(lib, name, restype, argtypes)


def _load_lib() -> ctypes.CDLL:
    errors: list[str] = []
    for candidate in candidate_library_paths():
        try:
            return ctypes.CDLL(candidate)
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")
    msg = "Unable to load PicoGK runtime. Tried:\n" + "\n".join(errors)
    raise PicoGKLoadError(msg)


def _configure(lib: ctypes.CDLL) -> None:
    # Library
    _bind(lib, "Library_Init", None, [ctypes.c_float])
    _bind(lib, "Library_Destroy", None, [])
    _bind(lib, "Library_GetName", None, [ctypes.c_char_p])
    _bind(lib, "Library_GetVersion", None, [ctypes.c_char_p])
    _bind(lib, "Library_GetBuildInfo", None, [ctypes.c_char_p])
    _bind(lib, "Library_VoxelsToMm", None, [ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind(lib, "Library_MmToVoxels", None, [ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])

    # Mesh
    _bind(lib, "Mesh_hCreate", ctypes.c_void_p, [])
    _bind(lib, "Mesh_hCreateFromVoxels", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "Mesh_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "Mesh_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "Mesh_nAddVertex", ctypes.c_int, [ctypes.c_void_p, ctypes.POINTER(Vec3)])
    _bind(lib, "Mesh_nVertexCount", ctypes.c_int, [ctypes.c_void_p])
    _bind(lib, "Mesh_GetVertex", None, [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(Vec3)])
    _bind(lib, "Mesh_nAddTriangle", ctypes.c_int, [ctypes.c_void_p, ctypes.POINTER(Triangle)])
    _bind(lib, "Mesh_nTriangleCount", ctypes.c_int, [ctypes.c_void_p])
    _bind(lib, "Mesh_GetTriangle", None, [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(Triangle)])
    _bind(lib, "Mesh_GetTriangleV", None, [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind(lib, "Mesh_GetBoundingBox", None, [ctypes.c_void_p, ctypes.POINTER(BBox3)])

    # Lattice
    _bind(lib, "Lattice_hCreate", ctypes.c_void_p, [])
    _bind(lib, "Lattice_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "Lattice_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "Lattice_AddSphere", None, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.c_float])
    _bind(lib, "Lattice_AddBeam", None, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3), ctypes.c_float, ctypes.c_float, ctypes.c_bool])

    # Voxels
    _bind(lib, "Voxels_hCreate", ctypes.c_void_p, [])
    _bind(lib, "Voxels_hCreateCopy", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "Voxels_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "Voxels_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "Voxels_BoolAdd", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind(lib, "Voxels_BoolSubtract", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind(lib, "Voxels_BoolIntersect", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind_if_exists(lib, "Voxels_BoolAddSmooth", None, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float])
    _bind(lib, "Voxels_Offset", None, [ctypes.c_void_p, ctypes.c_float])
    _bind(lib, "Voxels_DoubleOffset", None, [ctypes.c_void_p, ctypes.c_float, ctypes.c_float])
    _bind(lib, "Voxels_TripleOffset", None, [ctypes.c_void_p, ctypes.c_float])
    _bind(lib, "Voxels_Gaussian", None, [ctypes.c_void_p, ctypes.c_float])
    _bind(lib, "Voxels_Median", None, [ctypes.c_void_p, ctypes.c_float])
    _bind(lib, "Voxels_Mean", None, [ctypes.c_void_p, ctypes.c_float])
    _bind(lib, "Voxels_RenderMesh", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind(lib, "Voxels_RenderImplicit", None, [ctypes.c_void_p, ctypes.POINTER(BBox3), CallbackImplicitDistance])
    _bind(lib, "Voxels_IntersectImplicit", None, [ctypes.c_void_p, CallbackImplicitDistance])
    _bind(lib, "Voxels_RenderLattice", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind(lib, "Voxels_ProjectZSlice", None, [ctypes.c_void_p, ctypes.c_float, ctypes.c_float])
    _bind_if_exists(lib, "Voxels_bIsInside", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3)])
    _bind_if_exists(lib, "Voxels_bIsEqual", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_void_p])
    _bind_if_exists(lib, "Voxels_CalculateProperties", None, [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(BBox3)])
    _bind_if_exists(lib, "Voxels_GetSurfaceNormal", None, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind_if_exists(lib, "Voxels_bClosestPointOnSurface", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind_if_exists(lib, "Voxels_bRayCastToSurface", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind(lib, "Voxels_GetVoxelDimensions", None, [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)])
    _bind(lib, "Voxels_GetSlice", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)])
    _bind_if_exists(lib, "Voxels_GetInterpolatedSlice", None, [ctypes.c_void_p, ctypes.c_float, ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)])

    # PolyLine
    _bind(lib, "PolyLine_hCreate", ctypes.c_void_p, [ctypes.POINTER(ColorFloat)])
    _bind(lib, "PolyLine_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "PolyLine_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "PolyLine_nAddVertex", ctypes.c_int, [ctypes.c_void_p, ctypes.POINTER(Vec3)])
    _bind(lib, "PolyLine_nVertexCount", ctypes.c_int, [ctypes.c_void_p])
    _bind(lib, "PolyLine_GetVertex", None, [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(Vec3)])
    _bind(lib, "PolyLine_GetColor", None, [ctypes.c_void_p, ctypes.POINTER(ColorFloat)])

    # Viewer bindings kept for API completeness (not used by python viewer).
    _bind_if_exists(lib, "Viewer_hCreate", ctypes.c_void_p, [ctypes.c_char_p, ctypes.POINTER(Vec2), InfoCallback, UpdateCallback, KeyPressedCallback, MouseMovedCallback, MouseButtonCallback, ScrollWheelCallback, WindowSizeCallback])
    _bind_if_exists(lib, "Viewer_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_Destroy", None, [ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_RequestUpdate", None, [ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_bPoll", ctypes.c_bool, [ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_RequestScreenShot", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p])
    _bind_if_exists(lib, "Viewer_bLoadLightSetup", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int])
    _bind_if_exists(lib, "Viewer_RequestClose", None, [ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_AddMesh", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_RemoveMesh", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_AddPolyLine", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_RemovePolyLine", None, [ctypes.c_void_p, ctypes.c_void_p])
    _bind_if_exists(lib, "Viewer_SetGroupVisible", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_bool])
    _bind_if_exists(lib, "Viewer_SetGroupStatic", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_bool])
    _bind_if_exists(lib, "Viewer_SetGroupMaterial", None, [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ColorFloat), ctypes.c_float, ctypes.c_float])
    _bind_if_exists(lib, "Viewer_SetGroupMatrix", None, [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(Mat4)])

    # VDB
    _bind(lib, "VdbFile_hCreate", ctypes.c_void_p, [])
    _bind(lib, "VdbFile_hCreateFromFile", ctypes.c_void_p, [ctypes.c_char_p])
    _bind(lib, "VdbFile_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "VdbFile_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "VdbFile_bSaveToFile", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p])
    _bind(lib, "VdbFile_hGetVoxels", ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_int])
    _bind(lib, "VdbFile_nAddVoxels", ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p])
    _bind(lib, "VdbFile_hGetScalarField", ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_int])
    _bind(lib, "VdbFile_nAddScalarField", ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p])
    _bind(lib, "VdbFile_hGetVectorField", ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_int])
    _bind(lib, "VdbFile_nAddVectorField", ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p])
    _bind(lib, "VdbFile_nFieldCount", ctypes.c_int, [ctypes.c_void_p])
    _bind(lib, "VdbFile_GetFieldName", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p])
    _bind(lib, "VdbFile_nFieldType", ctypes.c_int, [ctypes.c_void_p, ctypes.c_int])

    # ScalarField
    _bind(lib, "ScalarField_hCreate", ctypes.c_void_p, [])
    _bind(lib, "ScalarField_hCreateCopy", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "ScalarField_hCreateFromVoxels", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "ScalarField_hBuildFromVoxels", ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_float, ctypes.c_float])
    _bind(lib, "ScalarField_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "ScalarField_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "ScalarField_SetValue", None, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.c_float])
    _bind(lib, "ScalarField_bGetValue", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(ctypes.c_float)])
    _bind(lib, "ScalarField_RemoveValue", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3)])
    _bind(lib, "ScalarField_GetVoxelDimensions", None, [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)])
    _bind(lib, "ScalarField_GetSlice", None, [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p])
    _bind(lib, "ScalarField_TraverseActive", None, [ctypes.c_void_p, CallbackScalarFieldTraverse])

    # VectorField
    _bind(lib, "VectorField_hCreate", ctypes.c_void_p, [])
    _bind(lib, "VectorField_hCreateCopy", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "VectorField_hCreateFromVoxels", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "VectorField_hBuildFromVoxels", ctypes.c_void_p, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.c_float])
    _bind(lib, "VectorField_bIsValid", ctypes.c_bool, [ctypes.c_void_p])
    _bind(lib, "VectorField_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "VectorField_SetValue", None, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind(lib, "VectorField_bGetValue", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)])
    _bind(lib, "VectorField_RemoveValue", ctypes.c_bool, [ctypes.c_void_p, ctypes.POINTER(Vec3)])
    _bind(lib, "VectorField_TraverseActive", None, [ctypes.c_void_p, CallbackVectorFieldTraverse])

    # Metadata
    _bind(lib, "Metadata_hFromVoxels", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "Metadata_hFromScalarField", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "Metadata_hFromVectorField", ctypes.c_void_p, [ctypes.c_void_p])
    _bind(lib, "Metadata_Destroy", None, [ctypes.c_void_p])
    _bind(lib, "Metadata_nCount", ctypes.c_int, [ctypes.c_void_p])
    _bind(lib, "Metadata_nNameLengthAt", ctypes.c_int, [ctypes.c_void_p, ctypes.c_int])
    _bind(lib, "Metadata_bGetNameAt", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int])
    _bind(lib, "Metadata_nTypeAt", ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p])
    _bind(lib, "Metadata_nStringLengthAt", ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p])
    _bind(lib, "Metadata_bGetStringAt", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int])
    _bind(lib, "Metadata_bGetFloatAt", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)])
    _bind(lib, "Metadata_bGetVectorAt", ctypes.c_bool, [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(Vec3)])
    _bind(lib, "Metadata_SetStringValue", None, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p])
    _bind(lib, "Metadata_SetFloatValue", None, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_float])
    _bind(lib, "Metadata_SetVectorValue", None, [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(Vec3)])
    _bind(lib, "MetaData_RemoveValue", None, [ctypes.c_void_p, ctypes.c_char_p])


_NATIVE: Native | None = None


def native() -> Native:
    global _NATIVE
    if _NATIVE is None:
        lib = _load_lib()
        _configure(lib)
        _NATIVE = Native(lib=lib)
    return _NATIVE
