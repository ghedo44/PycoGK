# Chapter 4: Base Shapes

## Purpose of Base Shapes

Base shape classes provide reusable parametric definitions of common engineering forms.

Examples include:

1. `BaseBox`
2. `BaseCylinder`
3. `BaseSphere`
4. `BasePipe` and `BasePipeSegment`
5. `BaseRing`, `BaseCone`, `BaseLens`, and others

## Core Pattern

Most base shapes expose a surface-point evaluation style API:

1. Ratios or normalized parameters in shape-local space.
2. Internal computation of world-space points.
3. Optional frame/spline transformation hooks.

This enables:

1. Consistent tessellation strategies.
2. Shape-agnostic utilities consuming a common sampling pattern.
3. Easier transformation and composition.

## Shape Composition Guidelines

1. Separate parameter validation from geometry evaluation.
2. Keep local coordinate logic simple and explicit.
3. Apply transformation hooks at the edge of point generation.
4. Avoid hidden side-effects in evaluation methods.

## Building Derived Shapes

When creating a new base shape:

1. Define a minimal parameter set.
2. Specify parameter ranges and constraints clearly.
3. Implement robust `vecGetSurfacePoint` behavior.
4. Reuse frame/spline utilities instead of re-implementing transforms.
5. Add targeted tests for corner/edge parameter values.

## Performance Notes

1. Vectorized operations can help but avoid sacrificing readability.
2. Cache repeated frame/spline computations when safe.
3. Keep sampling density configurable.

## Validation Checklist

1. Shape closes correctly where expected.
2. Orientation and winding remain consistent.
3. Bounding extents match parameter intent.
4. Degenerate parameter combinations are handled or rejected.

## Chapter Summary

Base shapes encapsulate domain geometry logic in reusable, testable units.

Next: modulation and utility helpers that make these shapes adaptive.
