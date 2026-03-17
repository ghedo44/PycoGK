from __future__ import annotations

from picogk import Lattice

from .._helpers import _add_sampled_beam
from ..beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell
from .i_lattice_type import ILatticeType


class BodyCentreLattice(ILatticeType):
	def AddCell(self, oLattice: Lattice, xCell: IUnitCell, xBeamThickness: IBeamThickness, nSubSamples: int = 2) -> None:
		aCornerPoints = xCell.aGetCornerPoints()
		if len(aCornerPoints) != 8:
			raise ValueError("Body Centre Lattice only supports Unit Cells with 8 Corners.")

		vecCPt = xCell.vecGetCellCentre()
		for vecCorner in aCornerPoints:
			_add_sampled_beam(oLattice, vecCorner, vecCPt, xBeamThickness, nSubSamples)


__all__ = ["BodyCentreLattice"]