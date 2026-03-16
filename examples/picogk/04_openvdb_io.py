from __future__ import annotations

from pathlib import Path

from picogk import Lattice, Mesh, OpenVdbFile, ScalarField, VectorField, VedoViewer, Voxels, go

"""
Example 04: OpenVDB IO

Creates voxels + scalar + vector fields and stores them in one .vdb file.
"""


OUT = Path("example_fields.vdb")


def main() -> None:
    viewer = VedoViewer(title="Example 04 - OpenVDB IO")

    def task() -> None:
        with Lattice() as lat:
            lat.add_sphere((0.0, 0.0, 0.0), 6.0)
            with Voxels.from_lattice(lat) as vox, ScalarField.from_voxels(vox) as sf, VectorField.build_from_voxels(vox, (1.0, 0.0, 0.0)) as vf:
                with Mesh.from_voxels(vox) as mesh:
                    viewer.add_mesh(mesh, color="lightyellow")
                    viewer.request_render()

                with OpenVdbFile() as vdb:
                    vdb.nAdd(vox, "vox")
                    vdb.nAdd(sf, "sf")
                    vdb.nAdd(vf, "vf")
                    vdb.SaveToFile(str(OUT))

                with OpenVdbFile(str(OUT)) as vdb2:
                    print("fields:", vdb2.nFieldCount())
                    for i in range(vdb2.nFieldCount()):
                        print(i, vdb2.strFieldName(i), vdb2.strFieldType(i))

    go(0.5, task, end_on_task_completion=False, viewer=viewer)
    print("written:", OUT.resolve())


if __name__ == "__main__":
    main()
