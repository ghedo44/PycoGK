from __future__ import annotations

import numpy as np

from shape_kernel._types import Vec3, as_np3, as_vec3


class RobinsonTriangle:
    def __init__(self, vecA: Vec3, vecB: Vec3, vecC: Vec3) -> None:
        self.m_vecA: Vec3 = as_vec3(vecA)
        self.m_vecB: Vec3 = as_vec3(vecB)
        self.m_vecC: Vec3 = as_vec3(vecC)
        self.m_vecCentre: np.ndarray = 0.5 * (as_np3(self.m_vecA) + as_np3(self.m_vecC))

    def oGetFlippedTriangle(self) -> "RobinsonTriangle":
        vec_new_b = as_np3(self.m_vecB) + 2.0 * (self.m_vecCentre - as_np3(self.m_vecB))
        return RobinsonTriangle(self.m_vecA, as_vec3(vec_new_b), self.m_vecC)


__all__ = ["RobinsonTriangle"]
