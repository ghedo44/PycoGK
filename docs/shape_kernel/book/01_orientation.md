# Chapter 1: Orientation

## What shapekernel Is

`shapekernel` is a high-level geometry composition layer.

It provides:

1. Shape abstractions such as `BaseBox`, `BaseCylinder`, `BasePipe`, and related classes.
2. Frame, spline, and modulation tools for parameterized modeling.
3. High-level helper facades (`Sh`, `MeshUtility`, `CylUtility`, `Measure`) to reduce low-level boilerplate.

## What shapekernel Is Not

`shapekernel` is not a separate runtime engine. It does not replace `picogk` or the native PicoGK runtime.

`shapekernel` builds and transforms geometry concepts, then delegates execution to `picogk` objects like `Mesh`, `Voxels`, and `Lattice`.

## Layering Model

Think in three layers:

1. Native runtime (`PicoGK` binary): execution and heavy geometry processing.
2. `picogk`: Python runtime bindings and low-level object model.
3. `shapekernel`: modeling composition and convenience layer.

Data and control flow mostly follow this direction:

1. Your shape logic in `shapekernel`.
2. Object creation/processing through `picogk` APIs.
3. Runtime execution in the native library.

## Why Use shapekernel

Use it when you want:

1. Reusable parametric shape patterns.
2. Cleaner expression of frame-aligned geometry.
3. Spline-driven control structures.
4. Less repetitive code for preview/measurement helper workflows.

## When To Drop To picogk

Use `picogk` directly when you need:

1. Native handle-level behavior or strict runtime control.
2. Full control of data IO and processing options.
3. Feature access not yet surfaced as a high-level helper.

## Chapter Summary

`shapekernel` is a composition layer built on `picogk`, not a separate runtime.

Next: how key concepts map between layers.
