# Chapter 3: Frames and Splines

## Why Frames and Splines Matter

Many non-trivial shapes are easier to express as:

1. A centerline/spine (spline).
2. A moving local coordinate frame along that spine.
3. Cross-section logic evaluated in local space.

`shapekernel` gives you primitives for this pattern.

## Frames

`LocalFrame` and `Frames` help define orientation and position over parameterized paths.

Core use cases:

1. Transport orientation along a path.
2. Build stable local axes for cross-section construction.
3. Express points and directions between local and world spaces.

Best practices:

1. Normalize direction vectors before frame creation.
2. Handle near-zero norms defensively.
3. Keep axis conventions explicit (which axis is forward/up/right).

## Splines

Spline helpers support control-point-driven geometry.

Common operations:

1. Reparameterize point sets.
2. Resample to a target density.
3. Generate transformed point lists for downstream meshing/lattice workflows.

Practical guidance:

1. Choose sample count based on curvature and target manufacturing/detail needs.
2. Keep resampling deterministic for reproducible outputs.
3. Validate spacing assumptions before using sampled points as structural supports.

## Combining Frames and Splines

Pattern:

1. Define spline control points.
2. Build sampled spine.
3. Construct aligned frames along the spine.
4. Evaluate shape/profile function in each frame.
5. Connect samples into mesh/lattice/voxel operations.

This pattern is the basis of pipes, swept forms, and manifold-like structures.

## Common Failure Modes

1. Frame flips due to ambiguous direction references.
2. Under-sampling causing faceting or instability.
3. Over-sampling causing excessive runtime cost.
4. Inconsistent coordinate conventions between local and world spaces.

Mitigations:

1. Add alignment checks and signed-angle sanity tests.
2. Profile with multiple sample budgets.
3. Keep helper functions pure and testable.

## Chapter Summary

Frames and splines are the core composition mechanism in `shapekernel`.

Next: how base shape classes package these ideas into reusable form.
