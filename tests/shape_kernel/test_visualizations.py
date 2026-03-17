from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from picogk import Library
from shape_kernel import Cp, LinearColorScale2D, MeshPainter, SmoothColorScale2D
from shape_kernel.functions import Sh


@dataclass
class _FakeMesh:
    triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]] = field(default_factory=list)

    def nTriangleCount(self) -> int:
        return len(self.triangles)

    def GetTriangle(self, index: int):
        return self.triangles[index]

    def nAddTriangle(self, a, b, c) -> None:
        self.triangles.append((a, b, c))


def test_color_scales_clamp_and_interpolate() -> None:
    linear = LinearColorScale2D(Cp.clrGreen, Cp.clrRed, 0.0, 10.0)
    smooth = SmoothColorScale2D(Cp.clrGreen, Cp.clrRed, 0.0, 10.0)

    assert linear.clrGetColor(-5.0) == pytest.approx(Cp.clrGreen)
    assert linear.clrGetColor(15.0) == pytest.approx(Cp.clrRed)

    mid = smooth.clrGetColor(5.0)
    assert 0.0 <= mid[0] <= 1.0
    assert 0.0 <= mid[1] <= 1.0
    assert mid[3] == pytest.approx(1.0)


def test_mesh_painter_groups_triangles_without_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    src = _FakeMesh(
        [
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        ]
    )
    monkeypatch.setattr(MeshPainter, "_build_submesh_classes", staticmethod(lambda _mesh, n: [_FakeMesh() for _ in range(n)]))

    scale = LinearColorScale2D(Cp.clrGreen, Cp.clrRed, 0.0, 1.0)
    segments = MeshPainter.PreviewCustomProperty(src, scale, lambda a, b, c: a[2] + b[2] + c[2], 3) # pyright: ignore[reportArgumentType]

    assert len(segments) == 3
    assert sum(segment.nTriangleCount() for segment, _clr in segments) == 2


def test_mesh_painter_uses_active_viewer_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    src = _FakeMesh([((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))])
    monkeypatch.setattr(MeshPainter, "_build_submesh_classes", staticmethod(lambda _mesh, n: [_FakeMesh() for _ in range(n)]))

    calls: list[tuple[object, tuple[float, float, float, float]]] = []
    monkeypatch.setattr(Sh, "PreviewMesh", staticmethod(lambda mesh, clr, **kwargs: calls.append((mesh, clr)) or 0))

    class _Viewer:
        pass

    Library.SetViewer(_Viewer()) # pyright: ignore[reportArgumentType]
    try:
        scale = LinearColorScale2D(Cp.clrGreen, Cp.clrRed, 0.0, 1.0)
        MeshPainter.PreviewCustomProperty(src, scale, lambda a, b, c: 0.5, 2) # pyright: ignore[reportArgumentType]
    finally:
        Library.ClearViewer()

    assert calls
