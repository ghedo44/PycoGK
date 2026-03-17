from __future__ import annotations

from picogk import Mesh, VedoViewer, go
from shape_kernel import BaseCylinder, Cp, LinearColorScale2D, LocalFrame, MeshPainter, RotationAnimator

"""
C# to Python visualization migration examples.

C#:
    MeshPainter.PreviewOverhangAngle(mesh, scale, false);
    MeshPainter.PreviewCustomProperty(mesh, scale, func);

Python:
    MeshPainter.PreviewOverhangAngle(mesh, scale, False)
    MeshPainter.PreviewCustomProperty(mesh, scale, func)

When a viewer is active, the Python MeshPainter helpers now preview automatically as well as returning
the generated submeshes and colors.
"""


def main() -> None:
    viewer = VedoViewer(title="ShapeKernel visualization migration", offscreen=False)

    def task() -> None:
        cyl = BaseCylinder.from_frame(LocalFrame((0.0, 0.0, -8.0)), 16.0, 5.0)
        cyl.SetLengthSteps(18)
        cyl.SetPolarSteps(64)
        cyl.SetRadialSteps(8)

        with cyl.voxConstruct() as vox:
            with Mesh.from_voxels(vox) as mesh:
                scale = LinearColorScale2D(Cp.clrGreen, Cp.clrRed, 0.0, 90.0)
                MeshPainter.PreviewOverhangAngle(mesh, scale, False)

                prop_scale = LinearColorScale2D(Cp.clrBlue, Cp.clrWarning, 0.0, 1.0)
                MeshPainter.PreviewCustomProperty(
                    mesh,
                    prop_scale,
                    lambda a, b, c: min(1.0, max(0.0, (a[2] + b[2] + c[2] + 24.0) / 48.0)),
                )

                RotationAnimator(viewer).Do(4.0)
                viewer.RequestUpdate()
                print("visualization migration demo ready")

    go(0.5, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
