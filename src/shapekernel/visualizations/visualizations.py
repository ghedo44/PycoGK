from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

import numpy as np

from picogk import Library, Mesh, VedoViewer

from .._types import Vec3, as_np3
from ..utils import SplineOperations



class IColorScale(ABC):
    @abstractmethod
    def clrGetColor(self, fValue: float) -> tuple[float, float, float, float]:
        raise NotImplementedError

    @abstractmethod
    def fGetMinValue(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def fGetMaxValue(self) -> float:
        raise NotImplementedError


class LinearColorScale2D(IColorScale):
    def __init__(
        self,
        clrMin: Sequence[float],
        clrMax: Sequence[float],
        fMinValue: float,
        fMaxValue: float,
    ) -> None:
        self.m_fMinValue = float(fMinValue)
        self.m_fMaxValue = float(fMaxValue)
        self.m_clrMin = tuple(float(v) for v in clrMin[:3])
        self.m_clrMax = tuple(float(v) for v in clrMax[:3])

    def fGetMinValue(self) -> float:
        return self.m_fMinValue

    def fGetMaxValue(self) -> float:
        return self.m_fMaxValue

    def fGetInterpolated(self, fValue1: float, fValue2: float, fValue: float) -> float:
        ratio = (fValue - self.m_fMinValue) / (self.m_fMaxValue - self.m_fMinValue)
        return fValue1 + ratio * (fValue2 - fValue1)

    def clrGetColor(self, fValue: float) -> tuple[float, float, float, float]:
        value = min(max(float(fValue), self.m_fMinValue), self.m_fMaxValue)
        r = self.fGetInterpolated(self.m_clrMin[0], self.m_clrMax[0], value)
        g = self.fGetInterpolated(self.m_clrMin[1], self.m_clrMax[1], value)
        b = self.fGetInterpolated(self.m_clrMin[2], self.m_clrMax[2], value)
        return (float(r), float(g), float(b), 1.0)


class SmoothColorScale2D(LinearColorScale2D):
    def fGetInterpolated(self, fValue1: float, fValue2: float, fValue: float) -> float:
        ratio = (fValue - self.m_fMinValue) / (self.m_fMaxValue - self.m_fMinValue)
        ratio = ratio * ratio * (3.0 - 2.0 * ratio)
        return fValue1 + ratio * (fValue2 - fValue1)


class CustomColorScale2D(LinearColorScale2D):
    def __init__(
        self,
        clrMin: Sequence[float],
        clrMax: Sequence[float],
        fMinValue: float,
        fMaxValue: float,
        fTransition: float,
        fSmoothness: float,
    ) -> None:
        super().__init__(clrMin, clrMax, fMinValue, fMaxValue)
        self.m_fTransition = float(fTransition)
        self.m_fSmoothness = float(fSmoothness)

    def fGetInterpolated(self, fValue1: float, fValue2: float, fValue: float) -> float:
        x = float(fValue)
        s = max(1e-9, self.m_fSmoothness)
        t = self.m_fTransition
        ratio = 1.0 / (1.0 + math.exp(-(x - t) / s))
        return fValue1 + ratio * (fValue2 - fValue1)


class ISpectrum(ABC):
    @abstractmethod
    def aGetRawRGBList(self) -> list[Vec3]:
        raise NotImplementedError


class RainboxSpectrum(ISpectrum):
    def aGetRawRGBList(self) -> list[Vec3]:
        return [
            (0.0, 0.0, 255.0),
            (0.0, 255.0, 0.0),
            (255.0, 255.0, 0.0),
            (255.0, 130.0, 0.0),
            (255.0, 0.0, 0.0),
        ]


class ColorScale3D(IColorScale):
    def __init__(self, xSpectrum: ISpectrum, fMinValue: float, fMaxValue: float) -> None:
        self.m_fMinValue = float(fMinValue)
        self.m_fMaxValue = float(fMaxValue)
        smooth = SplineOperations.aGetNURBSpline(xSpectrum.aGetRawRGBList(), 500)
        self.m_aSmoothRGBList = [as_np3(p) for p in SplineOperations.aGetReparametrizedSpline(smooth, 500)]

    def fGetMinValue(self) -> float:
        return self.m_fMinValue

    def fGetMaxValue(self) -> float:
        return self.m_fMaxValue

    def clrGetColor(self, fValue: float) -> tuple[float, float, float, float]:
        value = min(max(float(fValue), self.m_fMinValue), self.m_fMaxValue)
        ratio = (value - self.m_fMinValue) / (self.m_fMaxValue - self.m_fMinValue)
        idx = int(ratio * (len(self.m_aSmoothRGBList) - 1))
        rgb = self.m_aSmoothRGBList[idx]
        return (float(rgb[0] / 255.0), float(rgb[1] / 255.0), float(rgb[2] / 255.0), 1.0)



class MeshPainter:
    ColorScaleFunc = Callable[[Vec3, Vec3, Vec3], float]

    @staticmethod
    def _build_submesh_classes(oMesh: Mesh, nClasses: int) -> list[Mesh]:
        return [Mesh() for _ in range(int(nClasses))]

    @staticmethod
    def _emit_preview_groups(
        segments: list[tuple[Mesh, tuple[float, float, float, float]]],
        oViewer: VedoViewer | None = None,
    ) -> None:
        viewer = oViewer if oViewer is not None else Library.oViewer()
        if viewer is None:
            return
        from ..functions import Sh

        for msh, clr in segments:
            if msh.nTriangleCount() <= 0:
                continue
            Sh.PreviewMesh(msh, clr, oViewer=viewer) 

    @staticmethod
    def PreviewOverhangAngle(
        oMesh: Mesh,
        xScale: IColorScale,
        bShowOnlyDownFacing: bool,
        nClasses: int = 30,
        oViewer: VedoViewer | None = None,
    ) -> list[tuple[Mesh, tuple[float, float, float, float]]]:
        sub_meshes = MeshPainter._build_submesh_classes(oMesh, nClasses)
        fMinAngle = xScale.fGetMinValue()
        fMaxAngle = xScale.fGetMaxValue()
        dAngle = (fMaxAngle - fMinAngle) / (nClasses - 1.0)

        n_triangles = oMesh.nTriangleCount()
        for i in range(n_triangles):
            vecA, vecB, vecC = oMesh.GetTriangle(i)
            a = as_np3(vecA)
            b = as_np3(vecB)
            c = as_np3(vecC)
            normal = np.cross(a - b, c - b)
            n_norm = float(np.linalg.norm(normal))
            if n_norm <= 1e-12:
                continue
            normal = normal / n_norm

            dR = math.sqrt(float(normal[0] * normal[0] + normal[1] * normal[1]))
            dZ = abs(float(normal[2]))
            overhang = math.atan2(dZ, dR) / math.pi * 180.0
            overhang = min(max(overhang, 0.0), 90.0)

            if bShowOnlyDownFacing and normal[2] < 0.0:
                overhang = 0.0

            ratio = (overhang - fMinAngle) / (fMaxAngle - fMinAngle)
            index = int(min(max(ratio, 0.0), 1.0) * (nClasses - 1))
            sub_meshes[index].nAddTriangle(vecA, vecB, vecC)

        segments = [(sub_meshes[i], xScale.clrGetColor(fMinAngle + i * dAngle)) for i in range(nClasses)]
        MeshPainter._emit_preview_groups(segments, oViewer)
        return segments

    @staticmethod
    def PreviewCustomProperty(
        oMesh: Mesh,
        xScale: IColorScale,
        oColorFunc: ColorScaleFunc,
        nClasses: int = 30,
        oViewer: VedoViewer | None = None,
    ) -> list[tuple[Mesh, tuple[float, float, float, float]]]:
        sub_meshes = MeshPainter._build_submesh_classes(oMesh, nClasses)
        fMinValue = xScale.fGetMinValue()
        fMaxValue = xScale.fGetMaxValue()
        dValue = (fMaxValue - fMinValue) / (nClasses - 1.0)

        n_triangles = oMesh.nTriangleCount()
        for i in range(n_triangles):
            vecA, vecB, vecC = oMesh.GetTriangle(i)
            value = float(oColorFunc(vecA, vecB, vecC))
            ratio = min(max((value - fMinValue) / (fMaxValue - fMinValue), 0.0), 1.0)
            index = int(ratio * (nClasses - 1))
            sub_meshes[index].nAddTriangle(vecA, vecB, vecC)

        segments = [(sub_meshes[i], xScale.clrGetColor(fMinValue + i * dValue)) for i in range(nClasses)]
        MeshPainter._emit_preview_groups(segments, oViewer)
        return segments

    @staticmethod
    def PreviewCustomDeformation(
        oMesh: Mesh,
        xScale: IColorScale,
        oColorFunc: ColorScaleFunc,
        fnTrafo: Callable[[Vec3], Vec3],
        nClasses: int = 30,
        oViewer: VedoViewer | None = None,
    ) -> list[tuple[Mesh, tuple[float, float, float, float]]]:
        sub_meshes = MeshPainter._build_submesh_classes(oMesh, nClasses)
        fMinValue = xScale.fGetMinValue()
        fMaxValue = xScale.fGetMaxValue()
        dValue = (fMaxValue - fMinValue) / (nClasses - 1.0)

        n_triangles = oMesh.nTriangleCount()
        for i in range(n_triangles):
            vecA, vecB, vecC = oMesh.GetTriangle(i)
            value = float(oColorFunc(vecA, vecB, vecC))
            ratio = min(max((value - fMinValue) / (fMaxValue - fMinValue), 0.0), 1.0)
            index = int(ratio * (nClasses - 1))
            sub_meshes[index].nAddTriangle(fnTrafo(vecA), fnTrafo(vecB), fnTrafo(vecC))

        segments = [(sub_meshes[i], xScale.clrGetColor(fMinValue + i * dValue)) for i in range(nClasses)]
        MeshPainter._emit_preview_groups(segments, oViewer)
        return segments


class RotationAnimator:
    def __init__(self, oViewer: VedoViewer) -> None:
        self.m_oViewer = oViewer

    def Do(self, fStep: float = 0.5) -> None:
        fElevation = float(self.m_oViewer.m_fElevation)
        fCurrentOrbit = float(self.m_oViewer.m_fOrbit)
        self.m_oViewer.SetViewAngles(fCurrentOrbit + float(fStep), fElevation)

    def Run(self, nSteps: int = 360, fWaitSeconds: float = 0.01, fStep: float = 0.5) -> None:
        for _ in range(int(nSteps)):
            time.sleep(float(fWaitSeconds))
            self.Do(fStep)
