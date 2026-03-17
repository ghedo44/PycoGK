from __future__ import annotations

from picogk import Lattice
from shape_kernel import SplineOperations, Uf
from shape_kernel._types import as_np3, as_vec3

from .._helpers import _add_polyline_beam
from ..beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell
from .i_lattice_type import ILatticeType


class RandomSplineLattice(ILatticeType):
	def __init__(self, nPasses: int = 1) -> None:
		self.m_nPasses = int(nPasses)
		self.m_dX = 0.0
		self.m_dY = 0.0
		self.m_dZ = 0.0

	def AddCell(self, oLattice: Lattice, xCell: IUnitCell, xBeamThickness: IBeamThickness, nSubSamples: int = 2) -> None:
		vecSize = xCell.oGetCellBounding().vecSize()
		self.m_dX = float(vecSize[0])
		self.m_dY = float(vecSize[1])
		self.m_dZ = float(vecSize[2])

		aCornerPoints = xCell.aGetCornerPoints()
		for _ in range(self.m_nPasses):
			for i, vecStart in enumerate(aCornerPoints):
				j = i
				while j == i:
					j = int(Uf.fGetRandomLinear(0.0, float(len(aCornerPoints))))

				aPoints = [
					as_vec3(vecStart),
					as_vec3(as_np3(xCell.vecGetCellCentre()) + as_np3(self.vecGetNoise())),
					as_vec3(aCornerPoints[j]),
				]
				aSplinePoints = SplineOperations.aGetNURBSpline(aPoints, 20)
				_add_polyline_beam(oLattice, aSplinePoints, xBeamThickness)

	def vecGetNoise(self) -> tuple[float, float, float]:
		return (
			Uf.fGetRandomLinear(-0.3 * self.m_dX, 0.3 * self.m_dX),
			Uf.fGetRandomLinear(-0.3 * self.m_dY, 0.3 * self.m_dY),
			Uf.fGetRandomLinear(-0.3 * self.m_dZ, 0.3 * self.m_dZ),
		)


__all__ = ["RandomSplineLattice"]