from __future__ import annotations

import math

from picogk import Mesh, Voxels

from .._types import Vec3, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import SurfaceModulation
from .base_shape import BaseShape


class BaseCylinder(BaseShape):
	def __init__(
		self,
		aFrames: Frames,
		fRadius: float,
		*,
		_length_steps: int,
	) -> None:
		super().__init__()
		self.m_aFrames = aFrames
		self.SetLengthSteps(_length_steps)
		self.SetPolarSteps(360)
		self.SetRadialSteps(5)
		self.m_oRadiusModulation = SurfaceModulation(fRadius)

	@classmethod
	def from_frame(
		cls,
		oFrame: LocalFrame,
		fLength: float = 20.0,
		fRadius: float = 10.0,
	) -> "BaseCylinder":
		return cls(Frames.from_length(fLength, oFrame), fRadius, _length_steps=5)

	@classmethod
	def from_frames(
		cls,
		aFrames: Frames,
		fRadius: float = 10.0,
	) -> "BaseCylinder":
		return cls(aFrames, fRadius, _length_steps=500)

	def SetRadius(self, oModulation: SurfaceModulation) -> None:
		self.m_oRadiusModulation = oModulation
		self.SetLengthSteps(500)

	def SetRadialSteps(self, nRadialSteps: int) -> None:
		self.m_nRadialSteps = max(5, int(nRadialSteps))

	def SetPolarSteps(self, nPolarSteps: int) -> None:
		self.m_nPolarSteps = max(5, int(nPolarSteps))

	def SetLengthSteps(self, nLengthSteps: int) -> None:
		self.m_nLengthSteps = max(5, int(nLengthSteps))

	def voxConstruct(self) -> Voxels:
		return Voxels.from_mesh(self.mshConstruct())

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		self._add_top_surface(mesh)
		self._add_outer_mantle(mesh)
		self._add_bottom_surface(mesh)
		return mesh

	def _add_top_surface(self, mesh: Mesh) -> None:
		lr = self._length_ratio(self.m_nLengthSteps - 1)
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for ir in range(1, self.m_nRadialSteps):
				r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
				mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p1, r2), self.vecGetSurfacePoint(lr, p2, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p2, r2), self.vecGetSurfacePoint(lr, p2, r1))

	def _add_bottom_surface(self, mesh: Mesh) -> None:
		lr = self._length_ratio(0)
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for ir in range(1, self.m_nRadialSteps):
				r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
				mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p2, r2), self.vecGetSurfacePoint(lr, p1, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p2, r1), self.vecGetSurfacePoint(lr, p2, r2))

	def _add_outer_mantle(self, mesh: Mesh) -> None:
		rr = self._radius_ratio(self.m_nRadialSteps - 1)
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for il in range(1, self.m_nLengthSteps):
				l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p2, rr), self.vecGetSurfacePoint(l2, p1, rr))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l1, p2, rr), self.vecGetSurfacePoint(l2, p2, rr))

	def _radius_ratio(self, step: int) -> float:
		return (1.0 / float(self.m_nRadialSteps - 1)) * float(step)

	def _phi_ratio(self, step: int) -> float:
		return (1.0 / float(self.m_nPolarSteps - 1)) * float(step)

	def _length_ratio(self, step: int) -> float:
		return (1.0 / float(self.m_nLengthSteps - 1)) * float(step)

	def fGetRadius(self, fPhi: float, fLengthRatio: float) -> float:
		return self.m_oRadiusModulation.fGetModulation(fPhi, fLengthRatio)

	def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
		phi = 2.0 * math.pi * fPhiRatio
		spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
		lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
		ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
		radius = fRadiusRatio * self.fGetRadius(phi, fLengthRatio)
		pt = spine + (radius * math.cos(phi)) * lx + (radius * math.sin(phi)) * ly
		return self.m_fnTrafo(as_vec3(pt))


__all__ = ["BaseCylinder"]
