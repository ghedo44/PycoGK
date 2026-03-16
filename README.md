# pycogk

Python package for working with PicoGK from Python.

This is an **unofficial community** library.

- Official PicoGK project (C++ / C#): https://github.com/leap71/PicoGK
- This Python package repository: https://github.com/ghedo44/PycoGK

The package keeps a PicoGK-like API where practical while adapting parts of the experience to Python, including a vedo-based viewer layer.

## Project Layers: picogk and shapekernel

This repository ships two Python layers that are designed to work together.

### picogk (runtime and low-level API)

`picogk` is the runtime-facing layer.

It wraps the PicoGK native library via `ctypes` and exposes core primitives and utilities such as:

1. `Library`, `go`, and viewer orchestration.
2. `Lattice`, `Voxels`, `Mesh`, and `PolyLine`.
3. `ScalarField` and `VectorField`.
4. Native-format IO helpers and processing utilities.

Use `picogk` when you want direct control over runtime operations, lifecycle, and API behavior.

### shapekernel (high-level modeling layer)

`shapekernel` is a higher-level geometric modeling toolkit built on top of `picogk`.

It provides reusable shape abstractions and modeling workflows inspired by ShapeKernel concepts:

1. Parametric base shapes (`BaseBox`, `BaseCylinder`, `BaseSphere`, and more).
2. Frame/spline/modulation utilities for constructing complex geometry.
3. High-level helper toolkits (`Sh`, `Measure`, `MeshUtility`, `CylUtility`).
4. Visualization and migration helpers for ShapeKernel-style workflows.

Use `shapekernel` when you want expressive construction patterns and less low-level plumbing.

### Relationship Between Them

1. `shapekernel` depends on and uses `picogk` for runtime execution.
2. `picogk` does not depend on `shapekernel`.
3. You can adopt either layer independently, or combine both in one workflow.

Practical mental model:

1. Author geometry logic in `shapekernel` when useful.
2. Convert/process/render/export through `picogk` runtime objects.

## Why pycogk

Use pycogk when you want to script computational geometry workflows in Python while leveraging PicoGK runtime capabilities:

1. Build implicit geometry with lattices.
2. Convert to voxels and apply boolean/filter/offset operations.
3. Extract meshes and work with STL/VDB/CLI/TGA.
4. Create scalar/vector field workflows.
5. Preview and iterate quickly from Python.

## Install

From PyPI:

```bash
pip install pycogk
```

From this repository:

```bash
pip install "git+https://github.com/ghedo44/PycoGK.git"
```


## Import Name

The distribution name is `pycogk`, but the Python import is:

```python
import picogk
```

## Runtime Notes

pycogk loads the PicoGK native runtime using `ctypes`.

Bundled runtime targets currently include:

1. `win-x64`
2. `osx-arm64`

If your platform is not bundled, set `PICOGK_RUNTIME_PATH` to a compatible binary.

PowerShell example:

```powershell
$env:PICOGK_RUNTIME_PATH = "C:\path\to\picogk.1.7.dll"
python your_script.py
```

## Quick Start

```python
from picogk import Lattice, Voxels, Mesh, VedoViewer, go

viewer = VedoViewer(title="pycogk Quickstart")

def task() -> None:
  with Lattice() as lat:
    lat.AddSphere((0.0, 0.0, 0.0), 10.0)
    with Voxels.from_lattice(lat) as vox:
      with Mesh.from_voxels(vox) as msh:
        viewer.Add(msh, nGroupID=1)
        viewer.SetViewAngles(30.0, 20.0)
        viewer.RequestUpdate()
        print("triangles:", msh.nTriangleCount())

go(0.5, task, end_on_task_completion=False, viewer=viewer)
```

Close the viewer window to end the program.

## Documentation

Documentation is split into two tracks:

1. `picogk` docs: runtime-centric API and production workflows.
2. `shapekernel` docs: high-level shape, spline, frame, and modeling composition workflows.

### picogk docs

1. [Book Home](docs/picogk/BOOK.md)
2. [Chapter 1: Orientation](docs/picogk/book/01_orientation.md)
3. [Chapter 2: Installation and Runtime](docs/picogk/book/02_installation_and_runtime.md)
4. [Chapter 3: First Project](docs/picogk/book/03_first_project.md)
5. [Chapter 4: Core Concepts](docs/picogk/book/04_core_concepts.md)
6. [Chapter 5: Modeling Workflow](docs/picogk/book/05_modeling_workflow.md)
7. [Chapter 6: Viewer and Interaction](docs/picogk/book/06_viewer_and_interaction.md)
8. [Chapter 7: Data IO](docs/picogk/book/07_data_io.md)
9. [Chapter 8: Troubleshooting](docs/picogk/book/08_troubleshooting.md)
10. [Chapter 9: Production and Publishing](docs/picogk/book/09_production_and_publishing.md)

### shapekernel docs

1. [Book Home](docs/shapekernel/BOOK.md)
2. [Chapter 1: Orientation](docs/shapekernel/book/01_orientation.md)
3. [Chapter 2: Concept Mapping](docs/shapekernel/book/02_concept_mapping.md)
4. [Chapter 3: Frames and Splines](docs/shapekernel/book/03_frames_and_splines.md)
5. [Chapter 4: Base Shapes](docs/shapekernel/book/04_base_shapes.md)
6. [Chapter 5: Modulations and Utility Functions](docs/shapekernel/book/05_modulations_and_utilities.md)
7. [Chapter 6: Visualization and Preview](docs/shapekernel/book/06_visualization_and_preview.md)
8. [Chapter 7: Measurements and Runtime Helpers](docs/shapekernel/book/07_measurements_and_runtime_helpers.md)
9. [Chapter 8: Migration Guide](docs/shapekernel/book/08_migration_guide.md)

## Examples

Runnable examples are in [examples](examples):

1. [examples/basic_usage.py](examples/basic_usage.py)
2. [examples/01_lattice_to_mesh.py](examples/01_lattice_to_mesh.py)
3. [examples/02_voxel_boolean_filters.py](examples/02_voxel_boolean_filters.py)
4. [examples/03_scalar_vector_fields.py](examples/03_scalar_vector_fields.py)
5. [examples/04_openvdb_io.py](examples/04_openvdb_io.py)
6. [examples/05_stl_io_and_mesh_math.py](examples/05_stl_io_and_mesh_math.py)
7. [examples/06_slicing_and_cli.py](examples/06_slicing_and_cli.py)
8. [examples/07_images_and_tga.py](examples/07_images_and_tga.py)
9. [examples/08_animation_and_csv.py](examples/08_animation_and_csv.py)
10. [examples/09_polyline_and_viewer.py](examples/09_polyline_and_viewer.py)
11. [examples/10_utils_tempfolder_log.py](examples/10_utils_tempfolder_log.py)
12. [examples/11_viewer_controls_and_timelapse.py](examples/11_viewer_controls_and_timelapse.py)

ShapeKernel-focused examples are in [examples/shapekernel](examples/shapekernel):

1. [examples/shapekernel/example_spline.py](examples/shapekernel/example_spline.py)
2. [examples/shapekernel/ex_base_box_showcase.py](examples/shapekernel/ex_base_box_showcase.py)
3. [examples/shapekernel/ex_base_cylinder_showcase.py](examples/shapekernel/ex_base_cylinder_showcase.py)
4. [examples/shapekernel/ex_base_lens_showcase.py](examples/shapekernel/ex_base_lens_showcase.py)
5. [examples/shapekernel/ex_base_pipe_segment_showcase.py](examples/shapekernel/ex_base_pipe_segment_showcase.py)
6. [examples/shapekernel/ex_base_pipe_showcase.py](examples/shapekernel/ex_base_pipe_showcase.py)
7. [examples/shapekernel/ex_base_ring_showcase.py](examples/shapekernel/ex_base_ring_showcase.py)
8. [examples/shapekernel/ex_base_sphere_showcase.py](examples/shapekernel/ex_base_sphere_showcase.py)
9. [examples/shapekernel/ex_basic_lattices.py](examples/shapekernel/ex_basic_lattices.py)
10. [examples/shapekernel/ex_lattice_manifold_showcase.py](examples/shapekernel/ex_lattice_manifold_showcase.py)
11. [examples/shapekernel/ex_lattice_pipe_showcase.py](examples/shapekernel/ex_lattice_pipe_showcase.py)
12. [examples/shapekernel/migration_sh_preview_equivalents.py](examples/shapekernel/migration_sh_preview_equivalents.py)
13. [examples/shapekernel/migration_visualization_equivalents.py](examples/shapekernel/migration_visualization_equivalents.py)

## Status

pycogk is actively developed and has production-readiness gates, but it is still an unofficial project and not a drop-in official replacement.

For readiness details, see:

1. [Production Readiness](docs/picogk/PRODUCTION_READINESS.md)
2. [Parity Matrix](docs/picogk/PARITY_MATRIX.md)
3. [Publishing Guide](docs/picogk/PUBLISHING.md)
