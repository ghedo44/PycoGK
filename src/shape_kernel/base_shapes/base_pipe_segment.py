from __future__ import annotations

import math
from enum import Enum

from picogk import Mesh

from .._types import Vec3, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import LineModulation
from .base_pipe import BasePipe


class BasePipeSegment(BasePipe):
	class EMethod(Enum):
		START_END = "START_END"
		MID_RANGE = "MID_RANGE"

	def __init__(
		self,
		aFrames: Frames,
		fInnerRadius: float,
		fOuterRadius: float,
		oStartOrMidModulation: LineModulation,
		oEndOrRangeModulation: LineModulation,
		eMethod: "BasePipeSegment.EMethod",
		*,
		_length_steps: int,
	) -> None:
		super().__init__(aFrames, fInnerRadius, fOuterRadius, _length_steps=_length_steps)
		self.m_eMethod = eMethod
		if self.m_eMethod == self.EMethod.START_END:
			self.m_oMidModulation = 0.5 * (oStartOrMidModulation + oEndOrRangeModulation)
			self.m_oRangeModulation = oEndOrRangeModulation - oStartOrMidModulation
		else:
			self.m_oMidModulation = oStartOrMidModulation
			self.m_oRangeModulation = oEndOrRangeModulation

	@classmethod
	def from_frame(
		cls,
		oFrame: LocalFrame,
		fLength: float,
		fInnerRadius: float,
		fOuterRadius: float,
		oStartOrMidModulation: LineModulation,
		oEndOrRangeModulation: LineModulation,
		eMethod: "BasePipeSegment.EMethod",
	) -> "BasePipeSegment":
		return cls(
			Frames.from_length(fLength, oFrame),
			fInnerRadius,
			fOuterRadius,
			oStartOrMidModulation,
			oEndOrRangeModulation,
			eMethod,
			_length_steps=5,
		)

	@classmethod
	def from_frames(
		cls,
		aFrames: Frames,
		fInnerRadius: float,
		fOuterRadius: float,
		oStartOrMidModulation: LineModulation,
		oEndOrRangeModulation: LineModulation,
		eMethod: "BasePipeSegment.EMethod",
	) -> "BasePipeSegment":
		return cls(
			aFrames,
			fInnerRadius,
			fOuterRadius,
			oStartOrMidModulation,
			oEndOrRangeModulation,
			eMethod,
			_length_steps=500,
		)

	def mshConstruct(self) -> Mesh:
		mesh = super().mshConstruct()
		self._add_start_surface(mesh)
		self._add_end_surface(mesh)
		return mesh

	def _add_start_surface(self, mesh: Mesh) -> None:
		pr = self._phi_ratio(0)
		for il in range(1, self.m_nLengthSteps):
			l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
			for ir in range(1, self.m_nRadialSteps):
				r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l1, pr, r2), self.vecGetSurfacePoint(l2, pr, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l2, pr, r2), self.vecGetSurfacePoint(l2, pr, r1))

	def _add_end_surface(self, mesh: Mesh) -> None:
		pr = self._phi_ratio(self.m_nPolarSteps - 1)
		for il in range(1, self.m_nLengthSteps):
			l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
			for ir in range(1, self.m_nRadialSteps):
				r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l2, pr, r2), self.vecGetSurfacePoint(l1, pr, r2))
				mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l2, pr, r1), self.vecGetSurfacePoint(l2, pr, r2))

	def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
		spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
		lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
		ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
		phi = self.m_oMidModulation.fGetModulation(fLengthRatio) + (fPhiRatio - 0.5) * self.m_oRangeModulation.fGetModulation(fLengthRatio)
		outer = self.fGetOuterRadius(phi, fLengthRatio)
		inner = self.fGetInnerRadius(phi, fLengthRatio)
		radius = fRadiusRatio * (outer - inner) + inner
		pt = spine + (radius * math.cos(phi)) * lx + (radius * math.sin(phi)) * ly
		return self.m_fnTrafo(as_vec3(pt))


__all__ = ["BasePipeSegment"]
