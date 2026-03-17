from __future__ import annotations

import numpy as np

from picogk import Voxels
from shape_kernel._types import Vector3Like, as_np3
from shape_kernel.utils import Uf

from .i_beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell


class BoundaryBeamThickness(IBeamThickness):
	def __init__(self, fMinBeamThickness: float, fMaxBeamThickness: float) -> None:
		self.m_fMinBeamThickness = float(fMinBeamThickness)
		self.m_fMaxBeamThickness = float(fMaxBeamThickness)
		self.m_voxBounding: Voxels | None = None

	def fGetBeamThickness(self, vecPt: Vector3Like) -> float:
		if self.m_voxBounding is None:
			raise ValueError("No Boundary Voxels specified.")

		bSuccess, vecSurf = self.m_voxBounding.bClosestPointOnSurface(vecPt)
		if bSuccess is False:
			raise ValueError("No Closest Point found.")

		fDistance = float(np.linalg.norm(as_np3(vecSurf) - as_np3(vecPt)))
		return Uf.fTransSmooth(self.m_fMaxBeamThickness, self.m_fMinBeamThickness, fDistance, 15.0, 5.0)

	def UpdateCell(self, xCell: IUnitCell) -> None:
		return None

	def SetBoundingVoxels(self, voxBounding: Voxels) -> None:
		self.m_voxBounding = voxBounding


__all__ = ["BoundaryBeamThickness"]