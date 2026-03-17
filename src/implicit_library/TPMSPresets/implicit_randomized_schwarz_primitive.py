from __future__ import annotations

import math

from shape_kernel._types import Vector3Like, as_np3, as_vec3

from ..i_implicit import IImplicit
from ..random_deformation_field import RandomDeformationField


class ImplicitRandomizedSchwarzPrimitive(IImplicit):
	def __init__(self, fUnitSize: float, fWallThickness: float, oField: RandomDeformationField) -> None:
		self.m_fFrequencyScale = (2.0 * math.pi) / float(fUnitSize)
		self.m_fWallThickness = float(fWallThickness)
		self.m_oRandomField = oField

	def fSignedDistance(self, vecPt: Vector3Like) -> float:
		vecNoise = as_np3(self.m_oRandomField.vecGetData(vecPt))
		vecNewPt = as_np3(vecPt) + vecNoise
		dX, dY, dZ = as_vec3(vecNewPt)
		dDist = (
			math.cos(self.m_fFrequencyScale * dX)
			+ math.cos(self.m_fFrequencyScale * dY)
			+ math.cos(self.m_fFrequencyScale * dZ)
		)
		return abs(dDist) - 0.5 * self.m_fWallThickness


__all__ = ["ImplicitRandomizedSchwarzPrimitive"]