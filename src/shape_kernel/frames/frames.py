from __future__ import annotations

import math
from collections.abc import Sequence
from enum import Enum

import numpy as np

from .._types import Vec3, Vector3Like, as_np3, as_vec3, clamp01, normalized
from ..splines import ISpline
from ..utils import SplineOperations
from ..utils import VecOperations
from .local_frames import LocalFrame


class Frames(ISpline):
    class EFrameType(Enum):
        CYLINDRICAL = "CYLINDRICAL"
        SPHERICAL = "SPHERICAL"
        Z = "Z"
        MIN_ROTATION = "MIN_ROTATION"

    def __init__(
        self,
        aPoints: list[np.ndarray],
        aLocalX: list[np.ndarray],
        aLocalY: list[np.ndarray],
        aLocalZ: list[np.ndarray],
    ) -> None:
        self.m_aPoints = aPoints
        self.m_aLocalX = aLocalX
        self.m_aLocalY = aLocalY
        self.m_aLocalZ = aLocalZ
        self.m_vecLastLocalX: np.ndarray | None = None

    @classmethod
    def from_length(
        cls,
        fLength: float,
        oConstLocalFrame: LocalFrame,
        fReparametrisationSpacing: float = 1.0,
    ) -> "Frames":
        start = as_np3(oConstLocalFrame.vecGetPosition())
        direction = as_np3(oConstLocalFrame.vecGetLocalZ())
        end = start + float(fLength) * direction

        points = [as_np3(p) for p in SplineOperations.aGetReparametrizedSpline([start, end], fReparametrisationSpacing)]
        local_z = [as_np3(oConstLocalFrame.vecGetLocalZ()) for _ in points]
        local_x = [as_np3(oConstLocalFrame.vecGetLocalX()) for _ in points]
        local_y = [as_np3(oConstLocalFrame.vecGetLocalY()) for _ in points]
        return cls(points, local_x, local_y, local_z)

    @classmethod
    def from_points_and_frame(
        cls,
        aPoints: Sequence[Vector3Like],
        oConstLocalFrame: LocalFrame,
        fReparametrisationSpacing: float = 1.0,
    ) -> "Frames":
        points = [as_np3(p) for p in SplineOperations.aGetReparametrizedSpline(aPoints, fReparametrisationSpacing)]
        local_z = [as_np3(oConstLocalFrame.vecGetLocalZ()) for _ in points]
        local_x = [as_np3(oConstLocalFrame.vecGetLocalX()) for _ in points]
        local_y = [as_np3(oConstLocalFrame.vecGetLocalY()) for _ in points]
        return cls(points, local_x, local_y, local_z)

    @classmethod
    def from_points_and_target_x(
        cls,
        aPoints: Sequence[Vector3Like],
        vecTargetX: Vector3Like,
        fReparametrisationSpacing: float = 1.0,
    ) -> "Frames":
        target_x = normalized(vecTargetX)
        points = [as_np3(p) for p in SplineOperations.aGetReparametrizedSpline(aPoints, fReparametrisationSpacing)]
        local_z = cls._tangent_directions(points)
        local_x = [cls.vecAlignWithTargetX(z, target_x) for z in local_z]
        local_y = [normalized(LocalFrame.vecBuildLocalY(z, x)) for z, x in zip(local_z, local_x)]

        n_samples = len(points)
        points = [as_np3(p) for p in SplineOperations.aGetNURBSpline(points, n_samples)]
        local_x = [as_np3(p) for p in SplineOperations.aGetNURBSpline(local_x, n_samples)]
        local_y = [as_np3(p) for p in SplineOperations.aGetNURBSpline(local_y, n_samples)]
        local_z = [as_np3(p) for p in SplineOperations.aGetNURBSpline(local_z, n_samples)]
        return cls(points, local_x, local_y, local_z)

    @classmethod
    def from_points_and_frame_type(
        cls,
        aPoints: Sequence[Vector3Like],
        eFrameType: "Frames.EFrameType",
        fReparametrisationSpacing: float = 1.0,
    ) -> "Frames":
        points = [as_np3(p) for p in SplineOperations.aGetReparametrizedSpline(aPoints, fReparametrisationSpacing)]
        local_z = cls._tangent_directions(points)

        local_x: list[np.ndarray] = []
        last_local_x: np.ndarray | None = None
        for point, z_vec in zip(points, local_z):
            x_vec, last_local_x = cls._align_with_frame_type(point, z_vec, eFrameType, last_local_x)
            local_x.append(x_vec)

        local_y = [normalized(LocalFrame.vecBuildLocalY(z, x)) for z, x in zip(local_z, local_x)]
        out = cls(points, local_x, local_y, local_z)
        out.m_vecLastLocalX = last_local_x
        return out

    @staticmethod
    def _align_with_frame_type(
        vecPt: np.ndarray,
        vecLocalZ: np.ndarray,
        eFrameType: "Frames.EFrameType",
        last_local_x: np.ndarray | None,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        if eFrameType == Frames.EFrameType.MIN_ROTATION:
            if last_local_x is None:
                target_x = Frames.vecGetTargetX(vecPt, Frames.EFrameType.Z)
                last_local_x = Frames.vecAlignWithTargetX(vecLocalZ, target_x)
            local_x = Frames.vecAlignWithTargetX(vecLocalZ, last_local_x)
            return local_x, local_x

        target_x = Frames.vecGetTargetX(vecPt, eFrameType)
        local_x = Frames.vecAlignWithTargetX(vecLocalZ, target_x)
        return local_x, last_local_x

    @staticmethod
    def vecAlignWithTargetX(vecLocalZ: Vector3Like, vecTargetX: Vector3Like) -> np.ndarray:
        local_z = normalized(vecLocalZ)
        target_x = normalized(vecTargetX)
        init_x = VecOperations.vecGetOrthogonalDir(local_z)
        init_y = np.cross(init_x, local_z)

        max_dot = abs(float(np.dot(init_x, target_x)))
        final_x = init_x
        for angle in np.arange(0.0, 180.0, 0.01):
            phi = (2.0 * math.pi / 360.0) * float(angle)
            candidate = math.cos(phi) * init_x + math.sin(phi) * init_y
            dot_val = abs(float(np.dot(candidate, target_x)))
            if dot_val > max_dot:
                max_dot = dot_val
                final_x = candidate

        return normalized(VecOperations.vecFlipForAlignment(final_x, target_x))

    @staticmethod
    def vecGetTargetX(vecPt: Vector3Like, eFrameType: "Frames.EFrameType") -> np.ndarray:
        point = as_np3(vecPt)
        if eFrameType == Frames.EFrameType.CYLINDRICAL:
            return normalized((point[0], point[1], 0.0))
        if eFrameType == Frames.EFrameType.SPHERICAL:
            return normalized(point)
        return np.array([0.0, 0.0, 1.0], dtype=np.float64)

    @staticmethod
    def _tangent_directions(points: list[np.ndarray]) -> list[np.ndarray]:
        tangents: list[np.ndarray] = []
        for idx in range(1, len(points) - 1):
            tangents.append(normalized(points[idx] - points[idx - 1]))
        if not tangents:
            tangents = [np.array([0.0, 0.0, 1.0], dtype=np.float64)]
        tangents.insert(0, tangents[0])
        tangents.append(tangents[-1])
        return tangents

    def _interp(self, values: list[np.ndarray], fLengthRatio: float) -> np.ndarray:
        lr = clamp01(fLengthRatio)
        f_step = lr * max(0, len(values) - 1)
        i_lower = int(min(f_step, len(values) - 1))
        i_upper = int(min(f_step + 1.0, len(values) - 1))
        ds = f_step - i_lower
        return values[i_lower] + ds * (values[i_upper] - values[i_lower])

    def vecGetSpineAlongLength(self, fLengthRatio: float) -> Vec3:
        return as_vec3(self._interp(self.m_aPoints, fLengthRatio))

    def vec_get_spine_along_length(self, fLengthRatio: float) -> Vec3:
        return self.vecGetSpineAlongLength(fLengthRatio)

    def vecGetLocalXAlongLength(self, fLengthRatio: float) -> Vec3:
        return as_vec3(self._interp(self.m_aLocalX, fLengthRatio))

    def vec_get_local_x_along_length(self, fLengthRatio: float) -> Vec3:
        return self.vecGetLocalXAlongLength(fLengthRatio)

    def vecGetLocalYAlongLength(self, fLengthRatio: float) -> Vec3:
        return as_vec3(self._interp(self.m_aLocalY, fLengthRatio))

    def vec_get_local_y_along_length(self, fLengthRatio: float) -> Vec3:
        return self.vecGetLocalYAlongLength(fLengthRatio)

    def vecGetLocalZAlongLength(self, fLengthRatio: float) -> Vec3:
        return as_vec3(self._interp(self.m_aLocalZ, fLengthRatio))

    def vec_get_local_z_along_length(self, fLengthRatio: float) -> Vec3:
        return self.vecGetLocalZAlongLength(fLengthRatio)

    def oGetLocalFrame(self, fLengthRatio: float) -> LocalFrame:
        return LocalFrame(
            self.vecGetSpineAlongLength(fLengthRatio),
            self.vecGetLocalZAlongLength(fLengthRatio),
            self.vecGetLocalXAlongLength(fLengthRatio),
        )

    def aGetPoints(self, nSamples: int | None = 500) -> list[Vec3]:
        if nSamples is None:
            return [as_vec3(p) for p in self.m_aPoints]
        if nSamples <= 0:
            return []
        if nSamples == len(self.m_aPoints):
            return [as_vec3(p) for p in self.m_aPoints]
        return SplineOperations.aGetReparametrizedSpline(self.m_aPoints, int(nSamples))
