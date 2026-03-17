from __future__ import annotations

import math

from shape_kernel._types import Vector3Like, as_vec3

from picogk import IImplicit


class ImplicitSchwarzDiamond(IImplicit):
	def __init__(self, fUnitSize: float, fWallThickness: float) -> None:
		self.m_fFrequencyScale = 0.5 * (2.0 * math.pi) / float(fUnitSize)
		self.m_fWallThickness = float(fWallThickness)

	def fSignedDistance(self, vecPt: Vector3Like) -> float:
		dX, dY, dZ = as_vec3(vecPt)
		dDist = (
			math.cos(self.m_fFrequencyScale * dX) * math.cos(self.m_fFrequencyScale * dY) * math.cos(self.m_fFrequencyScale * dZ)
			- math.sin(self.m_fFrequencyScale * dX) * math.sin(self.m_fFrequencyScale * dY) * math.sin(self.m_fFrequencyScale * dZ)
		)
		return abs(dDist) - 0.5 * self.m_fWallThickness


__all__ = ["ImplicitSchwarzDiamond"]