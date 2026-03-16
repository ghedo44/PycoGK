
from dataclasses import dataclass
import math

from _common.types import Vector2Like, Vector3Like

from .._types import Vec3, _BBox3C, as_vec3, vec3_tuple


@dataclass
class BBox2:
    vecMin: tuple[float, float] = (float("inf"), float("inf"))
    vecMax: tuple[float, float] = (float("-inf"), float("-inf"))

    def __post_init__(self) -> None:
        self.vecMin = (float(self.vecMin[0]), float(self.vecMin[1]))
        self.vecMax = (float(self.vecMax[0]), float(self.vecMax[1]))
        if not self.bIsEmpty():
            if self.vecMin[0] > self.vecMax[0] or self.vecMin[1] > self.vecMax[1]:
                raise ValueError("BBox2 requires vecMin <= vecMax for non-empty boxes")

    def bIsEmpty(self) -> bool:
        return (
            math.isinf(self.vecMin[0])
            and self.vecMin[0] > 0.0
            and math.isinf(self.vecMin[1])
            and self.vecMin[1] > 0.0
            and math.isinf(self.vecMax[0])
            and self.vecMax[0] < 0.0
            and math.isinf(self.vecMax[1])
            and self.vecMax[1] < 0.0
        )

    def bContains(self, point: Vector2Like) -> bool:
        if self.bIsEmpty():
            return False
        x, y = float(point[0]), float(point[1])
        return (
            self.vecMin[0] <= x <= self.vecMax[0]
            and self.vecMin[1] <= y <= self.vecMax[1]
        )

    def Include(self, point: Vector2Like | "BBox2") -> None:
        if isinstance(point, BBox2):
            if point.bIsEmpty():
                return
            self.Include(point.vecMin)
            self.Include(point.vecMax)
            return
        x, y = float(point[0]), float(point[1])
        self.vecMin = (min(self.vecMin[0], x), min(self.vecMin[1], y))
        self.vecMax = (max(self.vecMax[0], x), max(self.vecMax[1], y))

    def Grow(self, fGrowBy: float) -> None:
        grow = float(fGrowBy)
        if self.bIsEmpty():
            self.vecMin = (-grow, -grow)
            self.vecMax = (grow, grow)
            return
        self.vecMin = (self.vecMin[0] - grow, self.vecMin[1] - grow)
        self.vecMax = (self.vecMax[0] + grow, self.vecMax[1] + grow)

    def vecSize(self) -> tuple[float, float]:
        return (self.vecMax[0] - self.vecMin[0], self.vecMax[1] - self.vecMin[1])

    def vecCenter(self) -> tuple[float, float]:
        size = self.vecSize()
        return (self.vecMin[0] + 0.5 * size[0], self.vecMin[1] + 0.5 * size[1])

    def __str__(self) -> str:
        return f"<Min: {self.vecMin} | Max: {self.vecMax}>"


class BBox3(_BBox3C):
    def __init__(
        self,
        min_xyz: Vector3Like | Vec3 | None = None,
        max_xyz: Vector3Like | Vec3 | None = None,
    ) -> None:
        if min_xyz is None and max_xyz is None:
            super().__init__(
                Vec3(float("inf"), float("inf"), float("inf")),
                Vec3(float("-inf"), float("-inf"), float("-inf")),
            )
            return

        if min_xyz is None or max_xyz is None:
            raise ValueError("BBox3 requires both min_xyz and max_xyz, or neither")

        vmin = as_vec3(min_xyz)
        vmax = as_vec3(max_xyz)
        if vmin.x > vmax.x or vmin.y > vmax.y or vmin.z > vmax.z:
            raise ValueError("BBox3 requires min_xyz <= max_xyz")
        super().__init__(vmin, vmax)

    @property
    def vecMin(self) -> Vec3:
        return self.min

    @vecMin.setter
    def vecMin(self, value: Vector3Like | Vec3) -> None:
        self.min = as_vec3(value)

    @property
    def vecMax(self) -> Vec3:
        return self.max

    @vecMax.setter
    def vecMax(self, value: Vector3Like | Vec3) -> None:
        self.max = as_vec3(value)

    def bIsEmpty(self) -> bool:
        return (
            math.isinf(self.min.x)
            and self.min.x > 0.0
            and math.isinf(self.min.y)
            and self.min.y > 0.0
            and math.isinf(self.min.z)
            and self.min.z > 0.0
            and math.isinf(self.max.x)
            and self.max.x < 0.0
            and math.isinf(self.max.y)
            and self.max.y < 0.0
            and math.isinf(self.max.z)
            and self.max.z < 0.0
        )

    def bContains(self, point: Vector3Like | Vec3) -> bool:
        if self.bIsEmpty():
            return False
        v = as_vec3(point)
        return (
            self.min.x <= v.x <= self.max.x
            and self.min.y <= v.y <= self.max.y
            and self.min.z <= v.z <= self.max.z
        )

    def Include(self, item: object, fZ: float = 0.0) -> None:
        if isinstance(item, BBox3):
            if item.bIsEmpty():
                return
            self.Include(item.min)
            self.Include(item.max)
            return

        if isinstance(item, BBox2):
            if item.bIsEmpty():
                return
            self.Include((item.vecMin[0], item.vecMin[1], float(fZ)))
            self.Include((item.vecMax[0], item.vecMax[1], float(fZ)))
            return

        v = as_vec3(item)  # type: ignore[arg-type]
        self.min = Vec3(min(self.min.x, v.x), min(self.min.y, v.y), min(self.min.z, v.z))
        self.max = Vec3(max(self.max.x, v.x), max(self.max.y, v.y), max(self.max.z, v.z))

    def Grow(self, fGrowBy: float) -> None:
        grow = float(fGrowBy)
        if self.bIsEmpty():
            self.min = Vec3(-grow, -grow, -grow)
            self.max = Vec3(grow, grow, grow)
            return
        self.min = Vec3(self.min.x - grow, self.min.y - grow, self.min.z - grow)
        self.max = Vec3(self.max.x + grow, self.max.y + grow, self.max.z + grow)

    def vecSize(self) -> tuple[float, float, float]:
        return (
            float(self.max.x - self.min.x),
            float(self.max.y - self.min.y),
            float(self.max.z - self.min.z),
        )

    def vecCenter(self) -> tuple[float, float, float]:
        sx, sy, sz = self.vecSize()
        return (
            float(self.min.x + 0.5 * sx),
            float(self.min.y + 0.5 * sy),
            float(self.min.z + 0.5 * sz),
        )

    def oAsBoundingBox2(self) -> BBox2:
        return BBox2(
            (float(self.min.x), float(self.min.y)),
            (float(self.max.x), float(self.max.y)),
        )

    def __str__(self) -> str:
        return f"<Min: {vec3_tuple(self.min)} | Max: {vec3_tuple(self.max)}>"

