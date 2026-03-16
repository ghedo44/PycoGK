from __future__ import annotations

import math

import pytest

from shapekernel import BaseBox, LineDecimation, ListOperations, LocalFrame, SplineOperations, Uf, VecOperations


def test_base_box_from_bbox_reconstructs_corners() -> None:
    box = BaseBox.from_bbox(((-1.0, -2.0, 0.0), (3.0, 4.0, 10.0)))

    assert box.vecGetSurfacePoint(-1.0, -1.0, 0.0) == pytest.approx((-1.0, -2.0, 0.0))
    assert box.vecGetSurfacePoint(1.0, 1.0, 1.0) == pytest.approx((3.0, 4.0, 10.0))


def test_list_operations_cover_sampling_and_extrema() -> None:
    values = [0.0, 10.0, 20.0]

    assert ListOperations.aOverSampleList(values, 2) == pytest.approx([0.0, 5.0, 10.0, 15.0, 20.0])
    assert ListOperations.aSubsampleList(values + [30.0, 40.0], 2) == pytest.approx([0.0, 20.0, 40.0])
    assert ListOperations.iGetIndexOfMaxValue(values) == 2
    assert ListOperations.iGetIndexOfMinValue(values) == 0


def test_line_decimation_preserves_endpoints_for_collinear_points() -> None:
    points = [(0.0, 0.0, z) for z in range(6)]
    decimated = LineDecimation(points, 0.01).aGetDecimatedPoints()

    assert decimated[0] == pytest.approx((0.0, 0.0, 0.0))
    assert decimated[-1] == pytest.approx((0.0, 0.0, 5.0))
    assert len(decimated) == 2


def test_spline_operations_interpolation_spacing_and_transforms() -> None:
    line = SplineOperations.aGetLinearInterpolation((0.0, 0.0, 0.0), (0.0, 0.0, 10.0), 6)
    assert len(line) == 6
    assert SplineOperations.aGetAveragePointSpacing(line) == pytest.approx(2.0)

    rotated = SplineOperations.aRotateListAroundZ([(1.0, 0.0, 0.0)], math.pi / 2.0)
    assert rotated[0] == pytest.approx((0.0, 1.0, 0.0), abs=1e-6)

    shifted = SplineOperations.aTranslateList(line, (1.0, 2.0, 3.0))
    assert shifted[0] == pytest.approx((1.0, 2.0, 3.0))

    first, second = SplineOperations.aSplitLists(line, 3)
    assert len(first) == 3
    assert len(second) == 3
    assert SplineOperations.aCombineLists([first, second]) == pytest.approx(line)


def test_spline_operations_frame_translation_and_closest_point() -> None:
    frame = LocalFrame((10.0, 0.0, 0.0))
    points = [(0.0, 0.0, 0.0), (0.0, 0.0, 5.0)]
    translated = SplineOperations.aTranslateListOntoFrame(frame, points)

    assert translated[0] == pytest.approx((10.0, 0.0, 0.0))
    assert SplineOperations.vecGetClosestPoint(translated, (11.0, 0.0, 0.5)) == pytest.approx((10.0, 0.0, 0.0))


def test_useful_formulas_fibonacci_and_shape_radii() -> None:
    circle = Uf.aGetFibonacciCirlePoints(5.0, 32)
    sphere = Uf.aGetFibonacciSpherePoints(3.0, 24)

    assert len(circle) == 32
    assert len(sphere) == 24
    assert max(VecOperations.fGetRadius(p) for p in circle) <= 5.0 + 1e-6
    assert max(math.sqrt(sum(c * c for c in p)) for p in sphere) <= 3.000001

    assert Uf.fGetSuperShapeRadius(0.0, Uf.ESuperShape.HEX) > 0.0
    assert Uf.fGetPolygonRadius(0.0, Uf.EPolygon.QUAD) > 0.0
