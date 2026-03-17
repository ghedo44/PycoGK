from __future__ import annotations

from picogk import Lattice
from shape_kernel._types import as_np3, as_vec3

from .._helpers import _add_sampled_beam
from ..beam_thickness import IBeamThickness
from ..unit_cells import IUnitCell
from .i_lattice_type import ILatticeType


class OctahedronLattice(ILatticeType):
	def AddCell(self, oLattice: Lattice, xCell: IUnitCell, xBeamThickness: IBeamThickness, nSubSamples: int = 2) -> None:
		aCornerPoints = xCell.aGetCornerPoints()
		if len(aCornerPoints) != 8:
			raise ValueError("Octahedron Lattice only supports Unit Cells with 8 Corners.")

		pts = [as_np3(point) for point in aCornerPoints]
		vecLowerFace = as_vec3(0.25 * (pts[0] + pts[1] + pts[2] + pts[3]))
		vecUpperFace = as_vec3(0.25 * (pts[4] + pts[5] + pts[6] + pts[7]))
		vecForwardFace = as_vec3(0.25 * (pts[4] + pts[5] + pts[0] + pts[1]))
		vecRightFace = as_vec3(0.25 * (pts[6] + pts[5] + pts[2] + pts[1]))
		vecBackwardFace = as_vec3(0.25 * (pts[6] + pts[7] + pts[2] + pts[3]))
		vecLeftFace = as_vec3(0.25 * (pts[4] + pts[7] + pts[0] + pts[3]))

		for vecPt1, vecPt2 in (
			(vecLowerFace, vecRightFace),
			(vecLowerFace, vecLeftFace),
			(vecLowerFace, vecForwardFace),
			(vecLowerFace, vecBackwardFace),
			(vecUpperFace, vecRightFace),
			(vecUpperFace, vecLeftFace),
			(vecUpperFace, vecForwardFace),
			(vecUpperFace, vecBackwardFace),
			(vecForwardFace, vecRightFace),
			(vecForwardFace, vecLeftFace),
			(vecBackwardFace, vecRightFace),
			(vecBackwardFace, vecLeftFace),
		):
			_add_sampled_beam(oLattice, vecPt1, vecPt2, xBeamThickness, nSubSamples)


__all__ = ["OctahedronLattice"]