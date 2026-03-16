from __future__ import annotations

from pathlib import Path

import pytest

from picogk import Cli, CsvTable, EStlUnit, ImageColor, ImageGrayScale, Lattice, Mesh, MeshIo, MeshMath, PolySlice, PolySliceStack, TempFolder, TgaIo, Vector3Ext, Voxels, go

try:
    from tests._helpers import runtime_available
except ModuleNotFoundError:
    from _helpers import runtime_available


def test_csv_table_roundtrip(tmp_path: Path) -> None:
    csv_path = tmp_path / "table.csv"

    table = CsvTable()
    table.SetColumnIds(["id", "name", "value"])
    table.SetKeyColumn(0)
    table.AddRow(["r1", "alpha", "10"])
    table.AddRow(["r2", "beta", "20"])
    table.Save(csv_path)

    loaded = CsvTable(csv_path)
    loaded.SetColumnIds(["id", "name", "value"])
    loaded.SetKeyColumn(0)

    assert loaded.nMaxColumnCount() == 3
    ok, value = loaded.bGetAt("r2", "value")
    assert ok
    assert value == "20"


def test_tga_grayscale_and_color_roundtrip(tmp_path: Path) -> None:
    gray_path = tmp_path / "gray.tga"
    color_path = tmp_path / "color.tga"

    gray = ImageGrayScale(4, 3)
    gray.SetValue(1, 1, 0.75)
    gray.SetValue(2, 2, 0.25)
    TgaIo.SaveTga(gray_path, gray)

    info_type, w, h = TgaIo.GetFileInfo(gray_path)
    assert w == 4 and h == 3
    assert int(info_type) == int(gray.eType)

    gray_loaded = TgaIo.LoadTga(gray_path)
    assert isinstance(gray_loaded, ImageGrayScale)
    assert abs(gray_loaded.fValue(1, 1) - 0.75) < 0.02

    color = ImageColor(2, 2)
    color.SetValue(0, 0, (1.0, 0.0, 0.0, 1.0))
    color.SetValue(1, 0, (0.0, 1.0, 0.0, 1.0))
    TgaIo.SaveTga(color_path, color)

    color_loaded = TgaIo.LoadTga(color_path)
    assert isinstance(color_loaded, ImageColor)
    r, g, b, _ = color_loaded.clrValue(0, 0)
    assert r > 0.9 and g < 0.1 and b < 0.1


def test_tempfolder_and_vector3ext() -> None:
    with TempFolder() as tf:
        p = Path(tf.strFolder)
        assert p.exists() and p.is_dir()
        (p / "a.txt").write_text("ok", encoding="utf-8")

    n = Vector3Ext.vecNormalized((0.0, 0.0, 5.0))
    assert abs(n[2] - 1.0) < 1e-6

    mirrored = Vector3Ext.vecMirrored((1.0, 2.0, 3.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert mirrored == pytest.approx((1.0, 2.0, -3.0))


def test_slice_extraction_and_cli_parse(tmp_path: Path) -> None:
    img = ImageGrayScale(8, 8)
    for y in range(8):
        for x in range(8):
            img.SetValue(x, y, -1.0 if 2 <= x <= 5 and 2 <= y <= 5 else 1.0)

    poly_slice = PolySlice.oFromSdf(img, 0.3, (10.0, 20.0), 0.5)
    assert not poly_slice.bIsEmpty()
    poly_slice.Close()

    stack = PolySliceStack([poly_slice])
    cli_path = tmp_path / "slice.cli"
    Cli.WriteSlicesToCliFile(stack, cli_path, Cli.EFormat.FirstLayerWithContent, strDate="2026-03-14", fUnitsInMM=0.1)

    parsed = Cli.oSlicesFromCliFile(cli_path)
    assert parsed.fUnitsHeader == 0.1
    assert parsed.nVersion == 200
    assert parsed.nLayers >= 1
    assert parsed.oSlices.nCount() >= 1


@pytest.mark.skipif(not runtime_available(), reason="PicoGK runtime not available")
def test_stl_save_load_helpers(tmp_path: Path) -> None:
    stl_path = tmp_path / "tri.stl"

    def task() -> None:
        with Mesh() as mesh:
            mesh.nAddTriangle((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0))
            MeshIo.SaveToStlFile(mesh, str(stl_path), EStlUnit.MM)

            loaded = MeshIo.mshFromStlFile(str(stl_path), EStlUnit.AUTO)
            try:
                assert loaded.nTriangleCount() == 1
                ok, idx = MeshMath.bFindTriangleFromSurfacePoint(loaded, (2.0, 2.0, 0.0))
                assert ok and idx == 0
            finally:
                loaded.close()

    go(0.5, task, end_on_task_completion=True)
    assert stl_path.exists()


@pytest.mark.skipif(not runtime_available(), reason="PicoGK runtime not available")
def test_voxels_vectorize_and_save_cli(tmp_path: Path) -> None:
    cli_path = tmp_path / "vox.cli"

    def task() -> None:
        with Lattice() as lat:
            lat.AddSphere((0.0, 0.0, 0.0), 6.0)
            with Voxels.from_lattice(lat) as vox:
                stack = vox.oVectorize(0.5)
                assert stack.nCount() > 0
                vox.SaveToCliFile(str(cli_path), 0.5, Cli.EFormat.FirstLayerWithContent)

    go(0.5, task, end_on_task_completion=True)
    assert cli_path.exists()

    parsed = Cli.oSlicesFromCliFile(cli_path)
    assert parsed.oSlices.nCount() > 0
