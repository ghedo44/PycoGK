from __future__ import annotations

import math

import numpy as np
from picogk import Mesh, Voxels

from .._types import Vec3, as_np3, as_vec3
from ..frames.local_frames import LocalFrame
from ..modulations import SurfaceModulation
from .base_shape import BaseShape


class BaseRing(BaseShape):
	def __init__(self, oFrame: LocalFrame, fRingRadius: float = 50.0, fRadius: float = 5.0) -> None:
		super().__init__()
		self.SetRadialSteps(360)
		self.SetPolarSteps(360)
		self.m_oFrame = oFrame
		self.m_fRingRadius = fRingRadius
		self.m_oRadiusModulation = SurfaceModulation(fRadius)

	def SetRadius(self, oModulation: SurfaceModulation) -> None:
		self.m_oRadiusModulation = oModulation

	def SetRadialSteps(self, nRadialSteps: int) -> None:
		self.m_nRadialSteps = max(5, int(nRadialSteps))

	def SetPolarSteps(self, nPolarSteps: int) -> None:
		self.m_nPolarSteps = max(5, int(nPolarSteps))

	def voxConstruct(self) -> Voxels:
		return Voxels.from_mesh(self.mshConstruct())

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		rr = 1.0
		for ia in range(self.m_nRadialSteps):
			lower = ia - 1
			if lower < 0:
				lower += self.m_nRadialSteps
			a1 = self._alpha_ratio(lower)
			a2 = self._alpha_ratio(ia)
			for ip in range(1, self.m_nPolarSteps):
				p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
				mesh.nAddTriangle(self.vecGetSurfacePoint(a1, p1, rr), self.vecGetSurfacePoint(a2, p1, rr), self.vecGetSurfacePoint(a2, p2, rr))
				mesh.nAddTriangle(self.vecGetSurfacePoint(a1, p1, rr), self.vecGetSurfacePoint(a2, p2, rr), self.vecGetSurfacePoint(a1, p2, rr))
		return mesh

	def _alpha_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nRadialSteps - 1)) * float(step)

	def _phi_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nPolarSteps - 1)) * float(step)

	def fGetRadius(self, fPhi: float, fLengthRatio: float) -> float:
		return self.m_oRadiusModulation.fGetModulation(fPhi, fLengthRatio)

	def vecGetSurfacePoint(self, fAlphaRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
		alpha = 2.0 * math.pi * fAlphaRatio
		phi = 2.0 * math.pi * fPhiRatio
		x = self.m_fRingRadius * math.cos(alpha)
		y = self.m_fRingRadius * math.sin(alpha)
		frame_pos = as_np3(self.m_oFrame.vecGetPosition())
		frame_x = as_np3(self.m_oFrame.vecGetLocalX())
		frame_y = as_np3(self.m_oFrame.vecGetLocalY())
		frame_z = as_np3(self.m_oFrame.vecGetLocalZ())
		spine = frame_pos + x * frame_x + y * frame_y
		local_x = spine - frame_pos
		norm = float(np.linalg.norm(local_x))
		if norm > 1e-12:
			local_x = local_x / norm
		local_y = frame_z
		radius = fRadiusRatio * self.fGetRadius(phi, alpha)
		pt = spine + (radius * math.cos(phi)) * local_x + (radius * math.sin(phi)) * local_y
		return self.m_fnTrafo(as_vec3(pt))


__all__ = ["BaseRing"]
