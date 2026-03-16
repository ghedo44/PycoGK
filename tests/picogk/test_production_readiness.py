from __future__ import annotations

from pathlib import Path

import pytest

import picogk
from picogk._config import _platform_native_subdirs, candidate_library_paths


def test_public_api_surface_contains_required_symbols() -> None:
    required = {
        "Library",
        "go",
        "Lattice",
        "Voxels",
        "Mesh",
        "ScalarField",
        "VectorField",
        "OpenVdbFile",
        "FieldMetadata",
        "PolyLine",
        "Cli",
        "CliIo",
        "CsvTable",
        "Image",
        "ImageBW",
        "ImageGrayScale",
        "ImageColor",
        "ImageRgb24",
        "ImageRgba32",
        "TgaIo",
        "MeshIo",
        "MeshMath",
        "FieldUtils",
        "TriangleVoxelization",
        "Utils",
        "Vector3Ext",
        "TempFolder",
        "LogFile",
        "VedoViewer",
    }

    exported = set(picogk.__all__)
    missing = sorted(required - exported)
    assert not missing, f"Missing required public symbols: {missing}"


def test_examples_inventory_is_present() -> None:
    root = Path(__file__).resolve().parents[2]
    examples = root / "examples" / "picogk"
    assert examples.is_dir(), "examples directory is missing"

    expected_files = {
        "basic_usage.py",
        "01_lattice_to_mesh.py",
        "02_voxel_boolean_filters.py",
        "03_scalar_vector_fields.py",
        "04_openvdb_io.py",
        "05_stl_io_and_mesh_math.py",
        "06_slicing_and_cli.py",
        "07_images_and_tga.py",
        "08_animation_and_csv.py",
        "09_polyline_and_viewer.py",
        "10_utils_tempfolder_log.py",
        "11_viewer_controls_and_timelapse.py",
    }

    present = {p.name for p in examples.glob("*.py")}
    missing = sorted(expected_files - present)
    assert not missing, f"Missing expected examples: {missing}"


def test_runtime_candidate_discovery_is_not_empty() -> None:
    candidates = candidate_library_paths()
    assert candidates, "No runtime candidates returned"


def test_bundled_runtime_present_for_platform_or_skip() -> None:
    root = Path(__file__).resolve().parents[2]
    native_root = root / "src" / "picogk" / "native"
    if not native_root.exists():
        pytest.skip("No bundled native runtime directory present")

    platform_dirs = [native_root / d for d in _platform_native_subdirs()]
    existing_dirs = [d for d in platform_dirs if d.exists()]
    if not existing_dirs:
        pytest.skip("No bundled runtime for current platform subdir list")

    files = [p for d in existing_dirs for p in d.rglob("*") if p.is_file()]
    assert files, "Platform runtime directories exist but contain no files"
