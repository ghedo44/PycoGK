# Chapter 5: Modulations and Utility Functions

## Modulation Concepts

Modulations let you vary shape properties over a domain such as:

1. Path length ratio.
2. Angular coordinate.
3. Cross-section position.

Typical modulation goals:

1. Radius tapering.
2. Profile deformation.
3. Material- or process-aware compensation.

## Utility Modules

`shapekernel` utility classes support operations that would otherwise become repetitive:

1. Grid/list operations for sampled control structures.
2. Geometric vector operations and coordinate transforms.
3. Decimation/interpolation helpers.
4. Implicit helper formulations.

## Good Modulation Design

1. Keep modulation functions deterministic.
2. Keep domains normalized (often `[0, 1]`) and document assumptions.
3. Clamp and validate where out-of-domain behavior is unsafe.
4. Distinguish geometric intent from numerical smoothing tricks.

## Numerical Robustness

1. Guard divisions and normalization with epsilon thresholds.
2. Avoid compounding precision drift in iterative transforms.
3. Use explicit conversion boundaries between tuple/list/ndarray forms.

## Integration Strategy

1. Build a base geometric skeleton first.
2. Apply modulation in a clearly ordered stage.
3. Convert to runtime objects only after shape intent is stabilized.

## Testing Strategy

1. Unit-test modulation functions independently.
2. Snapshot key sampled profiles for regression checks.
3. Add property-based checks where practical (monotonicity, bounds, continuity).

## Chapter Summary

Modulations and utilities turn static shapes into expressive, controlled geometry systems.

Next: preview and visualization workflows.
