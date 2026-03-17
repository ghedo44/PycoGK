
import math
from pathlib import Path

import numpy as np

from _common.types import ColorLike, Vector3Like
from .polyline import PolyLine
from .image_io import TgaIo
from .._viewer_protocol import IViewer
from .._common import to_rgba
from picogk._core.voxels import Voxels
from .image import ImageColor
from .fields import ScalarField, VectorField


class SdfVisualizer:
    @staticmethod
    def imgEncodeFromSdf(
        oField: ScalarField,
        fBackgroundValue: float,
        nSlice: int,
        _clrBackground: ColorLike | None = None,
        _clrSurface: ColorLike | None = None,
        _clrInside: ColorLike | None = None,
        _clrOutside: ColorLike | None = None,
        _clrDefect: ColorLike | None = None,
    ) -> ImageColor:
        dims = oField.GetVoxelDimensions()
        img = ImageColor(dims.x_size, dims.y_size)
        if nSlice >= dims.z_size:
            return img
        colors = {
            "bg": to_rgba(_clrBackground or (0.0, 0.4, 1.0, 1.0)),
            "surf": to_rgba(_clrSurface or (1.0, 1.0, 1.0, 1.0)),
            "in": to_rgba(_clrInside or (0.8, 0.2, 1.0, 1.0)),
            "out": to_rgba(_clrOutside or (0.2, 0.8, 0.2, 1.0)),
            "def": to_rgba(_clrDefect or (1.0, 0.33, 0.0, 1.0)),
        }
        sdf = oField.GetVoxelSlice(nSlice)
        for y in range(dims.y_size):
            for x in range(dims.x_size):
                f = float(sdf[y, x])
                if not math.isfinite(f):
                    clr = colors["def"]
                elif abs(f) < np.finfo(np.float32).eps:
                    clr = colors["surf"]
                elif abs(f - fBackgroundValue) < np.finfo(np.float32).eps:
                    clr = colors["bg"]
                elif f < 0.0:
                    t = min(1.0, abs(f) / max(abs(fBackgroundValue), 1e-6))
                    base = colors["in"]
                    clr = (base[0] * (1.0 - 0.35 * t), base[1] * (1.0 - 0.35 * t), base[2] * (1.0 - 0.35 * t), base[3])
                else:
                    t = min(1.0, abs(f) / max(abs(fBackgroundValue), 1e-6))
                    base = colors["out"]
                    clr = (base[0] * (1.0 - 0.35 * t), base[1] * (1.0 - 0.35 * t), base[2] * (1.0 - 0.35 * t), base[3])
                img.SetValue(x, y, clr)
        return img

    @staticmethod
    def bDoesSliceContainDefect(oField: ScalarField, nSlice: int) -> bool:
        dims = oField.GetVoxelDimensions()
        if nSlice >= dims.z_size:
            return False
        sdf = oField.GetVoxelSlice(nSlice)
        return bool(np.any(~np.isfinite(sdf)))

    @staticmethod
    def bVisualizeSdfSlicesAsTgaStack(
        oField: ScalarField,
        fBackgroundValue: float,
        strPath: str,
        strFilePrefix: str = "Sdf_",
        bOnlyDefective: bool = False,
        _clrBackground: ColorLike | None = None,
        _clrSurface: ColorLike | None = None,
        _clrInside: ColorLike | None = None,
        _clrOutside: ColorLike | None = None,
        _clrDefect: ColorLike | None = None,
    ) -> bool:
        path = Path(strPath)
        path.mkdir(parents=True, exist_ok=True)
        dims = oField.GetVoxelDimensions()
        found_defect = False
        for s in range(dims.z_size):
            has_defect = SdfVisualizer.bDoesSliceContainDefect(oField, s)
            found_defect = found_defect or has_defect
            if bOnlyDefective and not has_defect:
                continue
            img = SdfVisualizer.imgEncodeFromSdf(
                oField,
                fBackgroundValue,
                s,
                _clrBackground,
                _clrSurface,
                _clrInside,
                _clrOutside,
                _clrDefect,
            )
            TgaIo.SaveTga(path / f"{strFilePrefix}{s:05d}.tga", img)
        return found_defect


class ActiveVoxelCounterScalar:
    @staticmethod
    def nCount(oField: ScalarField) -> int:
        count = 0

        def _visit(_: tuple[float, float, float], __: float) -> None:
            nonlocal count
            count += 1

        oField.TraverseActive(_visit)
        return count


class SurfaceNormalFieldExtractor:
    @staticmethod
    def oExtract(
        vox: Voxels,
        fSurfaceThresholdVx: float = 0.5,
        vecDirectionFilter: Vector3Like | None = None,
        fDirectionFilterTolerance: float = 0.0,
        vecScaleBy: Vector3Like | None = None,
    ) -> VectorField:
        direction = np.array(vecDirectionFilter if vecDirectionFilter is not None else (0.0, 0.0, 0.0), dtype=np.float64)
        if np.linalg.norm(direction) > 1e-12:
            direction = direction / np.linalg.norm(direction)
        scale_by = np.array(vecScaleBy if vecScaleBy is not None else (1.0, 1.0, 1.0), dtype=np.float64)

        src = ScalarField.from_voxels(vox)
        dst = VectorField()

        def _visit(pos: tuple[float, float, float], value: float) -> None:
            if abs(value) > fSurfaceThresholdVx:
                return
            normal = np.array(vox.vecSurfaceNormal(pos), dtype=np.float64)
            nlen = np.linalg.norm(normal)
            if nlen <= 1e-12:
                return
            normal = normal / nlen
            if np.linalg.norm(direction) > 1e-12:
                dev = abs(1.0 - float(np.dot(normal, direction)))
                if dev > float(fDirectionFilterTolerance):
                    return
            v = normal * scale_by
            dst.SetValue(pos, (float(v[0]), float(v[1]), float(v[2])))

        src.TraverseActive(_visit)
        src.close()
        return dst


class VectorFieldMerge:
    @staticmethod
    def Merge(oSource: VectorField, oTarget: VectorField) -> None:
        def _visit(p: tuple[float, float, float], v: tuple[float, float, float]) -> None:
            oTarget.SetValue(p, v)

        oSource.TraverseActive(_visit)



class AddVectorFieldToViewer:
    @staticmethod
    def AddToViewer(oViewer: IViewer, oField: VectorField, clr: ColorLike, nStep: int = 10, fArrow: float = 1.0, nGroup: int = 0) -> None:
        if nStep <= 0:
            raise ValueError("nStep must be > 0")
        color = to_rgba(clr)
        count = 0

        def _visit(pos: tuple[float, float, float], vec: tuple[float, float, float]) -> None:
            nonlocal count
            count += 1
            if count < nStep:
                return
            count = 0

            poly = PolyLine(color)
            poly.nAddVertex(pos)
            if abs(vec[0]) < 1e-12 and abs(vec[1]) < 1e-12 and abs(vec[2]) < 1e-12:
                poly.AddCross(fArrow)
            else:
                poly.nAddVertex((pos[0] + vec[0], pos[1] + vec[1], pos[2] + vec[2]))
                poly.AddArrow(fArrow)

            add_fn = getattr(oViewer, "Add", None)
            if callable(add_fn):
                add_fn(poly, nGroup)

        oField.TraverseActive(_visit)


class FieldUtils:
    SdfVisualizer = SdfVisualizer
    ActiveVoxelCounterScalar = ActiveVoxelCounterScalar
    SurfaceNormalFieldExtractor = SurfaceNormalFieldExtractor
    VectorFieldMerge = VectorFieldMerge
    AddVectorFieldToViewer = AddVectorFieldToViewer

