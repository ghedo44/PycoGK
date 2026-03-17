from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from .._types import Vec3, Vector3Like, as_np3, as_vec3, normalized

if TYPE_CHECKING:
	from ..frames.local_frames import LocalFrame


class VecOperations:
	@staticmethod
	def R(vecPt: Vector3Like) -> float:
		return VecOperations.fGetRadius(vecPt)

	@staticmethod
	def Normalize(vecA: Vector3Like) -> Vec3:
		return as_vec3(normalized(vecA))

	@staticmethod
	def ConvertTo3D(vecFlat: tuple[float, float] | list[float], fZ: float = 0.0) -> Vec3:
		if len(vecFlat) < 2:
			raise ValueError("vecFlat must contain at least 2 coordinates")
		return as_vec3((float(vecFlat[0]), float(vecFlat[1]), float(fZ)))

	@staticmethod
	def ConvertTo2D(vecA: Vector3Like) -> tuple[float, float]:
		vec = as_np3(vecA)
		return (float(vec[0]), float(vec[1]))

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
		phi = VecOperations.fGetPhi(vecPt)
		z = float(as_np3(vecPt)[2])
		return VecOperations.vecGetCylPoint(new_r, phi, z)

	@staticmethod
	def vecUpdatePhi(vecPt: Vector3Like, dPhi: float) -> Vec3:
		r = VecOperations.fGetRadius(vecPt)
		new_phi = VecOperations.fGetPhi(vecPt) + float(dPhi)
		z = float(as_np3(vecPt)[2])
		return VecOperations.vecGetCylPoint(r, new_phi, z)

	@staticmethod
	def vecUpdateZ(vecPt: Vector3Like, dZ: float) -> Vec3:
		return VecOperations.vecSetZ(vecPt, float(as_np3(vecPt)[2]) + float(dZ))

	@staticmethod
	def vecRotateAroundZ(vecPt: Vector3Like, dPhi: float, vecAxisOrigin: Vector3Like | None = None) -> Vec3:
		origin = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(vecAxisOrigin)
		diff = as_np3(vecPt) - origin
		phi = float(math.atan2(float(diff[1]), float(diff[0])))
		r = float(math.sqrt(float(diff[0]) ** 2 + float(diff[1]) ** 2))
		new_diff = np.array([r * math.cos(phi + float(dPhi)), r * math.sin(phi + float(dPhi)), float(diff[2])], dtype=np.float64)
		return as_vec3(new_diff + origin)

	@staticmethod
	def vecExpressPointInFrame(oFrame: LocalFrame, vecPt: Vector3Like) -> Vec3:
		pt = as_np3(vecPt) - as_np3(oFrame.vecGetPosition())
		x = float(np.dot(pt, as_np3(oFrame.vecGetLocalX())))
		y = float(np.dot(pt, as_np3(oFrame.vecGetLocalY())))
		z = float(np.dot(pt, as_np3(oFrame.vecGetLocalZ())))
		return (x, y, z)

	@staticmethod
	def vecTranslateDirectionOntoFrame(oFrame: LocalFrame, vecDir: Vector3Like) -> Vec3:
		origin = np.zeros(3, dtype=np.float64)
		pt1 = as_np3(VecOperations.vecTranslatePointOntoFrame(oFrame, origin))
		pt2 = as_np3(VecOperations.vecTranslatePointOntoFrame(oFrame, as_np3(vecDir)))
		return as_vec3(pt2 - pt1)

	@staticmethod
	def vecGetDirectionToAxis(oFrame: LocalFrame, vecPt: Vector3Like) -> Vec3:
		pt = as_np3(vecPt) - as_np3(oFrame.vecGetPosition())
		lx = as_np3(oFrame.vecGetLocalX())
		ly = as_np3(oFrame.vecGetLocalY())
		d = float(np.dot(pt, lx)) * lx + float(np.dot(pt, ly)) * ly
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
		origin = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(VecOperations.vecSetZ(vecAxisOrigin, 0.0))
		p1 = as_np3(vecPt1)
		p2 = as_np3(vecPt2)
		d_angle = VecOperations.fGetAngleBetween(p1 - origin, p2 - origin)
		side1 = normalized(p1 - origin)
		r_pos = as_np3(VecOperations.vecRotateAroundZ(as_vec3(p1), d_angle))
		r_neg = as_np3(VecOperations.vecRotateAroundZ(as_vec3(p1), -d_angle))
		sense = 1 if float(np.linalg.norm(p2 - r_neg)) >= float(np.linalg.norm(p2 - r_pos)) else -1
		r1 = VecOperations.fGetRadius(as_vec3(p1 - origin))
		r2 = VecOperations.fGetRadius(as_vec3(p2 - origin))
		ir = r1 + float(fRatio) * (r2 - r1)
		iz = float(p1[2]) + float(fRatio) * (float(p2[2]) - float(p1[2]))
		inter = as_np3(VecOperations.vecRotateAroundZ(as_vec3(ir * side1), sense * float(fRatio) * d_angle))
		return as_vec3(as_np3(VecOperations.vecSetZ(as_vec3(inter), iz)) + origin)

	@staticmethod
	def vecSphericalInterpolation(
		vecPt1: Vector3Like,
		vecPt2: Vector3Like,
		fRatio: float,
		vecAxisOrigin: Vector3Like | None = None,
	) -> Vec3:
		origin = np.zeros(3, dtype=np.float64) if vecAxisOrigin is None else as_np3(vecAxisOrigin)
		p1 = as_np3(vecPt1)
		p2 = as_np3(vecPt2)
		d_angle = VecOperations.fGetAngleBetween(p1 - origin, p2 - origin)
		side1 = normalized(p1 - origin)
		normal = np.cross(side1, normalized(p2 - origin))
		r_pos = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(p1), d_angle, as_vec3(normal)))
		r_neg = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(p1), -d_angle, as_vec3(normal)))
		sense = 1 if float(np.linalg.norm(p2 - r_neg)) >= float(np.linalg.norm(p2 - r_pos)) else -1
		r1 = float(np.linalg.norm(p1 - origin))
		r2 = float(np.linalg.norm(p2 - origin))
		ir = r1 + float(fRatio) * (r2 - r1)
		inter = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(ir * side1), sense * float(fRatio) * d_angle, as_vec3(normal)))
		return as_vec3(inter + origin)

	@staticmethod
	def fGetSignedAngleBetween(vecA: Vector3Like, vecB: Vector3Like, vecRefNormal: Vector3Like) -> float:
		a, b, ref = as_np3(vecA), as_np3(vecB), as_np3(vecRefNormal)
		if float(np.dot(a, a)) < 1e-20 or float(np.dot(b, b)) < 1e-20 or float(np.dot(ref, ref)) < 1e-20:
			raise ValueError("Vector3 with zero length.")
		a, b, ref = normalized(a), normalized(b), normalized(ref)
		normal = as_np3(VecOperations.vecFlipForAlignment(np.cross(a, b), ref))
		theta = abs(VecOperations.fGetAngleBetween(a, b))
		r_pos = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(b), theta, as_vec3(normal)))
		r_neg = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(b), -theta, as_vec3(normal)))
		return theta if float(np.dot(a, r_neg)) <= float(np.dot(a, r_pos)) else -theta

	@staticmethod
	def bCheckAlignment(vecDir: Vector3Like, vecTargetDir: Vector3Like) -> bool:
		d = as_np3(vecDir)
		t = as_np3(vecTargetDir)
		return float(np.dot(t, d)) >= float(np.dot(t, -d))


__all__ = ["VecOperations"]
