from __future__ import annotations

from picogk import Lattice, Voxels

from .._types import Vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import LineModulation
from .base_shape import BaseShape


class LatticePipe(BaseShape):
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
		self.m_oRadiusModulation = LineModulation(fRadius)

	@classmethod
	def from_frame(
		cls,
		oFrame: LocalFrame,
		fLength: float = 20.0,
		fRadius: float = 10.0,
	) -> "LatticePipe":
		return cls(Frames.from_length(fLength, oFrame), fRadius, _length_steps=100)

	@classmethod
	def from_frames(
		cls,
		aFrames: Frames,
		fRadius: float = 10.0,
	) -> "LatticePipe":
		return cls(aFrames, fRadius, _length_steps=500)

	def SetRadius(self, oModulation: LineModulation) -> None:
		self.m_oRadiusModulation = oModulation

	def SetLengthSteps(self, nLengthSteps: int) -> None:
		self.m_nLengthSteps = int(nLengthSteps)

	def voxConstruct(self) -> Voxels:
		return Voxels.from_lattice(self.latConstruct())

	def latConstruct(self) -> Lattice:
		lattice = Lattice()
		for iz in range(1, self.m_nLengthSteps):
			lr0 = (1.0 / self.m_nLengthSteps) * (iz - 1)
			lr1 = (1.0 / self.m_nLengthSteps) * iz
			p0 = self.vecGetSpinePoint(lr0)
			p1 = self.vecGetSpinePoint(lr1)
			b0 = self.fGetRadius(lr0)
			b1 = self.fGetRadius(lr1)
			lattice.add_beam(p0, p1, b0, b1)
		return lattice

	def vecGetSpinePoint(self, fLengthRatio: float) -> Vec3:
		return self.m_fnTrafo(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))

	def fGetRadius(self, fLengthRatio: float) -> float:
		return self.m_oRadiusModulation.fGetModulation(fLengthRatio)


__all__ = ["LatticePipe"]
