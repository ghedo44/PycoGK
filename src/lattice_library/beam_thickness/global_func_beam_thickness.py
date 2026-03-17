from __future__ import annotations

from picogk import Voxels
from shape_kernel._types import Vector3Like, as_vec3
from shape_kernel.utils import Uf

from .i_beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell


class GlobalFuncBeamThickness(IBeamThickness):
	def __init__(self, fMinBeamThickness: float, fMaxBeamThickness: float) -> None:
		self.m_fMinBeamThickness = float(fMinBeamThickness)
		self.m_fMaxBeamThickness = float(fMaxBeamThickness)

	def UpdateCell(self, xCell: IUnitCell) -> None:
		return None

	def fGetBeamThickness(self, vecPt: Vector3Like) -> float:
		pt = as_vec3(vecPt)
		fRatio = min(max(0.02 * float(pt[0]), 0.0), 1.0)
		return Uf.fTransFixed(self.m_fMinBeamThickness, self.m_fMaxBeamThickness, fRatio)

	def SetBoundingVoxels(self, voxBounding: Voxels) -> None:
		return None


__all__ = ["GlobalFuncBeamThickness"]