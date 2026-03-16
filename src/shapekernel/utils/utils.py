from __future__ import annotations

import math
import random
from dataclasses import dataclass
from collections.abc import Callable, Sequence
from enum import Enum

import numpy as np

from .._types import Vec3, Vector3Like, as_np3, as_vec3, normalized


@dataclass
class LocalFrame:
    _position: np.ndarray
    _local_x: np.ndarray
    _local_y: np.ndarray
    _local_z: np.ndarray

    def __init__(
        self,
        vecPos: Vector3Like = (0.0, 0.0, 0.0),
        vecLocalZ: Vector3Like = (0.0, 0.0, 1.0),
        vecLocalX: Vector3Like | None = None,
    ) -> None:
        pos = as_np3(vecPos)
        local_z = normalized(vecLocalZ)
        if float(np.linalg.norm(local_z)) <= 1e-12:
            raise ValueError("Local Z Coordinate has a length of Zero!")
        if vecLocalX is None:
            local_x = VecOperations.vecGetOrthogonalDir(local_z)
        else:
            local_x = normalized(vecLocalX)
            if float(np.linalg.norm(local_x)) <= 1e-12:
                raise ValueError("Local X Coordinate has a length of Zero!")
        local_y = LocalFrame.vecBuildLocalY(local_z, local_x)

        self._position = pos
        self._local_x = normalized(local_x)
        self._local_y = normalized(local_y)
        self._local_z = normalized(local_z)

    def vecGetPosition(self) -> Vec3:
        return as_vec3(self._position)

    def vec_get_position(self) -> Vec3:
        return self.vecGetPosition()

    def vecGetLocalX(self) -> Vec3:
        return as_vec3(self._local_x)

    def vec_get_local_x(self) -> Vec3:
        return self.vecGetLocalX()

    def vecGetLocalY(self) -> Vec3:
        return as_vec3(self._local_y)

    def vec_get_local_y(self) -> Vec3:
        return self.vecGetLocalY()

    def vecGetLocalZ(self) -> Vec3:
        return as_vec3(self._local_z)

    def vec_get_local_z(self) -> Vec3:
        return self.vecGetLocalZ()

    def oInvert(self, bMirrorZ: bool, bMirrorX: bool) -> "LocalFrame":
        z = -self._local_z if bMirrorZ else self._local_z
        x = -self._local_x if bMirrorX else self._local_x
        return LocalFrame(self._position, z, x)

    def oTranslate(self, vecTranslate: Vector3Like) -> "LocalFrame":
        return LocalFrame(self._position + as_np3(vecTranslate), self._local_z, self._local_x)

    def oRotate(self, dPhi: float, vecAxis: Vector3Like) -> "LocalFrame":
        x = VecOperations.vecRotateAroundAxis(self._local_x, dPhi, vecAxis)
        z = VecOperations.vecRotateAroundAxis(self._local_z, dPhi, vecAxis)
        return LocalFrame(self._position, z, x)

    @staticmethod
    def oGetInvertFrame(oFrame: "LocalFrame", bMirrorZ: bool, bMirrorX: bool) -> "LocalFrame":
        return oFrame.oInvert(bMirrorZ, bMirrorX)

    @staticmethod
    def oGetTranslatedFrame(oFrame: "LocalFrame", vecTranslate: Vector3Like) -> "LocalFrame":
        return oFrame.oTranslate(vecTranslate)

    @staticmethod
    def oGetRotatedFrame(oFrame: "LocalFrame", dPhi: float, vecAxis: Vector3Like) -> "LocalFrame":
        return oFrame.oRotate(dPhi, vecAxis)

    @staticmethod
    def vecBuildLocalY(vecLocalZ: Vector3Like, vecLocalX: Vector3Like) -> Vec3:
        z = as_np3(vecLocalZ)
        x = as_np3(vecLocalX)
        return as_vec3(np.cross(z, x))


