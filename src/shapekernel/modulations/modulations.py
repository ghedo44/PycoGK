from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np
from picogk import Image

from .._types import Vector3Like, as_np3, clamp01

ImageLike = Image


class LineModulation:
    class ECoord(Enum):
        X = "X"
        Y = "Y"
        Z = "Z"

    RatioFunc = Callable[[float], float]

    def __init__(self, source: float | RatioFunc) -> None:
        self.m_fConstValue: float = 0.0
        self.m_aXValues: list[float] = []
        self.m_aYValues: list[float] = []

        if callable(source):
            self.m_oFunc = source
            return

        self.m_fConstValue = float(source)
        self.m_oFunc = self._const_line_func

    @classmethod
    def from_discrete(
        cls,
        aDiscretePoints: Sequence[Vector3Like],
        eValues: "LineModulation.ECoord",
        eAxis: "LineModulation.ECoord",
    ) -> "LineModulation":
        points = [as_np3(p) for p in aDiscretePoints]
        if not points:
            raise ValueError("aDiscretePoints cannot be empty")

        mod = cls(0.0)
        mod.m_aXValues = []
        mod.m_aYValues = []

        first_x = cls._coord(points[0], eAxis)
        first_y = cls._coord(points[0], eValues)
        mod.m_aXValues.append(first_x)
        mod.m_aYValues.append(first_y)

        for point in points[1:]:
            x_val = cls._coord(point, eAxis)
            y_val = cls._coord(point, eValues)
            if x_val > mod.m_aXValues[-1]:
                mod.m_aXValues.append(x_val)
                mod.m_aYValues.append(y_val)

        if mod.m_aXValues[0] > 0.0:
            mod.m_aXValues.insert(0, 0.0)
            mod.m_aYValues.insert(0, mod.m_aYValues[0])
        if mod.m_aXValues[-1] < 1.0:
            mod.m_aXValues.append(1.0)
            mod.m_aYValues.append(mod.m_aYValues[-1])

        mod.m_oFunc = mod._discrete_interp
        return mod

    @staticmethod
    def _coord(vecPt: np.ndarray, coord: "LineModulation.ECoord") -> float:
        if coord == LineModulation.ECoord.Y:
            return float(vecPt[1])
        if coord == LineModulation.ECoord.Z:
            return float(vecPt[2])
        return float(vecPt[0])

    def _const_line_func(self, fRatio: float) -> float:
        return self.m_fConstValue

    def _discrete_interp(self, fX: float) -> float:
        x = clamp01(fX)
        idx = int(np.searchsorted(self.m_aXValues, x, side="left"))
        upper = min(idx, len(self.m_aXValues) - 1)
        lower = max(upper - 1, 0)

        lower_x = self.m_aXValues[lower]
        upper_x = self.m_aXValues[upper]
        if upper_x == lower_x:
            return self.m_aYValues[lower]

        ratio = (x - lower_x) / (upper_x - lower_x)
        return self.m_aYValues[lower] + ratio * (self.m_aYValues[upper] - self.m_aYValues[lower])

    def fGetModulation(self, fRatio: float) -> float:
        return float(self.m_oFunc(float(fRatio)))

    def f_get_modulation(self, fRatio: float) -> float:
        return self.fGetModulation(fRatio)

    def __mul__(self, fFactor: float) -> "LineModulation":
        return LineModulation(lambda lr: float(fFactor) * self.fGetModulation(lr))

    def __rmul__(self, fFactor: float) -> "LineModulation":
        return self.__mul__(fFactor)

    def __add__(self, other: "LineModulation") -> "LineModulation":
        return LineModulation(lambda lr: self.fGetModulation(lr) + other.fGetModulation(lr))

    def __sub__(self, other: "LineModulation") -> "LineModulation":
        return LineModulation(lambda lr: self.fGetModulation(lr) - other.fGetModulation(lr))


@dataclass
class Distribution:
    m_fTotalLength: float
    m_oModulation: LineModulation


