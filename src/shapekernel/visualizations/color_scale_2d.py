from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Sequence


class IColorScale(ABC):
	@abstractmethod
	def clrGetColor(self, fValue: float) -> tuple[float, float, float, float]:
		raise NotImplementedError

	@abstractmethod
	def fGetMinValue(self) -> float:
		raise NotImplementedError

	@abstractmethod
	def fGetMaxValue(self) -> float:
		raise NotImplementedError


class LinearColorScale2D(IColorScale):
	def __init__(
		self,
		clrMin: Sequence[float],
		clrMax: Sequence[float],
		fMinValue: float,
		fMaxValue: float,
	) -> None:
		self.m_fMinValue = float(fMinValue)
		self.m_fMaxValue = float(fMaxValue)
		self.m_clrMin = tuple(float(v) for v in clrMin[:3])
		self.m_clrMax = tuple(float(v) for v in clrMax[:3])

	def fGetMinValue(self) -> float:
		return self.m_fMinValue

	def fGetMaxValue(self) -> float:
		return self.m_fMaxValue

	def fGetInterpolated(self, fValue1: float, fValue2: float, fValue: float) -> float:
		ratio = (fValue - self.m_fMinValue) / (self.m_fMaxValue - self.m_fMinValue)
		return fValue1 + ratio * (fValue2 - fValue1)

	def clrGetColor(self, fValue: float) -> tuple[float, float, float, float]:
		value = min(max(float(fValue), self.m_fMinValue), self.m_fMaxValue)
		r = self.fGetInterpolated(self.m_clrMin[0], self.m_clrMax[0], value)
		g = self.fGetInterpolated(self.m_clrMin[1], self.m_clrMax[1], value)
		b = self.fGetInterpolated(self.m_clrMin[2], self.m_clrMax[2], value)
		return (float(r), float(g), float(b), 1.0)


class SmoothColorScale2D(LinearColorScale2D):
	def fGetInterpolated(self, fValue1: float, fValue2: float, fValue: float) -> float:
		ratio = (fValue - self.m_fMinValue) / (self.m_fMaxValue - self.m_fMinValue)
		ratio = ratio * ratio * (3.0 - 2.0 * ratio)
		return fValue1 + ratio * (fValue2 - fValue1)


class CustomColorScale2D(LinearColorScale2D):
	def __init__(
		self,
		clrMin: Sequence[float],
		clrMax: Sequence[float],
		fMinValue: float,
		fMaxValue: float,
		fTransition: float,
		fSmoothness: float,
	) -> None:
		super().__init__(clrMin, clrMax, fMinValue, fMaxValue)
		self.m_fTransition = float(fTransition)
		self.m_fSmoothness = float(fSmoothness)

	def fGetInterpolated(self, fValue1: float, fValue2: float, fValue: float) -> float:
		x = float(fValue)
		s = max(1e-9, self.m_fSmoothness)
		t = self.m_fTransition
		ratio = 1.0 / (1.0 + math.exp(-(x - t) / s))
		return fValue1 + ratio * (fValue2 - fValue1)


__all__ = ["IColorScale", "LinearColorScale2D", "SmoothColorScale2D", "CustomColorScale2D"]