class VecOperations:
    @staticmethod
    def vecGetOrthogonalDir(vecDir: Vector3Like) -> np.ndarray:
        direction = normalized(vecDir)
        non_parallel = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        if abs(float(np.dot(direction, non_parallel))) > 0.95:
            non_parallel = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        return normalized(np.cross(direction, non_parallel))

    @staticmethod
    def vecFlipForAlignment(vecDir: Vector3Like, vecTargetDir: Vector3Like) -> np.ndarray:
        d = as_np3(vecDir)
        t = as_np3(vecTargetDir)
        return d if float(np.dot(t, d)) >= float(np.dot(t, -d)) else -d

    @staticmethod
    def fGetAngleBetween(vecA: Vector3Like, vecB: Vector3Like) -> float:
        a = normalized(vecA)
        b = normalized(vecB)
        dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
        theta = float(math.acos(dot))
        if math.isnan(theta) and abs(dot) == 1.0:
            return math.pi
        return theta

    @staticmethod
    def vecRotateAroundAxis(
        vecPt: Vector3Like,
        dPhi: float,
        vecAxis: Vector3Like,
        vecAxisOrigin: Vector3Like | None = None,
    ) -> Vec3:
        point = as_np3(vecPt)
        axis = normalized(vecAxis)
        origin = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(vecAxisOrigin)
        rel = point - origin
        cos_phi = math.cos(dPhi)
        sin_phi = math.sin(dPhi)
        rot = rel * cos_phi + np.cross(axis, rel) * sin_phi + axis * float(np.dot(axis, rel)) * (1.0 - cos_phi)
        return as_vec3(rot + origin)

    @staticmethod
    def vecTranslatePointOntoFrame(oFrame: LocalFrame, vecPt: Vector3Like) -> Vec3:
        p = as_np3(vecPt)
        origin = as_np3(oFrame.vecGetPosition())
        x = as_np3(oFrame.vecGetLocalX())
        y = as_np3(oFrame.vecGetLocalY())
        z = as_np3(oFrame.vecGetLocalZ())
        return as_vec3(origin + p[0] * x + p[1] * y + p[2] * z)

    @staticmethod
    def vecGetPlanarDir(vecPt: Vector3Like) -> np.ndarray:
        pt = as_np3(vecPt)
        planar = np.array([pt[0], pt[1], 0.0], dtype=np.float64)
        length = float(np.linalg.norm(planar))
        if length <= 1e-12:
            return np.array([1.0, 0.0, 0.0], dtype=np.float64)
        return planar / length

    @staticmethod
    def vecSetZ(vecPt: Vector3Like, zValue: float) -> Vec3:
        pt = as_np3(vecPt).copy()
        pt[2] = float(zValue)
        return as_vec3(pt)

    @staticmethod
    def vecSetRadius(vecPt: Vector3Like, radius: float) -> Vec3:
        pt = as_np3(vecPt).copy()
        planar = np.array([pt[0], pt[1]], dtype=np.float64)
        length = float(np.linalg.norm(planar))
        target = float(radius)
        if length <= 1e-12:
            pt[0] = target
            pt[1] = 0.0
            return as_vec3(pt)
        scale = target / length
        pt[0] *= scale
        pt[1] *= scale
        return as_vec3(pt)

    @staticmethod
    def vecGetCylPoint(fRadius: float, fPhi: float, fZ: float) -> Vec3:
        r = float(fRadius)
        return as_vec3(np.array([r * math.cos(float(fPhi)), r * math.sin(float(fPhi)), float(fZ)], dtype=np.float64))

    @staticmethod
    def vecGetSphPoint(fRadius: float, fPhi: float, fTheta: float) -> Vec3:
        r, phi, theta = float(fRadius), float(fPhi), float(fTheta)
        return as_vec3(np.array([r * math.cos(phi) * math.cos(theta), r * math.sin(phi) * math.cos(theta), r * math.sin(theta)], dtype=np.float64))

    @staticmethod
    def fGetRadius(vecPt: Vector3Like) -> float:
        pt = as_np3(vecPt)
        return float(math.sqrt(float(pt[0]) ** 2 + float(pt[1]) ** 2))

    @staticmethod
    def fGetPhi(vecPt: Vector3Like) -> float:
        pt = as_np3(vecPt)
        return float(math.atan2(float(pt[1]), float(pt[0])))

    @staticmethod
    def fGetTheta(vecPt: Vector3Like) -> float:
        r = VecOperations.fGetRadius(vecPt)
        return float(math.atan2(float(as_np3(vecPt)[2]), r))

    @staticmethod
    def vecSetPhi(vecPt: Vector3Like, fNewPhi: float) -> Vec3:
        r = VecOperations.fGetRadius(vecPt)
        z = float(as_np3(vecPt)[2])
        return VecOperations.vecGetCylPoint(r, float(fNewPhi), z)

    @staticmethod
    def vecUpdateRadius(vecPt: Vector3Like, dRadius: float) -> Vec3:
        new_r = VecOperations.fGetRadius(vecPt) + float(dRadius)
        phi   = VecOperations.fGetPhi(vecPt)
        z     = float(as_np3(vecPt)[2])
        return VecOperations.vecGetCylPoint(new_r, phi, z)

    @staticmethod
    def vecUpdatePhi(vecPt: Vector3Like, dPhi: float) -> Vec3:
        r       = VecOperations.fGetRadius(vecPt)
        new_phi = VecOperations.fGetPhi(vecPt) + float(dPhi)
        z       = float(as_np3(vecPt)[2])
        return VecOperations.vecGetCylPoint(r, new_phi, z)

    @staticmethod
    def vecUpdateZ(vecPt: Vector3Like, dZ: float) -> Vec3:
        return VecOperations.vecSetZ(vecPt, float(as_np3(vecPt)[2]) + float(dZ))

    @staticmethod
    def vecRotateAroundZ(vecPt: Vector3Like, dPhi: float, vecAxisOrigin: Vector3Like | None = None) -> Vec3:
        origin   = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(vecAxisOrigin)
        diff     = as_np3(vecPt) - origin
        phi      = float(math.atan2(float(diff[1]), float(diff[0])))
        r        = float(math.sqrt(float(diff[0]) ** 2 + float(diff[1]) ** 2))
        new_diff = np.array([r * math.cos(phi + float(dPhi)), r * math.sin(phi + float(dPhi)), float(diff[2])], dtype=np.float64)
        return as_vec3(new_diff + origin)

    @staticmethod
    def vecExpressPointInFrame(oFrame: LocalFrame, vecPt: Vector3Like) -> Vec3:
        pt = as_np3(vecPt) - as_np3(oFrame.vecGetPosition())
        x  = float(np.dot(pt, as_np3(oFrame.vecGetLocalX())))
        y  = float(np.dot(pt, as_np3(oFrame.vecGetLocalY())))
        z  = float(np.dot(pt, as_np3(oFrame.vecGetLocalZ())))
        return (x, y, z)

    @staticmethod
    def vecTranslateDirectionOntoFrame(oFrame: LocalFrame, vecDir: Vector3Like) -> Vec3:
        origin = np.zeros(3, dtype=np.float64)
        pt1    = as_np3(VecOperations.vecTranslatePointOntoFrame(oFrame, origin))
        pt2    = as_np3(VecOperations.vecTranslatePointOntoFrame(oFrame, as_np3(vecDir)))
        return as_vec3(pt2 - pt1)

    @staticmethod
    def vecGetDirectionToAxis(oFrame: LocalFrame, vecPt: Vector3Like) -> Vec3:
        pt  = as_np3(vecPt) - as_np3(oFrame.vecGetPosition())
        lx  = as_np3(oFrame.vecGetLocalX())
        ly  = as_np3(oFrame.vecGetLocalY())
        d   = float(np.dot(pt, lx)) * lx + float(np.dot(pt, ly)) * ly
        mag = float(np.linalg.norm(d))
        return as_vec3(d / mag) if mag > 1e-12 else as_vec3(lx)

    @staticmethod
    def fGetRadiusToAxis(oFrame: LocalFrame, vecPt: Vector3Like) -> float:
        pt = as_np3(vecPt) - as_np3(oFrame.vecGetPosition())
        lx = as_np3(oFrame.vecGetLocalX())
        ly = as_np3(oFrame.vecGetLocalY())
        return float(math.sqrt(float(np.dot(pt, lx)) ** 2 + float(np.dot(pt, ly)) ** 2))

    @staticmethod
    def fGetPhiToAxis(oFrame: LocalFrame, vecPt: Vector3Like) -> float:
        pt = as_np3(vecPt) - as_np3(oFrame.vecGetPosition())
        lx = as_np3(oFrame.vecGetLocalX())
        ly = as_np3(oFrame.vecGetLocalY())
        return float(math.atan2(float(np.dot(pt, ly)), float(np.dot(pt, lx))))

    @staticmethod
    def vecLinearInterpolation(vecPt1: Vector3Like, vecPt2: Vector3Like, fRatio: float) -> Vec3:
        p1 = as_np3(vecPt1)
        p2 = as_np3(vecPt2)
        return as_vec3(p1 + float(fRatio) * (p2 - p1))

    @staticmethod
    def vecCylindricalInterpolation(
        vecPt1: Vector3Like,
        vecPt2: Vector3Like,
        fRatio: float,
        vecAxisOrigin: Vector3Like | None = None,
    ) -> Vec3:
        origin  = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(VecOperations.vecSetZ(vecAxisOrigin, 0.0))
        p1      = as_np3(vecPt1)
        p2      = as_np3(vecPt2)
        d_angle = VecOperations.fGetAngleBetween(p1 - origin, p2 - origin)
        side1   = normalized(p1 - origin)
        r_pos   = as_np3(VecOperations.vecRotateAroundZ(as_vec3(p1), d_angle))
        r_neg   = as_np3(VecOperations.vecRotateAroundZ(as_vec3(p1), -d_angle))
        sense   = 1 if float(np.linalg.norm(p2 - r_neg)) >= float(np.linalg.norm(p2 - r_pos)) else -1
        r1      = VecOperations.fGetRadius(as_vec3(p1 - origin))
        r2      = VecOperations.fGetRadius(as_vec3(p2 - origin))
        ir      = r1 + float(fRatio) * (r2 - r1)
        iz      = float(p1[2]) + float(fRatio) * (float(p2[2]) - float(p1[2]))
        inter   = as_np3(VecOperations.vecRotateAroundZ(as_vec3(ir * side1), sense * float(fRatio) * d_angle))
        return as_vec3(as_np3(VecOperations.vecSetZ(as_vec3(inter), iz)) + origin)

    @staticmethod
    def vecSphericalInterpolation(
        vecPt1: Vector3Like,
        vecPt2: Vector3Like,
        fRatio: float,
        vecAxisOrigin: Vector3Like | None = None,
    ) -> Vec3:
        origin  = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(vecAxisOrigin)
        p1      = as_np3(vecPt1)
        p2      = as_np3(vecPt2)
        d_angle = VecOperations.fGetAngleBetween(p1 - origin, p2 - origin)
        side1   = normalized(p1 - origin)
        normal  = np.cross(side1, normalized(p2 - origin))
        r_pos   = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(p1), d_angle, as_vec3(normal)))
        r_neg   = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(p1), -d_angle, as_vec3(normal)))
        sense   = 1 if float(np.linalg.norm(p2 - r_neg)) >= float(np.linalg.norm(p2 - r_pos)) else -1
        r1      = float(np.linalg.norm(p1 - origin))
        r2      = float(np.linalg.norm(p2 - origin))
        ir      = r1 + float(fRatio) * (r2 - r1)
        inter   = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(ir * side1), sense * float(fRatio) * d_angle, as_vec3(normal)))
        return as_vec3(inter + origin)

    @staticmethod
    def fGetSignedAngleBetween(vecA: Vector3Like, vecB: Vector3Like, vecRefNormal: Vector3Like) -> float:
        a, b, ref = as_np3(vecA), as_np3(vecB), as_np3(vecRefNormal)
        if float(np.dot(a, a)) < 1e-20 or float(np.dot(b, b)) < 1e-20 or float(np.dot(ref, ref)) < 1e-20:
            raise ValueError("Vector3 with zero length.")
        a, b, ref = normalized(a), normalized(b), normalized(ref)
        normal    = as_np3(VecOperations.vecFlipForAlignment(np.cross(a, b), ref))
        theta     = abs(VecOperations.fGetAngleBetween(a, b))
        r_pos     = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(b), theta, as_vec3(normal)))
        r_neg     = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(b), -theta, as_vec3(normal)))
        return theta if float(np.dot(a, r_neg)) <= float(np.dot(a, r_pos)) else -theta

    @staticmethod
    def bCheckAlignment(vecDir: Vector3Like, vecTargetDir: Vector3Like) -> bool:
        d = as_np3(vecDir)
        t = as_np3(vecTargetDir)
        return float(np.dot(t, d)) >= float(np.dot(t, -d))


