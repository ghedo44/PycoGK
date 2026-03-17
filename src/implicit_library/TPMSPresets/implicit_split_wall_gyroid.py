from __future__ import annotations

import math

from shape_kernel._types import Vector3Like, as_vec3

from picogk import IImplicit


class ImplicitSplitWallGyroid(IImplicit):
	def __init__(self, fUnitSize: float, fWallThickness: float, bSide: bool) -> None:
		self.m_fFrequencyScale = (2.0 * math.pi) / float(fUnitSize)
		self.m_fWallThickness = float(fWallThickness)
		self.m_bSide = bool(bSide)

	def fSignedDistance(self, vecPt: Vector3Like) -> float:
		dX, dY, dZ = as_vec3(vecPt)
		dDist = (
			math.sin(self.m_fFrequencyScale * dX) * math.cos(self.m_fFrequencyScale * dY)
			+ math.sin(self.m_fFrequencyScale * dY) * math.cos(self.m_fFrequencyScale * dZ)
			+ math.sin(self.m_fFrequencyScale * dZ) * math.cos(self.m_fFrequencyScale * dX)
		)
		if self.m_bSide:
			return max(dDist, abs(dDist) - 0.5 * self.m_fWallThickness)
		return max(-dDist, abs(dDist) - 0.5 * self.m_fWallThickness)


__all__ = ["ImplicitSplitWallGyroid"]