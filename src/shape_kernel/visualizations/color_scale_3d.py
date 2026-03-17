from __future__ import annotations

from .._types import as_np3
from ..utils import SplineOperations
from .color_scale_2d import IColorScale
from .rainbox_spectrum import ISpectrum


class ColorScale3D(IColorScale):
	def __init__(self, xSpectrum: ISpectrum, fMinValue: float, fMaxValue: float) -> None:
		self.m_fMinValue = float(fMinValue)
		self.m_fMaxValue = float(fMaxValue)
		smooth = SplineOperations.aGetNURBSpline(xSpectrum.aGetRawRGBList(), 500)
		self.m_aSmoothRGBList = [as_np3(p) for p in SplineOperations.aGetReparametrizedSpline(smooth, 500)]

	def fGetMinValue(self) -> float:
		return self.m_fMinValue

	def fGetMaxValue(self) -> float:
		return self.m_fMaxValue

	def clrGetColor(self, fValue: float) -> tuple[float, float, float, float]:
		value = min(max(float(fValue), self.m_fMinValue), self.m_fMaxValue)
		ratio = (value - self.m_fMinValue) / (self.m_fMaxValue - self.m_fMinValue)
		idx = int(ratio * (len(self.m_aSmoothRGBList) - 1))
		rgb = self.m_aSmoothRGBList[idx]
		return (float(rgb[0] / 255.0), float(rgb[1] / 255.0), float(rgb[2] / 255.0), 1.0)


__all__ = ["ColorScale3D"]
