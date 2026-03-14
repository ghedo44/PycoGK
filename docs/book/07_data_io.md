# Chapter 7: Data IO

## OpenVDB

Use `OpenVdbFile` to store voxels and fields with metadata.

Typical pattern:

1. Create/compute data.
2. Add objects with field names.
3. Save to `.vdb`.
4. Re-open and inspect field types.

## STL Mesh IO

`MeshIo` and `Mesh` methods support loading/saving STL with unit handling.

Recommendations:

1. Keep explicit unit choices in scripts.
2. Record scale/offset transformations in logs.
3. Validate triangle count after import.

## CLI Slicing

`Cli` and `PolySlice*` support contour slicing workflows and CLI export.

Use cases:

1. Layered manufacturing toolchains.
2. Custom contour post-processing.
3. Slice-level QA and debug visualization.

## TGA and Image Utilities

Image classes and `TgaIo` help with:

1. Slice visualization.
2. Field/debug image generation.
3. Pipeline diagnostics.

## Metadata Hygiene

Use `FieldMetadata` consistently:

1. Add project identifiers.
2. Persist voxel size and version info.
3. Store generation parameters.

This makes outputs reproducible and auditable.

## Chapter Summary

You can now move data in/out reliably and preserve context with metadata.
