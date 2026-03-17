from __future__ import annotations

from shape_kernel._types import Vector3Like

from lattice_library import IBeamThickness

from .coordinate_trafo import ICoordinateTrafo
from .i_implicit import IImplicit
from .raw_tpms_patterns import IRawTPMSPattern
from .splitting_logic import ISplittingLogic


class ImplicitModular(IImplicit):
	def __init__(
		self,
		xRawTPMSPattern: IRawTPMSPattern,
		xWallThickness: IBeamThickness,
		xCoordinateTrafo: ICoordinateTrafo,
		xSplittingLogic: ISplittingLogic,
	) -> None:
		self.m_xWallThickness = xWallThickness
		self.m_xCoordinateTrafo = xCoordinateTrafo
		self.m_xRawTPMSPattern = xRawTPMSPattern
		self.m_xSplittingLogic = xSplittingLogic

	def fSignedDistance(self, vecPt: Vector3Like) -> float:
		fX, fY, fZ = self.m_xCoordinateTrafo.Apply(vecPt)
		fRawSignedDistance = self.m_xRawTPMSPattern.fGetSignedDistance(fX, fY, fZ)
		fWallThickness = self.m_xWallThickness.fGetBeamThickness(vecPt)
		return self.m_xSplittingLogic.fGetAdvancedSignedDistance(fRawSignedDistance, fWallThickness)


__all__ = ["ImplicitModular"]