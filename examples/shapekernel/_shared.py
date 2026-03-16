from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sys
from typing import Any, Protocol, cast

from picogk import Mesh, Voxels, go
from shapekernel import Frames, LocalFrame, TangentialControlSpline

class _MeshShape(Protocol):
    def voxConstruct(self) -> Any:
        ...


class _LatticeShape(Protocol):
    def latConstruct(self) -> Any:
        ...


def _set_if_present(obj: object, method_name: str, value: int) -> None:
    fn = getattr(obj, method_name, None)
    if callable(fn):
        fn(value)


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def example_frames() -> Frames:
    spline = TangentialControlSpline.from_frames(
        LocalFrame((-10.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        LocalFrame((10.0, 14.0, 24.0), (0.0, 1.0, 1.0)),
    )
    return Frames.from_points_and_target_x(spline.aGetPoints(50), (0.0, 1.0, 0.0), 1.0)


def run_mesh_example(title: str, build_shape: Callable[[], object]) -> None:

    def task() -> None:
        shape = build_shape()
        _set_if_present(shape, "SetPolarSteps", 48)
        _set_if_present(shape, "SetAzimuthalSteps", 48)
        _set_if_present(shape, "SetRadialSteps", 10)
        _set_if_present(shape, "SetLengthSteps", 20)
        _set_if_present(shape, "SetWidthSteps", 10)
        _set_if_present(shape, "SetDepthSteps", 10)
        _set_if_present(shape, "SetHeightSteps", 10)

        with cast(_MeshShape, shape).voxConstruct() as voxels:
            with Mesh.from_voxels(voxels) as mesh:
                print(f"{title}: vertices={mesh.vertex_count()} triangles={mesh.triangle_count()}")

    go(0.5, task, end_on_task_completion=True)


def run_lattice_example(title: str, build_shape: Callable[[], object]) -> None:

    def task() -> None:
        shape = build_shape()
        _set_if_present(shape, "SetLengthSteps", 40)
        with Voxels.from_lattice(cast(_LatticeShape, shape).latConstruct()) as voxels:
            with Mesh.from_voxels(voxels) as mesh:
                print(f"{title}: vertices={mesh.vertex_count()} triangles={mesh.triangle_count()}")

    go(0.5, task, end_on_task_completion=True)
