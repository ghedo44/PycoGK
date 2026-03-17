from __future__ import annotations

import math

from shape_kernel._types import Vector3Like, as_vec3
from shape_kernel.utils import VecOperations

from ..i_implicit import IImplicit


class ImplicitRadialGyroid(IImplicit):
	def __init__(self, nUnitsPerRound: int, fUnitSizeInZ: float, fWallThickness: float) -> None:
		self.m_fFrequencyScale = (2.0 * math.pi) / float(fUnitSizeInZ)
		self.m_fWallThickness = float(fWallThickness)
		self.m_nSamplesPerRound = int(nUnitsPerRound)

	def fSignedDistance(self, vecPt: Vector3Like) -> float:
		pt = as_vec3(vecPt)
		fRadius = VecOperations.fGetRadius(pt)
		dPhi = (2.0 * math.pi) / float(self.m_nSamplesPerRound)
		fPhi = VecOperations.fGetPhi(pt) + math.pi
		fPhiIntervals = fPhi / dPhi
		fUnitSize = (2.0 * math.pi) / self.m_fFrequencyScale
		dX = fRadius
		dY = fPhiIntervals * fUnitSize
		dZ = float(pt[2])

		dDist = (
			math.sin(self.m_fFrequencyScale * dX) * math.cos(self.m_fFrequencyScale * dY)
			+ math.sin(self.m_fFrequencyScale * dY) * math.cos(self.m_fFrequencyScale * dZ)
			+ math.sin(self.m_fFrequencyScale * dZ) * math.cos(self.m_fFrequencyScale * dX)
		)
		return abs(dDist) - 0.5 * self.m_fWallThickness


__all__ = ["ImplicitRadialGyroid"]