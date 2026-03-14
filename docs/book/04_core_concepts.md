# Chapter 4: Core Concepts

## 1. Voxel Size

`go(voxel_size_mm, ...)` sets the global runtime voxel size.

Smaller voxel size:

1. Better precision.
2. More memory use.
3. Longer processing time.

Larger voxel size:

1. Faster operations.
2. Less memory use.
3. Less geometric detail.

## 2. Object Lifetimes

Most objects wrap native handles (`Mesh`, `Voxels`, `ScalarField`, `VectorField`, `OpenVdbFile`, `PolyLine`).

Use context managers:

```python
with Voxels() as vox:
    ...
```

This prevents handle leaks and keeps scripts stable.

## 3. Voxels vs Mesh

Voxels are ideal for robust booleans and morphology.

Meshes are ideal for:

1. Surface export.
2. Interop with CAD/CAM/printing tools.
3. Triangle-based analysis.

Common pattern:

1. Build and process in voxels.
2. Convert to mesh near the output stage.

## 4. Fields

`ScalarField` and `VectorField` attach values to space positions.

Typical uses:

1. Simulation-like scalar data.
2. Directional guides.
3. Metadata-driven post-processing.

`FieldMetadata` stores key-value data alongside fields and voxel objects.

## 5. API Aliases

The package supports both Pythonic names and PicoGK-style names in many places.

Examples:

1. `add_sphere` and `AddSphere`
2. `mesh.triangle_count()` and `mesh.nTriangleCount()`

## Chapter Summary

You now understand the engineering tradeoffs and model behind pycogk.

Next: full modeling workflows.
