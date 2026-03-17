# Chapter 8: Migration Guide

## Goal

This chapter helps users migrate ShapeKernel-style scripts to the Python `shapekernel` + `picogk` stack.

## Migration Strategy

1. Start from behavior parity, not line-by-line translation.
2. Preserve geometry intent first.
3. Re-introduce optimization and stylistic refactors after tests pass.

## Practical Steps

1. Identify source script shape primitives and workflow stages.
2. Map each stage to `shapekernel` or `picogk` responsibility.
3. Build a minimal runnable path with preview output.
4. Compare results visually and numerically.
5. Add regression tests around key invariants.

## Common Mapping Patterns

1. Frame/spline construction:
   map to `LocalFrame`, `Frames`, and spline utilities.
2. Primitive and composed shapes:
   map to `Base*` classes and helper constructors.
3. Preview wrappers:
   map to `Sh` helper equivalents.
4. Runtime transforms/exports:
   map to `picogk` low-level APIs.

## Typical Pitfalls

1. Mixing runtime and modeling responsibilities in one function.
2. Assuming identical defaults for sampling or orientation.
3. Ignoring unit or voxel-size implications on measured output.
4. Overusing high-level helpers when low-level runtime control is required.

## Validation Framework

For each migrated script, verify:

1. Topology-level sanity (counts, connectivity assumptions).
2. Geometric sanity (bounds, expected key points).
3. Measurement tolerances at fixed voxel/resolution settings.
4. Export readability in downstream tools.

## Recommended Project Structure

1. `model/` for shape composition code.
2. `runtime/` for execution and IO orchestration.
3. `tests/` for parity and regression checks.
4. `examples/` for reproducible demonstration scripts.

## Final Notes

Migration succeeds fastest when you keep the layer contract clear:

1. `shapekernel` for expressive geometry composition.
2. `picogk` for runtime operations and interoperability.

That separation keeps code easier to test, debug, and maintain.
