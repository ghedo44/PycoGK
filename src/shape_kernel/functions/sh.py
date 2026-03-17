from __future__ import annotations

import math
import numpy as np

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence, cast

from picogk import BBox3, IImplicit, Lattice, Library, Mesh, PolyLine, VedoViewer, Voxels
from picogk._types import ColorFloat

from .._types import ColorLike, Vec3, Vector3Like, as_np3, as_vec3
from ..frames.local_frames import LocalFrame
from ..utils import GridOperations, VecOperations

if TYPE_CHECKING:
    from ..base_shapes import BaseBox, BaseCylinder, BasePipe, BaseRing
    from ..frames import Frames


class Sh:
    nNumberOfGroups = 0

    @staticmethod
    def _resolve_viewer(oViewer: VedoViewer | None = None) -> VedoViewer:
        viewer = oViewer if oViewer is not None else Library.oViewer()
        if viewer is None:
            raise RuntimeError("No active viewer. Pass viewer=... to picogk.go(...) or call the preview helper with oViewer=...")
        return viewer # pyright: ignore[reportReturnType]

    @staticmethod
    def _color_rgba(clrColor: ColorLike, alpha: float | None = None) -> tuple[float, float, float, float]:
        if isinstance(clrColor, ColorFloat):
            rgba = (float(clrColor.r), float(clrColor.g), float(clrColor.b), float(clrColor.a))
        else:
            clr = tuple(float(v) for v in clrColor)
            if len(clr) == 3:
                rgba = (clr[0], clr[1], clr[2], 1.0)
            elif len(clr) == 4:
                rgba = (clr[0], clr[1], clr[2], clr[3])
            else:
                raise ValueError("Color must have 3 or 4 components")
        if alpha is None:
            return rgba
        return (rgba[0], rgba[1], rgba[2], float(alpha))

    @staticmethod
    def _next_group_id() -> int:
        group_id = int(Sh.nNumberOfGroups)
        Sh.nNumberOfGroups += 1
        return group_id

    @staticmethod
    def ResetPreviewGroups() -> None:
        Sh.nNumberOfGroups = 0

    @staticmethod
    def _is_point_like(value: object) -> bool:
        if isinstance(value, (str, bytes)):
            return False
        try:
            seq = cast(Sequence[float], value)
            if len(seq) != 3:
                return False
            float(seq[0])
            float(seq[1])
            float(seq[2])
            return True
        except Exception:
            return False

    @staticmethod
    def _is_point_sequence(value: object) -> bool:
        if isinstance(value, (str, bytes)):
            return False
        try:
            seq = cast(Sequence[object], value)
        except Exception:
            return False
        return len(seq) > 0 and Sh._is_point_like(seq[0])

    @staticmethod
    def _parse_preview_style(args: Sequence[object], start: int) -> tuple[float, float, float]:
        values = [0.9, 0.4, 0.7]
        for index in range(min(3, max(0, len(args) - start))):
            values[index] = float(cast(float, args[start + index]))
        return (values[0], values[1], values[2])

    @staticmethod
    def _preview_curve_samples(
        fnPoint: Callable[[float, float], Vec3],
        clrColor: ColorLike,
        param1_values: Sequence[float],
        param2_values: Sequence[float],
        *,
        nCurveSamples: int,
        oViewer: VedoViewer | None = None,
    ) -> list[int]:
        groups: list[int] = []
        for value in param1_values:
            points = [fnPoint(value, t) for t in param2_values]
            groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        if nCurveSamples > 0:
            for value in param2_values:
                points = [fnPoint(t, value) for t in np.linspace(0.0, 1.0, nCurveSamples)]
                groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        return groups

    @staticmethod
    def voxOffset(vox: Voxels, fDistInMM: float) -> Voxels:
        return vox.voxOffset(fDistInMM)

    @staticmethod
    def voxSmoothen(vox: Voxels, fSmoothInMM: float) -> Voxels:
        return vox.voxSmoothen(fSmoothInMM)

    @staticmethod
    def voxOverOffset(vox: Voxels, fInitialDistInMM: float, fFinalDistInMM: float) -> Voxels:
        return vox.voxOverOffset(fInitialDistInMM, fFinalDistInMM)

    @staticmethod
    def voxExtrudeZSlice(vox: Voxels, fStartHeight: float, fEndHeight: float) -> Voxels:
        return vox.voxProjectZSlice(fStartHeight, fEndHeight)

    @staticmethod
    def voxUnion(vox1: Voxels | Sequence[Voxels], vox2: Voxels | None = None) -> Voxels:
        if vox2 is None:
            if not isinstance(vox1, Sequence):
                raise TypeError("voxUnion expects (Voxels, Voxels) or (Sequence[Voxels])")
            return Voxels.voxCombineAll(vox1)
        if isinstance(vox1, Sequence):
            raise TypeError("voxUnion binary form expects two Voxels arguments")
        return vox1.voxBoolAdd(vox2)

    @staticmethod
    def voxSubtract(vox1: Voxels, vox2: Voxels) -> Voxels:
        return vox1.voxBoolSubtract(vox2)

    @staticmethod
    def voxIntersect(vox1: Voxels, vox2: Voxels) -> Voxels:
        return vox1.voxBoolIntersect(vox2)

    @staticmethod
    def voxIntersectImplicit(vox: Voxels, sdfObject: IImplicit) -> Voxels:
        return vox.voxIntersectImplicit(sdfObject)

    @staticmethod
    def vecGetClosestSurfacePoint(vox: Voxels, vecPt: Vector3Like) -> tuple[float, float, float]:
        return vox.vecClosestPointOnSurface(vecPt)

    @staticmethod
    def vecGetProjectedSurfacePoint(vox: Voxels, vecPt: Vector3Like, vecDir: Vector3Like) -> tuple[float, float, float]:
        return vox.vecRayCastToSurface(vecPt, vecDir)

    @staticmethod
    def oGetBoundingBox(vox: Voxels) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        return vox.oCalculateBoundingBox()

    @staticmethod
    def latFromLine(aPoints: Sequence[Vector3Like], fBeam: float) -> Lattice:
        oLattice = Lattice()
        for i in range(1, len(aPoints)):
            oLattice.AddBeam(aPoints[i - 1], aPoints[i], fBeam, fBeam, True)
        return oLattice

    @staticmethod
    def AddLine(oLattice: Lattice, aPoints: Sequence[Vector3Like], fBeam: float) -> None:
        for i in range(1, len(aPoints)):
            oLattice.AddBeam(aPoints[i - 1], aPoints[i], fBeam, fBeam, True)

    @staticmethod
    def latFromPoints(aPoints: Sequence[Vector3Like], fBeam: float) -> Lattice:
        oLattice = Lattice()
        for p in aPoints:
            oLattice.AddSphere(p, fBeam)
        return oLattice

    @staticmethod
    def latFromEdges(aEdges: Sequence[Sequence[Vector3Like]], fBeam: float) -> Lattice:
        oLattice = Lattice()
        for edge in aEdges:
            for i in range(1, len(edge)):
                oLattice.AddBeam(edge[i - 1], edge[i], fBeam, fBeam, True)
        return oLattice

    @staticmethod
    def latFromPoint(vecPt: Vector3Like, fBeam: float) -> Lattice:
        oLattice = Lattice()
        oLattice.AddSphere(vecPt, fBeam)
        return oLattice

    @staticmethod
    def latFromGrid(aGrid: Sequence[Sequence[Vector3Like]], fBeam: float) -> Lattice:
        oLattice = Lattice()
        for row in aGrid:
            Sh.AddLine(oLattice, row, fBeam)
        if aGrid:
            rows = len(aGrid)
            cols = len(aGrid[0])
            for c in range(cols):
                for r in range(1, rows):
                    oLattice.AddBeam(aGrid[r - 1][c], aGrid[r][c], fBeam, fBeam, True)
        return oLattice

    @staticmethod
    def latFromBeam(vecPt1: Vector3Like, vecPt2: Vector3Like, fBeam1: float, fBeam2: float | None = None, bRounded: bool = True) -> Lattice:
        oLattice = Lattice()
        beam2 = fBeam1 if fBeam2 is None else fBeam2
        oLattice.AddBeam(vecPt1, vecPt2, fBeam1, beam2, bRounded)
        return oLattice

    @staticmethod
    def voxShell(vox: Voxels, fNegOffset: float, fPosOffset: float, fSmooth: float = 0.0) -> Voxels:
        return vox.voxShell(fNegOffset, fPosOffset, fSmooth)

    @staticmethod
    def ExportMeshToSTLFile(oMesh: Mesh, strFilePath: str) -> None:
        try:
            oMesh.SaveToStlFile(strFilePath)
            Library.Log("STL Export: {0} exported.", strFilePath)
        except Exception as e:
            Library.Log("Could not save STL: {0}", str(e))

    @staticmethod
    def ExportVoxelsToSTLFile(oVoxels: Voxels, strFilePath: str) -> None:
        with Mesh.from_voxels(oVoxels) as mesh:
            Sh.ExportMeshToSTLFile(mesh, strFilePath)

    @staticmethod
    def ExportVoxelsToVDBFile(oVoxels: Voxels, strFilePath: str) -> None:
        try:
            oVoxels.SaveToVdbFile(strFilePath)
            Library.Log("VDB Export: {0} exported.", strFilePath)
        except Exception as e:
            Library.Log("Could not save VDB: {0}", str(e))

    @staticmethod
    def ExportVoxelsToCLIFile(oVoxels: Voxels, strFilePath: str) -> None:
        try:
            oVoxels.SaveToCliFile(strFilePath)
            Library.Log("CLI Export: {0} exported.", strFilePath)
        except Exception as e:
            Library.Log("Could not save CLI: {0}", str(e))

    class EExport(Enum):
        STL = "STL"
        TGA = "TGA"
        PNG = "PNG"
        CSV = "CSV"
        VDB = "VDB"
        CLI = "CLI"

    @staticmethod
    def strGetExportPath(eExport: "Sh.EExport", strFilename: str) -> str:
        ext = f".{eExport.value}"
        return str(Path.cwd() / f"{strFilename}{ext}")

    @staticmethod
    def PreviewMesh(
        oMesh: Mesh,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        viewer = Sh._resolve_viewer(oViewer)
        group_id = Sh._next_group_id()
        viewer.SetGroupMaterial(group_id, Sh._color_rgba(clrColor, fTransparency), fMetallic, fRoughness)
        viewer.Add(oMesh, group_id)
        return group_id

    @staticmethod
    def PreviewVoxels(
        oVoxels: Voxels,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        viewer = Sh._resolve_viewer(oViewer)
        group_id = Sh._next_group_id()
        viewer.SetGroupMaterial(group_id, Sh._color_rgba(clrColor, fTransparency), fMetallic, fRoughness)
        viewer.Add(oVoxels, group_id)
        return group_id

    @staticmethod
    def PreviewLattice(
        oLattice: Lattice,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        with Voxels.from_lattice(oLattice) as oVoxels:
            return Sh.PreviewVoxels(oVoxels, clrColor, fTransparency, fMetallic, fRoughness, oViewer=oViewer)

    @staticmethod
    def PreviewPoint(
        vecPt: Vector3Like,
        fBeam: float,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        from ..base_shapes import BaseSphere

        oBall = BaseSphere(LocalFrame(vecPt), fBeam)
        return Sh.PreviewMesh(oBall.mshConstruct(), clrColor, fTransparency, fMetallic, fRoughness, oViewer=oViewer)

    @staticmethod
    def PreviewBeam(
        vecPt1: Vector3Like,
        fBeam1: float,
        vecPt2: Vector3Like,
        fBeam2: float,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        oLattice = Lattice()
        oLattice.AddBeam(vecPt1, vecPt2, fBeam1, fBeam2, True)
        return Sh.PreviewLattice(oLattice, clrColor, fTransparency, fMetallic, fRoughness, oViewer=oViewer)

    @staticmethod
    def PreviewLine(
        aPoints_or_pt1: Sequence[Vector3Like] | Vector3Like,
        clrColor_or_pt2: ColorLike | Vector3Like,
        clrColor: ColorLike | None = None,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        if clrColor is None:
            points = cast(Sequence[Vector3Like], aPoints_or_pt1)
            color = cast(ColorLike, clrColor_or_pt2)
        else:
            points = [cast(Vector3Like, aPoints_or_pt1), cast(Vector3Like, clrColor_or_pt2)]
            color = clrColor

        viewer = Sh._resolve_viewer(oViewer)
        group_id = Sh._next_group_id()
        with PolyLine(Sh._color_rgba(color)) as oLine:
            oLine.Add(points)
            viewer.Add(oLine, group_id)
        return group_id

    @staticmethod
    def PreviewGrid(aGrid: Sequence[Sequence[Vector3Like]], clrColor: ColorLike, *, oViewer: VedoViewer | None = None) -> list[int]:
        groups = [Sh.PreviewLine(row, clrColor, oViewer=oViewer) for row in aGrid]
        groups.extend(Sh.PreviewLine(row, clrColor, oViewer=oViewer) for row in GridOperations.aGetInverseGrid(aGrid))
        return groups

    @staticmethod
    def PreviewEdges(aEdges: Sequence[Sequence[Vector3Like]], clrColor: ColorLike, *, oViewer: VedoViewer | None = None) -> list[int]:
        return [Sh.PreviewLine(edge, clrColor, oViewer=oViewer) for edge in aEdges]

    @staticmethod
    def PreviewPointCloud(
        aPoints: Sequence[Vector3Like],
        fBeam: float,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> list[int]:
        return [
            Sh.PreviewPoint(point, fBeam, clrColor, fTransparency, fMetallic, fRoughness, oViewer=oViewer)
            for point in aPoints
        ]

    @staticmethod
    def PreviewFrame(oFrame: LocalFrame, fSize: float, *, oViewer: VedoViewer | None = None) -> list[int]:
        from ..visualizations import Cp

        viewer = Sh._resolve_viewer(oViewer)
        pos = as_np3(oFrame.vecGetPosition())
        axes = [
            (Cp.clrRed, as_np3(oFrame.vecGetLocalX())),
            (Cp.clrGreen, as_np3(oFrame.vecGetLocalY())),
            (Cp.clrBlue, as_np3(oFrame.vecGetLocalZ())),
        ]
        groups: list[int] = [Sh.PreviewPoint(oFrame.vecGetPosition(), 0.5, Cp.clrBlack, oViewer=viewer)]
        for clr, axis in axes:
            group_id = Sh._next_group_id()
            with PolyLine(Sh._color_rgba(clr)) as oLine:
                oLine.nAddVertex(as_vec3(pos))
                oLine.nAddVertex(as_vec3(pos + float(fSize) * axis))
                oLine.AddArrow(0.2 * float(fSize))
                viewer.Add(oLine, group_id)
            groups.append(group_id)
        return groups

    @staticmethod
    def PreviewFrames(aFrames: Frames, fSize: float, *, oViewer: VedoViewer | None = None) -> list[int]:
        from ..frames import Frames
        from ..utils import SplineOperations

        if not isinstance(aFrames, Frames):
            raise TypeError("PreviewFrames expects a Frames instance")
        fTotalLength = SplineOperations.fGetTotalLength(aFrames.aGetPoints(100))
        nSamples = max(2, int(2.0 * fTotalLength / max(float(fSize), 1e-9)))
        groups: list[int] = []
        for i in range(nSamples):
            fLR = float(i) / float(max(1, nSamples - 1))
            groups.extend(Sh.PreviewFrame(aFrames.oGetLocalFrame(fLR), fSize, oViewer=oViewer))
        return groups

    @staticmethod
    def PreviewCircleSection(
        oFrame: LocalFrame,
        fRadius: float,
        clrColor: ColorLike,
        fTransparency: float = 0.9,
        fMetallic: float = 0.4,
        fRoughness: float = 0.7,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        vecPt1 = as_np3(oFrame.vecGetPosition())
        vecPt2 = vecPt1 + as_np3(oFrame.vecGetLocalZ())
        oLattice = Lattice()
        oLattice.AddBeam(as_vec3(vecPt1), as_vec3(vecPt2), fRadius, fRadius, False)
        return Sh.PreviewLattice(oLattice, clrColor, fTransparency, fMetallic, fRoughness, oViewer=oViewer)

    @staticmethod
    def PreviewCircle(
        oFrame_or_centre: LocalFrame | Vector3Like,
        fRadius: float,
        clrColor: ColorLike,
        *,
        oViewer: VedoViewer | None = None,
    ) -> int:
        if isinstance(oFrame_or_centre, LocalFrame):
            oFrame = oFrame_or_centre
        else:
            oFrame = LocalFrame(oFrame_or_centre)
        aPoints = [
            VecOperations.vecTranslatePointOntoFrame(oFrame, VecOperations.vecGetCylPoint(fRadius, 2.0 * math.pi * i / 99.0, 0.0))
            for i in range(100)
        ]
        return Sh.PreviewLine(aPoints, clrColor, oViewer=oViewer)

    @staticmethod
    def PreviewCylinderWireframe(
        oCyl: BaseCylinder,
        clrColor: ColorLike,
        nRadialSamples: int = 4,
        nLengthSamples: int = 10,
        *,
        oViewer: VedoViewer | None = None,
    ) -> list[int]:
        from ..base_shapes import BaseCylinder

        if not isinstance(oCyl, BaseCylinder):
            raise TypeError("PreviewCylinderWireframe expects a BaseCylinder")
        groups: list[int] = []
        for nLengthSample in range(max(2, int(nLengthSamples))):
            fLengthRatio = float(nLengthSample) / float(max(1, nLengthSamples - 1))
            points = [oCyl.vecGetSurfacePoint(fLengthRatio, float(i) / 99.0, 1.0) for i in range(100)]
            groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        for nRadialSample in range(max(1, int(nRadialSamples))):
            fPhiRatio = float(nRadialSample) / float(max(1, nRadialSamples))
            points = [oCyl.vecGetSurfacePoint(float(i) / 999.0, fPhiRatio, 1.0) for i in range(1000)]
            groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        return groups

    @staticmethod
    def PreviewPipeWireframe(
        oPipe: BasePipe,
        clrColor: ColorLike,
        nRadialSamples: int = 4,
        nLengthSamples: int = 10,
        *,
        oViewer: VedoViewer | None = None,
    ) -> list[int]:
        from ..base_shapes import BasePipe

        if not isinstance(oPipe, BasePipe):
            raise TypeError("PreviewPipeWireframe expects a BasePipe")
        groups: list[int] = []
        for radius_ratio in (1.0, 0.0):
            for nLengthSample in range(max(2, int(nLengthSamples))):
                fLengthRatio = float(nLengthSample) / float(max(1, nLengthSamples - 1))
                points = [oPipe.vecGetSurfacePoint(fLengthRatio, float(i) / 99.0, radius_ratio) for i in range(100)]
                groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        for radius_ratio in (1.0, 0.0):
            for nRadialSample in range(max(2, int(nRadialSamples))):
                fPhiRatio = float(nRadialSample) / float(max(1, nRadialSamples - 1))
                points = [oPipe.vecGetSurfacePoint(float(i) / 99.0, fPhiRatio, radius_ratio) for i in range(100)]
                groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        return groups

    @staticmethod
    def PreviewBoxWireframe(
        oBox_or_bbox: BaseBox | BBox3 | tuple[Vector3Like, Vector3Like],
        clrColor: ColorLike,
        *,
        oViewer: VedoViewer | None = None,
    ) -> list[int]:
        from ..base_shapes import BaseBox

        if isinstance(oBox_or_bbox, BaseBox):
            oBox = oBox_or_bbox
        elif isinstance(oBox_or_bbox, BBox3):
            oBox = BaseBox.from_bbox(oBox_or_bbox)
        else:
            oBox = BaseBox.from_bbox(cast(tuple[Vector3Like, Vector3Like], oBox_or_bbox))

        lines = [
            [oBox.vecGetSurfacePoint(-1, -1, 0), oBox.vecGetSurfacePoint(-1, 1, 0), oBox.vecGetSurfacePoint(1, 1, 0), oBox.vecGetSurfacePoint(1, -1, 0), oBox.vecGetSurfacePoint(-1, -1, 0)],
            [oBox.vecGetSurfacePoint(-1, -1, 1), oBox.vecGetSurfacePoint(-1, 1, 1), oBox.vecGetSurfacePoint(1, 1, 1), oBox.vecGetSurfacePoint(1, -1, 1), oBox.vecGetSurfacePoint(-1, -1, 1)],
            [oBox.vecGetSurfacePoint(-1, -1, 0), oBox.vecGetSurfacePoint(-1, -1, 1)],
            [oBox.vecGetSurfacePoint(-1, 1, 0), oBox.vecGetSurfacePoint(-1, 1, 1)],
            [oBox.vecGetSurfacePoint(1, 1, 0), oBox.vecGetSurfacePoint(1, 1, 1)],
            [oBox.vecGetSurfacePoint(1, -1, 0), oBox.vecGetSurfacePoint(1, -1, 1)],
        ]
        return [Sh.PreviewLine(line, clrColor, oViewer=oViewer) for line in lines]

    @staticmethod
    def PreviewRingWireframe(
        oRing: BaseRing,
        clrColor: ColorLike,
        nRadialSamples: int = 4,
        nLengthSamples: int = 10,
        *,
        oViewer: VedoViewer | None = None,
    ) -> list[int]:
        from ..base_shapes import BaseRing

        if not isinstance(oRing, BaseRing):
            raise TypeError("PreviewRingWireframe expects a BaseRing")
        groups: list[int] = []
        for nLengthSample in range(max(2, int(nLengthSamples))):
            fLengthRatio = float(nLengthSample) / float(max(1, nLengthSamples - 1))
            points = [oRing.vecGetSurfacePoint(fLengthRatio, float(i) / 99.0, 1.0) for i in range(100)]
            groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        for nRadialSample in range(max(2, int(nRadialSamples))):
            fPhiRatio = float(nRadialSample) / float(max(1, nRadialSamples - 1))
            points = [oRing.vecGetSurfacePoint(float(i) / 499.0, fPhiRatio, 1.0) for i in range(500)]
            groups.append(Sh.PreviewLine(points, clrColor, oViewer=oViewer))
        return groups

    @staticmethod
    def Preview(*args: object, oViewer: VedoViewer | None = None, **kwargs: object) -> object:
        if not args:
            raise TypeError("Preview expects at least one positional argument")

        obj = args[0]
        if isinstance(obj, Mesh):
            transparency, metallic, roughness = Sh._parse_preview_style(args, 2)
            return Sh.PreviewMesh(obj, cast(ColorLike, args[1]), transparency, metallic, roughness, oViewer=oViewer, **kwargs)
        if isinstance(obj, Voxels):
            transparency, metallic, roughness = Sh._parse_preview_style(args, 2)
            return Sh.PreviewVoxels(obj, cast(ColorLike, args[1]), transparency, metallic, roughness, oViewer=oViewer, **kwargs)
        if isinstance(obj, Lattice):
            transparency, metallic, roughness = Sh._parse_preview_style(args, 2)
            return Sh.PreviewLattice(obj, cast(ColorLike, args[1]), transparency, metallic, roughness, oViewer=oViewer, **kwargs)
        if isinstance(obj, LocalFrame):
            if len(args) >= 2 and isinstance(args[1], (int, float)):
                return Sh.PreviewFrame(obj, float(args[1]), oViewer=oViewer)
            raise TypeError("Preview(LocalFrame, ...) expects Preview(frame, size)")
        if isinstance(obj, BBox3):
            return Sh.PreviewBoxWireframe(obj, cast(ColorLike, args[1]), oViewer=oViewer)

        from ..base_shapes import BaseBox, BaseCylinder, BasePipe, BaseRing
        from ..frames import Frames

        if isinstance(obj, Frames):
            return Sh.PreviewFrames(obj, float(cast(float, args[1])), oViewer=oViewer)
        if isinstance(obj, BaseCylinder):
            return Sh.PreviewCylinderWireframe(obj, cast(ColorLike, args[1]), oViewer=oViewer)
        if isinstance(obj, BasePipe):
            return Sh.PreviewPipeWireframe(obj, cast(ColorLike, args[1]), oViewer=oViewer)
        if isinstance(obj, BaseBox):
            return Sh.PreviewBoxWireframe(obj, cast(ColorLike, args[1]), oViewer=oViewer)
        if isinstance(obj, BaseRing):
            return Sh.PreviewRingWireframe(obj, cast(ColorLike, args[1]), oViewer=oViewer)
        if Sh._is_point_like(obj) and len(args) >= 3 and isinstance(args[1], (int, float)):
            transparency, metallic, roughness = Sh._parse_preview_style(args, 3)
            return Sh.PreviewPoint(cast(Vector3Like, obj), float(cast(float, args[1])), cast(ColorLike, args[2]), transparency, metallic, roughness, oViewer=oViewer, **kwargs)
        if Sh._is_point_sequence(obj) and len(args) >= 2:
            return Sh.PreviewLine(cast(Sequence[Vector3Like], obj), cast(ColorLike, args[1]), oViewer=oViewer)

        raise TypeError(f"Unsupported Preview target: {type(obj)!r}")



