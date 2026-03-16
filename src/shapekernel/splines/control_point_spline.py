from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from .i_spline import ISpline

from .._types import Vec3, Vector3Like, as_np3, as_vec3, clamp01


class ControlPointSpline(ISpline):
    class EEnds:
        OPEN = "OPEN"
        CLOSED = "CLOSED"

    def __init__(self, aControlPoints: Sequence[Vector3Like], nDegree: int = 2, eEnds: str = EEnds.OPEN) -> None:
        self.m_aControlPoints = [as_np3(p) for p in aControlPoints]
        self.m_eEnds = eEnds
        self.m_fError = 1e-7

        if self.m_eEnds == self.EEnds.CLOSED and len(self.m_aControlPoints) > 1:
            if float(np.linalg.norm(self.m_aControlPoints[0] - self.m_aControlPoints[-1])) < self.m_fError:
                self.m_aControlPoints.pop()

        self.m_nDegree = int(nDegree)
        self.m_aKnot = self.aGetKnotVector()

    def aGetKnotVector(self) -> list[float]:
        n_control = len(self.m_aControlPoints)
        if self.m_eEnds == self.EEnds.CLOSED:
            for idx in range(n_control - 1):
                self.m_aControlPoints.append(self.m_aControlPoints[idx].copy())
            n_control = len(self.m_aControlPoints)

        n_knots = n_control + self.m_nDegree + 1
        n_valid_range = n_knots - self.m_nDegree - (self.m_nDegree + 1)
        d_r = 1.0 / float(n_valid_range)

        knots: list[float] = []
        for idx in range(n_knots):
            value = -(d_r * self.m_nDegree) + d_r * idx
            if self.m_eEnds == self.EEnds.OPEN:
                value = clamp01(value)
            knots.append(float(value))
        return knots

    def aGetPoints(self, nSamples: int = 500) -> list[Vec3]:
        points: list[Vec3] = []
        for idx in range(int(nSamples)):
            lr = float(idx) / float(max(1, nSamples - 1))
            points.append(self.vecGetPointAt(lr))
        return points

    def vecGetPointAt(self, fLengthRatio: float) -> Vec3:
        point = np.zeros(3, dtype=np.float64)
        for idx, control_point in enumerate(self.m_aControlPoints):
            point += self.fBaseFunc(fLengthRatio, idx, self.m_nDegree) * control_point
        return as_vec3(point)

    def fBaseFunc(self, fLengthRatio: float, nControlPoint: int, nDegree: int) -> float:
        if nDegree == 0:
            left = self.m_aKnot[nControlPoint]
            right = self.m_aKnot[nControlPoint + 1]
            if (left <= fLengthRatio < right) or (
                abs(fLengthRatio - right) < self.m_fError and abs(fLengthRatio - self.m_aKnot[-1]) < self.m_fError
            ):
                return 1.0
            return 0.0

        value = 0.0
        left_den = self.m_aKnot[nControlPoint + nDegree] - self.m_aKnot[nControlPoint]
        if abs(left_den) > self.m_fError:
            value += (
                (fLengthRatio - self.m_aKnot[nControlPoint])
                / left_den
                * self.fBaseFunc(fLengthRatio, nControlPoint, nDegree - 1)
            )

        right_den = self.m_aKnot[nControlPoint + nDegree + 1] - self.m_aKnot[nControlPoint + 1]
        if abs(right_den) > self.m_fError:
            value += (
                (self.m_aKnot[nControlPoint + nDegree + 1] - fLengthRatio)
                / right_den
                * self.fBaseFunc(fLengthRatio, nControlPoint + 1, nDegree - 1)
            )
        return float(value)

