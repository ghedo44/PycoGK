from __future__ import annotations

import time
from pathlib import Path

from picogk import (
    AnimViewRotate,
    Animation,
    Easing,
    Lattice,
    Mesh,
    PolyLine,
    VedoViewer,
    Voxels,
    go,
)

"""
Example 11: C#-style viewer controls adapted to vedo.

Demonstrates:
- Add/Remove and group-based styling
- camera controls (angles/FOV/zoom/projection)
- screenshot capture
- timelapse capture
- animation-driven camera movement

Runs offscreen and writes images under ./_out_viewer.
"""


def main() -> None:
    out_dir = Path("_out_viewer")
    out_dir.mkdir(parents=True, exist_ok=True)

    viewer = VedoViewer(title="Viewer Controls Demo", offscreen=True)

    def task() -> None:
        with Lattice() as lat:
            lat.AddSphere((0.0, 0.0, 0.0), 9.0)
            lat.AddBeam((-12.0, 0.0, 0.0), (12.0, 0.0, 0.0), 2.2, 2.2)

            with Voxels.from_lattice(lat) as vox:
                vox.Gaussian(0.8)
                actor_vox = viewer.Add(vox, nGroupID=1)

                with Mesh.from_voxels(vox) as msh:
                    actor_mesh = viewer.Add(msh, nGroupID=2)

                with PolyLine((0.95, 0.2, 0.2, 1.0)) as axis:
                    axis.Add([(-15, 0, 0), (0, 0, 0), (15, 0, 0)])
                    axis.AddArrow(1.2)
                    viewer.Add(axis, nGroupID=3)

                viewer.SetBackgroundColor((0.08, 0.10, 0.14, 1.0))
                viewer.SetGroupMaterial(1, (0.35, 0.65, 1.0, 0.35), 0.0, 0.7)
                viewer.SetGroupMaterial(2, (0.9, 0.9, 0.95, 1.0), 0.15, 0.35)
                viewer.SetGroupMaterial(3, (1.0, 0.2, 0.2, 1.0), 0.0, 1.0)
                viewer.SetGroupStatic(3, True)

                viewer.SetViewAngles(30.0, 25.0)
                viewer.SetFov(40.0)
                viewer.SetZoom(1.0)
                viewer.SetPerspective(True)
                viewer.RequestUpdate()
                viewer.RequestScreenShot(str(out_dir / "viewer_initial.png"))

                view_rot = AnimViewRotate(viewer, (30.0, 25.0), (165.0, 15.0))

                anim = Animation(
                    lambda t: view_rot.Do(Easing.fEasingFunction(float(t), Easing.EEasing.SINE_INOUT)),
                    1.0,
                    Animation.EType.ONCE,
                )
                viewer.AddAnimation(anim)

                viewer.StartTimeLapse(
                    120.0,
                    str(out_dir),
                    strFileName="timelapse_",
                    nStartFrame=0,
                    bPaused=False,
                )

                for _ in range(10):
                    viewer.AdjustViewAngles(10.0, 0.0)
                    viewer.RequestUpdate()
                    time.sleep(0.13)

                viewer.StopTimeLapse()
                viewer.SetGroupVisible(1, False)
                viewer.RequestUpdate()
                viewer.RequestScreenShot(str(out_dir / "viewer_mesh_only.png"))

                viewer.Remove(actor_mesh)
                viewer.Remove(actor_vox)
                viewer.LogStatistics()

    go(0.5, task, end_on_task_completion=True, viewer=viewer)


if __name__ == "__main__":
    main()
