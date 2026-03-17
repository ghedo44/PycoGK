from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from picogk import Image
from .line_modulation import LineModulation


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
        self.m_oImage: Image | None = None
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
    def from_image(cls, oImage: Image, oMappingFunc: MappingFunc) -> "SurfaceModulation":
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
