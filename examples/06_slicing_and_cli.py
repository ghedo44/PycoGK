from __future__ import annotations

from pathlib import Path

from picogk import Cli, Lattice, Mesh, VedoViewer, Voxels, go

"""
Example 06: Slicing and CLI export/parse
"""


OUT_CLI = Path("example_slices.cli")
OUT_SVG = Path("example_slice.svg")


def main() -> None:
    viewer = VedoViewer(title="Example 06 - Slicing and CLI")

    def task() -> None:
        with Lattice() as lat:
            lat.add_sphere((0.0, 0.0, 0.0), 8.0)
            with Voxels.from_lattice(lat) as vox:
                with Mesh.from_voxels(vox) as mesh:
                    viewer.add_mesh(mesh, color="lightsteelblue")
                    viewer.request_render()

                stack = vox.oVectorize(0.5)
                print("stack layers:", stack.nCount())

                vox.SaveToCliFile(str(OUT_CLI), 0.5, Cli.EFormat.FirstLayerWithContent)
                parsed = Cli.oSlicesFromCliFile(str(OUT_CLI))
                print("parsed layers:", parsed.oSlices.nCount())
                print("warnings:", parsed.strWarnings or "<none>")

                first = parsed.oSlices.oSliceAt(0)
                first.SaveToSvgFile(OUT_SVG, bSolid=False)

    go(0.5, task, end_on_task_completion=False, viewer=viewer)
    print("written:", OUT_CLI.resolve())
    print("written:", OUT_SVG.resolve())


if __name__ == "__main__":
    main()