class GenericContour(Distribution):
    pass


class SurfaceModulation:
    class EInput(Enum):
        FUNC = "FUNC"
        IMAGE = "IMAGE"

    class ELine(Enum):
        FIRST = "FIRST"
        SECOND = "SECOND"

    MappingFunc = Callable[[float], float]
    RatioFunc = Callable[[float, float], float]

    def __init__(self, source: float | RatioFunc) -> None:
        self.m_fConstValue = 0.0
        self.m_oFunc: SurfaceModulation.RatioFunc
        self.m_eInput = self.EInput.FUNC
        self.m_eLine = self.ELine.SECOND
        self.m_oLineModulation: LineModulation | None = None
        self.m_oImage: ImageLike | None = None
        self.m_oMappingFunc: SurfaceModulation.MappingFunc | None = None

        if callable(source):
            self.m_oFunc = source
            return

        self.m_fConstValue = float(source)
        self.m_oFunc = self._const_surface_func

    @classmethod
    def from_line_modulation(
        cls,
        oLineModulation: LineModulation,
        eLine: "SurfaceModulation.ELine" = ELine.SECOND,
    ) -> "SurfaceModulation":
        mod = cls(0.0)
        mod.m_oLineModulation = oLineModulation
        mod.m_eLine = eLine
        mod.m_oFunc = mod._line_surface_func
        mod.m_eInput = mod.EInput.FUNC
        return mod

    @classmethod
    def from_image(cls, oImage: ImageLike, oMappingFunc: MappingFunc) -> "SurfaceModulation":
        mod = cls(0.0)
        mod.m_oImage = oImage
        mod.m_oMappingFunc = oMappingFunc
        mod.m_eInput = mod.EInput.IMAGE
        return mod

    def _const_surface_func(self, fPhi: float, fLengthRatio: float) -> float:
        return self.m_fConstValue

    def _line_surface_func(self, fPhi: float, fLengthRatio: float) -> float:
        if self.m_oLineModulation is None:
            raise RuntimeError("Line modulation source is not configured")
        if self.m_eLine == self.ELine.FIRST:
            return self.m_oLineModulation.fGetModulation(fPhi)
        return self.m_oLineModulation.fGetModulation(fLengthRatio)

    def oGetInputType(self) -> "SurfaceModulation.EInput":
        return self.m_eInput

    def fGetModulation(self, fPhi: float, fLengthRatio: float) -> float:
        if self.m_eInput == self.EInput.FUNC:
            return float(self.m_oFunc(float(fPhi), float(fLengthRatio)))

        if self.m_oImage is None or self.m_oMappingFunc is None:
            raise RuntimeError("Image modulation source is not configured")

        nXRange = int(self.m_oImage.nWidth) - 1
        nYRange = int(self.m_oImage.nHeight) - 1
        x = int(round(nXRange - fPhi * nXRange))
        y = int(round(fLengthRatio * nYRange))
        gray = float(self.m_oImage.fValue(x, y))
        return float(self.m_oMappingFunc(gray))

    def f_get_modulation(self, fPhi: float, fLengthRatio: float) -> float:
        return self.fGetModulation(fPhi, fLengthRatio)

    def __mul__(self, fFactor: float) -> "SurfaceModulation":
        return SurfaceModulation(lambda phi, lr: float(fFactor) * self.fGetModulation(phi, lr))

    def __rmul__(self, fFactor: float) -> "SurfaceModulation":
        return self.__mul__(fFactor)

    def __add__(self, other: "SurfaceModulation") -> "SurfaceModulation":
        return SurfaceModulation(lambda phi, lr: self.fGetModulation(phi, lr) + other.fGetModulation(phi, lr))

    def __sub__(self, other: "SurfaceModulation") -> "SurfaceModulation":
        return SurfaceModulation(lambda phi, lr: self.fGetModulation(phi, lr) - other.fGetModulation(phi, lr))
