from __future__ import annotations

from picogk import Lattice, Mesh, VedoViewer, Voxels, go


def main() -> None:
    viewer = VedoViewer(title="PicoGK Python")

    def task() -> None:
        with Lattice() as lat:
            lat.add_sphere((0.0, 0.0, 0.0), 5.0)
            lat.add_beam((-10.0, 0.0, 0.0), (10.0, 0.0, 0.0), 2.0, 2.0)

            with Voxels.from_lattice(lat) as vox:
                vox.triple_offset(.6).gaussian(2)
                with Mesh.from_voxels(vox) as mesh:
                    actor_id = viewer.add_mesh(mesh, color="lightblue")
                    viewer.request_render()
                    print("Vertices:", mesh.vertex_count())
                    print("Triangles:", mesh.triangle_count())
                    print("Actor ID:", actor_id)

    go(0.05, task, end_on_task_completion=False, viewer=viewer)


if __name__ == "__main__":
    main()
