from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from ..splines import ControlPointSpline

from .._types import Vec3, Vector3Like, as_np3, as_vec3

if TYPE_CHECKING:
    from ..frames.local_frames import LocalFrame
    
from .vec_operations import VecOperations

from picogk import Voxels

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
