from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from .._types import Vec3, Vector3Like, as_np3, as_vec3, clamp01, normalized
from ..utils.utils import LocalFrame, VecOperations

if TYPE_CHECKING:
    from picogk import Voxels


class ISpline(ABC):
    @abstractmethod
    def aGetPoints(self, nSamples: int | None = 500) -> list[Vec3]:
        raise NotImplementedError


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


class SplineOperations:
    @staticmethod
    def aGetReparametrizedSpline(aPoints: Sequence[Vector3Like], target: int | float) -> list[Vec3]:
        points = [as_np3(p) for p in aPoints]
        if len(points) < 2:
            return [as_vec3(p) for p in points]

        if type(target) is float:
            total_length = SplineOperations.fGetTotalLength(aPoints)
            n_target_samples = int(max(10.0, total_length / max(float(target), 1e-6)))
        else:
            n_target_samples = int(target)

        lengths = SplineOperations.aGetLengthsAtIndices(aPoints)
        spine_len = lengths[-1]
        target_step = spine_len / max(1, n_target_samples)

        out: list[np.ndarray] = [points[0]]
        for sample_idx in range(1, n_target_samples):
            target_len = target_step * sample_idx
            upper_idx = 1
            while upper_idx < len(points) and lengths[upper_idx] < target_len:
                upper_idx += 1
            upper_idx = min(upper_idx, len(points) - 1)
            lower_idx = max(upper_idx - 1, 0)

            lower_len = lengths[lower_idx]
            upper_len = lengths[upper_idx]
            if abs(upper_len - lower_len) <= 1e-12:
                ds = 0.0
            else:
                ds = (target_len - lower_len) / (upper_len - lower_len)
            out.append(points[lower_idx] + ds * (points[upper_idx] - points[lower_idx]))

        out.append(points[-1])
        return [as_vec3(p) for p in out]

    @staticmethod
    def aGetNURBSpline(aControlPoints: Sequence[Vector3Like], nSamples: int) -> list[Vec3]:
        return ControlPointSpline(aControlPoints, 2, ControlPointSpline.EEnds.OPEN).aGetPoints(nSamples)

    @staticmethod
    def aGetLengthsAtIndices(aPoints: Sequence[Vector3Like]) -> list[float]:
        points = [as_np3(p) for p in aPoints]
        out = [0.0]
        total = 0.0
        for idx in range(1, len(points)):
            total += float(np.linalg.norm(points[idx] - points[idx - 1]))
            out.append(total)
        return out

    @staticmethod
    def fGetTotalLength(aPoints: Sequence[Vector3Like]) -> float:
        lengths = SplineOperations.aGetLengthsAtIndices(aPoints)
        return lengths[-1] if lengths else 0.0

    @staticmethod
    def aGetLinearInterpolation(vecStart: Vector3Like, vecEnd: Vector3Like, nSamples: int) -> list[Vec3]:
        start = as_np3(vecStart)
        end   = as_np3(vecEnd)
        n     = max(2, int(nSamples))
        return [as_vec3(start + (float(i) / float(n - 1)) * (end - start)) for i in range(n)]

    @staticmethod
    def aGetSnappedSpline(aPoints: Sequence[Vector3Like], voxTarget: "Voxels") -> list[Vec3]:
        out: list[Vec3] = []
        for pt in aPoints:
            p = as_np3(pt)
            _ok, snap = voxTarget.closest_point_on_surface((float(p[0]), float(p[1]), float(p[2])))
            out.append(snap)
        return out

    @staticmethod
    def aGetAveragePointSpacing(aPoints: Sequence[Vector3Like]) -> float:
        pts = list(aPoints)
        if len(pts) < 2:
            return 0.0
        return SplineOperations.fGetTotalLength(pts) / float(len(pts) - 1)

    @staticmethod
    def aSplitLists(aList: Sequence[Vector3Like], iFirstIndexOfSecondList: int) -> tuple[list[Vec3], list[Vec3]]:
        idx    = int(iFirstIndexOfSecondList)
        first  = [as_vec3(aList[i]) for i in range(len(aList)) if i < idx]
        second = [as_vec3(aList[i]) for i in range(len(aList)) if i >= idx]
        return first, second

    @staticmethod
    def aCombineLists(aLists: Sequence[Sequence[Vector3Like]]) -> list[Vec3]:
        out: list[Vec3] = []
        for lst in aLists:
            for pt in lst:
                out.append(as_vec3(pt))
        return out

    @staticmethod
    def aRotateListAroundZ(aList: Sequence[Vector3Like], fAngle: float) -> list[Vec3]:
        return [VecOperations.vecRotateAroundZ(pt, float(fAngle)) for pt in aList]

    @staticmethod
    def aTranslateList(aList: Sequence[Vector3Like], vecShift: Vector3Like) -> list[Vec3]:
        shift = as_np3(vecShift)
        return [as_vec3(as_np3(pt) + shift) for pt in aList]

    @staticmethod
    def aScaleList(aList: Sequence[Vector3Like], fScale: float) -> list[Vec3]:
        s = float(fScale)
        return [as_vec3(as_np3(pt) * s) for pt in aList]

    @staticmethod
    def aOverSampleList(aList: Sequence[Vector3Like], iSamplesPerStep: int) -> list[Vec3]:
        out: list[Vec3] = []
        pts = list(aList)
        n   = int(iSamplesPerStep)
        for i in range(1, len(pts)):
            for j in range(n):
                t = float(j) / float(n)
                out.append(as_vec3(as_np3(pts[i - 1]) + t * (as_np3(pts[i]) - as_np3(pts[i - 1]))))
        out.append(as_vec3(pts[-1]))
        return out

    @staticmethod
    def aSubSampleList(aList: Sequence[Vector3Like], iSampleSize: int) -> list[Vec3]:
        pts  = list(aList)
        step = max(1, int(iSampleSize))
        out  = [as_vec3(pts[i]) for i in range(0, len(pts), step)]
        if tuple(as_np3(out[-1])) != tuple(as_np3(pts[-1])):
            out.append(as_vec3(pts[-1]))
        return out

    @staticmethod
    def aTranslateListOntoFrame(oFrame: LocalFrame, aList: Sequence[Vector3Like]) -> list[Vec3]:
        return [VecOperations.vecTranslatePointOntoFrame(oFrame, pt) for pt in aList]

    @staticmethod
    def aExpressListInFrame(oFrame: LocalFrame, aList: Sequence[Vector3Like]) -> list[Vec3]:
        return [VecOperations.vecExpressPointInFrame(oFrame, pt) for pt in aList]

    @staticmethod
    def aRotateListAroundAxis(
        aList: Sequence[Vector3Like],
        dPhi: float,
        vecAxis: Vector3Like,
        vecAxisOrigin: Vector3Like | None = None,
    ) -> list[Vec3]:
        return [VecOperations.vecRotateAroundAxis(pt, float(dPhi), vecAxis, vecAxisOrigin) for pt in aList]

    @staticmethod
    def vecGetAverage(aPoints: Sequence[Vector3Like]) -> Vec3:
        pts = [as_np3(p) for p in aPoints]
        if not pts:
            return (0.0, 0.0, 0.0)
        return as_vec3(np.mean(np.stack(pts, axis=0), axis=0))

    @staticmethod
    def vecGetClosestPoint(aPoints: Sequence[Vector3Like], vecStart: Vector3Like) -> Vec3:
        start    = as_np3(vecStart)
        best_d   = float("inf")
        best_pt  = as_np3(aPoints[0])
        for pt in aPoints:
            p = as_np3(pt)
            d = float(np.dot(p - start, p - start))
            if d < best_d:
                best_d  = d
                best_pt = p
        return as_vec3(best_pt)

    @staticmethod
    def fGetDistanceToClosestPoint(aPoints: Sequence[Vector3Like], vecStart: Vector3Like) -> float:
        start  = as_np3(vecStart)
        min_sq = float("inf")
        for pt in aPoints:
            p = as_np3(pt)
            d = float(np.dot(p - start, p - start))
            if d < min_sq:
                min_sq = d
        import math as _math
        return float(_math.sqrt(min_sq))

    @staticmethod
    def aGetClusteredPoints(aPoints: Sequence[Vector3Like], fClusteringRange: float) -> list[Vec3]:
        threshold = float(fClusteringRange) ** 2
        result    = [as_vec3(aPoints[0])]
        for pt in aPoints[1:]:
            near = as_np3(SplineOperations.vecGetClosestPoint(result, pt))
            diff = as_np3(pt) - near
            if float(np.dot(diff, diff)) > threshold:
                result.append(as_vec3(pt))
        return result
