from __future__ import annotations

from pathlib import Path

from picogk import EStlUnit, Mesh, MeshMath, VedoViewer, go

"""
Example 05: STL IO and mesh math
"""


OUT = Path("example_mesh.stl")


def main() -> None:
    viewer = VedoViewer(title="Example 05 - STL IO and Mesh Math")

    def task() -> None:
        with Mesh() as mesh:
            mesh.nAddTriangle((0.0, 0.0, 0.0), (20.0, 0.0, 0.0), (0.0, 20.0, 0.0))
            mesh.SaveToStlFile(str(OUT), EStlUnit.MM)

        loaded = Mesh.mshFromStlFile(str(OUT), EStlUnit.AUTO)
        try:
            viewer.add_mesh(loaded, color="lightcoral")
            viewer.request_render()
            print("loaded triangles:", loaded.nTriangleCount())
            ok, idx = MeshMath.bFindTriangleFromSurfacePoint(loaded, (2.0, 2.0, 0.0))
            print("query hit:", ok, "triangle index:", idx)
        finally:
            loaded.close()

    go(0.5, task, end_on_task_completion=False, viewer=viewer)
    print("written:", OUT.resolve())


if __name__ == "__main__":
    main()
