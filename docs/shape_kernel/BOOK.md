# shapekernel User Book

This book explains `shapekernel` in depth.

`shapekernel` is the high-level modeling package in this repository. It uses `picogk` as the execution/runtime layer.

## Who This Is For

1. Engineers and developers who want reusable shape abstractions.
2. Existing ShapeKernel users migrating from C# examples.
3. Users who want to compose frame/spline/modulation workflows before dropping to runtime operations.

## How This Book Relates To picogk Docs

1. Use this book for modeling composition and shape authoring.
2. Use the `picogk` book for runtime lifecycle, low-level API details, and production operations.
3. Read both if you build end-to-end pipelines.

## Table of Contents

1. [Chapter 1: Orientation](book/01_orientation.md)
2. [Chapter 2: Concept Mapping](book/02_concept_mapping.md)
3. [Chapter 3: Frames and Splines](book/03_frames_and_splines.md)
4. [Chapter 4: Base Shapes](book/04_base_shapes.md)
5. [Chapter 5: Modulations and Utility Functions](book/05_modulations_and_utilities.md)
6. [Chapter 6: Visualization and Preview](book/06_visualization_and_preview.md)
7. [Chapter 7: Measurements and Runtime Helpers](book/07_measurements_and_runtime_helpers.md)
8. [Chapter 8: Migration Guide](book/08_migration_guide.md)

## Learning Outcomes

After this book, you should be able to:

1. Explain exactly how `shapekernel` depends on `picogk`.
2. Build parameterized shapes and drive them with frames/splines.
3. Apply modulations and utility workflows in a structured way.
4. Use preview and measurement helpers responsibly.
5. Migrate ShapeKernel-style scripts to the Python package with minimal confusion.
