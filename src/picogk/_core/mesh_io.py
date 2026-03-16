from __future__ import annotations

from enum import IntEnum
import struct
from typing import TYPE_CHECKING

from _common.types import Vector3Like
import numpy as np
from pathlib import Path

if TYPE_CHECKING:
    from .mesh import Mesh


class EStlUnit(IntEnum):
    AUTO = 0
    MM = 1
    CM = 2
    M = 3
    FT = 4
    IN = 5


def _stl_unit_scale_to_mm(unit: EStlUnit) -> float:
    return {
        EStlUnit.MM: 1.0,
        EStlUnit.CM: 10.0,
        EStlUnit.M: 1000.0,
        EStlUnit.FT: 304.8,
        EStlUnit.IN: 25.4,
    }.get(unit, 1.0)


class MeshIo:
    @staticmethod
    def mshFromStlFile(
        strFilePath: str,
        eLoadUnit: EStlUnit = EStlUnit.AUTO,
        fPostScale: float = 1.0,
        vecPostOffsetMM: Vector3Like | None = None,
    ) -> Mesh:
        from .mesh import Mesh

        path = Path(strFilePath)
        raw = path.read_bytes()
        if len(raw) < 84:
            raise ValueError("Failed to read STL file, header too short")
        header = raw[:80].decode("ascii", errors="ignore")
        offset = np.array(
            vecPostOffsetMM if vecPostOffsetMM is not None else (0.0, 0.0, 0.0),
            dtype=np.float64,
        )

        load_unit = eLoadUnit
        if load_unit == EStlUnit.AUTO:
            h = header.lower()
            if "units=cm" in h:
                load_unit = EStlUnit.CM
            elif "units= m" in h:
                load_unit = EStlUnit.M
            elif "units=ft" in h:
                load_unit = EStlUnit.FT
            elif "units=in" in h:
                load_unit = EStlUnit.IN
            else:
                load_unit = EStlUnit.MM

        scale = _stl_unit_scale_to_mm(load_unit) * float(fPostScale)
        msh = Mesh()
        msh.m_strLoadHeaderData = header.strip()
        msh.m_eLoadUnits = load_unit

        is_ascii = raw.startswith(b"solid") and (b"vertex" in raw[:2048])
        if is_ascii:
            text = raw.decode("ascii", errors="ignore")
            verts: list[tuple[float, float, float]] = []
            for line in text.splitlines():
                line = line.strip().lower()
                if line.startswith("vertex "):
                    parts = line.split()
                    if len(parts) >= 4:
                        v = np.array(
                            (float(parts[1]), float(parts[2]), float(parts[3])),
                            dtype=np.float64,
                        )
                        v = (v * scale) + offset
                        verts.append((float(v[0]), float(v[1]), float(v[2])))
                        if len(verts) == 3:
                            msh.nAddTriangle(verts[0], verts[1], verts[2])
                            verts.clear()
        else:
            tri_count = struct.unpack("<I", raw[80:84])[0]
            cursor = 84
            for _ in range(tri_count):
                if cursor + 50 > len(raw):
                    break
                data = raw[cursor : cursor + 50]
                cursor += 50
                v0 = np.array(struct.unpack("<3f", data[12:24]), dtype=np.float64)
                v1 = np.array(struct.unpack("<3f", data[24:36]), dtype=np.float64)
                v2 = np.array(struct.unpack("<3f", data[36:48]), dtype=np.float64)
                v0 = (v0 * scale) + offset
                v1 = (v1 * scale) + offset
                v2 = (v2 * scale) + offset
                msh.nAddTriangle(
                    tuple(v0.tolist()), tuple(v1.tolist()), tuple(v2.tolist())
                )

        if msh.nTriangleCount() == 0:
            msh.close()
            raise ValueError(
                "Imported STL mesh is empty (zero triangles), failed to load"
            )
        return msh

    @staticmethod
    def SaveToStlFile(
        mesh: Mesh,
        strFilePath: str,
        eUnit: EStlUnit = EStlUnit.AUTO,
        vecOffsetMM: Vector3Like | None = None,
        fScale: float = 1.0,
    ) -> None:
        unit = eUnit
        if unit == EStlUnit.AUTO:
            unit = getattr(mesh, "m_eLoadUnits", EStlUnit.MM)
        unit_tag = {
            EStlUnit.CM: "UNITS=cm",
            EStlUnit.M: "UNITS= m",
            EStlUnit.FT: "UNITS=ft",
            EStlUnit.IN: "UNITS=in",
        }.get(unit, "UNITS=mm")
        header = f"PicoGK {unit_tag}".ljust(80, " ").encode("ascii", errors="ignore")
        conv = 1.0 / _stl_unit_scale_to_mm(unit)
        offset = np.array(
            vecOffsetMM if vecOffsetMM is not None else (0.0, 0.0, 0.0),
            dtype=np.float64,
        )

        with open(strFilePath, "wb") as handle:
            handle.write(header)
            handle.write(struct.pack("<I", mesh.nTriangleCount()))
            for i in range(mesh.nTriangleCount()):
                a, b, c = mesh.GetTriangle(i)
                va = (np.array(a, dtype=np.float64) + offset) * fScale * conv
                vb = (np.array(b, dtype=np.float64) + offset) * fScale * conv
                vc = (np.array(c, dtype=np.float64) + offset) * fScale * conv
                normal = np.cross(vb - va, vc - va)
                nlen = np.linalg.norm(normal)
                if nlen > 1e-12:
                    normal = normal / nlen
                else:
                    normal = np.array((0.0, 0.0, 1.0), dtype=np.float64)
                handle.write(
                    struct.pack(
                        "<3f", float(normal[0]), float(normal[1]), float(normal[2])
                    )
                )
                handle.write(
                    struct.pack("<3f", float(va[0]), float(va[1]), float(va[2]))
                )
                handle.write(
                    struct.pack("<3f", float(vb[0]), float(vb[1]), float(vb[2]))
                )
                handle.write(
                    struct.pack("<3f", float(vc[0]), float(vc[1]), float(vc[2]))
                )
                handle.write(struct.pack("<H", 0))
