from __future__ import annotations

import numpy as np
from .control_point_spline import ControlPointSpline

from .._types import Vec3, Vector3Like, as_np3, as_vec3
from .i_spline import ISpline


class CylindricalControlSpline(ISpline):
    class EDirection:
        RADIAL = "RADIAL"
        TANGENTIAL = "TANGENTIAL"
        Z = "Z"

    def __init__(self, vecStart: Vector3Like) -> None:
        self.m_aControlPoints: list[np.ndarray] = [as_np3(vecStart)]

    def AddRelativeStep(self, eDir: str, fStepLength: float) -> None:
        last_pos = self.m_aControlPoints[-1]
        if eDir == self.EDirection.Z:
            new_pos = last_pos + float(fStepLength) * np.array([0.0, 0.0, 1.0], dtype=np.float64)
            self.m_aControlPoints.append(new_pos)
            return
        radial_dir = np.array([last_pos[0], last_pos[1], 0.0], dtype=np.float64)
        radial_norm = float(np.linalg.norm(radial_dir))
        if radial_norm <= 1e-12:
            radial_dir = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        else:
            radial_dir = radial_dir / radial_norm

        if eDir == self.EDirection.RADIAL:
            new_pos = last_pos + float(fStepLength) * radial_dir
        else:
            tangential = np.cross(np.array([0.0, 0.0, 1.0], dtype=np.float64), radial_dir)
            tangential_norm = float(np.linalg.norm(tangential))
            if tangential_norm <= 1e-12:
                tangential = np.array([0.0, 1.0, 0.0], dtype=np.float64)
            else:
                tangential = tangential / tangential_norm
            new_pos = last_pos + float(fStepLength) * tangential
        self.m_aControlPoints.append(new_pos)

    def AddAbsoluteStep(self, eDir: str, fNewValue: float) -> None:
        last_pos = self.m_aControlPoints[-1].copy()
        if eDir == self.EDirection.Z:
            last_pos[2] = float(fNewValue)
            self.m_aControlPoints.append(last_pos)
            return
        if eDir == self.EDirection.RADIAL:
            radial = np.array([last_pos[0], last_pos[1]], dtype=np.float64)
            norm = float(np.linalg.norm(radial))
            if norm <= 1e-12:
                last_pos[0] = float(fNewValue)
                last_pos[1] = 0.0
            else:
                scale = float(fNewValue) / norm
                last_pos[0] *= scale
                last_pos[1] *= scale
            self.m_aControlPoints.append(last_pos)

    def aGetPoints(self, nSamples: int | None = 500) -> list[Vec3]:
        if nSamples is None:
            nSamples = 500
        bspline = ControlPointSpline([as_vec3(p) for p in self.m_aControlPoints])
        return bspline.aGetPoints(nSamples)

