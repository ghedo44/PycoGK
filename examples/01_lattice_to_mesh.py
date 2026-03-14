from __future__ import annotations

from picogk import Lattice, Mesh, VedoViewer, Voxels, go

"""
Example 01: Lattice -> Voxels -> Mesh

This script demonstrates the most common PicoGK pipeline:
1) Build implicit primitives with Lattice
2) Render to Voxels
3) Extract a Mesh and inspect counts
"""


def main() -> None:
    viewer = VedoViewer(title="Example 01 - Lattice to Mesh")

    def task() -> None:
        with Lattice() as lat:
            lat.add_sphere((0.0, 0.0, 0.0), 8.0)
            lat.add_beam((-12.0, 0.0, 0.0), (12.0, 0.0, 0.0), 2.5, 2.5)

            with Voxels.from_lattice(lat) as vox:
                # Smooth surface in voxel space before meshing.
                vox.triple_offset(0.4).gaussian(1.0)

                with Mesh.from_voxels(vox) as mesh:
                    actor_id = viewer.add_mesh(mesh, color="lightblue")
                    viewer.request_render()
                    print("Vertices:", mesh.vertex_count())
                    print("Triangles:", mesh.triangle_count())
                    print("Bounding box:", mesh.bounding_box())
                    print("Actor ID:", actor_id)

    go(0.5, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
