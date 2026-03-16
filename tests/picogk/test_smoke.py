from __future__ import annotations

from pathlib import Path

from picogk._core.voxels import ESliceMode
import pytest

from picogk import Lattice, Mesh, OpenVdbFile, PolyLine, ScalarField, VectorField, Voxels, go

try:
    from tests._helpers import runtime_available
except ModuleNotFoundError:
    from _helpers import runtime_available


pytestmark = pytest.mark.skipif(not runtime_available(), reason="PicoGK runtime not available")


def test_go_runs_task_and_closes() -> None:
    completed: list[bool] = []

    def task() -> None:
        with Voxels() as v1, Voxels() as v2:
            with Lattice() as lat:
                lat.add_sphere((0.0, 0.0, 0.0), 10.0)
                v1.render_lattice(lat)
                v2.render_lattice(lat)
            completed.append(True)

    go(0.5, task, end_on_task_completion=True)
    assert completed


def test_voxels_bool_ops() -> None:
    def task() -> None:
        with Lattice() as a, Lattice() as b:
            a.add_sphere((0.0, 0.0, 0.0), 10.0)
            b.add_sphere((5.0, 0.0, 0.0), 10.0)

            with Voxels.from_lattice(a) as va, Voxels.from_lattice(b) as vb:
                va.bool_add(vb)
                assert va.is_valid()

                va.bool_subtract(vb)
                assert va.is_valid()

                va.bool_intersect(vb)
                assert va.is_valid()

    go(0.5, task, end_on_task_completion=True)


def test_mesh_from_voxels() -> None:
    def task() -> None:
        with Lattice() as lat:
            lat.add_sphere((0.0, 0.0, 0.0), 10.0)
            with Voxels.from_lattice(lat) as vox:
                with Mesh.from_voxels(vox) as mesh:
                    assert mesh.vertex_count() > 0
                    assert mesh.triangle_count() > 0

    go(0.5, task, end_on_task_completion=True)


def test_runtime_parity_aliases_and_helpers(tmp_path: Path) -> None:
    def task() -> None:
        with Lattice() as lat:
            lat.AddSphere((0.0, 0.0, 0.0), 8.0)
            lat.AddBeam((-8.0, 0.0, 0.0), (8.0, 0.0, 0.0), 2.0, 2.0)

            with Voxels.from_lattice(lat) as vox:
                assert vox.nSliceCount() > 0
                assert vox.GetVoxelSlice(0, ESliceMode.BlackWhite).ndim == 2
                assert vox.oMetaData().strTypeAt("PicoGK.Class") == "string"

                with Mesh.from_voxels(vox) as mesh:
                    mirrored = mesh.mshCreateMirrored((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                    try:
                        assert mirrored.Append(mesh).nTriangleCount() >= mesh.nTriangleCount()
                    finally:
                        mirrored.close()

                with ScalarField.from_voxels(vox) as scalar_field:
                    hits: list[tuple[tuple[float, float, float], float]] = []
                    scalar_field.TraverseActive(lambda pos, value: hits.append((pos, value)) if len(hits) < 2 else None)
                    assert hits

                with VectorField.build_from_voxels(vox, (1.0, 0.0, 0.0)) as vector_field:
                    hits_v: list[tuple[tuple[float, float, float], tuple[float, float, float]]] = []
                    vector_field.TraverseActive(lambda pos, value: hits_v.append((pos, value)) if len(hits_v) < 2 else None)
                    assert hits_v

    go(0.5, task, end_on_task_completion=True)


def test_vdb_and_polyline_helpers(tmp_path: Path) -> None:
    vdb_path = tmp_path / "parity.vdb"

    def task() -> None:
        with Lattice() as lat:
            lat.AddSphere((0.0, 0.0, 0.0), 6.0)
            with Voxels.from_lattice(lat) as vox, ScalarField.from_voxels(vox) as scalar_field, VectorField.build_from_voxels(vox, (1.0, 0.0, 0.0)) as vector_field:
                with OpenVdbFile() as vdb:
                    assert vdb.nAdd(vox, "vox") == 0
                    assert vdb.nAdd(scalar_field, "sf") == 1
                    assert vdb.nAdd(vector_field, "vf") == 2
                    vdb.SaveToFile(str(vdb_path))
                    assert vdb.nFieldCount() == 3
                    assert vdb.strFieldType(0) == "Voxels"
                    assert vdb.bIsPicoGKCompatible()
                    assert vdb.fPicoGKVoxelSizeMM() > 0.0

        with PolyLine() as polyline:
            polyline.Add([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])
            polyline.AddArrow(0.5)
            polyline.AddCross(0.25)
            assert polyline.nVertexCount() > 2
            bbox_min, bbox_max = polyline.oBoundingBox()
            assert bbox_max[0] >= bbox_min[0]

    go(0.5, task, end_on_task_completion=True)
    assert vdb_path.exists()
