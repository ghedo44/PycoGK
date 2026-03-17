from __future__ import annotations

import math
from typing import Any, cast

import pytest
from picogk._types import vec3_tuple

from lattice_library import (
	BodyCentreLattice,
	BoundaryBeamThickness,
	CellBasedBeamThickness,
	ConformalCellArray,
	ConformalShowcaseShapes,
	ConstantBeamThickness,
	CuboidCell,
	GlobalFuncBeamThickness,
	OctahedronLattice,
	RandomSplineLattice,
	RegularCellArray,
	RegularUnitCell,
)


class FakeLattice:
	def __init__(self) -> None:
		self.beams: list[tuple[tuple[float, float, float], tuple[float, float, float], float, float]] = []

	def AddBeam(self, vecPt1, vecPt2, fRadius1, fRadius2) -> None:
		self.beams.append((tuple(vecPt1), tuple(vecPt2), float(fRadius1), float(fRadius2)))


class FakeVoxels:
	def __init__(self, bbox=((0.0, 0.0, 0.0), (10.0, 10.0, 10.0))) -> None:
		self._bbox = bbox

	def CalculateProperties(self):
		return 1000.0, self._bbox

	def bClosestPointOnSurface(self, vecPt):
		return True, (float(vecPt[0]), float(vecPt[1]), 15.0)


def test_cuboid_cell_matches_basic_geometry() -> None:
	cell = CuboidCell(
		(0.0, 0.0, 0.0),
		(0.0, 2.0, 0.0),
		(4.0, 2.0, 0.0),
		(4.0, 0.0, 0.0),
		(0.0, 0.0, 6.0),
		(0.0, 2.0, 6.0),
		(4.0, 2.0, 6.0),
		(4.0, 0.0, 6.0),
	)

	assert cell.vecGetCellCentre() == pytest.approx((2.0, 1.0, 3.0))
	assert vec3_tuple(cell.oGetCellBounding().vecMin) == pytest.approx((0.0, 0.0, 0.0))
	assert vec3_tuple(cell.oGetCellBounding().vecMax) == pytest.approx((4.0, 2.0, 6.0))


def test_regular_unit_cell_builds_one_cell() -> None:
	array = RegularUnitCell(10.0, 20.0, 30.0)
	assert len(array.aGetUnitCells()) == 1


def test_regular_cell_array_uses_bounding_box_grid() -> None:
	array = RegularCellArray(cast(Any, FakeVoxels(bbox=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))), 10.0, 10.0, 10.0)
	assert len(array.aGetUnitCells()) == 8


def test_body_centre_lattice_adds_eight_beams() -> None:
	cell = RegularUnitCell(10.0, 10.0, 10.0).aGetUnitCells()[0]
	lattice = FakeLattice()
	BodyCentreLattice().AddCell(lattice, cell, ConstantBeamThickness(2.0), 2)
	assert len(lattice.beams) == 8
	assert all(beam[2:] == (1.0, 1.0) for beam in lattice.beams)


def test_octahedron_lattice_adds_twelve_beams() -> None:
	cell = RegularUnitCell(10.0, 10.0, 10.0).aGetUnitCells()[0]
	lattice = FakeLattice()
	OctahedronLattice().AddCell(lattice, cell, ConstantBeamThickness(4.0), 2)
	assert len(lattice.beams) == 12
	assert all(beam[2:] == (2.0, 2.0) for beam in lattice.beams)


def test_random_spline_lattice_adds_segmented_beams() -> None:
	cell = RegularUnitCell(10.0, 10.0, 10.0).aGetUnitCells()[0]
	lattice = FakeLattice()
	RandomSplineLattice().AddCell(lattice, cell, ConstantBeamThickness(2.0), 2)
	assert len(lattice.beams) == 8 * 19


def test_cell_based_beam_thickness_requires_cell_and_interpolates() -> None:
	beam = CellBasedBeamThickness(1.0, 3.0)
	with pytest.raises(ValueError):
		beam.fGetBeamThickness((0.0, 0.0, 0.0))

	cell = RegularUnitCell(10.0, 10.0, 10.0).aGetUnitCells()[0]
	beam.UpdateCell(cell)
	assert beam.fGetBeamThickness(cell.vecGetCellCentre()) == pytest.approx(1.0)


def test_boundary_beam_thickness_uses_surface_distance() -> None:
	beam = BoundaryBeamThickness(1.0, 5.0)
	beam.SetBoundingVoxels(cast(Any, FakeVoxels()))
	value = beam.fGetBeamThickness((0.0, 0.0, 10.0))
	assert 1.0 <= value <= 5.0


def test_global_func_beam_thickness_clamps_ratio() -> None:
	beam = GlobalFuncBeamThickness(1.0, 3.0)
	assert beam.fGetBeamThickness((0.0, 0.0, 0.0)) == pytest.approx(1.0)
	assert beam.fGetBeamThickness((100.0, 0.0, 0.0)) == pytest.approx(3.0)


def test_conformal_cell_array_builds_expected_count() -> None:
	box = ConformalShowcaseShapes.oGetBox_01()
	array = ConformalCellArray(box, 2, 3, 4)
	assert len(array.aGetUnitCells()) == 24


def test_showcase_segment_factory_returns_pipe_segment() -> None:
	segment = ConformalShowcaseShapes.oGetSegment_01()
	pt = segment.vecGetSurfacePoint(0.5, 0.5, 0.5)
	assert len(pt) == 3
	assert math.isfinite(pt[0])