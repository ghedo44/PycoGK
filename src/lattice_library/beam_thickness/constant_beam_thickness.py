from __future__ import annotations

from picogk import Voxels
from shape_kernel._types import Vector3Like

from .i_beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell


class ConstantBeamThickness(IBeamThickness):
	def __init__(self, fBeamThickness: float) -> None:
		self.m_fBeamThickness = float(fBeamThickness)

	def fGetBeamThickness(self, vecPt: Vector3Like) -> float:
		return self.m_fBeamThickness

	def UpdateCell(self, xCell: IUnitCell) -> None:
		return None

	def SetBoundingVoxels(self, voxBounding: Voxels) -> None:
		return None


__all__ = ["ConstantBeamThickness"]