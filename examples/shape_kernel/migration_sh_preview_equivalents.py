from __future__ import annotations

from picogk import Mesh, VedoViewer, go
from shape_kernel import BaseBox, Cp, LocalFrame, Sh

"""
C# to Python preview migration examples.

C#:
    Sh.Preview(mesh, Cp.clrCrystal);
    Sh.Preview(voxels, Cp.clrRock);
    Sh.PreviewLine(points, Cp.clrWarning);
    Sh.Preview(frame, 4f);

Python:
    Sh.Preview(mesh, Cp.clrCrystal)
    Sh.Preview(voxels, Cp.clrRock)
    Sh.PreviewLine(points, Cp.clrWarning)
    Sh.Preview(frame, 4.0)

The active viewer is picked up automatically when running inside picogk.go(..., viewer=viewer).
"""


def main() -> None:
    viewer = VedoViewer(title="ShapeKernel Sh.Preview migration", offscreen=False)

    def task() -> None:
        Sh.ResetPreviewGroups()
        box = BaseBox.from_frame(LocalFrame((0.0, 0.0, 0.0)), 12.0, 10.0, 8.0)
        box.SetLengthSteps(10)
        box.SetWidthSteps(8)
        box.SetDepthSteps(8)

        with box.voxConstruct() as vox:
            with Mesh.from_voxels(vox) as mesh:
                Sh.Preview(mesh, Cp.clrCrystal)
                Sh.Preview(vox, Cp.clrRock)
                Sh.PreviewLine([(-8.0, -8.0, 0.0), (8.0, -8.0, 0.0), (8.0, 8.0, 0.0)], Cp.clrWarning)
                Sh.Preview(LocalFrame((0.0, 0.0, 0.0)), 4.0)
                Sh.PreviewCircle(LocalFrame((0.0, 0.0, 0.0)), 6.0, Cp.clrBlue)
                viewer.SetViewAngles(35.0, 25.0)
                viewer.RequestUpdate()
                print("preview groups:", Sh.nNumberOfGroups)

    go(0.5, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
