from __future__ import annotations

import math

import numpy as np
from picogk import Lattice

from .._types import Vector3Like, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from .lattice_pipe import LatticePipe


class LatticeManifold(LatticePipe):
	def __init__(
		self,
		aFrames: Frames,
		fRadius: float,
		fMaxOverhangAngle: float,
		bExtendBothSides: bool,
		fMinPrintableRadius: float,
		*,
		_length_steps: int,
	) -> None:
		super().__init__(aFrames, fRadius, _length_steps=_length_steps)
		self.m_fMaxPrintableRadius = fMinPrintableRadius
		self.m_fLimitAngle = fMaxOverhangAngle
		self.m_bExtendBothSides = bExtendBothSides

	@classmethod
	def from_frame(
		cls,
		oFrame: LocalFrame,
		fLength: float = 20.0,
		fRadius: float = 10.0,
		fMaxOverhangAngle: float = 45.0,
		bExtendBothSides: bool = False,
		fMinPrintableRadius: float = 0.1,
	) -> "LatticeManifold":
		return cls(
			Frames.from_length(fLength, oFrame),
			fRadius,
			fMaxOverhangAngle,
			bExtendBothSides,
			fMinPrintableRadius,
			_length_steps=100,
		)

	@classmethod
	def from_frames(
		cls,
		aFrames: Frames,
		fRadius: float = 10.0,
		fMaxOverhangAngle: float = 45.0,
		bExtendBothSides: bool = False,
		fMinPrintableRadius: float = 0.1,
	) -> "LatticeManifold":
		return cls(
			aFrames,
			fRadius,
			fMaxOverhangAngle,
			bExtendBothSides,
			fMinPrintableRadius,
			_length_steps=500,
		)

	def latConstruct(self) -> Lattice:
		lattice = Lattice()
		for iz in range(self.m_nLengthSteps):
			lr = (1.0 / self.m_nLengthSteps) * iz
			p = self.vecGetSpinePoint(lr)
			beam = self.fGetRadius(lr)
			lattice.add_beam(p, p, beam, beam)
			self._add_tip(lattice, p, beam, True)
			if self.m_bExtendBothSides:
				self._add_tip(lattice, p, beam, False)
		return lattice

	def _add_tip(self, lattice: Lattice, vecPt: Vector3Like, fBeam: float, bZPositive: bool = True) -> None:
		half_alpha = 90.0 - self.m_fLimitAngle
		r = fBeam
		h = r * (1.0 - math.cos(math.radians(half_alpha)))
		s = 2.0 * r * math.sin(math.radians(half_alpha))
		tip_length = math.tan(math.radians(half_alpha)) * (0.5 * s - self.m_fMaxPrintableRadius)
		p = as_np3(vecPt)

		if bZPositive:
			mid = p + (r - h) * np.array([0.0, 0.0, 1.0], dtype=np.float64)
			tip = mid + tip_length * np.array([0.0, 0.0, 1.0], dtype=np.float64)
		else:
			mid = p - (r - h) * np.array([0.0, 0.0, 1.0], dtype=np.float64)
			tip = mid - tip_length * np.array([0.0, 0.0, 1.0], dtype=np.float64)

		lattice.add_beam(as_vec3(mid), as_vec3(tip), 0.5 * s, self.m_fMaxPrintableRadius, False)


__all__ = ["LatticeManifold"]
