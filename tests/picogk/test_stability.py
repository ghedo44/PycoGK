from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from picogk import Lattice, VedoViewer, Voxels, go

from tests._helpers import runtime_available


pytestmark = pytest.mark.skipif(not runtime_available(), reason="PicoGK runtime not available")


def test_repeated_go_lifecycle_stability() -> None:
    for _ in range(6):
        def task() -> None:
            with Lattice() as lat:
                lat.AddSphere((0.0, 0.0, 0.0), 5.0)
                with Voxels.from_lattice(lat) as vox:
                    assert vox.is_valid()

        go(0.5, task, end_on_task_completion=True)


def test_offscreen_viewer_repeated_open_close(tmp_path: Path) -> None:
    if os.getenv("PICOGK_ENABLE_VIEWER_STABILITY", "0") != "1":
        pytest.skip("Set PICOGK_ENABLE_VIEWER_STABILITY=1 to run viewer stress gate")

    out = tmp_path / "viewer_stability"
    out.mkdir(parents=True, exist_ok=True)

    for i in range(3):
        viewer = VedoViewer(title=f"stability-{i}", offscreen=True)

        def task() -> None:
            with Lattice() as lat:
                lat.AddSphere((0.0, 0.0, 0.0), 6.0)
                with Voxels.from_lattice(lat) as vox:
                    viewer.Add(vox, nGroupID=1)
                    viewer.RequestUpdate()
                    time.sleep(0.05)
                    viewer.RequestScreenShot(str(out / f"frame_{i}.png"))

        go(0.5, task, end_on_task_completion=True, viewer=viewer)

    images = list(out.glob("frame_*.png"))
    assert len(images) == 3
