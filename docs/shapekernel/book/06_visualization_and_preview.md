# Chapter 6: Visualization and Preview

## Preview Layer Overview

The `Sh` helper family provides high-level preview utilities layered on top of the viewer/runtime APIs.

Use preview to:

1. Inspect generated geometry quickly.
2. Validate orientation and sampling assumptions.
3. Compare intermediate results before committing to export.

## Typical Preview Objects

1. Mesh previews.
2. Voxel previews.
3. Lattice previews.
4. Primitive aids (points, lines, wireframes, local frames).

## Material and Color Practices

1. Keep color mapping semantically meaningful (function, state, or process stage).
2. Use transparency intentionally to inspect nested structures.
3. Keep metallic/roughness values consistent across comparable artifacts.

## Viewer Lifecycle

Remember that viewer orchestration lives in `picogk` (`go`, viewer object ownership, update loop).

`shapekernel` preview helpers are convenience wrappers and should not be treated as standalone lifecycle managers.

## Debugging With Preview

1. Visualize frames and local axes before diagnosing shape defects.
2. Preview sampled spline points to spot parameterization issues.
3. Render both source and transformed geometry to verify transform correctness.

## Recommended Workflow

1. Start with low sampling density and coarse previews.
2. Validate orientation/continuity.
3. Increase fidelity.
4. Validate measurement outputs.
5. Export final assets.

## Chapter Summary

Preview tools are for fast geometric feedback; runtime control still belongs to `picogk`.

Next: measurement utilities and runtime helper integration.
