from __future__ import annotations

import math
import random
from enum import Enum
from typing import Any, cast

from .._types import Vec3, Vector3Like, as_np3, as_vec3


class Uf:
	_random: random.Random = random.Random()
	_bspline: object | None = None

	@classmethod
	def _get_bspline(cls) -> object:
		if cls._bspline is None:
			from ..splines import ControlPointSpline

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
		pt = cast(Any, bspline).vecGetPointAt(float(fS))
		ratio = float(pt[0])
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
		t = Uf._fGetNormalizedTangensHyperbolicus(fS, fTransitionS, fSmooth)
		p1 = as_np3(vecPt1)
		p2 = as_np3(vecPt2)
		return as_vec3(p1 * (1.0 - t) + p2 * t)

	@staticmethod
	def fLimitValue(fValue: float, fMin: float, fMax: float) -> float:
		return max(float(fMin), min(float(fMax), float(fValue)))

	@staticmethod
	def fGetRandomGaussian(fMean: float, fStdDev: float, oRandom: random.Random | None = None) -> float:
		rng = oRandom if oRandom is not None else Uf._random
		x1 = max(1.0 - rng.random(), 1e-300)
		x2 = 1.0 - rng.random()
		y1 = float(math.sqrt(-2.0 * math.log(x1)) * math.cos(2.0 * math.pi * x2))
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
		r_out = float(fOuterRadius)
		golden = math.pi * (1.0 + math.sqrt(5.0))
		for i in range(int(nSamples)):
			k = i + 0.5
			r = math.sqrt(k / float(nSamples))
			phi = golden * k
			pts.append((r_out * r * math.cos(phi), r_out * r * math.sin(phi), 0.0))
		return pts

	@staticmethod
	def aGetFibonacciSpherePoints(fOuterRadius: float, nSamples: int) -> list[Vec3]:
		pts: list[Vec3] = []
		r_out = float(fOuterRadius)
		golden = math.pi * (1.0 + math.sqrt(5.0))
		for i in range(int(nSamples)):
			k = i + 0.5
			phi_a = math.acos(1.0 - 2.0 * k / float(nSamples))
			theta = golden * k
			pts.append(
				(
					r_out * math.cos(theta) * math.sin(phi_a),
					r_out * math.sin(theta) * math.sin(phi_a),
					r_out * math.cos(phi_a),
				)
			)
		return pts

	class ESuperShape(Enum):
		ROUND = 0
		HEX = 1
		QUAD = 2
		TRI = 3

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
			return 1.0
		fM = float(cast(float, fM_or_shape))
		a = math.pow(abs(math.cos(0.25 * fM * float(fPhi))), float(fN2))
		b = math.pow(abs(math.sin(0.25 * fM * float(fPhi))), float(fN3))
		return float(math.pow(a + b, -1.0 / float(fN1)))

	class EPolygon(Enum):
		HEX = 0
		QUAD = 1
		TRI = 2

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
		nM = int(cast(int, nM_or_polygon))
		d_phi = float(fPhi) % (2.0 * math.pi / float(nM))
		return float(math.cos(math.pi / float(nM)) / math.cos(d_phi - math.pi / float(nM)))


__all__ = ["Uf"]
