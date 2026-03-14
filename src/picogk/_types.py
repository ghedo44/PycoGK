from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Iterable, Sequence


class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]


class Vec3(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]


class Triangle(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int), ("b", ctypes.c_int), ("c", ctypes.c_int)]


class ColorFloat(ctypes.Structure):
    _fields_ = [
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("a", ctypes.c_float),
    ]


class BBox3(ctypes.Structure):
    _fields_ = [("min", Vec3), ("max", Vec3)]


class Mat4(ctypes.Structure):
    _fields_ = [(f"m{i}", ctypes.c_float) for i in range(16)]


Vector3Like = Sequence[float]


@dataclass(frozen=True)
class VoxelDimensions:
    x_origin: int
    y_origin: int
    z_origin: int
    x_size: int
    y_size: int
    z_size: int


def as_vec3(value: Vector3Like | Vec3) -> Vec3:
    if isinstance(value, Vec3):
        return value
    if len(value) != 3:
        raise ValueError("Expected 3 values for Vec3")
    return Vec3(float(value[0]), float(value[1]), float(value[2]))


def as_bbox3(min_xyz: Vector3Like, max_xyz: Vector3Like) -> BBox3:
    return BBox3(as_vec3(min_xyz), as_vec3(max_xyz))


def vec3_tuple(v: Vec3) -> tuple[float, float, float]:
    return (float(v.x), float(v.y), float(v.z))


def iter_vec3(values: Iterable[Vector3Like]) -> Iterable[Vec3]:
    for value in values:
        yield as_vec3(value)
