from __future__ import annotations

from abc import ABC, abstractmethod

from shape_kernel._types import Vector3Like, as_vec3
from shape_kernel.utils import Uf, VecOperations


class ICoordinateTrafo(ABC):
	@abstractmethod
	def Apply(self, vecPt: Vector3Like) -> tuple[float, float, float]:
		raise NotImplementedError


class ScaleTrafo(ICoordinateTrafo):
	def __init__(self, fUnitX: float, fUnitY: float, fUnitZ: float) -> None:
		self.m_fUnitX = float(fUnitX)
		self.m_fUnitY = float(fUnitY)
		self.m_fUnitZ = float(fUnitZ)

	def Apply(self, vecPt: Vector3Like) -> tuple[float, float, float]:
		pt = as_vec3(vecPt)
		return (
			float(pt[0] / self.m_fUnitX),
			float(pt[1] / self.m_fUnitY),
			float(pt[2] / self.m_fUnitZ),
		)


class FunctionalScaleTrafo(ICoordinateTrafo):
	def Apply(self, vecPt: Vector3Like) -> tuple[float, float, float]:
		pt = as_vec3(vecPt)
		fRatio = min(max(float(pt[2]) / 50.0, 0.0), 1.0)
		fUnit = Uf.fTransFixed(20.0, 5.0, fRatio)
		return (float(pt[0] / fUnit), float(pt[1] / fUnit), 10.0)


class RadialTrafo(ICoordinateTrafo):
	def __init__(self, nSamplesPerRound: int, dPhiPerZ: float) -> None:
		self.m_nSamplesPerRound = int(nSamplesPerRound)
		self.m_dPhiPerZ = float(dPhiPerZ)

	def Apply(self, vecPt: Vector3Like) -> tuple[float, float, float]:
		pt = as_vec3(vecPt)
		fZ = float(pt[2])
		fRadius = VecOperations.fGetRadius(pt)
		fPhi = VecOperations.fGetPhi(pt) + self.m_dPhiPerZ * fZ
		return (fRadius, float(self.m_nSamplesPerRound * fPhi), fZ)


class CombinedTrafo(ICoordinateTrafo):
	def __init__(self, aTrafos: list[ICoordinateTrafo]) -> None:
		self.m_aTrafos = aTrafos

	def Apply(self, vecPt: Vector3Like) -> tuple[float, float, float]:
		fX, fY, fZ = as_vec3(vecPt)
		current: tuple[float, float, float] = (fX, fY, fZ)
		for xTrafo in self.m_aTrafos:
			current = xTrafo.Apply(current)
		return current


__all__ = [
	"ICoordinateTrafo",
	"ScaleTrafo",
	"FunctionalScaleTrafo",
	"RadialTrafo",
	"CombinedTrafo",
]
