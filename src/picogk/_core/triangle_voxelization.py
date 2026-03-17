import numpy as np

from _common.types import Vector3Like

from .mesh import Mesh
from .voxels import IBoundedImplicit, Voxels


class ImplicitTriangle(IBoundedImplicit):
    def __init__(self, vecA: Vector3Like, vecB: Vector3Like, vecC: Vector3Like, fThickness: float) -> None:
        self._a = np.array(vecA, dtype=np.float64)
        self._b = np.array(vecB, dtype=np.float64)
        self._c = np.array(vecC, dtype=np.float64)
        self._thickness = float(fThickness)

        bounds_min = np.minimum(np.minimum(self._a, self._b), self._c) - self._thickness
        bounds_max = np.maximum(np.maximum(self._a, self._b), self._c) + self._thickness
        self._bounds = (tuple(bounds_min.tolist()), tuple(bounds_max.tolist()))

    @property
    def oBounds(self) -> tuple[Vector3Like, Vector3Like]:
        return self._bounds

    @staticmethod
    def _closest_point_on_triangle(point: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        ab = b - a
        ac = c - a
        ap = point - a
        d1 = np.dot(ab, ap)
        d2 = np.dot(ac, ap)
        if d1 <= 0.0 and d2 <= 0.0:
            return a
        bp = point - b
        d3 = np.dot(ab, bp)
        d4 = np.dot(ac, bp)
        if d3 >= 0.0 and d4 <= d3:
            return b
        vc = d1 * d4 - d3 * d2
        if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
            v = d1 / (d1 - d3)
            return a + (v * ab)
        cp = point - c
        d5 = np.dot(ab, cp)
        d6 = np.dot(ac, cp)
        if d6 >= 0.0 and d5 <= d6:
            return c
        vb = d5 * d2 - d1 * d6
        if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
            w = d2 / (d2 - d6)
            return a + (w * ac)
        va = d3 * d6 - d5 * d4
        if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
            w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
            return b + (w * (c - b))
        denom = 1.0 / (va + vb + vc)
        v_ab = vb * denom
        v_ac = vc * denom
        return a + (v_ab * ab) + (v_ac * ac)

    def fSignedDistance(self, vec: Vector3Like) -> float:
        p = np.array(vec, dtype=np.float64)
        cp = self._closest_point_on_triangle(p, self._a, self._b, self._c)
        return float(np.linalg.norm(p - cp) - self._thickness)


class ImplicitMesh(IBoundedImplicit):
    def __init__(self, msh: Mesh, fThickness: float) -> None:
        self._triangles: list[ImplicitTriangle] = []
        bounds_min = np.array((float("inf"), float("inf"), float("inf")), dtype=np.float64)
        bounds_max = np.array((float("-inf"), float("-inf"), float("-inf")), dtype=np.float64)

        for i in range(msh.nTriangleCount()):
            a, b, c = msh.GetTriangle(i)
            tri = ImplicitTriangle(a, b, c, fThickness)
            self._triangles.append(tri)
            tmin = np.array(tri.oBounds[0], dtype=np.float64)
            tmax = np.array(tri.oBounds[1], dtype=np.float64)
            bounds_min = np.minimum(bounds_min, tmin)
            bounds_max = np.maximum(bounds_max, tmax)

        self._bounds = (tuple(bounds_min.tolist()), tuple(bounds_max.tolist()))

    @property
    def oBounds(self) -> tuple[Vector3Like, Vector3Like]:
        return self._bounds

    def fSignedDistance(self, vec: Vector3Like) -> float:
        return min((tri.fSignedDistance(vec) for tri in self._triangles), default=1e9)


class TriangleVoxelization:
    @staticmethod
    def voxVoxelizeHollow(mesh: Mesh, fThickness: float) -> Voxels:
        implicit = ImplicitMesh(mesh, fThickness)
        return Voxels.from_bounded_implicit(implicit)


