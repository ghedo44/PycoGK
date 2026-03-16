from __future__ import annotations

from picogk import PolyLine, VedoViewer, go

"""
Example 09: PolyLine and VedoViewer

Requires a GUI environment.
"""


def main() -> None:
    viewer = VedoViewer(title="PolyLine Demo")

    def task() -> None:
        with PolyLine((1.0, 0.3, 0.2, 1.0)) as line:
            line.Add([
                (-5.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (5.0, 0.0, 0.0),
            ])
            line.AddArrow(1.0)
            line.AddCross(0.5)
            viewer.Add(line, nGroupID=2)
            viewer.SetGroupMaterial(2, (1.0, 0.3, 0.2, 1.0), 0.0, 1.0)
            viewer.SetViewAngles(20.0, 20.0)
            viewer.RequestUpdate()
            print("vertices:", line.nVertexCount())

    go(0.5, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
