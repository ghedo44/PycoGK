from __future__ import annotations

import math

from picogk import Mesh, Voxels

from .._types import Vec3, as_np3, as_vec3
from ..frames.local_frames import LocalFrame
from ..modulations import SurfaceModulation
from .base_shape import BaseShape


class BaseLens(BaseShape):
	def __init__(self, oFrame: LocalFrame, fHeight: float, fInnerRadius: float, fOuterRadius: float) -> None:
		super().__init__()
		self.m_oFrame = oFrame
		self.SetRadialSteps(5)
		self.SetPolarSteps(360)
		self.SetHeightSteps(5)
		self.m_fInnerRadius = fInnerRadius
		self.m_fOuterRadius = fOuterRadius
		self.m_oLowerModulation = SurfaceModulation(0.0)
		self.m_oUpperModulation = SurfaceModulation(fHeight)

	def SetHeight(self, oLowerModulation: SurfaceModulation, oUpperModulation: SurfaceModulation) -> None:
		self.m_oLowerModulation = oLowerModulation
		self.m_oUpperModulation = oUpperModulation
		self.SetRadialSteps(500)

	def SetRadialSteps(self, nRadialSteps: int) -> None:
		self.m_nRadialSteps = max(5, int(nRadialSteps))

	def SetPolarSteps(self, nPolarSteps: int) -> None:
		self.m_nPolarSteps = max(5, int(nPolarSteps))

	def SetHeightSteps(self, nHeightSteps: int) -> None:
		self.m_nHeightSteps = max(5, int(nHeightSteps))

	def voxConstruct(self) -> Voxels:
		return Voxels.from_mesh(self.mshConstruct())

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for ir in range(1, self.m_nRadialSteps):
				r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
				mesh.nAddTriangle(self.vecGetSurfacePoint(1.0, p1, r1), self.vecGetSurfacePoint(1.0, p1, r2), self.vecGetSurfacePoint(1.0, p2, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(1.0, p1, r1), self.vecGetSurfacePoint(1.0, p2, r2), self.vecGetSurfacePoint(1.0, p2, r1))
				mesh.nAddTriangle(self.vecGetSurfacePoint(0.0, p1, r1), self.vecGetSurfacePoint(0.0, p2, r2), self.vecGetSurfacePoint(0.0, p1, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(0.0, p1, r1), self.vecGetSurfacePoint(0.0, p2, r1), self.vecGetSurfacePoint(0.0, p2, r2))
			for ih in range(1, self.m_nHeightSteps):
				h1, h2 = self._height_ratio(ih - 1), self._height_ratio(ih)
				r_in = self._radius_ratio(0)
				r_out = self._radius_ratio(self.m_nRadialSteps - 1)
				mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_in), self.vecGetSurfacePoint(h2, p1, r_in), self.vecGetSurfacePoint(h2, p2, r_in))
				mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_in), self.vecGetSurfacePoint(h2, p2, r_in), self.vecGetSurfacePoint(h1, p2, r_in))
				mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_out), self.vecGetSurfacePoint(h2, p2, r_out), self.vecGetSurfacePoint(h2, p1, r_out))
				mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_out), self.vecGetSurfacePoint(h1, p2, r_out), self.vecGetSurfacePoint(h2, p2, r_out))
		return mesh

	def _radius_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nRadialSteps - 1)) * float(step)

	def _phi_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nPolarSteps - 1)) * float(step)

	def _height_ratio(self, step: int) -> float:
		return (1.0 / (self.m_nHeightSteps - 1)) * float(step)

	def fGetHeight(self, fHeightRatio: float, fPhi: float, fRadiusRatio: float) -> float:
		low = self.m_oLowerModulation.fGetModulation(fPhi, fRadiusRatio)
		high = self.m_oUpperModulation.fGetModulation(fPhi, fRadiusRatio)
		return low + fHeightRatio * (high - low)

	def vecGetSurfacePoint(self, fHeightRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
		phi = 2.0 * math.pi * fPhiRatio
		radius = (self.m_fOuterRadius - self.m_fInnerRadius) * fRadiusRatio + self.m_fInnerRadius
		z = self.fGetHeight(fHeightRatio, phi, fRadiusRatio)
		x = radius * math.cos(phi)
		y = radius * math.sin(phi)
		pos = as_np3(self.m_oFrame.vecGetPosition())
		lx = as_np3(self.m_oFrame.vecGetLocalX())
		ly = as_np3(self.m_oFrame.vecGetLocalY())
		lz = as_np3(self.m_oFrame.vecGetLocalZ())
		return self.m_fnTrafo(as_vec3(pos + x * lx + y * ly + z * lz))


__all__ = ["BaseLens"]