class GridOperations:
    @staticmethod
    def aGetListInX(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[Vec3]:
        return [as_vec3(p) for p in aGrid[int(index)]]

    @staticmethod
    def aGetListInY(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[Vec3]:
        idx = int(index)
        return [as_vec3(row[idx]) for row in aGrid]

    @staticmethod
    def aAddListInX(aGrid: Sequence[Sequence[Vector3Like]], aList: Sequence[Vector3Like]) -> list[list[Vec3]]:
        out = [[as_vec3(p) for p in row] for row in aGrid]
        out.append([as_vec3(p) for p in aList])
        return out

    @staticmethod
    def aAddListInY(aGrid: Sequence[Sequence[Vector3Like]], aList: Sequence[Vector3Like]) -> list[list[Vec3]]:
        out = [[as_vec3(p) for p in row] for row in aGrid]
        col = [as_vec3(p) for p in aList]
        if len(out) != len(col):
            raise ValueError("Column length must match grid height")
        for i in range(len(out)):
            out[i].append(col[i])
        return out

    @staticmethod
    def aRemoveListInX(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[list[Vec3]]:
        idx = int(index)
        out = [[as_vec3(p) for p in row] for row in aGrid]
        if idx < 0 or idx >= len(out):
            raise IndexError(idx)
        del out[idx]
        return out

    @staticmethod
    def aRemoveListInY(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[list[Vec3]]:
        idx = int(index)
        out = [[as_vec3(p) for p in row] for row in aGrid]
        for row in out:
            if idx < 0 or idx >= len(row):
                raise IndexError(idx)
            del row[idx]
        return out

    @staticmethod
    def aGetInverseGrid(aGrid: Sequence[Sequence[Vector3Like]]) -> list[list[Vec3]]:
        if not aGrid:
            return []
        h = len(aGrid)
        w = len(aGrid[0])
        return [[as_vec3(aGrid[i][j]) for i in range(h)] for j in range(w)]


class BisectionException(Exception):
    pass


class Bisection:
    Func = Callable[[float], float]

    def __init__(
        self,
        oFunc: Func,
        fMinInput: float,
        fMaxInput: float,
        fTargetOutput: float,
        fEpsilon: float = 0.01,
        nMaxIterations: int = 500,
    ) -> None:
        self.m_oFunc = oFunc
        self.m_fEpsilon = float(fEpsilon)
        self.m_fMinInput = float(fMinInput)
        self.m_fMaxInput = float(fMaxInput)
        self.m_fTargetOutput = float(fTargetOutput)
        self.m_nIterations = 0
        self.m_nMaxIterations = int(nMaxIterations)
        self.m_fRemainingDiff = float(self.m_fMaxInput - self.m_fMinInput)
        self.m_fBestGuess = float(self.m_fMinInput)

    def fGetOutputFromFunc(self, fInput: float) -> float:
        return float(self.m_oFunc(float(fInput))) - self.m_fTargetOutput

    def fFindOptimalInput(self) -> float:
        f_min = self.m_fMinInput
        f_max = self.m_fMaxInput
        out_min = self.fGetOutputFromFunc(f_min)
        out_max = self.fGetOutputFromFunc(f_max)
        if out_min * out_max >= 0.0:
            raise BisectionException("No valid limits.")

        mid = f_min
        self.m_fRemainingDiff = f_max - f_min
        while self.m_fRemainingDiff >= self.m_fEpsilon:
            mid = 0.5 * (f_min + f_max)
            out_mid = self.fGetOutputFromFunc(mid)
            if out_mid == 0.0:
                break
            if out_mid * self.fGetOutputFromFunc(f_min) < 0.0:
                f_max = mid
            else:
                f_min = mid

            self.m_fRemainingDiff = f_max - f_min
            self.m_nIterations += 1
            self.m_fBestGuess = mid

            if self.m_nIterations == self.m_nMaxIterations:
                raise BisectionException("No solution reached after max number of interations.")

        return float(mid)

    def nGetIterations(self) -> int:
        return int(self.m_nIterations)

    def fGetRemainingDiff(self) -> float:
        return float(self.m_fRemainingDiff)

    def fGetBestGuess(self) -> float:
        return float(self.m_fBestGuess)


class ImplicitGyroid:
    def __init__(self, fUnitSize: float, fThicknessRatio: float) -> None:
        self.m_fFrequencyScale = (2.0 * math.pi) / float(fUnitSize)
        self.m_fThicknessRatio = float(fThicknessRatio)

    @staticmethod
    def fGetThicknessRatio(fWallThickness: float, fUnitSize: float) -> float:
        return float(fWallThickness) * 10.0 / float(fUnitSize)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        x, y, z = as_vec3(vecPt)
        dist = (
            math.sin(self.m_fFrequencyScale * x) * math.cos(self.m_fFrequencyScale * y)
            + math.sin(self.m_fFrequencyScale * y) * math.cos(self.m_fFrequencyScale * z)
            + math.sin(self.m_fFrequencyScale * z) * math.cos(self.m_fFrequencyScale * x)
        )
        return float(abs(dist) - 0.5 * self.m_fThicknessRatio)


class ImplicitSphere:
    def __init__(self, vecCentre: Vector3Like, fRadius: float) -> None:
        self.m_vecCentre = as_np3(vecCentre)
        self.m_fRadius = float(fRadius)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        return float(np.linalg.norm(as_np3(vecPt) - self.m_vecCentre) - self.m_fRadius)


class ImplicitGenus:
    def __init__(self, fGap: float) -> None:
        self.m_fGap = float(fGap)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        x, y, z = as_vec3(vecPt)
        return float(
            2.0 * y * (y * y - 3.0 * x * x) * (1.0 - z * z)
            + (x * x + y * y) ** 2
            - (9.0 * z * z - 1.0) * (1.0 - z * z)
            - self.m_fGap
        )


class ImplicitSuperEllipsoid:
    def __init__(
        self,
        vecCentre: Vector3Like,
        fAx: float,
        fAy: float,
        fAz: float,
        fEpsilon1: float,
        fEpsilon2: float,
    ) -> None:
        self.m_vecCentre = as_np3(vecCentre)
        self.m_fAx = float(fAx)
        self.m_fAy = float(fAy)
        self.m_fAz = float(fAz)
        self.m_fEpsilon1 = float(fEpsilon1)
        self.m_fEpsilon2 = float(fEpsilon2)

    def fSignedDistance(self, vecPt: Vector3Like) -> float:
        x, y, z = as_np3(vecPt)
        d_x = abs(x + self.m_vecCentre[0]) / self.m_fAx
        d_y = abs(y + self.m_vecCentre[1]) / self.m_fAy
        d_z = abs(z + self.m_vecCentre[2]) / self.m_fAz
        dist = (
            (d_x ** (2.0 / self.m_fEpsilon2) + d_y ** (2.0 / self.m_fEpsilon2))
            ** (self.m_fEpsilon2 / self.m_fEpsilon1)
            + d_z ** (2.0 / self.m_fEpsilon1)
        )
        return float(dist - 1.0)


class ListOperations:
    @staticmethod
    def aOverSampleList(aList: list[float], iSamplesPerStep: int) -> list[float]:
        out: list[float] = []
        for i in range(1, len(aList)):
            for j in range(int(iSamplesPerStep)):
                t = float(j) / float(iSamplesPerStep)
                out.append(float(aList[i - 1]) + t * (float(aList[i]) - float(aList[i - 1])))
        out.append(float(aList[-1]))
        return out

    @staticmethod
    def aSubsampleList(aList: list[float], iSampleSize: int) -> list[float]:
        out: list[float] = []
        step = max(1, int(iSampleSize))
        i = 0
        while i < len(aList):
            out.append(float(aList[i]))
            i += step
        if out[-1] != float(aList[-1]):
            out.append(float(aList[-1]))
        return out

    @staticmethod
    def iGetIndexOfMaxValue(aList: list[float]) -> int:
        max_val = float("-inf")
        idx = -1
        for i, v in enumerate(aList):
            if float(v) > max_val:
                max_val = float(v)
                idx = i
        return idx

    @staticmethod
    def iGetIndexOfMinValue(aList: list[float]) -> int:
        min_val = float("inf")
        idx = -1
        for i, v in enumerate(aList):
            if float(v) < min_val:
                min_val = float(v)
                idx = i
        return idx


class LineDecimation:
    def __init__(self, aPoints: Sequence[Vector3Like], fMaxError: float) -> None:
        self._pts = [as_np3(p) for p in aPoints]
        i_start = 0
        indices: list[int] = [0]
        while i_start < len(self._pts) - 1:
            i_end   = self._iGetNextIndex(i_start, float(fMaxError))
            i_start = i_end
            indices.append(i_start)
        self._decimated: list[Vec3] = [as_vec3(self._pts[i]) for i in indices]

    def _iGetNextIndex(self, i_start: int, fMaxError: float) -> int:
        if i_start > len(self._pts) - 2:
            return len(self._pts) - 1
        i_end    = i_start + 1
        line_pts = list(self._pts[i_start : i_start + 2])
        for i_idx in range(i_start + 2, len(self._pts)):
            line_pts.append(self._pts[i_idx])
            if LineDecimation._fGetMaxError(line_pts) > fMaxError:
                break
            i_end = i_idx
        return i_end

    @staticmethod
    def _fGetMaxError(line_pts: list[np.ndarray]) -> float:
        line_dir = line_pts[-1] - line_pts[0]
        max_err  = 0.0
        for i in range(1, len(line_pts) - 1):
            pointer = line_pts[i] - line_pts[0]
            angle   = VecOperations.fGetAngleBetween(pointer, line_dir)
            err     = math.sin(angle) * float(np.linalg.norm(pointer))
            if err > max_err:
                max_err = err
        return max_err

    def aGetDecimatedPoints(self) -> list[Vec3]:
        return list(self._decimated)


class CSVWriter:
    def __init__(self, strFilename: str) -> None:
        self._filename = str(strFilename)
        self._writer   = open(self._filename, "w", newline="", encoding="utf-8")

    def AddLine(self, strLine: str) -> None:
        self._writer.write(str(strLine) + "\n")

    def ExportCSVFile(self) -> None:
        try:
            self._writer.flush()
        except Exception as exc:
            print(f"Could not save CSV: {exc}")

    def __del__(self) -> None:
        try:
            self._writer.close()
        except Exception:
            pass


class Uf:
    _random: random.Random = random.Random()
    _bspline: object | None = None  # ControlPointSpline, lazily initialised

    @classmethod
    def _get_bspline(cls) -> object:
        if cls._bspline is None:
            from ..splines import ControlPointSpline  # lazy – avoids circular import
            ctrl_pts = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (1.0, 0.0, 1.0)]
            cls._bspline = ControlPointSpline(ctrl_pts)
        return cls._bspline

    @staticmethod
    def Wait(fSeconds: float) -> None:
        import time
        time.sleep(float(fSeconds))

    @staticmethod
    def fTransFixed(fValue1: float, fValue2: float, fS: float) -> float:
        bspline = Uf._get_bspline()
        pt      = bspline.vecGetPointAt(float(fS))  # type: ignore[union-attr]
        ratio   = float(pt[0])
        return float(fValue1) + ratio * (float(fValue2) - float(fValue1))

    @staticmethod
    def vecTransFixed(vecPt1: Vector3Like, vecPt2: Vector3Like, fS: float) -> Vec3:
        p1 = as_vec3(vecPt1)
        p2 = as_vec3(vecPt2)
        return (
            Uf.fTransFixed(p1[0], p2[0], fS),
            Uf.fTransFixed(p1[1], p2[1], fS),
            Uf.fTransFixed(p1[2], p2[2], fS),
        )

    @staticmethod
    def _fGetNormalizedTangensHyperbolicus(fS: float, fTransitionS: float, fSmooth: float) -> float:
        return float(0.5 + 0.5 * math.tanh((float(fS) - float(fTransitionS)) / float(fSmooth)))

    @staticmethod
    def fTransSmooth(fValue1: float, fValue2: float, fS: float, fTransitionS: float, fSmooth: float) -> float:
        t = Uf._fGetNormalizedTangensHyperbolicus(fS, fTransitionS, fSmooth)
        return float(fValue1) * (1.0 - t) + float(fValue2) * t

    @staticmethod
    def vecTransSmooth(vecPt1: Vector3Like, vecPt2: Vector3Like, fS: float, fTransitionS: float, fSmooth: float) -> Vec3:
        t  = Uf._fGetNormalizedTangensHyperbolicus(fS, fTransitionS, fSmooth)
        p1 = as_np3(vecPt1)
        p2 = as_np3(vecPt2)
        return as_vec3(p1 * (1.0 - t) + p2 * t)

    @staticmethod
    def fGetRandomGaussian(fMean: float, fStdDev: float, oRandom: random.Random | None = None) -> float:
        rng = oRandom if oRandom is not None else Uf._random
        x1  = max(1.0 - rng.random(), 1e-300)
        x2  = 1.0 - rng.random()
        y1  = float(math.sqrt(-2.0 * math.log(x1)) * math.cos(2.0 * math.pi * x2))
        return y1 * float(fStdDev) + float(fMean)

    @staticmethod
    def fGetRandomLinear(fMin: float, fMax: float, oRandom: random.Random | None = None) -> float:
        rng = oRandom if oRandom is not None else Uf._random
        return float(fMin) + (float(fMax) - float(fMin)) * rng.random()

    @staticmethod
    def bGetRandomBool(oRandom: random.Random | None = None) -> bool:
        return Uf.fGetRandomLinear(0.0, 1.0, oRandom) > 0.5

    @staticmethod
    def aGetFibonacciCirlePoints(fOuterRadius: float, nSamples: int) -> list[Vec3]:
        pts: list[Vec3] = []
        r_out  = float(fOuterRadius)
        golden = math.pi * (1.0 + math.sqrt(5.0))
        for i in range(int(nSamples)):
            k   = i + 0.5
            r   = math.sqrt(k / float(nSamples))
            phi = golden * k
            pts.append((r_out * r * math.cos(phi), r_out * r * math.sin(phi), 0.0))
        return pts

    @staticmethod
    def aGetFibonacciSpherePoints(fOuterRadius: float, nSamples: int) -> list[Vec3]:
        pts: list[Vec3] = []
        r_out  = float(fOuterRadius)
        golden = math.pi * (1.0 + math.sqrt(5.0))
        for i in range(int(nSamples)):
            k     = i + 0.5
            phi_a = math.acos(1.0 - 2.0 * k / float(nSamples))
            theta = golden * k
            pts.append((
                r_out * math.cos(theta) * math.sin(phi_a),
                r_out * math.sin(theta) * math.sin(phi_a),
                r_out * math.cos(phi_a),
            ))
        return pts

    # -- Super-shapes ---------------------------------------------------------
    class ESuperShape(Enum):
        ROUND = 0
        HEX   = 1
        QUAD  = 2
        TRI   = 3

    @staticmethod
    def fGetSuperShapeRadius(fPhi: float, fM_or_shape: object, fN1: float = 1.0, fN2: float = 1.0, fN3: float = 1.0) -> float:
        if isinstance(fM_or_shape, Uf.ESuperShape):
            e = fM_or_shape
            if e == Uf.ESuperShape.HEX:
                return Uf.fGetSuperShapeRadius(fPhi, 6.0, 2.0, 1.2, 1.2)
            if e == Uf.ESuperShape.QUAD:
                return Uf.fGetSuperShapeRadius(fPhi, 4.0, 20.0, 15.0, 15.0)
            if e == Uf.ESuperShape.TRI:
                return Uf.fGetSuperShapeRadius(fPhi, 3.0, 3.0, 4.0, 4.0)
            return 1.0  # ROUND
        fM = float(fM_or_shape)  # type: ignore[arg-type]
        a  = math.pow(abs(math.cos(0.25 * fM * float(fPhi))), float(fN2))
        b  = math.pow(abs(math.sin(0.25 * fM * float(fPhi))), float(fN3))
        return float(math.pow(a + b, -1.0 / float(fN1)))

    # -- Polygonal shapes -----------------------------------------------------
    class EPolygon(Enum):
        HEX  = 0
        QUAD = 1
        TRI  = 2

    @staticmethod
    def fGetPolygonRadius(fPhi: float, nM_or_polygon: object) -> float:
        if isinstance(nM_or_polygon, Uf.EPolygon):
            e = nM_or_polygon
            if e == Uf.EPolygon.HEX:
                return Uf.fGetPolygonRadius(fPhi, 6)
            if e == Uf.EPolygon.QUAD:
                return Uf.fGetPolygonRadius(fPhi, 4)
            if e == Uf.EPolygon.TRI:
                return Uf.fGetPolygonRadius(fPhi, 3)
            return 1.0
        nM    = int(nM_or_polygon)  # type: ignore[arg-type]
        d_phi = float(fPhi) % (2.0 * math.pi / float(nM))
        return float(math.cos(math.pi / float(nM)) / math.cos(d_phi - math.pi / float(nM)))
