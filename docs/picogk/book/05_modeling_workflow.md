# Chapter 5: Modeling Workflow

## Voxel-First Pipeline

A robust engineering pattern is voxel-first:

1. Build primitives with `Lattice`.
2. Convert to `Voxels`.
3. Apply booleans and offsets.
4. Convert to `Mesh` for export.

Example:

```python
from picogk import Lattice, Voxels, Mesh, go


def task() -> None:
    with Lattice() as a, Lattice() as b:
        a.AddSphere((0, 0, 0), 10)
        b.AddSphere((6, 0, 0), 10)

        with Voxels.from_lattice(a) as va, Voxels.from_lattice(b) as vb:
            va.BoolAdd(vb)
            va.Offset(0.5)
            va.Median(0.4)

            with Mesh.from_voxels(va) as msh:
                msh.SaveToStlFile("result.stl")


go(0.5, task, end_on_task_completion=True)
```

## Shell and Fillet Concepts

Useful high-level operators:

1. `voxShell(...)` for thin-wall shapes.
2. `Fillet(...)` and `Smoothen(...)` for softened transitions.

These methods combine lower-level voxel operations.

## Field-Driven Workflow

1. Start from `Voxels`.
2. Build `ScalarField` / `VectorField`.
3. Traverse active values and compute domain-specific metrics.
4. Save to VDB with metadata.

## Tips For Reliable Results

1. Use consistent units in millimeters.
2. Keep voxel size stable per project branch.
3. Save intermediate VDB snapshots for reproducibility.
4. Log final bounding boxes and triangle counts.

## Chapter Summary

You now have repeatable modeling patterns for production scripts.
