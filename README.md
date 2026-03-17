# pycogk

Python package for using PicoGK and related LEAP 71 geometry libraries from Python.

This is an **unofficial community** library.

- Official PicoGK project (C++ / C#): https://github.com/leap71/PicoGK
- This Python package repository: https://github.com/ghedo44/PycoGK

The goal is to keep a PicoGK-like API where practical while adapting the workflow to Python, including a `vedo`-based viewer layer.

## Library Summary

This repository currently ships six Python libraries.

| Library | Primary role | Inspired by C# repo | Typical use |
| --- | --- | --- | --- |
| `picogk` | Runtime bridge and core geometry API | `PicoGK` | Lattice/voxel/mesh/field creation, IO, viewer orchestration |
| `shape_kernel` | High-level modeling toolkit | `LEAP71_ShapeKernel` | Base shapes, frames/splines, utility functions, composition workflows |
| `lattice_library` | Beam-lattice workflow framework | `LEAP71_LatticeLibrary` | Cell arrays + lattice logic + beam thickness strategy |
| `implicit_library` | TPMS/implicit construction framework | `LEAP71_LatticeLibrary` (Implicit Library part) | Modular implicits, coordinate transforms, split/wall logic |
| `penrose_pattern` | 2D Penrose tiling primitives | `LEAP71_QuasiCrystals` | Aperiodic 2D tilings and subdivision logic |
| `quasi_crystal` | 3D quasi-crystal building blocks | `LEAP71_QuasiCrystals` | Icosahedral face/tile inflation and quasi-crystal assembly |

## Architecture At A Glance

Practical dependency picture:

1. `picogk` is the runtime-facing foundation.
2. `shape_kernel` builds on `picogk`.
3. `lattice_library` and `implicit_library` build on `picogk` (and interoperate with each other).
4. `penrose_pattern` and `quasi_crystal` provide aperiodic tiling/quasi-crystal logic and can be combined with `picogk` visualization/output workflows.

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

The distribution name is `pycogk`, while imports are per-library:

```python
import picogk
import shape_kernel
import lattice_library
import implicit_library
import penrose_pattern
import quasi_crystal
```

## Runtime Notes

`pycogk` loads the PicoGK native runtime using `ctypes`.

Bundled runtime targets currently include:

1. `win-x64`
2. `osx-arm64`

If your platform is not bundled, set `PICOGK_RUNTIME_PATH` to a compatible binary.

PowerShell example:

```powershell
$env:PICOGK_RUNTIME_PATH = "C:\path\to\picogk.1.7.dll"
python your_script.py
```

## Quick Start (`picogk`)

```python
from picogk import Lattice, Mesh, VedoViewer, Voxels, go

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

## In-Depth: `picogk`

`picogk` is the low-level runtime API. It wraps the PicoGK native library and exposes core primitives needed by the rest of the stack.

Main capabilities include:

1. Runtime lifecycle and viewer orchestration via `Library`, `go`, and viewer interfaces.
2. Geometry primitives such as `Lattice`, `Voxels`, `Mesh`, and `PolyLine`.
3. Field workflows with `ScalarField`, `VectorField`, metadata, and field utilities.
4. IO and processing helpers for mesh, image, slice, CSV, CLI, OpenVDB, and utility workflows.

Use `picogk` when you need direct, explicit control over runtime objects and conversion steps.

## In-Depth: `shape_kernel`

`shape_kernel` is a higher-level modeling toolkit inspired by LEAP 71 ShapeKernel concepts. In the original C# framing, ShapeKernel bridges low-level kernel operations and higher-level engineering design intent.

Main capabilities include:

1. Parametric base shapes (`BaseBox`, `BaseCylinder`, `BaseSphere`, `BasePipe`, `BaseLens`, and more).
2. Frame and spline infrastructure (`LocalFrame`, `Frames`, control splines, tangential splines).
3. Modulations and geometric composition helpers (`LineModulation`, `SurfaceModulation`, `Sh`).
4. Utility classes for measurement, mesh operations, cylindrical utilities, and color/visualization helpers.

Use `shape_kernel` when you want expressive modeling code with less low-level plumbing.

## In-Depth: `lattice_library`

`lattice_library` ports the flexible lattice workflow from the C# Lattice Library. The core idea is to keep three concerns independent so they can be recombined:

1. Cell array generation (`ICellArray` and concrete arrays).
2. Lattice connection logic (`ILatticeType` and concrete lattice types).
3. Beam thickness strategy (`IBeamThickness` and concrete thickness models).

Representative classes include:

1. Cell arrays: `RegularUnitCell`, `RegularCellArray`, `ConformalCellArray`.
2. Lattice types: `BodyCentreLattice`, `OctahedronLattice`, `RandomSplineLattice`.
3. Thickness models: `ConstantBeamThickness`, `CellBasedBeamThickness`, `GlobalFuncBeamThickness`, `BoundaryBeamThickness`.

Use `lattice_library` when designing beam-based infill/meta-material workflows where topology and thickness rules are customized independently.

## In-Depth: `implicit_library`

`implicit_library` ports the Implicit Library concepts from the C# Lattice Library project. It focuses on TPMS-style implicits and modular composition logic.

Main capabilities include:

1. Coordinate transformations (`ScaleTrafo`, `RadialTrafo`, `FunctionalScaleTrafo`, `CombinedTrafo`).
2. Splitting logic and signed-region control (`FullWallLogic`, `FullVoidLogic`, half-wall and void variants).
3. Raw TPMS patterns (`RawGyroidTPMSPattern`, `RawLidinoidTPMSPattern`, Schwarz variants, transitions).
4. Modular implicit assembly (`ImplicitModular`) and ready presets in `TPMSPresets`.

Use `implicit_library` when constructing procedural implicit materials with tunable wall/void behavior and spatial transforms.

## In-Depth: `penrose_pattern`

`penrose_pattern` provides 2D aperiodic tiling primitives inspired by the Penrose workflow from the C# Quasi Crystals repository.

Main capabilities include:

1. Penrose pattern generation via tile subdivision logic.
2. Tile primitives such as `RhombicTile`, `LargeRhombicTile`, and `SmallRhombicTile`.
3. Supporting geometric entities like `RobinsonTriangle`.

Use `penrose_pattern` when you need non-periodic 2D tilings with local order and no translational symmetry.

## In-Depth: `quasi_crystal`

`quasi_crystal` provides 3D quasi-crystal building blocks, aligned with the C# quasi-crystal concepts (icosahedral faces, quasi-tiles, and inflation/substitution rules).

Main capabilities include:

1. Rhombic-face representation (`IcosehedralFace`).
2. Quasi-tile families (`QuasiTile`, `QuasiTile_01` to `QuasiTile_04`).
3. Inflation/subdivision support (`QuasiTileInflation`).
4. Crystal-level assembly utilities (`QuasiCrystal`).

Use `quasi_crystal` when exploring aperiodic 3D structures and rule-driven quasi-tile expansion.

## Documentation

Current long-form docs are available for:

1. `picogk`
2. `shape_kernel`

### `picogk` docs

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

### `shape_kernel` docs

1. [Book Home](docs/shape_kernel/BOOK.md)
2. [Chapter 1: Orientation](docs/shape_kernel/book/01_orientation.md)
3. [Chapter 2: Concept Mapping](docs/shape_kernel/book/02_concept_mapping.md)
4. [Chapter 3: Frames and Splines](docs/shape_kernel/book/03_frames_and_splines.md)
5. [Chapter 4: Base Shapes](docs/shape_kernel/book/04_base_shapes.md)
6. [Chapter 5: Modulations and Utility Functions](docs/shape_kernel/book/05_modulations_and_utilities.md)
7. [Chapter 6: Visualization and Preview](docs/shape_kernel/book/06_visualization_and_preview.md)
8. [Chapter 7: Measurements and Runtime Helpers](docs/shape_kernel/book/07_measurements_and_runtime_helpers.md)
9. [Chapter 8: Migration Guide](docs/shape_kernel/book/08_migration_guide.md)

For `lattice_library`, `implicit_library`, `penrose_pattern`, and `quasi_crystal`, use source and tests as the current reference points.

## Examples

Runnable examples are organized by library focus.

### `picogk` examples

1. [examples/picogk/basic_usage.py](examples/picogk/basic_usage.py)
2. [examples/picogk/01_lattice_to_mesh.py](examples/picogk/01_lattice_to_mesh.py)
3. [examples/picogk/02_voxel_boolean_filters.py](examples/picogk/02_voxel_boolean_filters.py)
4. [examples/picogk/03_scalar_vector_fields.py](examples/picogk/03_scalar_vector_fields.py)
5. [examples/picogk/04_openvdb_io.py](examples/picogk/04_openvdb_io.py)
6. [examples/picogk/05_stl_io_and_mesh_math.py](examples/picogk/05_stl_io_and_mesh_math.py)
7. [examples/picogk/06_slicing_and_cli.py](examples/picogk/06_slicing_and_cli.py)
8. [examples/picogk/07_images_and_tga.py](examples/picogk/07_images_and_tga.py)
9. [examples/picogk/08_animation_and_csv.py](examples/picogk/08_animation_and_csv.py)
10. [examples/picogk/09_polyline_and_viewer.py](examples/picogk/09_polyline_and_viewer.py)
11. [examples/picogk/10_utils_tempfolder_log.py](examples/picogk/10_utils_tempfolder_log.py)
12. [examples/picogk/11_viewer_controls_and_timelapse.py](examples/picogk/11_viewer_controls_and_timelapse.py)

### `shape_kernel` examples

1. [examples/shape_kernel/example_spline.py](examples/shape_kernel/example_spline.py)
2. [examples/shape_kernel/ex_base_box_showcase.py](examples/shape_kernel/ex_base_box_showcase.py)
3. [examples/shape_kernel/ex_base_cylinder_showcase.py](examples/shape_kernel/ex_base_cylinder_showcase.py)
4. [examples/shape_kernel/ex_base_lens_showcase.py](examples/shape_kernel/ex_base_lens_showcase.py)
5. [examples/shape_kernel/ex_base_pipe_segment_showcase.py](examples/shape_kernel/ex_base_pipe_segment_showcase.py)
6. [examples/shape_kernel/ex_base_pipe_showcase.py](examples/shape_kernel/ex_base_pipe_showcase.py)
7. [examples/shape_kernel/ex_base_ring_showcase.py](examples/shape_kernel/ex_base_ring_showcase.py)
8. [examples/shape_kernel/ex_base_sphere_showcase.py](examples/shape_kernel/ex_base_sphere_showcase.py)
9. [examples/shape_kernel/ex_basic_lattices.py](examples/shape_kernel/ex_basic_lattices.py)
10. [examples/shape_kernel/ex_lattice_manifold_showcase.py](examples/shape_kernel/ex_lattice_manifold_showcase.py)
11. [examples/shape_kernel/ex_lattice_pipe_showcase.py](examples/shape_kernel/ex_lattice_pipe_showcase.py)
12. [examples/shape_kernel/migration_sh_preview_equivalents.py](examples/shape_kernel/migration_sh_preview_equivalents.py)
13. [examples/shape_kernel/migration_visualization_equivalents.py](examples/shape_kernel/migration_visualization_equivalents.py)

### Additional library references

Integration and behavior checks for additional libraries are currently covered in tests:

1. `tests/lattice_library`
2. `tests/implicit_library`

## Status

`pycogk` is actively developed and has production-readiness gates, but it is still an unofficial project and not a drop-in official replacement.

For readiness details, see:

1. [Production Readiness](docs/picogk/PRODUCTION_READINESS.md)
2. [Parity Matrix](docs/picogk/PARITY_MATRIX.md)
3. [Publishing Guide](docs/picogk/PUBLISHING.md)
