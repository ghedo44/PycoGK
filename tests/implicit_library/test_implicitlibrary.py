from __future__ import annotations

import math

import pytest
from lattice_library import ConstantBeamThickness
from picogk import IImplicit

from implicit_library import (
	CombinedTrafo,
	FullWallLogic,
	FunctionalScaleTrafo,
	ImplicitLidinoid,
	ImplicitModular,
	ImplicitRadialGyroid,
	ImplicitSchwarzDiamond,
	ImplicitSchwarzPrimitive,
	NegativeVoidLogic,
	PositiveHalfWallLogic,
	RadialTrafo,
	RawGyroidTPMSPattern,
	RawSchwarzPrimitiveTPMSPattern,
	RawTransitionTPMSPattern,
	ScaleTrafo,
)


def test_scale_trafo() -> None:
	trafo = ScaleTrafo(2.0, 4.0, 5.0)
	assert trafo.Apply((10.0, 8.0, 15.0)) == pytest.approx((5.0, 2.0, 3.0))


def test_functional_scale_trafo() -> None:
	trafo = FunctionalScaleTrafo()
	x, y, z = trafo.Apply((20.0, 20.0, 50.0))
	assert z == pytest.approx(10.0)
	assert x == pytest.approx(4.0)
	assert y == pytest.approx(4.0)


def test_radial_and_combined_trafo() -> None:
	radial = RadialTrafo(10, 0.0)
	x, y, z = radial.Apply((1.0, 0.0, 3.0))
	assert x == pytest.approx(1.0)
	assert y == pytest.approx(0.0)
	assert z == pytest.approx(3.0)

	combined = CombinedTrafo([ScaleTrafo(2.0, 2.0, 2.0), ScaleTrafo(2.0, 2.0, 2.0)])
	assert combined.Apply((8.0, 8.0, 8.0)) == pytest.approx((2.0, 2.0, 2.0))


def test_raw_patterns_and_transition() -> None:
	gyro = RawGyroidTPMSPattern()
	prim = RawSchwarzPrimitiveTPMSPattern()
	trans = RawTransitionTPMSPattern()
	assert math.isfinite(gyro.fGetSignedDistance(0.2, 0.3, 0.4))
	assert math.isfinite(prim.fGetSignedDistance(0.2, 0.3, 0.4))
	assert math.isfinite(trans.fGetSignedDistance(0.2, 0.3, 0.4))


def test_splitting_logic_classes() -> None:
	full = FullWallLogic()
	half = PositiveHalfWallLogic()
	void = NegativeVoidLogic()
	assert full.fGetAdvancedSignedDistance(0.4, 0.2) == pytest.approx(0.3)
	assert half.fGetAdvancedSignedDistance(-0.4, 0.2) == pytest.approx(0.3)
	assert void.fGetAdvancedSignedDistance(-0.4, 0.2) == pytest.approx(-0.3)


def test_implicit_modular_composition() -> None:
	o = ImplicitModular(
		RawGyroidTPMSPattern(),
		ConstantBeamThickness(0.5),
		ScaleTrafo(10.0, 10.0, 10.0),
		FullWallLogic(),
	)
	assert math.isfinite(o.fSignedDistance((1.0, 2.0, 3.0)))


def test_tpms_presets_basic_eval() -> None:
	presets = [
		ImplicitLidinoid(10.0, 0.5),
		ImplicitRadialGyroid(24, 10.0, 0.5),
		ImplicitSchwarzDiamond(10.0, 0.5),
		ImplicitSchwarzPrimitive(10.0, 0.5),
	]
	for preset in presets:
		assert math.isfinite(preset.fSignedDistance((1.2, -0.3, 2.5)))


def test_implicit_objects_implement_interface() -> None:
	o = ImplicitModular(
		RawGyroidTPMSPattern(),
		ConstantBeamThickness(0.5),
		ScaleTrafo(10.0, 10.0, 10.0),
		FullWallLogic(),
	)
	assert isinstance(o, IImplicit)
	assert math.isfinite(o.fSignedDistance((1.0, 2.0, 3.0)))