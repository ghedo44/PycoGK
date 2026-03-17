from enum import IntEnum
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from _common.types import ColorLike, Vector2Like
from .._common import to_rgba
from .._viewer_protocol import IViewer
from .._core.image import Image
from .._core.polyline import PolyLine
from .bbox import BBox2


class PolyContour:
    class EWinding(IntEnum):
        UNKNOWN = 0
        CLOCKWISE = 1
        COUNTERCLOCKWISE = 2

    @staticmethod
    def strWindingAsString(eWinding: "PolyContour.EWinding") -> str:
        if eWinding == PolyContour.EWinding.COUNTERCLOCKWISE:
            return "[counter-clockwise]"
        if eWinding == PolyContour.EWinding.CLOCKWISE:
            return "[clockwise]"
        return "[unknown/degenerate]"

    def __init__(self, vertices: Iterable[Vector2Like], eWinding: "PolyContour.EWinding" = EWinding.UNKNOWN) -> None:
        self._vertices = [(float(v[0]), float(v[1])) for v in vertices]
        if len(self._vertices) < 3:
            raise ValueError("Polyline with less than 3 points makes no sense")
        self._bbox = BBox2()
        for v in self._vertices:
            self._bbox.Include(v)
        self._winding = self.eDetectWinding(self._vertices) if eWinding == self.EWinding.UNKNOWN else eWinding

    @staticmethod
    def eDetectWinding(vertices: Sequence[Vector2Like]) -> "PolyContour.EWinding":
        if len(vertices) < 3:
            return PolyContour.EWinding.UNKNOWN
        area = 0.0
        for i in range(len(vertices)):
            j = (i + 1) % len(vertices)
            area += (vertices[j][0] - vertices[i][0]) * (vertices[j][1] + vertices[i][1])
        if area > 0:
            return PolyContour.EWinding.CLOCKWISE
        if area < 0:
            return PolyContour.EWinding.COUNTERCLOCKWISE
        return PolyContour.EWinding.UNKNOWN

    def AddVertex(self, vec: Vector2Like) -> None:
        v = (float(vec[0]), float(vec[1]))
        self._vertices.append(v)
        self._bbox.Include(v)

    def DetectWinding(self) -> None:
        self._winding = self.eDetectWinding(self._vertices)

    def eWinding(self) -> "PolyContour.EWinding":
        return self._winding

    def oVertices(self) -> list[tuple[float, float]]:
        return list(self._vertices)

    def Close(self) -> None:
        if not self._vertices:
            return
        if self._vertices[0] != self._vertices[-1]:
            self._vertices.append(self._vertices[0])

    def AsSvgPolyline(self) -> str:
        pts = " ".join(f"{x},{y}" for x, y in self._vertices + [self._vertices[0]])
        stroke = "red"
        if self._winding == self.EWinding.CLOCKWISE:
            stroke = "blue"
        elif self._winding == self.EWinding.COUNTERCLOCKWISE:
            stroke = "black"
        return f"<polyline points='{pts}' stroke='{stroke}' fill='none' stroke-width='0.1' />\n"

    def AsSvgPath(self) -> str:
        parts: list[str] = []
        for i, (x, y) in enumerate(self._vertices):
            if i == 0:
                parts.append(f"M{x},{y}")
            else:
                parts.append(f"L{x},{y}")
        parts.append("Z")
        return " ".join(parts)

    def oBBox(self) -> BBox2:
        return self._bbox

    def nCount(self) -> int:
        return len(self._vertices)

    def vecVertex(self, n: int) -> tuple[float, float]:
        return self._vertices[n]


