from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .._types import Vec3, Vector3Like, as_np3, as_vec3, clamp01


class ControlPointSurface:
    class EEnds:
        OPEN = "OPEN"
        CLOSED = "CLOSED"

    def __init__(
        self,
        aControlGrid: Sequence[Sequence[Vector3Like]],
        nDegreeU: int = 2,
        nDegreeV: int = 2,
        eEndsU: str = EEnds.OPEN,
        eEndsV: str = EEnds.OPEN,
    ) -> None:
        self.m_aControlGrid = [[as_np3(p) for p in row] for row in aControlGrid]
        if not self.m_aControlGrid or not self.m_aControlGrid[0]:
            raise ValueError("aControlGrid cannot be empty")

        self.m_nDegreeU = int(nDegreeU)
        self.m_nDegreeV = int(nDegreeV)
        self.m_eEndsU = eEndsU
        self.m_eEndsV = eEndsV
        self.m_fError = 1e-7

        if self.m_eEndsU == self.EEnds.CLOSED and len(self.m_aControlGrid) > 1:
            if float(np.linalg.norm(self.m_aControlGrid[0][0] - self.m_aControlGrid[-1][0])) < self.m_fError:
                self.m_aControlGrid.pop()

        if self.m_eEndsV == self.EEnds.CLOSED and len(self.m_aControlGrid[0]) > 1:
            if float(np.linalg.norm(self.m_aControlGrid[0][0] - self.m_aControlGrid[0][-1])) < self.m_fError:
                self.m_aControlGrid = [row[:-1] for row in self.m_aControlGrid]

        self.m_aKnotU = self.aGetUKnotVector(len(self.m_aControlGrid), self.m_nDegreeU, self.m_eEndsU)
        self.m_aKnotV = self.aGetVKnotVector(len(self.m_aControlGrid[0]), self.m_nDegreeV, self.m_eEndsV)

    def aGetUKnotVector(self, nNumberOfControlPoints: int, nDegree: int, eEnds: str) -> list[float]:
        if eEnds == self.EEnds.CLOSED:
            before = len(self.m_aControlGrid)
            for i in range(before - 1):
                self.m_aControlGrid.append([p.copy() for p in self.m_aControlGrid[i]])
            nNumberOfControlPoints = len(self.m_aControlGrid)

        n_knots = int(nNumberOfControlPoints) + int(nDegree) + 1
        n_valid_range = n_knots - int(nDegree) - (int(nDegree) + 1)
        d_r = 1.0 / float(n_valid_range)
        out: list[float] = []
        for i in range(n_knots):
            value = -(d_r * nDegree) + d_r * i
            if eEnds == self.EEnds.OPEN:
                value = clamp01(value)
            out.append(float(value))
        return out

    def aGetVKnotVector(self, nNumberOfControlPoints: int, nDegree: int, eEnds: str) -> list[float]:
        if eEnds == self.EEnds.CLOSED:
            before = len(self.m_aControlGrid[0])
            for row_idx in range(len(self.m_aControlGrid)):
                row = self.m_aControlGrid[row_idx]
                for i in range(before - 1):
                    row.append(row[i].copy())
            nNumberOfControlPoints = len(self.m_aControlGrid[0])

        n_knots = int(nNumberOfControlPoints) + int(nDegree) + 1
        n_valid_range = n_knots - int(nDegree) - (int(nDegree) + 1)
        d_r = 1.0 / float(n_valid_range)
        out: list[float] = []
        for i in range(n_knots):
            value = -(d_r * nDegree) + d_r * i
            if eEnds == self.EEnds.OPEN:
                value = clamp01(value)
            out.append(float(value))
        return out

    def aGetGrid(self, nUSamples: int = 500, nVSamples: int = 500) -> list[list[Vec3]]:
        grid: list[list[Vec3]] = []
        for i in range(int(nUSamples)):
            u_ratio = float(i) / float(max(1, nUSamples - 1))
            row: list[Vec3] = []
            for j in range(int(nVSamples)):
                v_ratio = float(j) / float(max(1, nVSamples - 1))
                row.append(self.vecGetPointAt(u_ratio, v_ratio))
            grid.append(row)
        return grid

    def vecGetPointAt(self, fURatio: float, fVRatio: float) -> Vec3:
        point = np.zeros(3, dtype=np.float64)
        for u in range(len(self.m_aControlGrid)):
            u_base = self.fBaseFunc(self.m_aKnotU, fURatio, u, self.m_nDegreeU)
            for v in range(len(self.m_aControlGrid[u])):
                v_base = self.fBaseFunc(self.m_aKnotV, fVRatio, v, self.m_nDegreeV)
                point += u_base * v_base * self.m_aControlGrid[u][v]
        return as_vec3(point)

    def fBaseFunc(self, aKnot: Sequence[float], fLengthRatio: float, nControlPoint: int, nDegree: int) -> float:
        if nDegree == 0:
            left = aKnot[nControlPoint]
            right = aKnot[nControlPoint + 1]
            if (left <= fLengthRatio < right) or (
                abs(fLengthRatio - right) < self.m_fError and abs(fLengthRatio - aKnot[-1]) < self.m_fError
            ):
                return 1.0
            return 0.0

        value = 0.0
        left_den = aKnot[nControlPoint + nDegree] - aKnot[nControlPoint]
        if abs(left_den) > self.m_fError:
            value += (
                (fLengthRatio - aKnot[nControlPoint])
                / left_den
                * self.fBaseFunc(aKnot, fLengthRatio, nControlPoint, nDegree - 1)
            )

        right_den = aKnot[nControlPoint + nDegree + 1] - aKnot[nControlPoint + 1]
        if abs(right_den) > self.m_fError:
            value += (
                (aKnot[nControlPoint + nDegree + 1] - fLengthRatio)
                / right_den
                * self.fBaseFunc(aKnot, fLengthRatio, nControlPoint + 1, nDegree - 1)
            )

        return float(value)

    def aGetControlGrid(self) -> list[list[Vec3]]:
        return [[as_vec3(p) for p in row] for row in self.m_aControlGrid]

    def vecGetControlPoint(self, u: int, v: int) -> Vec3:
        return as_vec3(self.m_aControlGrid[int(u)][int(v)])

    def UpdateControlPoint(self, vecPt: Vector3Like, u: int, v: int) -> None:
        self.m_aControlGrid[int(u)][int(v)] = as_np3(vecPt)

