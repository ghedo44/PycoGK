from __future__ import annotations

import math

import numpy as np
from picogk import IImplicit

from .._types import Vector3Like, as_np3, as_vec3


class ImplicitGyroid(IImplicit):
    def __init__(self, fUnitSize: float, fThicknessRatio: float) -> None:
        self.m_fFrequencyScale = (2.0 * math.pi) / float(fUnitSize)
        self.m_fThicknessRatio = float(fThicknessRatio)

    @staticmethod
    def fGetThicknessRatio(fWallThickness: float, fUnitSize: float) -> float:
        return float(fWallThickness) * 10.0 / float(fUnitSize)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        x, y, z = as_vec3(vecPt)
        dist = (
            math.sin(self.m_fFrequencyScale * x) * math.cos(self.m_fFrequencyScale * y)
            + math.sin(self.m_fFrequencyScale * y) * math.cos(self.m_fFrequencyScale * z)
            + math.sin(self.m_fFrequencyScale * z) * math.cos(self.m_fFrequencyScale * x)
        )
        return float(abs(dist) - 0.5 * self.m_fThicknessRatio)


class ImplicitSphere(IImplicit):
    def __init__(self, vecCentre: Vector3Like, fRadius: float) -> None:
        self.m_vecCentre = as_np3(vecCentre)
        self.m_fRadius = float(fRadius)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        return float(np.linalg.norm(as_np3(vecPt) - self.m_vecCentre) - self.m_fRadius)


class ImplicitGenus(IImplicit):
    def __init__(self, fGap: float) -> None:
        self.m_fGap = float(fGap)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        x, y, z = as_vec3(vecPt)
        return float(
            2.0 * y * (y * y - 3.0 * x * x) * (1.0 - z * z)
            + (x * x + y * y) ** 2
            - (9.0 * z * z - 1.0) * (1.0 - z * z)
            - self.m_fGap
        )


class ImplicitSuperEllipsoid(IImplicit):
    def __init__(
        self,
        vecCentre: Vector3Like,
        fAx: float,
        fAy: float,
        fAz: float,
        fEpsilon1: float,
        fEpsilon2: float,
    ) -> None:
        self.m_vecCentre = as_np3(vecCentre)
        self.m_fAx = float(fAx)
        self.m_fAy = float(fAy)
        self.m_fAz = float(fAz)
        self.m_fEpsilon1 = float(fEpsilon1)
        self.m_fEpsilon2 = float(fEpsilon2)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        x, y, z = as_np3(vecPt)
        d_x = abs(x + self.m_vecCentre[0]) / self.m_fAx
        d_y = abs(y + self.m_vecCentre[1]) / self.m_fAy
        d_z = abs(z + self.m_vecCentre[2]) / self.m_fAz
        dist = (
            (d_x ** (2.0 / self.m_fEpsilon2) + d_y ** (2.0 / self.m_fEpsilon2))
            ** (self.m_fEpsilon2 / self.m_fEpsilon1)
            + d_z ** (2.0 / self.m_fEpsilon1)
        )
        return float(dist - 1.0)


__all__ = [
    "ImplicitGyroid",
    "ImplicitSphere",
    "ImplicitGenus",
    "ImplicitSuperEllipsoid",
]
