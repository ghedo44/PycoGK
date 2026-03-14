# Chapter 3: First Project

## Goal

Create a simple shape, process it in voxels, convert to mesh, and inspect basic stats.

## Complete Script

```python
from picogk import Lattice, Voxels, Mesh, go


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
                print("Vertices:", msh.nVertexCount())
                print("Triangles:", msh.nTriangleCount())


go(0.5, task, end_on_task_completion=True)
```

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
