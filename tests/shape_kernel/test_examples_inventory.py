from __future__ import annotations

from pathlib import Path


def test_shapekernel_examples_inventory_is_present() -> None:
    root = Path(__file__).resolve().parents[2]
    examples = root / "examples" / "shape_kernel"
    assert examples.is_dir(), "shapekernel examples directory is missing"

    expected = {
        "example_spline.py",
        "ex_base_box_showcase.py",
        "ex_base_cylinder_showcase.py",
        "ex_base_lens_showcase.py",
        "ex_base_pipe_segment_showcase.py",
        "ex_base_pipe_showcase.py",
        "ex_base_ring_showcase.py",
        "ex_base_sphere_showcase.py",
        "ex_basic_lattices.py",
        "ex_lattice_manifold_showcase.py",
        "ex_lattice_pipe_showcase.py",
        "migration_sh_preview_equivalents.py",
        "migration_visualization_equivalents.py",
    }

    present = {path.name for path in examples.glob("*.py") if path.name != "_shared.py"}
    missing = sorted(expected - present)
    assert not missing, f"Missing expected shapekernel examples: {missing}"
