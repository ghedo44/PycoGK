from __future__ import annotations

import math
from abc import ABC, abstractmethod

from shape_kernel.utils import Uf


class IRawTPMSPattern(ABC):
	@abstractmethod
	def fGetSignedDistance(self, fX: float, fY: float, fZ: float) -> float:
		raise NotImplementedError


class RawGyroidTPMSPattern(IRawTPMSPattern):
	m_fFrequencyScale = 2.0 * math.pi

	def fGetSignedDistance(self, fX: float, fY: float, fZ: float) -> float:
		return (
			math.sin(self.m_fFrequencyScale * fX) * math.cos(self.m_fFrequencyScale * fY)
			+ math.sin(self.m_fFrequencyScale * fY) * math.cos(self.m_fFrequencyScale * fZ)
			+ math.sin(self.m_fFrequencyScale * fZ) * math.cos(self.m_fFrequencyScale * fX)
		)


class RawLidinoidTPMSPattern(IRawTPMSPattern):
	m_fFrequencyScale = 0.5 * (2.0 * math.pi)

	def fGetSignedDistance(self, fX: float, fY: float, fZ: float) -> float:
		return (
			+0.5
			* (
				math.sin(2.0 * self.m_fFrequencyScale * fX) * math.cos(self.m_fFrequencyScale * fY) * math.sin(self.m_fFrequencyScale * fZ)
				+ math.sin(2.0 * self.m_fFrequencyScale * fY) * math.cos(self.m_fFrequencyScale * fZ) * math.sin(self.m_fFrequencyScale * fX)
				+ math.sin(2.0 * self.m_fFrequencyScale * fZ) * math.cos(self.m_fFrequencyScale * fX) * math.sin(self.m_fFrequencyScale * fY)
			)
			- 0.5
			* (
				math.cos(2.0 * self.m_fFrequencyScale * fX) * math.cos(2.0 * self.m_fFrequencyScale * fY)
				+ math.cos(2.0 * self.m_fFrequencyScale * fY) * math.cos(2.0 * self.m_fFrequencyScale * fZ)
				+ math.cos(2.0 * self.m_fFrequencyScale * fZ) * math.cos(2.0 * self.m_fFrequencyScale * fX)
			)
		)


class RawSchwarzPrimitiveTPMSPattern(IRawTPMSPattern):
	m_fFrequencyScale = 2.0 * math.pi

	def fGetSignedDistance(self, fX: float, fY: float, fZ: float) -> float:
		return (
			math.cos(self.m_fFrequencyScale * fX)
			+ math.cos(self.m_fFrequencyScale * fY)
			+ math.cos(self.m_fFrequencyScale * fZ)
		)


class RawSchwarzDiamondTPMSPattern(IRawTPMSPattern):
	m_fFrequencyScale = 0.5 * (2.0 * math.pi)

	def fGetSignedDistance(self, fX: float, fY: float, fZ: float) -> float:
		return (
			math.cos(self.m_fFrequencyScale * fX) * math.cos(self.m_fFrequencyScale * fY) * math.cos(self.m_fFrequencyScale * fZ)
			- math.sin(self.m_fFrequencyScale * fX) * math.sin(self.m_fFrequencyScale * fY) * math.sin(self.m_fFrequencyScale * fZ)
		)


class RawTransitionTPMSPattern(IRawTPMSPattern):
	def __init__(self) -> None:
		self.m_xTPMS_01 = RawSchwarzDiamondTPMSPattern()
		self.m_xTPMS_02 = RawSchwarzPrimitiveTPMSPattern()

	def fGetSignedDistance(self, fX: float, fY: float, fZ: float) -> float:
		fDist_01 = self.m_xTPMS_01.fGetSignedDistance(fX, fY, fZ)
		fDist_02 = self.m_xTPMS_02.fGetSignedDistance(fX, fY, fZ)
		fRatio = min(max((fX + 2.0) / 5.0, 0.0), 1.0)
		return Uf.fTransFixed(fDist_01, fDist_02, fRatio)


__all__ = [
	"IRawTPMSPattern",
	"RawGyroidTPMSPattern",
	"RawLidinoidTPMSPattern",
	"RawSchwarzPrimitiveTPMSPattern",
	"RawSchwarzDiamondTPMSPattern",
	"RawTransitionTPMSPattern",
]