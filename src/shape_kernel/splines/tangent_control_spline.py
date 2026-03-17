from __future__ import annotations

import numpy as np
from .control_point_spline import ControlPointSpline
from .i_spline import ISpline

from .._types import Vec3, Vector3Like, as_np3, as_vec3, normalized
from ..frames.local_frames import LocalFrame


class TangentialControlSpline(ISpline):
    def __init__(self, oBSpline: ControlPointSpline) -> None:
        self.m_oBSpline = oBSpline

    @classmethod
    def from_vectors(
        cls,
        vecStart: Vector3Like,
        vecEnd: Vector3Like,
        vecStartDir: Vector3Like,
        vecEndDir: Vector3Like,
        fStartTangentStrength: float = -1.0,
        fEndTangentStrenth: float = -1.0,
        bRelativeStartStrength: bool = False,
        bRelativeEndStrength: bool = False,
    ) -> "TangentialControlSpline":
        start = as_np3(vecStart)
        end = as_np3(vecEnd)
        start_dir = normalized(vecStartDir)
        end_dir = normalized(vecEndDir)
        distance = float(np.linalg.norm(start - end))

        start_strength = fStartTangentStrength
        end_strength = fEndTangentStrenth

        if start_strength == -1.0:
            start_strength = 0.3 * distance
        if end_strength == -1.0:
            end_strength = 0.3 * distance
        if bRelativeStartStrength:
            start_strength *= distance
        if bRelativeEndStrength:
            end_strength *= distance

        control_points = [
            as_vec3(start),
            as_vec3(start + start_strength * start_dir),
            as_vec3(end - end_strength * end_dir),
            as_vec3(end),
        ]
        return cls(ControlPointSpline(control_points))

    @classmethod
    def from_frames(
        cls,
        oStartFrame: LocalFrame,
        oEndFrame: LocalFrame,
        fStartTangentStrength: float = -1.0,
        fEndTangentStrenth: float = -1.0,
        bRelativeStartStrength: bool = False,
        bRelativeEndStrength: bool = False,
    ) -> "TangentialControlSpline":
        return cls.from_vectors(
            oStartFrame.vecGetPosition(),
            oEndFrame.vecGetPosition(),
            oStartFrame.vecGetLocalZ(),
            oEndFrame.vecGetLocalZ(),
            fStartTangentStrength,
            fEndTangentStrenth,
            bRelativeStartStrength,
            bRelativeEndStrength,
        )

    def aGetPoints(self, nSamples: int | None = 500) -> list[Vec3]:
        if nSamples is None:
            nSamples = 500
        return self.m_oBSpline.aGetPoints(nSamples)

