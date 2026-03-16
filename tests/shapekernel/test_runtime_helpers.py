from __future__ import annotations

from typing import cast

import pytest

from picogk import Library, Mesh, VedoViewer, go
from shapekernel import BaseBox, Cp, CylUtility, LinearColorScale2D, LocalFrame, Measure, MeshPainter, MeshUtility, Sh

from tests._helpers import runtime_available


pytestmark = pytest.mark.skipif(not runtime_available(), reason="PicoGK runtime not available")


def test_measure_and_mesh_utility_runtime() -> None:
    def task() -> None:
        with CylUtility.voxGetCyl(0.0, 10.0, 3.0) as vox:
            assert Measure.fGetVolume(vox) > 0.0
            assert Measure.fGetSurfaceArea(vox) > 0.0
            cog = Measure.vecGetCentreOfGravity(vox)
            assert cog[2] == pytest.approx(5.0, abs=1.0)

        with MeshUtility.mshFromQuad((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)) as quad:
            assert quad.nTriangleCount() == 2

        with MeshUtility.mshFromGrid(
            [
                [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                [(0.0, 1.0, 0.0), (1.0, 1.0, 0.0)],
            ]
        ) as grid:
            assert grid.nTriangleCount() == 2

    go(0.5, task, end_on_task_completion=True)


def test_sh_preview_helpers_and_mesh_painter_runtime() -> None:
    class _Viewer:
        def __init__(self) -> None:
            self.groups: list[int] = []
            self.materials: list[tuple[int, tuple[float, float, float, float], float, float]] = []

        def SetGroupMaterial(self, nGroupID: int, clr, fMetallic: float, fRoughness: float) -> None:
            rgba = (float(clr[0]), float(clr[1]), float(clr[2]), float(clr[3]))
            self.materials.append((nGroupID, rgba, float(fMetallic), float(fRoughness)))

        def Add(self, xObject: object, nGroupID: int = 0) -> int:
            self.groups.append(int(nGroupID))
            return int(nGroupID)

    viewer = _Viewer()

    def task() -> None:
        Sh.ResetPreviewGroups()
        Library.SetViewer(cast(VedoViewer, viewer))
        shape = BaseBox.from_frame(LocalFrame((0.0, 0.0, 0.0)), 10.0, 8.0, 6.0)
        shape.SetWidthSteps(8)
        shape.SetDepthSteps(8)
        shape.SetLengthSteps(8)

        try:
            with shape.voxConstruct() as vox:
                with Mesh.from_voxels(vox) as mesh:
                    Sh.Preview(mesh, Cp.clrCrystal)
                    Sh.Preview(vox, Cp.clrRock)
                    Sh.PreviewLine([(0.0, 0.0, 0.0), (5.0, 0.0, 0.0)], Cp.clrWarning)
                    Sh.PreviewFrame(LocalFrame((0.0, 0.0, 0.0)), 4.0)
                    Sh.PreviewCircle(LocalFrame((0.0, 0.0, 0.0)), 3.0, Cp.clrBlue)
                    scale = LinearColorScale2D(Cp.clrGreen, Cp.clrRed, 0.0, 1.0)
                    MeshPainter.PreviewCustomProperty(mesh, scale, lambda a, b, c: 0.5)
                    assert Sh.nNumberOfGroups > 0
        finally:
            Library.ClearViewer()

    go(0.5, task, end_on_task_completion=True)
    assert viewer.groups
    assert viewer.materials
