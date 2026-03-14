from __future__ import annotations

from picogk import Lattice, Mesh, VedoViewer, Voxels, go

"""
Example 02: Voxel booleans and filters

Demonstrates add/subtract/intersect and common filters.
"""


def main() -> None:
    viewer = VedoViewer(title="Example 02 - Voxel Booleans")

    def task() -> None:
        with Lattice() as a, Lattice() as b:
            a.add_sphere((0.0, 0.0, 0.0), 10.0)
            b.add_sphere((6.0, 0.0, 0.0), 8.0)

            with Voxels.from_lattice(a) as va, Voxels.from_lattice(b) as vb:
                union = va.vox_bool_add(vb)
                diff = va.vox_bool_subtract(vb)
                inter = va.vox_bool_intersect(vb)

                union.gaussian(1.5)
                diff.median(1.0)
                inter.mean(1.0)

                print("union slices:", union.nSliceCount())
                print("diff slices:", diff.nSliceCount())
                print("inter slices:", inter.nSliceCount())

                with Mesh.from_voxels(union) as msh_union, Mesh.from_voxels(diff) as msh_diff, Mesh.from_voxels(inter) as msh_inter:
                    viewer.add_mesh(msh_union, color="lightgreen")
                    viewer.add_mesh(msh_diff, color="orange")
                    viewer.add_mesh(msh_inter, color="lightblue")
                    viewer.request_render()

                union.close()
                diff.close()
                inter.close()

    go(0.5, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