class PolySlice:
    def __init__(self, fZPos: float) -> None:
        self.m_fZPos = float(fZPos)
        self._contours: list[PolyContour] = []
        self._bbox = BBox2()

    def fZPos(self) -> float:
        return self.m_fZPos

    def AddContour(self, contour: PolyContour) -> None:
        self._contours.append(contour)
        self._bbox.Include(contour.oBBox())

    def nContours(self) -> int:
        return len(self._contours)

    def oContourAt(self, index: int) -> PolyContour:
        return self._contours[index]

    def oBBox(self) -> BBox2:
        return self._bbox

    def bIsEmpty(self) -> bool:
        return len(self._contours) == 0

    def Close(self) -> None:
        for c in self._contours:
            c.Close()

    def SaveToSvgFile(self, strPath: str | Path, bSolid: bool, oBBoxToUse: BBox2 | None = None) -> None:
        bbox = oBBoxToUse or self._bbox
        sx = bbox.vecMax[0] - bbox.vecMin[0]
        sy = bbox.vecMax[1] - bbox.vecMin[1]
        with open(strPath, "w", encoding="utf-8") as handle:
            handle.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
            handle.write("<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n")
            handle.write(
                f"<svg xmlns='http://www.w3.org/2000/svg' version='1.1' viewBox='{bbox.vecMin[0]} {bbox.vecMin[1]} {sx} {sy}' width='{sx}mm' height='{sy}mm'>\n"
            )
            handle.write("<g>\n")
            if not bSolid:
                for c in self._contours:
                    handle.write(c.AsSvgPolyline())
            else:
                path = " ".join(c.AsSvgPath() for c in self._contours)
                handle.write(f"<path d='{path}' fill='black'/>\n")
            handle.write("</g>\n</svg>\n")

    @staticmethod
    def _zero_crossing(a: float, b: float) -> float:
        den = a - b
        if abs(den) < 1e-8:
            return 0.5
        return float(np.clip(a / den, 0.0, 1.0))

    @staticmethod
    def oFromSdf(img: Image, fZPos: float, vecOffset: Vector2Like, fScale: float) -> "PolySlice":
        slice_obj = PolySlice(fZPos)
        if img.nWidth < 2 or img.nHeight < 2:
            return slice_obj
        ox, oy = float(vecOffset[0]), float(vecOffset[1])

        segs: list[tuple[tuple[float, float], tuple[float, float]]] = []
        edge_map = {
            1: ((3, 0),),
            2: ((0, 1),),
            3: ((3, 1),),
            4: ((1, 2),),
            5: ((3, 2), (0, 1)),
            6: ((0, 2),),
            7: ((3, 2),),
            8: ((2, 3),),
            9: ((0, 2),),
            10: ((0, 1), (2, 3)),
            11: ((1, 2),),
            12: ((1, 3),),
            13: ((0, 1),),
            14: ((0, 3),),
        }
        for y in range(img.nHeight - 1):
            for x in range(img.nWidth - 1):
                corners = [img.fValue(x, y), img.fValue(x + 1, y), img.fValue(x + 1, y + 1), img.fValue(x, y + 1)]
                idx = 0
                if corners[0] < 0.0:
                    idx |= 1
                if corners[1] < 0.0:
                    idx |= 2
                if corners[2] < 0.0:
                    idx |= 4
                if corners[3] < 0.0:
                    idx |= 8
                if idx == 0 or idx == 15:
                    continue
                cross: dict[int, tuple[float, float]] = {}
                if idx in edge_map:
                    if any(e in (0, 1, 2, 3) for pair in edge_map[idx] for e in pair):
                        cross[0] = (x + PolySlice._zero_crossing(corners[0], corners[1]), y)
                        cross[1] = (x + 1, y + PolySlice._zero_crossing(corners[1], corners[2]))
                        cross[2] = (x + PolySlice._zero_crossing(corners[3], corners[2]), y + 1)
                        cross[3] = (x, y + PolySlice._zero_crossing(corners[0], corners[3]))
                    for e0, e1 in edge_map[idx]:
                        p0 = cross[e0]
                        p1 = cross[e1]
                        segs.append(((ox + p0[0] * fScale, oy + p0[1] * fScale), (ox + p1[0] * fScale, oy + p1[1] * fScale)))

        remaining = segs[:]
        while remaining:
            a, b = remaining.pop()
            contour = [a, b]
            changed = True
            while changed and remaining:
                changed = False
                for i, (s0, s1) in enumerate(remaining):
                    if np.hypot(contour[-1][0] - s0[0], contour[-1][1] - s0[1]) < 1e-3:
                        contour.append(s1)
                        remaining.pop(i)
                        changed = True
                        break
                    if np.hypot(contour[-1][0] - s1[0], contour[-1][1] - s1[1]) < 1e-3:
                        contour.append(s0)
                        remaining.pop(i)
                        changed = True
                        break
            if len(contour) >= 3:
                try:
                    slice_obj.AddContour(PolyContour(contour))
                except ValueError:
                    pass
        return slice_obj


class PolySliceStack:
    def __init__(self, slices: Sequence[PolySlice] | None = None) -> None:
        self._slices = list(slices or [])
        self._bbox = BBox2()
        for sl in self._slices:
            self._bbox.Include(sl.oBBox())

    def AddSlice(self, poly_slice: PolySlice) -> None:
        self._slices.append(poly_slice)
        self._bbox.Include(poly_slice.oBBox())

    def AddSlices(self, slices: Sequence[PolySlice]) -> None:
        for sl in slices:
            self.AddSlice(sl)

    def nCount(self) -> int:
        return len(self._slices)

    def oSliceAt(self, index: int) -> PolySlice:
        return self._slices[index]

    def oBBox(self) -> BBox2:
        return self._bbox

    def oSlices(self) -> list[PolySlice]:
        return list(self._slices)

    def AddToViewer(
        self,
        oViewer: IViewer,
        clrOutside: ColorLike | None = None,
        clrInside: ColorLike | None = None,
        clrDegenerate: ColorLike | None = None,
        nGroup: int = 0,
    ) -> None:
        degenerate = to_rgba(clrDegenerate or (2.0 / 3.0, 2.0 / 3.0, 2.0 / 3.0, 2.0 / 3.0))
        inside = to_rgba(clrInside or (2.0 / 3.0, 2.0 / 3.0, 2.0 / 3.0, 2.0 / 3.0))
        outside = to_rgba(clrOutside or (1.0, 0.0, 0.0, 2.0 / 3.0))

        add_fn = getattr(oViewer, "Add", None)
        if not callable(add_fn):
            raise TypeError("oViewer must expose an Add method")

        for sl in self._slices:
            for idx in range(sl.nContours()):
                contour = sl.oContourAt(idx)

                color = degenerate
                if contour.eWinding() == PolyContour.EWinding.CLOCKWISE:
                    color = inside
                elif contour.eWinding() == PolyContour.EWinding.COUNTERCLOCKWISE:
                    color = outside

                poly = PolyLine(color)
                for vec in contour.oVertices():
                    poly.nAddVertex((vec[0], vec[1], sl.fZPos()))

                add_fn(poly, int(nGroup))

