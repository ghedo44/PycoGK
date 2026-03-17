from __future__ import annotations

import numpy as np

from picogk import Voxels
from shape_kernel._types import Vector3Like, as_np3
from shape_kernel.utils import Uf

from .i_beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell


class CellBasedBeamThickness(IBeamThickness):
	def __init__(self, fMinBeamThickness: float, fMaxBeamThickness: float) -> None:
		self.m_fMinBeamThickness = float(fMinBeamThickness)
		self.m_fMaxBeamThickness = float(fMaxBeamThickness)
		self.m_xCell: IUnitCell | None = None

	def UpdateCell(self, xCell: IUnitCell) -> None:
		self.m_xCell = xCell

	def fGetBeamThickness(self, vecPt: Vector3Like) -> float:
		if self.m_xCell is None:
			raise ValueError("No Unit Cell specified.")

		vecCentre = as_np3(self.m_xCell.vecGetCellCentre())
		vecPoint = as_np3(vecPt)
		fDist = float(np.linalg.norm(vecPoint - vecCentre))
		vecSize = as_np3(self.m_xCell.oGetCellBounding().vecSize())
		fHalfDiag = 0.5 * float(np.linalg.norm(vecSize))
		if fHalfDiag <= 1e-12:
			fRatio = 0.0
		else:
			fRatio = min(max(fDist / fHalfDiag, 0.0), 1.0)
		return Uf.fTransFixed(self.m_fMinBeamThickness, self.m_fMaxBeamThickness, fRatio)

	def SetBoundingVoxels(self, voxBounding: Voxels) -> None:
		return None


__all__ = ["CellBasedBeamThickness"]