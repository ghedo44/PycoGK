from __future__ import annotations

from typing import Any, Sequence, TypeAlias

import numpy as np
from numpy.typing import NDArray

NumericArray: TypeAlias = NDArray[np.floating[Any]] | NDArray[np.integer[Any]]
FloatSequence: TypeAlias = Sequence[float]

Vector2Like: TypeAlias = FloatSequence | NumericArray
Vector3Like: TypeAlias = FloatSequence | NumericArray
ColorLike: TypeAlias = FloatSequence | NumericArray


def as_np3(value: Vector3Like) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError("Expected a 3D vector")
    return arr


def as_tuple3(value: Vector3Like) -> tuple[float, float, float]:
    arr = as_np3(value)
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def np_vec3(value: Vector3Like) -> NDArray[np.float64]:
    return as_np3(value)


def clamp01(value: float) -> float:
    return float(np.clip(float(value), 0.0, 1.0))


def normalized(value: Vector3Like, eps: float = 1e-12) -> NDArray[np.float64]:
    arr = as_np3(value)
    length = float(np.linalg.norm(arr))
    if length <= eps:
        return np.zeros(3, dtype=np.float64)
    return arr / length