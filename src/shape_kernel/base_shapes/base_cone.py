from __future__ import annotations

from picogk import Voxels

from ..frames.local_frames import LocalFrame
from ..modulations import SurfaceModulation
from .base_cylinder import BaseCylinder
from .base_shape import BaseShape


class BaseCone(BaseShape):
	def __init__(self, oFrame: LocalFrame, fLength: float, fStartRadius: float, fEndRadius: float) -> None:
		super().__init__()
		self.m_fStartRadius = fStartRadius
		self.m_fEndRadius = fEndRadius
		self.m_oCyl = BaseCylinder.from_frame(oFrame, fLength=fLength)
		self.m_oCyl.SetRadius(SurfaceModulation(self.fGetLinearRadius))

	def fGetLinearRadius(self, fPhi: float, fLengthRatio: float) -> float:
		lr = max(0.0, min(1.0, fLengthRatio))
		return self.m_fStartRadius + lr * (self.m_fEndRadius - self.m_fStartRadius)

	def voxConstruct(self) -> Voxels:
		self.m_oCyl.SetTransformation(self.m_fnTrafo)
		return self.m_oCyl.voxConstruct()

	def oGetBaseCylinder(self) -> BaseCylinder:
		return self.m_oCyl


__all__ = ["BaseCone"]
