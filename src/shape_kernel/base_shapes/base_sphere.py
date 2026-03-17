from __future__ import annotations

import math

from picogk import Mesh, Voxels

from .._types import Vec3, as_np3, as_vec3
from ..frames.local_frames import LocalFrame
from ..modulations import SurfaceModulation
from .base_shape import BaseShape


class BaseSphere(BaseShape):
	def __init__(self, oFrame: LocalFrame, fRadius: float = 10.0) -> None:
		super().__init__()
		self.SetAzimuthalSteps(360)
		self.SetPolarSteps(180)
		self.m_oFrame = oFrame
		self.m_oRadiusModulation = SurfaceModulation(fRadius)

	def SetRadius(self, oModulation: SurfaceModulation) -> None:
		self.m_oRadiusModulation = oModulation

	def SetAzimuthalSteps(self, nAzimuthalSteps: int) -> None:
		self.m_nAzimuthalSteps = int(nAzimuthalSteps)

	def SetPolarSteps(self, nPolarSteps: int) -> None:
		self.m_nPolarSteps = int(nPolarSteps)

	def voxConstruct(self) -> Voxels:
		return Voxels.from_mesh(self.mshConstruct())

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		rr = 1.0
		for it in range(1, self.m_nAzimuthalSteps):
			t1 = (1.0 / (self.m_nAzimuthalSteps - 1)) * (it - 1)
			t2 = (1.0 / (self.m_nAzimuthalSteps - 1)) * it
			for ip in range(1, self.m_nPolarSteps):
				p1 = (1.0 / (self.m_nPolarSteps - 1)) * (ip - 1)
				p2 = (1.0 / (self.m_nPolarSteps - 1)) * ip
				mesh.nAddTriangle(self.vecGetSurfacePoint(t1, p1, rr), self.vecGetSurfacePoint(t2, p1, rr), self.vecGetSurfacePoint(t2, p2, rr))
				mesh.nAddTriangle(self.vecGetSurfacePoint(t1, p1, rr), self.vecGetSurfacePoint(t2, p2, rr), self.vecGetSurfacePoint(t1, p2, rr))
		return mesh

	def fGetRadius(self, fPhi: float, fLengthRatio: float) -> float:
		return self.m_oRadiusModulation.fGetModulation(fPhi, fLengthRatio)

	def vecGetSurfacePoint(self, fPhiRatio: float, fThetaRatio: float, fRadiusRatio: float) -> Vec3:
		theta = math.pi * fThetaRatio
		phi = 2.0 * math.pi * fPhiRatio
		fRadius = fRadiusRatio * self.fGetRadius(phi, theta)
		fx = fRadius * math.cos(phi) * math.sin(theta)
		fy = fRadius * math.sin(phi) * math.sin(theta)
		fz = fRadius * math.cos(theta)
		pos = as_np3(self.m_oFrame.vecGetPosition())
		lx = as_np3(self.m_oFrame.vecGetLocalX())
		ly = as_np3(self.m_oFrame.vecGetLocalY())
		lz = as_np3(self.m_oFrame.vecGetLocalZ())
		return self.m_fnTrafo(as_vec3(pos + fx * lx + fy * ly + fz * lz))


__all__ = ["BaseSphere"]
