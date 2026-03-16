from __future__ import annotations

from datetime import datetime
import math
import os
from pathlib import Path
import sys
import tempfile
import time

from _common.types import Vector3Like


class Utils:
    @staticmethod
    def bFileExists(path: str | Path) -> bool:
        return Path(path).is_file()

    @staticmethod
    def bFolderExists(path: str | Path) -> bool:
        return Path(path).is_dir()

    @staticmethod
    def strGetFullPath(path: str | Path) -> str:
        return str(Path(path).resolve())

    @staticmethod
    def strGetFileName(path: str | Path) -> str:
        return Path(path).name

    @staticmethod
    def strGetFileNameWithoutExtension(path: str | Path) -> str:
        return Path(path).stem

    @staticmethod
    def strGetFolderName(path: str | Path) -> str:
        return Path(path).parent.name

    @staticmethod
    def strGetFileExtension(path: str | Path) -> str:
        return Path(path).suffix

    @staticmethod
    def strGetFileNameWithOtherExtension(path: str | Path, extension: str) -> str:
        p = Path(path)
        if extension and not extension.startswith("."):
            extension = "." + extension
        return str(p.with_suffix(extension))

    @staticmethod
    def strReplaceFileName(path: str | Path, new_name: str) -> str:
        return str(Path(path).with_name(new_name))

    @staticmethod
    def strShorten(text: str, max_len: int = 48) -> str:
        if max_len < 6:
            max_len = 6
        if len(text) <= max_len:
            return text
        lead = max_len // 2 - 1
        trail = max_len - lead - 3
        return text[:lead] + "..." + text[-trail:]

    @staticmethod
    def strStripQuotesFromPath(strPath: str) -> str:
        if len(strPath) >= 2 and strPath[0] == '"' and strPath[-1] == '"':
            return strPath[1:-1]
        return strPath

    @staticmethod
    def bWaitForFileExistence(strFile: str | Path, fTimeOut: float = 1000000.0) -> bool:
        deadline = time.monotonic() + max(0.0, float(fTimeOut))
        target = Path(strFile)
        while time.monotonic() < deadline:
            if target.exists():
                return True
            time.sleep(0.1)
        return target.exists()

    @staticmethod
    def strHomeFolder() -> str:
        return str(Path.home())

    @staticmethod
    def strDocumentsFolder() -> str:
        docs = Path.home() / "Documents"
        return str(docs if docs.exists() else Path.home())

    @staticmethod
    def strProjectRootFolder() -> str:
        return str(Path.cwd())

    @staticmethod
    def strPicoGKSourceCodeFolder() -> str:
        return str(Path(Utils.strProjectRootFolder()) / "PicoGK")

    @staticmethod
    def strExecutableFolder() -> str:
        return str(Path(sys.argv[0]).resolve().parent)

    @staticmethod
    def strDateTimeFilename(strPrefix: str, strPostfix: str) -> str:
        return f"{strPrefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}{strPostfix}"

    @staticmethod
    def SetMatrixRow(mat: list[float], n: int, f1: float, f2: float, f3: float, f4: float) -> None:
        if len(mat) < 16:
            raise ValueError("mat must have at least 16 entries")
        if n < 0 or n > 3:
            raise ValueError("matrix row index must be in 0..3")
        base = n * 4
        mat[base] = float(f1)
        mat[base + 1] = float(f2)
        mat[base + 2] = float(f3)
        mat[base + 3] = float(f4)

    @staticmethod
    def matLookAt(vecEye: Vector3Like, vecLookAt: Vector3Like) -> tuple[float, ...]:
        ex, ey, ez = float(vecEye[0]), float(vecEye[1]), float(vecEye[2])
        lx, ly, lz = float(vecLookAt[0]), float(vecLookAt[1]), float(vecLookAt[2])

        vx, vy, vz = ex - lx, ey - ly, ez - lz
        vlen = math.sqrt(vx * vx + vy * vy + vz * vz)
        if vlen <= 1e-12:
            raise ValueError("vecEye must differ from vecLookAt")
        vx, vy, vz = vx / vlen, vy / vlen, vz / vlen

        zx, zy, zz = 0.0, 0.0, 1.0
        rx = zy * vz - zz * vy
        ry = zz * vx - zx * vz
        rz = zx * vy - zy * vx
        rlen = math.sqrt(rx * rx + ry * ry + rz * rz)
        if rlen <= 1e-12:
            rx, ry, rz = 1.0, 0.0, 0.0
            rlen = 1.0
        rx, ry, rz = rx / rlen, ry / rlen, rz / rlen

        ux = vy * rz - vz * ry
        uy = vz * rx - vx * rz
        uz = vx * ry - vy * rx

        mat = [0.0] * 16
        Utils.SetMatrixRow(mat, 0, rx, ux, vx, 0.0)
        Utils.SetMatrixRow(mat, 1, ry, uy, vy, 0.0)
        Utils.SetMatrixRow(mat, 2, rz, uz, vz, 0.0)
        Utils.SetMatrixRow(mat, 3, -(rx * ex + ry * ey + rz * ez), -(ux * ex + uy * ey + uz * ez), -(vx * ex + vy * ey + vz * ez), 1.0)
        return tuple(mat)

    @staticmethod
    def _voxel_size() -> float:
        from .library import Library

        return max(1e-6, float(getattr(Library, "voxel_size_mm", 0.5)))

    @staticmethod
    def mshCreateCube(
        vecScaleOrBox: Vector3Like | tuple[Vector3Like, Vector3Like] | None = None,
        vecOffsetMM: Vector3Like | None = None,
    ):
        from .mesh import Mesh

        if vecScaleOrBox is not None and len(vecScaleOrBox) == 2 and len(vecScaleOrBox[0]) == 3 and len(vecScaleOrBox[1]) == 3:  # type: ignore[index]
            bmin = vecScaleOrBox[0]  # type: ignore[index]
            bmax = vecScaleOrBox[1]  # type: ignore[index]
            scale = (float(bmax[0]) - float(bmin[0]), float(bmax[1]) - float(bmin[1]), float(bmax[2]) - float(bmin[2]))
            offset = (
                0.5 * (float(bmax[0]) + float(bmin[0])),
                0.5 * (float(bmax[1]) + float(bmin[1])),
                0.5 * (float(bmax[2]) + float(bmin[2])),
            )
        else:
            scale = tuple(float(v) for v in (vecScaleOrBox or (1.0, 1.0, 1.0)))
            offset = tuple(float(v) for v in (vecOffsetMM or (0.0, 0.0, 0.0)))

        sx, sy, sz = scale
        ox, oy, oz = offset

        mesh = Mesh()
        cube = [
            (-0.5 * sx + ox, -0.5 * sy + oy, -0.5 * sz + oz),
            (-0.5 * sx + ox, -0.5 * sy + oy, 0.5 * sz + oz),
            (-0.5 * sx + ox, 0.5 * sy + oy, -0.5 * sz + oz),
            (-0.5 * sx + ox, 0.5 * sy + oy, 0.5 * sz + oz),
            (0.5 * sx + ox, -0.5 * sy + oy, -0.5 * sz + oz),
            (0.5 * sx + ox, -0.5 * sy + oy, 0.5 * sz + oz),
            (0.5 * sx + ox, 0.5 * sy + oy, -0.5 * sz + oz),
            (0.5 * sx + ox, 0.5 * sy + oy, 0.5 * sz + oz),
        ]

        mesh.nAddTriangle(cube[0], cube[1], cube[3])
        mesh.nAddTriangle(cube[0], cube[3], cube[2])
        mesh.nAddTriangle(cube[4], cube[6], cube[7])
        mesh.nAddTriangle(cube[4], cube[7], cube[5])
        mesh.nAddTriangle(cube[0], cube[2], cube[6])
        mesh.nAddTriangle(cube[0], cube[6], cube[4])
        mesh.nAddTriangle(cube[1], cube[5], cube[7])
        mesh.nAddTriangle(cube[1], cube[7], cube[3])
        mesh.nAddTriangle(cube[2], cube[3], cube[7])
        mesh.nAddTriangle(cube[2], cube[7], cube[6])
        mesh.nAddTriangle(cube[0], cube[4], cube[5])
        mesh.nAddTriangle(cube[0], cube[5], cube[1])

        return mesh

    @staticmethod
    def mshCreateCylinder(vecScale: Vector3Like | None = None, vecOffsetMM: Vector3Like | None = None, iSides: int = 0):
        from .mesh import Mesh

        sx, sy, sz = tuple(float(v) for v in (vecScale or (1.0, 1.0, 1.0)))
        ox, oy, oz = tuple(float(v) for v in (vecOffsetMM or (0.0, 0.0, 0.0)))
        a = sx * 0.5
        b = sy * 0.5
        if iSides <= 0:
            av = a / Utils._voxel_size()
            bv = b / Utils._voxel_size()
            p = math.pi * (3.0 * (av + bv) - math.sqrt((3.0 * av + bv) * (av + 3.0 * bv)))
            iSides = max(3, 2 * int(math.ceil(p)))
        iSides = max(3, int(iSides))

        mesh = Mesh()
        bottom_center = (ox, oy, oz - sz * 0.5)
        top_center = (bottom_center[0], bottom_center[1], bottom_center[2] + sz)
        prev_bottom = (a + bottom_center[0], bottom_center[1], bottom_center[2])
        prev_top = (prev_bottom[0], prev_bottom[1], prev_bottom[2] + sz)
        step = 2.0 * math.pi / iSides
        for i in range(1, iSides + 1):
            angle = i * step
            this_bottom = (math.cos(angle) * a + bottom_center[0], math.sin(angle) * b + bottom_center[1], bottom_center[2])
            this_top = (this_bottom[0], this_bottom[1], this_bottom[2] + sz)

            mesh.nAddTriangle(top_center, prev_top, this_top)
            mesh.nAddTriangle(prev_bottom, this_bottom, prev_top)
            mesh.nAddTriangle(this_bottom, this_top, prev_top)
            mesh.nAddTriangle(bottom_center, this_bottom, prev_bottom)

            prev_bottom = this_bottom
            prev_top = this_top
        return mesh

    @staticmethod
    def mshCreateCone(vecScale: Vector3Like | None = None, vecOffsetMM: Vector3Like | None = None, iSides: int = 0):
        from .mesh import Mesh

        sx, sy, sz = tuple(float(v) for v in (vecScale or (1.0, 1.0, 1.0)))
        ox, oy, oz = tuple(float(v) for v in (vecOffsetMM or (0.0, 0.0, 0.0)))
        a = sx * 0.5
        b = sy * 0.5
        if iSides <= 0:
            av = a / Utils._voxel_size()
            bv = b / Utils._voxel_size()
            p = math.pi * (3.0 * (av + bv) - math.sqrt((3.0 * av + bv) * (av + 3.0 * bv)))
            iSides = max(3, 2 * int(math.ceil(p)))
        iSides = max(3, int(iSides))

        mesh = Mesh()
        bottom_center = (ox, oy, oz - sz * 0.5)
        top = (bottom_center[0], bottom_center[1], bottom_center[2] + sz)
        prev_bottom = (a + bottom_center[0], bottom_center[1], bottom_center[2])
        step = 2.0 * math.pi / iSides
        for i in range(1, iSides + 1):
            angle = i * step
            this_bottom = (math.cos(angle) * a + bottom_center[0], math.sin(angle) * b + bottom_center[1], bottom_center[2])
            mesh.nAddTriangle(prev_bottom, this_bottom, top)
            mesh.nAddTriangle(bottom_center, this_bottom, prev_bottom)
            prev_bottom = this_bottom
        return mesh

    @staticmethod
    def mshCreateGeoSphere(vecScale: Vector3Like | None = None, vecOffsetMM: Vector3Like | None = None, iSubdivisions: int = 0):
        from .mesh import Mesh

        sx, sy, sz = tuple(float(v) for v in (vecScale or (1.0, 1.0, 1.0)))
        ox, oy, oz = tuple(float(v) for v in (vecOffsetMM or (0.0, 0.0, 0.0)))
        rx, ry, rz = sx * 0.5, sy * 0.5, sz * 0.5

        def normalize_to_radii(v: tuple[float, float, float]) -> tuple[float, float, float]:
            x, y, z = v
            l = math.sqrt((x / max(1e-12, rx)) ** 2 + (y / max(1e-12, ry)) ** 2 + (z / max(1e-12, rz)) ** 2)
            if l <= 1e-12:
                return (0.0, 0.0, rz)
            return (x / l, y / l, z / l)

        t = (1.0 + math.sqrt(5.0)) / 2.0
        base = [
            (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
            (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
            (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
        ]
        verts = [normalize_to_radii((float(x) * rx, float(y) * ry, float(z) * rz)) for x, y, z in base]
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
        ]

        if iSubdivisions <= 0:
            area = 4.0 * math.pi * (((rx * ry) ** 1.6 + (ry * rz) ** 1.6 + (rz * rx) ** 1.6) / 3.0) ** (1.0 / 1.6)
            target = int(math.ceil(area / Utils._voxel_size() / Utils._voxel_size()))
            iSubdivisions = 1
            tris = 80
            while iSubdivisions < 8 and tris < target:
                iSubdivisions += 1
                tris = 20 * (1 << (2 * iSubdivisions))

        def midpoint(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
            return normalize_to_radii(((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5))

        for _ in range(max(0, int(iSubdivisions))):
            new_faces: list[tuple[int, int, int]] = []
            cache: dict[tuple[int, int], int] = {}

            def mid_idx(i: int, j: int) -> int:
                key = (i, j) if i < j else (j, i)
                if key in cache:
                    return cache[key]
                verts.append(midpoint(verts[i], verts[j]))
                idx = len(verts) - 1
                cache[key] = idx
                return idx

            for i0, i1, i2 in faces:
                a = mid_idx(i0, i1)
                b = mid_idx(i1, i2)
                c = mid_idx(i2, i0)
                new_faces.extend([(i0, a, c), (i1, b, a), (i2, c, b), (a, b, c)])
            faces = new_faces

        mesh = Mesh()
        for i0, i1, i2 in faces:
            a = verts[i0]
            b = verts[i1]
            c = verts[i2]
            mesh.nAddTriangle((a[0] + ox, a[1] + oy, a[2] + oz), (b[0] + ox, b[1] + oy, b[2] + oz), (c[0] + ox, c[1] + oy, c[2] + oz))
        return mesh

    def Dispose(self) -> None:
        return None


class TempFolder:
    def __init__(self) -> None:
        self.strFolder = tempfile.mkdtemp(prefix="picogk_")
        self._disposed = False

    def dispose(self) -> None:
        if self._disposed:
            return
        try:
            for file_path in Path(self.strFolder).glob("*"):
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)
            Path(self.strFolder).rmdir()
        except Exception:
            pass
        self._disposed = True

    def __enter__(self) -> "TempFolder":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.dispose()

