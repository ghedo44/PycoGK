from __future__ import annotations


import ctypes
import math
from typing import Sequence


from _common.types import Vector3Like

from .._base import HandleOwner
from .._errors import PicoGKInvalidHandleError
from .._types import ColorFloat, Vec3, as_vec3, vec3_tuple

from .library import Library

class PolyLine(HandleOwner):
    def __init__(self, color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)) -> None:
        clr = ColorFloat(*[float(c) for c in color])
        h = Library._lib().PolyLine_hCreate(ctypes.byref(clr))
        if not h:
            raise PicoGKInvalidHandleError("PolyLine_hCreate returned null")
        super().__init__(h)
        self._bbox_min = [float("inf"), float("inf"), float("inf")]
        self._bbox_max = [float("-inf"), float("-inf"), float("-inf")]

    def _destroy_native(self) -> None:
        Library._lib().PolyLine_Destroy(self._handle)

    def add_vertex(self, xyz: Vector3Like) -> int:
        self._ensure_open()
        v = as_vec3(xyz)
        self._bbox_min[0] = min(self._bbox_min[0], float(v.x))
        self._bbox_min[1] = min(self._bbox_min[1], float(v.y))
        self._bbox_min[2] = min(self._bbox_min[2], float(v.z))
        self._bbox_max[0] = max(self._bbox_max[0], float(v.x))
        self._bbox_max[1] = max(self._bbox_max[1], float(v.y))
        self._bbox_max[2] = max(self._bbox_max[2], float(v.z))
        return int(Library._lib().PolyLine_nAddVertex(self.handle, ctypes.byref(v)))

    nAddVertex = add_vertex

    def Add(self, vertices: Sequence[Vector3Like]) -> "PolyLine":
        for vertex in vertices:
            self.add_vertex(vertex)
        return self

    def vertex_count(self) -> int:
        self._ensure_open()
        return int(Library._lib().PolyLine_nVertexCount(self.handle))

    nVertexCount = vertex_count

    def get_vertex(self, index: int) -> tuple[float, float, float]:
        self._ensure_open()
        v = Vec3()
        Library._lib().PolyLine_GetVertex(self.handle, int(index), ctypes.byref(v))
        return vec3_tuple(v)

    vecVertexAt = get_vertex

    def get_color(self) -> tuple[float, float, float, float]:
        clr = ColorFloat()
        Library._lib().PolyLine_GetColor(self.handle, ctypes.byref(clr))
        return (float(clr.r), float(clr.g), float(clr.b), float(clr.a))

    GetColor = get_color

    def bounding_box(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        if self.vertex_count() == 0:
            return ((float("inf"), float("inf"), float("inf")), (float("-inf"), float("-inf"), float("-inf")))
        return (
            (self._bbox_min[0], self._bbox_min[1], self._bbox_min[2]),
            (self._bbox_max[0], self._bbox_max[1], self._bbox_max[2]),
        )

    oBoundingBox = bounding_box

    def AddArrow(self, size_mm: float = 1.0, direction: Vector3Like | None = None) -> "PolyLine":
        if self.vertex_count() < 1:
            return self
        if direction is None:
            if self.vertex_count() < 2:
                return self
            start = self.get_vertex(self.vertex_count() - 2)
            end = self.get_vertex(self.vertex_count() - 1)
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            dz = end[2] - start[2]
        else:
            dx, dy, dz = direction
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length <= 1e-12:
            return self
        dx /= length
        dy /= length
        dz /= length
        init = (1.0, 0.0, 0.0) if abs(dx) < 0.999 else (0.0, 1.0, 0.0)
        ux = dy * init[2] - dz * init[1]
        uy = dz * init[0] - dx * init[2]
        uz = dx * init[1] - dy * init[0]
        ul = math.sqrt(ux * ux + uy * uy + uz * uz)
        ux, uy, uz = ux / ul, uy / ul, uz / ul
        vx = dy * uz - dz * uy
        vy = dz * ux - dx * uz
        vz = dx * uy - dy * ux
        tip = self.get_vertex(self.vertex_count() - 1)
        base = (tip[0] - dx * size_mm, tip[1] - dy * size_mm, tip[2] - dz * size_mm)
        self.add_vertex((base[0] + ux * size_mm / 2, base[1] + uy * size_mm / 2, base[2] + uz * size_mm / 2))
        self.add_vertex((base[0] - ux * size_mm / 2, base[1] - uy * size_mm / 2, base[2] - uz * size_mm / 2))
        self.add_vertex(tip)
        self.add_vertex((base[0] + vx * size_mm / 2, base[1] + vy * size_mm / 2, base[2] + vz * size_mm / 2))
        self.add_vertex((base[0] - vx * size_mm / 2, base[1] - vy * size_mm / 2, base[2] - vz * size_mm / 2))
        self.add_vertex(tip)
        return self

    def AddCross(self, size_mm: float = 1.0) -> "PolyLine":
        if self.vertex_count() < 1:
            return self
        cx, cy, cz = self.get_vertex(self.vertex_count() - 1)
        self.add_vertex((cx + size_mm, cy, cz))
        self.add_vertex((cx - size_mm, cy, cz))
        self.add_vertex((cx, cy, cz))
        self.add_vertex((cx, cy + size_mm, cz))
        self.add_vertex((cx, cy - size_mm, cz))
        self.add_vertex((cx, cy, cz))
        self.add_vertex((cx, cy, cz + size_mm))
        self.add_vertex((cx, cy, cz - size_mm))
        self.add_vertex((cx, cy, cz))
        return self



