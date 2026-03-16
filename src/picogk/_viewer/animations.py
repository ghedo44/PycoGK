from __future__ import annotations

import math
from typing import TYPE_CHECKING, Sequence

import numpy as np

if TYPE_CHECKING:
    from .vedo_viewer import VedoViewer

class AnimGroupMatrixRotate:
    def __init__(
        self,
        oViewer: "VedoViewer",
        nGroup: int,
        matInit: Sequence[float],
        vecAxis: Sequence[float],
        fDegrees: float,
    ) -> None:
        if len(matInit) != 16:
            raise ValueError("matInit must contain 16 values")
        self._viewer = oViewer
        self._group = int(nGroup)
        self._mat_init = np.array(matInit, dtype=np.float64).reshape((4, 4))
        axis = np.array(vecAxis, dtype=np.float64)
        n = float(np.linalg.norm(axis))
        if n <= 1e-12:
            raise ValueError("vecAxis must be non-zero")
        self._axis = axis / n
        self._degrees = float(fDegrees)

    def Do(self, fFactor: float) -> None:
        theta = math.radians(float(fFactor) * self._degrees)
        x, y, z = self._axis.tolist()
        c = math.cos(theta)
        s = math.sin(theta)
        t = 1.0 - c
        rot = np.array(
            [
                [t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0.0],
                [t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0.0],
                [t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        mat = self._mat_init @ rot
        self._viewer.SetGroupMatrix(self._group, tuple(float(v) for v in mat.reshape(-1)))


class AnimViewRotate:
    def __init__(self, oViewer: "VedoViewer", vecFrom: Sequence[float], vecTo: Sequence[float]) -> None:
        if len(vecFrom) < 2 or len(vecTo) < 2:
            raise ValueError("vecFrom and vecTo must contain at least 2 values")
        self._viewer = oViewer
        self._from = (float(vecFrom[0]), float(vecFrom[1]))
        self._to = (float(vecTo[0]), float(vecTo[1]))

    def Do(self, fFactor: float) -> None:
        factor = float(fFactor)
        orbit = self._from[0] + ((self._to[0] - self._from[0]) * factor)
        elevation = self._from[1] + ((self._to[1] - self._from[1]) * factor)
        self._viewer.SetViewAngles(orbit, elevation)

