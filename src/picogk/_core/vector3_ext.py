from typing import Sequence

import numpy as np

from _common.types import Vector3Like


class Vector3Ext:
    @staticmethod
    def vecNormalized(vec: Vector3Like) -> tuple[float, float, float]:
        v = np.array(vec, dtype=np.float64)
        n = np.linalg.norm(v)
        if n <= 1e-12:
            return (0.0, 0.0, 0.0)
        v = v / n
        return (float(v[0]), float(v[1]), float(v[2]))

    @staticmethod
    def vecMirrored(vec: Vector3Like, vecPlanePoint: Vector3Like, vecPlaneNormalUnitVector: Vector3Like) -> tuple[float, float, float]:
        v = np.array(vec, dtype=np.float64)
        p = np.array(vecPlanePoint, dtype=np.float64)
        n = np.array(vecPlaneNormalUnitVector, dtype=np.float64)
        ln = np.linalg.norm(n)
        if ln <= 1e-12:
            raise ValueError("vecPlaneNormalUnitVector must be non-zero")
        n = n / ln
        out = v - (2.0 * np.dot(v - p, n) * n)
        return (float(out[0]), float(out[1]), float(out[2]))

    @staticmethod
    def vecTransformed(vec: Vector3Like, mat: Sequence[float]) -> tuple[float, float, float]:
        if len(mat) != 16:
            raise ValueError("mat must have 16 values (row-major 4x4)")
        m = np.array(mat, dtype=np.float64).reshape((4, 4))
        v = np.array((float(vec[0]), float(vec[1]), float(vec[2]), 1.0), dtype=np.float64)
        out = m @ v
        return (float(out[0]), float(out[1]), float(out[2]))


