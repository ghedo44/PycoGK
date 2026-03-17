from __future__ import annotations

from _common.types import ColorLike, Vector3Like, as_np3, as_tuple3, clamp01, normalized, np_vec3

Vec3 = tuple[float, float, float]


def as_vec3(value: Vector3Like) -> Vec3:
    return as_tuple3(value)


__all__ = ["ColorLike", "Vec3", "Vector3Like", "as_np3", "as_vec3", "clamp01", "normalized", "np_vec3"]
