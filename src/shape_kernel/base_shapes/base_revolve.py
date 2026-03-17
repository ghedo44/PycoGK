from __future__ import annotations

import math

from picogk import Mesh, Voxels

from .._types import Vec3, as_np3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import GenericContour, LineModulation
from ..utils import VecOperations
from .base_shape import BaseShape


class BaseRevolve(BaseShape):
	def __init__(self, oFrame: LocalFrame, aFrames: Frames, fInwardRadius: float = 3.0, fOutwardRadius: float = 3.0) -> None:
		super().__init__()
		self.m_oFrame = oFrame
		self.m_aFrames = aFrames
		self.SetRadialSteps(100)
		self.SetPolarSteps(360)
		self.SetLengthSteps(500)
		self.m_oOuterRadiusModulation = LineModulation(fOutwardRadius)
		self.m_oInnerRadiusModulation = LineModulation(fInwardRadius)

	def SetRadius(self, oInnerRadiusOverCylinder: LineModulation, oOuterRadiusOverCylinder: LineModulation) -> None:
		self.m_oInnerRadiusModulation = oInnerRadiusOverCylinder
		self.m_oOuterRadiusModulation = oOuterRadiusOverCylinder

	def SetRadialSteps(self, nRadialSteps: int) -> None:
		self.m_nRadialSteps = max(5, int(nRadialSteps))

	def SetPolarSteps(self, nPolarSteps: int) -> None:
		self.m_nPolarSteps = max(5, int(nPolarSteps))

	def SetLengthSteps(self, nLengthSteps: int) -> None:
		self.m_nLengthSteps = max(5, int(nLengthSteps))

	def fGetInnerRadius(self, fLengthRatio: float) -> float:
		return self.m_oInnerRadiusModulation.fGetModulation(fLengthRatio)

	def fGetOuterRadius(self, fLengthRatio: float) -> float:
		return self.m_oOuterRadiusModulation.fGetModulation(fLengthRatio)

	def voxConstruct(self) -> Voxels:
		return Voxels.from_mesh(self.mshConstruct())

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for ir in range(1, self.m_nRadialSteps):
				r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
				l0, lN = self._length_ratio(0), self._length_ratio(self.m_nLengthSteps - 1)
				mesh.nAddTriangle(self.vecGetSurfacePoint(lN, p1, r1), self.vecGetSurfacePoint(lN, p1, r2), self.vecGetSurfacePoint(lN, p2, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(lN, p1, r1), self.vecGetSurfacePoint(lN, p2, r2), self.vecGetSurfacePoint(lN, p2, r1))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l0, p1, r1), self.vecGetSurfacePoint(l0, p2, r2), self.vecGetSurfacePoint(l0, p1, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l0, p1, r1), self.vecGetSurfacePoint(l0, p2, r1), self.vecGetSurfacePoint(l0, p2, r2))
			for il in range(1, self.m_nLengthSteps):
				l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
				r_in = self._radius_ratio(0)
				r_out = self._radius_ratio(self.m_nRadialSteps - 1)
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_in), self.vecGetSurfacePoint(l2, p1, r_in), self.vecGetSurfacePoint(l2, p2, r_in))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_in), self.vecGetSurfacePoint(l2, p2, r_in), self.vecGetSurfacePoint(l1, p2, r_in))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_out), self.vecGetSurfacePoint(l2, p2, r_out), self.vecGetSurfacePoint(l2, p1, r_out))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_out), self.vecGetSurfacePoint(l1, p2, r_out), self.vecGetSurfacePoint(l2, p2, r_out))
		return mesh

	def _radius_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nRadialSteps - 1)) * float(step)

	def _phi_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nPolarSteps - 1)) * float(step)

	def _length_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nLengthSteps - 1)) * float(step)

	def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
		spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
		lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
		phi = (2.0 * math.pi) * fPhiRatio
		outward = self.fGetOuterRadius(fLengthRatio)
		inward = -self.fGetInnerRadius(fLengthRatio)
		radius = fRadiusRatio * (outward - inward) + inward
		pt = spine + radius * lx
		rotated = VecOperations.vecRotateAroundAxis(pt, phi, self.m_oFrame.vecGetLocalZ(), self.m_oFrame.vecGetPosition())
		return self.m_fnTrafo(rotated)

	@staticmethod
	def aGetFramesFromContour(oContour: GenericContour, oFrame: LocalFrame | None = None) -> Frames:
		frame = oFrame if oFrame is not None else LocalFrame()
		samples = 500
		points: list[Vec3] = []
		for i in range(samples):
			lr = float(i) / float(samples - 1)
			z = lr * oContour.m_fTotalLength
			radius = oContour.m_oModulation.fGetModulation(lr)
			rel = (radius, 0.0, z)
			points.append(VecOperations.vecTranslatePointOntoFrame(frame, rel))
		return Frames.from_points_and_frame_type(points, Frames.EFrameType.CYLINDRICAL, 0.5)


__all__ = ["BaseRevolve"]
