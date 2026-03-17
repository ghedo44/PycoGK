from __future__ import annotations

from typing import Callable

from picogk import Image

from .._types import Vec3, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import LineModulation, SurfaceModulation
from .base_box import BaseBox
from .base_shape import BaseShape


class BaseLogoBox(BaseBox):
	def __init__(self, oFrame: LocalFrame, fLength: float, fRefWidth: float, oImage: Image, oMappingFunc: Callable[[float], float]) -> None:
		BaseShape.__init__(self)
		self.m_aFrames = Frames.from_length(fLength, oFrame)
		self.m_nWidthSteps = int(oImage.nWidth)
		self.m_nDepthSteps = int(oImage.nHeight)
		self.m_nLengthSteps = 5
		fDepth = (float(oImage.nHeight) / float(oImage.nWidth)) * fRefWidth
		self.m_oWidthModulation = LineModulation(fRefWidth)
		self.m_oDepthModulation = LineModulation(fDepth)
		self.m_oTopModulation = SurfaceModulation.from_image(oImage, oMappingFunc)

	def fGetWidth(self) -> float:
		return self.m_oWidthModulation.m_fConstValue

	def fGetDepth(self) -> float:
		return self.m_oDepthModulation.m_fConstValue

	def vecGetSurfacePoint(self, fWidthRatio: float, fDepthRatio: float, fLengthRatio: float) -> Vec3:
		spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
		lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
		ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
		lz = as_np3(self.m_aFrames.vecGetLocalZAlongLength(fLengthRatio))

		x = 0.5 * fWidthRatio * self.m_oWidthModulation.m_fConstValue
		y = 0.5 * fDepthRatio * self.m_oDepthModulation.m_fConstValue
		pt = spine + x * lx + y * ly

		if abs(fLengthRatio - 1.0) < 0.0003:
			img_w = 1.0 - (0.5 + 0.5 * fWidthRatio)
			img_h = 1.0 - (0.5 + 0.5 * fDepthRatio)
			dz = self.m_oTopModulation.fGetModulation(img_w, img_h)
			pt = pt + dz * lz

		return self.m_fnTrafo(as_vec3(pt))


__all__ = ["BaseLogoBox"]
