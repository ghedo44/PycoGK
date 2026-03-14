from __future__ import annotations

from pathlib import Path


EXPECTED_CSHARP_SYMBOLS = {
    "ActiveVoxelCounterScalar",
    "AddVectorFieldToViewer",
    "Animation",
    "AnimationQueue",
    "AnimGroupMatrixRotate",
    "AnimViewRotate",
    "CliIo",
    "Config",
    "CsvTable",
    "Easing",
    "FieldMetadata",
    "ImageColor",
    "ImageGrayScale",
    "ImageRgb24",
    "ImageRgba32",
    "ImplicitMesh",
    "ImplicitTriangle",
    "KeyAction",
    "KeyHandler",
    "Lattice",
    "Library",
    "LogFile",
    "Mesh",
    "OpenVdbFile",
    "PolyContour",
    "PolyLine",
    "PolySlice",
    "PolySliceStack",
    "Result",
    "RotateToNextRoundAngleAction",
    "ScalarField",
    "SdfVisualizer",
    "SurfaceNormalFieldExtractor",
    "TempFolder",
    "TgaIo",
    "Utils",
    "VectorField",
    "VectorFieldMerge",
    "Viewer",
    "Voxels",
}

VALID_STATUSES = {"matched", "adapted", "not-implemented"}


def _read_parity_lines() -> list[str]:
    matrix_path = Path(__file__).resolve().parents[1] / "docs" / "PARITY_MATRIX.md"
    text = matrix_path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip().startswith("| ")]


def test_parity_matrix_file_exists() -> None:
    matrix_path = Path(__file__).resolve().parents[1] / "docs" / "PARITY_MATRIX.md"
    assert matrix_path.exists(), "docs/PARITY_MATRIX.md is missing"


def test_parity_matrix_contains_all_expected_symbols() -> None:
    lines = _read_parity_lines()
    symbol_lines = [line for line in lines if not line.startswith("| ---") and "| Status |" not in line]

    found_symbols: set[str] = set()
    for line in symbol_lines:
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        symbol, status = parts[0], parts[1]
        if symbol in EXPECTED_CSHARP_SYMBOLS:
            found_symbols.add(symbol)
        assert status in VALID_STATUSES, f"Invalid parity status '{status}' for symbol '{symbol}'"

    missing = sorted(EXPECTED_CSHARP_SYMBOLS - found_symbols)
    assert not missing, f"PARITY_MATRIX.md missing symbols: {missing}"
