# Chapter 2: Concept Mapping

## Overview

This chapter maps common geometry concerns to their `shapekernel` and `picogk` roles.

## Concept Table

1. Runtime lifecycle:
   `picogk` responsibility (`go`, `Library`, viewer loop).
2. Parametric shape definitions:
   `shapekernel` responsibility (`Base*` classes and derived shape logic).
3. Field and voxel processing:
   mostly `picogk` (`Voxels`, `ScalarField`, `VectorField`), often orchestrated from `shapekernel` helper flows.
4. Preview convenience:
   `shapekernel.Sh` helper layer built on `picogk` viewer/material operations.
5. Measurements:
   `shapekernel.Measure` convenience methods delegating to runtime-backed operations.

## Typical End-To-End Pipeline

1. Define shape intent in `shapekernel`.
2. Sample/build geometry (mesh/lattice/voxels).
3. Perform booleans, offsets, remeshing, or field processing via `picogk`.
4. Preview and inspect intermediate outputs.
5. Export artifacts and metadata.

## Type and Data Contracts

`shapekernel` primarily works with Python-friendly vector forms (tuple/list/ndarray) for composition.

`picogk` converts those forms to native-compatible types when crossing the runtime boundary.

Keep this distinction in mind:

1. Input flexibility in modeling code.
2. Canonical conversion when calling runtime operations.

## Design Guidance

1. Keep domain logic and parameter rules in `shapekernel` classes/helpers.
2. Keep runtime interoperability logic in `picogk`.
3. Do not duplicate native-bound semantics in high-level helpers unless required for compatibility fallback.

## Chapter Summary

You now have a mental map for where logic should live.

Next: frames and splines as the backbone of many shape workflows.
