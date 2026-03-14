# pycogk

Python package for working with PicoGK from Python.

This is an unofficial community library.

- Official PicoGK project (C++ / C#): https://github.com/leap71/PicoGK
- This Python package repository: https://github.com/ghedo44/PycoGK

The package keeps a PicoGK-like API where practical while adapting parts of the experience to Python, including a vedo-based viewer layer.

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

New-user docs are organized like a book:

1. [Book Home](docs/BOOK.md)
2. [Chapter 1: Orientation](docs/book/01_orientation.md)
3. [Chapter 2: Installation and Runtime](docs/book/02_installation_and_runtime.md)
4. [Chapter 3: First Project](docs/book/03_first_project.md)
5. [Chapter 4: Core Concepts](docs/book/04_core_concepts.md)
6. [Chapter 5: Modeling Workflow](docs/book/05_modeling_workflow.md)
7. [Chapter 6: Viewer and Interaction](docs/book/06_viewer_and_interaction.md)
8. [Chapter 7: Data IO](docs/book/07_data_io.md)
9. [Chapter 8: Troubleshooting](docs/book/08_troubleshooting.md)
10. [Chapter 9: Production and Publishing](docs/book/09_production_and_publishing.md)

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

## Status

pycogk is actively developed and has production-readiness gates, but it is still an unofficial project and not a drop-in official replacement.

For readiness details, see:

1. [Production Readiness](docs/PRODUCTION_READINESS.md)
2. [Parity Matrix](docs/PARITY_MATRIX.md)
3. [Publishing Guide](docs/PUBLISHING.md)
