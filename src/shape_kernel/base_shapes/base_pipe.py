from __future__ import annotations

import math

from picogk import Mesh

from .._types import Vec3, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import SurfaceModulation
from .base_cylinder import BaseCylinder


class BasePipe(BaseCylinder):
	def __init__(
		self,
		aFrames: Frames,
		fInnerRadius: float,
		fOuterRadius: float,
		*,
		_length_steps: int,
	) -> None:
		super().__init__(aFrames, fOuterRadius, _length_steps=_length_steps)
		self.m_oInnerRadiusModulation = SurfaceModulation(fInnerRadius)
		self.m_oOuterRadiusModulation = SurfaceModulation(fOuterRadius)

	@classmethod
	def from_frame(
		cls,
		oFrame: LocalFrame,
		fLength: float = 20.0,
		fInnerRadius: float = 10.0,
		fOuterRadius: float = 20.0,
	) -> "BasePipe":
		return cls(Frames.from_length(fLength, oFrame), fInnerRadius, fOuterRadius, _length_steps=5)

	@classmethod
	def from_frames(
		cls,
		aFrames: Frames,
		fInnerRadius: float = 10.0,
		fOuterRadius: float = 20.0,
	) -> "BasePipe":
		return cls(aFrames, fInnerRadius, fOuterRadius, _length_steps=500)

	def SetRadius(self, oInnerRadiusOverCylinder: SurfaceModulation, oOuterRadiusOverCylinder: SurfaceModulation) -> None:
		self.m_oInnerRadiusModulation = oInnerRadiusOverCylinder
		self.m_oOuterRadiusModulation = oOuterRadiusOverCylinder
		self.SetLengthSteps(500)

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		self._add_top_surface(mesh)
		self._add_bottom_surface(mesh)
		self._add_inner_mantle(mesh)
		self._add_outer_mantle(mesh)
		return mesh

	def _add_outer_mantle(self, mesh: Mesh) -> None:
		rr = self._radius_ratio(self.m_nRadialSteps - 1)
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for il in range(1, self.m_nLengthSteps):
				l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p2, rr), self.vecGetSurfacePoint(l2, p1, rr))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l1, p2, rr), self.vecGetSurfacePoint(l2, p2, rr))

	def _add_inner_mantle(self, mesh: Mesh) -> None:
		rr = self._radius_ratio(0)
		for ip in range(1, self.m_nPolarSteps):
			p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
			for il in range(1, self.m_nLengthSteps):
				l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p1, rr), self.vecGetSurfacePoint(l2, p2, rr))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p2, rr), self.vecGetSurfacePoint(l1, p2, rr))

	def fGetInnerRadius(self, fPhi: float, fLengthRatio: float) -> float:
		return self.m_oInnerRadiusModulation.fGetModulation(fPhi, fLengthRatio)

	def fGetOuterRadius(self, fPhi: float, fLengthRatio: float) -> float:
		return self.m_oOuterRadiusModulation.fGetModulation(fPhi, fLengthRatio)

	def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
		phi = 2.0 * math.pi * fPhiRatio
		spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
		lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
		ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
		outer = self.fGetOuterRadius(phi, fLengthRatio)
		inner = self.fGetInnerRadius(phi, fLengthRatio)
		radius = fRadiusRatio * (outer - inner) + inner
		pt = spine + (radius * math.cos(phi)) * lx + (radius * math.sin(phi)) * ly
		return self.m_fnTrafo(as_vec3(pt))


__all__ = ["BasePipe"]
