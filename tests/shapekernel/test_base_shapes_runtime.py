from __future__ import annotations

import math

import pytest

from picogk import Mesh, Voxels, go
from shapekernel import (
    BaseBox,
    BaseCone,
    BaseCylinder,
    BaseLens,
    BaseLogoBox,
    BasePipe,
    BasePipeSegment,
    BaseRevolve,
    BaseRing,
    BaseSphere,
    Frames,
    GenericContour,
    LatticeManifold,
    LatticePipe,
    LineModulation,
    LocalFrame,
    TangentialControlSpline,
)

from tests._helpers import runtime_available


class _TestImage:
    nWidth = 8
    nHeight = 6

    def fValue(self, x: int, y: int) -> float:
        return float((x + y) % 4) / 3.0


pytestmark = pytest.mark.skipif(not runtime_available(), reason="PicoGK runtime not available")


def _example_frames() -> Frames:
    spline = TangentialControlSpline.from_frames(
        LocalFrame((-10.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        LocalFrame((10.0, 12.0, 20.0), (0.0, 1.0, 1.0)),
    )
    return Frames.from_points_and_target_x(spline.aGetPoints(40), (0.0, 1.0, 0.0), 1.0)


@pytest.mark.parametrize(
    ("name", "factory", "expects_lattice"),
    [
        ("box", lambda: BaseBox.from_frame(LocalFrame((0.0, 0.0, 0.0)), 12.0, 8.0, 6.0), False),
        ("cone", lambda: BaseCone(LocalFrame((0.0, 0.0, 0.0)), 16.0, 6.0, 2.0), False),
        ("cylinder", lambda: BaseCylinder.from_frame(LocalFrame((0.0, 0.0, 0.0)), 14.0, 5.0), False),
        ("lens", lambda: BaseLens(LocalFrame((0.0, 0.0, 0.0)), 6.0, 2.0, 8.0), False),
        ("logo_box", lambda: BaseLogoBox(LocalFrame((0.0, 0.0, 0.0)), 8.0, 10.0, _TestImage(), lambda g: 2.0 * g), False), # pyright: ignore[reportArgumentType]
        ("pipe", lambda: BasePipe.from_frame(LocalFrame((0.0, 0.0, 0.0)), 16.0, 2.0, 6.0), False),
        (
            "pipe_segment",
            lambda: BasePipeSegment.from_frame(
                LocalFrame((0.0, 0.0, 0.0)),
                18.0,
                2.0,
                6.0,
                LineModulation(lambda lr: 0.4 * math.pi * lr),
                LineModulation(lambda lr: math.pi * (0.35 + 0.1 * math.sin(4.0 * lr))),
                BasePipeSegment.EMethod.MID_RANGE,
            ),
            False,
        ),
        (
            "revolve",
            lambda: BaseRevolve(
                LocalFrame((0.0, 0.0, 0.0)),
                BaseRevolve.aGetFramesFromContour(GenericContour(15.0, LineModulation(lambda lr: 4.0 + 2.0 * lr))),
                1.5,
                2.5,
            ),
            False,
        ),
        ("ring", lambda: BaseRing(LocalFrame((0.0, 0.0, 0.0)), 12.0, 3.0), False),
        ("sphere", lambda: BaseSphere(LocalFrame((0.0, 0.0, 0.0)), 5.0), False),
        ("lattice_pipe", lambda: LatticePipe.from_frames(_example_frames(), 2.5), True),
        ("lattice_manifold", lambda: LatticeManifold.from_frames(_example_frames(), 2.5, 45.0, True, 0.3), True),
    ],
)
def test_shapekernel_base_shapes_voxelize_to_non_empty_mesh(name: str, factory, expects_lattice: bool) -> None:
    def task() -> None:
        shape = factory()

        if hasattr(shape, "SetPolarSteps"):
            shape.SetPolarSteps(36)
        if hasattr(shape, "SetAzimuthalSteps"):
            shape.SetAzimuthalSteps(36)
        if hasattr(shape, "SetRadialSteps"):
            shape.SetRadialSteps(8)
        if hasattr(shape, "SetLengthSteps"):
            shape.SetLengthSteps(12)
        if hasattr(shape, "SetWidthSteps"):
            shape.SetWidthSteps(8)
        if hasattr(shape, "SetDepthSteps"):
            shape.SetDepthSteps(8)
        if hasattr(shape, "SetHeightSteps"):
            shape.SetHeightSteps(8)

        if expects_lattice:
            with Voxels.from_lattice(shape.latConstruct()) as voxels:
                with Mesh.from_voxels(voxels) as mesh:
                    assert mesh.vertex_count() > 0, name
                    assert mesh.triangle_count() > 0, name
        else:
            with shape.voxConstruct() as voxels:
                with Mesh.from_voxels(voxels) as mesh:
                    assert mesh.vertex_count() > 0, name
                    assert mesh.triangle_count() > 0, name

    go(0.5, task, end_on_task_completion=True)
