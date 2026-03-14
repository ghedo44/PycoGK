# Chapter 3: First Project

## Goal

Create a simple shape, process it in voxels, convert to mesh, inspect stats, and display the result in the viewer.

## Complete Script

```python
from picogk import Lattice, Voxels, Mesh, VedoViewer, go


viewer = VedoViewer(title="First Project")


def task() -> None:
    with Lattice() as lat:
        lat.AddSphere((0.0, 0.0, 0.0), 10.0)
        lat.AddBeam((-15.0, 0.0, 0.0), (15.0, 0.0, 0.0), 2.0, 2.0)

        with Voxels.from_lattice(lat) as vox:
            vox.Gaussian(0.5)
            vox.Offset(0.3)

            volume, (bmin, bmax) = vox.CalculateProperties()
            print("Volume:", volume)
            print("BBox min:", bmin)
            print("BBox max:", bmax)

            with Mesh.from_voxels(vox) as msh:
                viewer.Add(msh, nGroupID=1)
                viewer.SetViewAngles(30.0, 20.0)
                viewer.SetZoom(2.0)
                viewer.RequestUpdate()
                print("Vertices:", msh.nVertexCount())
                print("Triangles:", msh.nTriangleCount())


go(0.5, task, end_on_task_completion=False, viewer=viewer)
```

Close the viewer window to end the program.

## Why `go(...)` Matters

`go(...)` handles runtime setup and teardown safely.

Without it, forgetting to initialize/destroy runtime can cause hard-to-debug behavior.

## Recommended Workflow

1. Start with one small shape.
2. Add one operation at a time.
3. Print measurements after each major step.
4. Export intermediate artifacts when debugging.

## Chapter Summary

You built a complete first geometry pipeline.

Next: deep core concepts.
