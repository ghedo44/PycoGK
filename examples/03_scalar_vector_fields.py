from __future__ import annotations

from picogk import FieldUtils, Lattice, Mesh, ScalarField, VedoViewer, Voxels, go

"""
Example 03: Scalar and vector fields

Shows conversion from Voxels, traversal, and metadata access.
"""


def main() -> None:
    viewer = VedoViewer(title="Example 03 - Scalar and Vector Fields")

    def task() -> None:
        with Lattice() as lat:
            lat.add_sphere((0.0, 0.0, 0.0), 7.0)
            with Voxels.from_lattice(lat) as vox:
                with Mesh.from_voxels(vox) as mesh:
                    viewer.add_mesh(mesh, color="plum")
                    viewer.request_render()

                with ScalarField.from_voxels(vox) as sf:
                    hits = []
                    sf.traverse_active(lambda p, v: hits.append((p, v)) if len(hits) < 5 else None)
                    print("sample scalar entries:", len(hits))
                    print("scalar metadata count:", sf.oMetaData().nCount())

                vf = FieldUtils.SurfaceNormalFieldExtractor.oExtract(vox, fSurfaceThresholdVx=0.6)
                try:
                    vhits = []
                    vf.traverse_active(lambda p, v: vhits.append((p, v)) if len(vhits) < 5 else None)
                    print("sample vector entries:", len(vhits))
                finally:
                    vf.close()

    go(0.5, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
