from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from _common.types import Vector3Like

if TYPE_CHECKING:
    from .mesh import Mesh


class MeshMath:
    @staticmethod
    def bPointLiesOnTriangle(vecP: Vector3Like, vecA: Vector3Like, vecB: Vector3Like, vecC: Vector3Like) -> bool:
        p = np.array(vecP, dtype=np.float64)
        a = np.array(vecA, dtype=np.float64) - p
        b = np.array(vecB, dtype=np.float64) - p
        c = np.array(vecC, dtype=np.float64) - p
        u = np.cross(b, c)
        v = np.cross(c, a)
        w = np.cross(a, b)
        return float(np.dot(u, v)) >= 0.0 and float(np.dot(u, w)) >= 0.0

    @staticmethod
    def bFindTriangleFromSurfacePoint(mesh: Mesh, vecSurfacePoint: Vector3Like) -> tuple[bool, int]:
        for i in range(mesh.nTriangleCount()):
            a, b, c = mesh.GetTriangle(i)
            if MeshMath.bPointLiesOnTriangle(vecSurfacePoint, a, b, c):
                return (True, i)
        return (False, (2**31) - 1)

