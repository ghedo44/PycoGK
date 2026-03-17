from __future__ import annotations

import math

from shape_kernel import BaseBox, BaseLens, BasePipeSegment, LineModulation, LocalFrame, SurfaceModulation
from shape_kernel._types import Vec3

from ..unit_cells import CuboidCell, IUnitCell
from .i_cell_array import ICellArray


class ConformalCellArray(ICellArray):
	def __init__(self, oShape: BaseBox | BaseLens | BasePipeSegment, nNumberInX: int, nNumberInY: int, nNumberInZ: int) -> None:
		self.m_nNumberInX = int(nNumberInX)
		self.m_nNumberInY = int(nNumberInY)
		self.m_nNumberInZ = int(nNumberInZ)
		self.m_aUnitCells: list[IUnitCell] = []

		if isinstance(oShape, BaseBox):
			self._build_from_box(oShape)
		elif isinstance(oShape, BaseLens):
			self._build_from_lens(oShape)
		elif isinstance(oShape, BasePipeSegment):
			self._build_from_segment(oShape)
		else:
			raise TypeError("ConformalCellArray supports BaseBox, BaseLens, and BasePipeSegment only.")

	def _build_from_box(self, oBox: BaseBox) -> None:
		for nX in range(1, self.m_nNumberInX + 1):
			for nY in range(1, self.m_nNumberInY + 1):
				for nZ in range(1, self.m_nNumberInZ + 1):
					self.m_aUnitCells.append(
						CuboidCell(
							self.vecGetInternalBoxPt(oBox, nX - 1, nY - 1, nZ - 1),
							self.vecGetInternalBoxPt(oBox, nX, nY - 1, nZ - 1),
							self.vecGetInternalBoxPt(oBox, nX, nY, nZ - 1),
							self.vecGetInternalBoxPt(oBox, nX - 1, nY, nZ - 1),
							self.vecGetInternalBoxPt(oBox, nX - 1, nY - 1, nZ),
							self.vecGetInternalBoxPt(oBox, nX, nY - 1, nZ),
							self.vecGetInternalBoxPt(oBox, nX, nY, nZ),
							self.vecGetInternalBoxPt(oBox, nX - 1, nY, nZ),
						)
					)

	def _build_from_lens(self, oLens: BaseLens) -> None:
		for nX in range(1, self.m_nNumberInX + 1):
			for nY in range(1, self.m_nNumberInY + 1):
				for nZ in range(1, self.m_nNumberInZ + 1):
					self.m_aUnitCells.append(
						CuboidCell(
							self.vecGetInternalLensPt(oLens, nX - 1, nY - 1, nZ - 1),
							self.vecGetInternalLensPt(oLens, nX, nY - 1, nZ - 1),
							self.vecGetInternalLensPt(oLens, nX, nY, nZ - 1),
							self.vecGetInternalLensPt(oLens, nX - 1, nY, nZ - 1),
							self.vecGetInternalLensPt(oLens, nX - 1, nY - 1, nZ),
							self.vecGetInternalLensPt(oLens, nX, nY - 1, nZ),
							self.vecGetInternalLensPt(oLens, nX, nY, nZ),
							self.vecGetInternalLensPt(oLens, nX - 1, nY, nZ),
						)
					)

	def _build_from_segment(self, oSegment: BasePipeSegment) -> None:
		for nX in range(1, self.m_nNumberInX + 1):
			for nY in range(1, self.m_nNumberInY + 1):
				for nZ in range(1, self.m_nNumberInZ + 1):
					self.m_aUnitCells.append(
						CuboidCell(
							self.vecGetInternalSegmentPt(oSegment, nX - 1, nY - 1, nZ - 1),
							self.vecGetInternalSegmentPt(oSegment, nX, nY - 1, nZ - 1),
							self.vecGetInternalSegmentPt(oSegment, nX, nY, nZ - 1),
							self.vecGetInternalSegmentPt(oSegment, nX - 1, nY, nZ - 1),
							self.vecGetInternalSegmentPt(oSegment, nX - 1, nY - 1, nZ),
							self.vecGetInternalSegmentPt(oSegment, nX, nY - 1, nZ),
							self.vecGetInternalSegmentPt(oSegment, nX, nY, nZ),
							self.vecGetInternalSegmentPt(oSegment, nX - 1, nY, nZ),
						)
					)

	def vecGetInternalBoxPt(self, oBox: BaseBox, nX: int, nY: int, nZ: int) -> Vec3:
		fLengthRatio = float(nZ) / float(self.m_nNumberInZ)
		fWidthRatio = (2.0 * float(nX) / float(self.m_nNumberInX)) - 1.0
		fDepthRatio = (2.0 * float(nY) / float(self.m_nNumberInY)) - 1.0
		return oBox.vecGetSurfacePoint(fWidthRatio, fDepthRatio, fLengthRatio)

	def vecGetInternalLensPt(self, oLens: BaseLens, nX: int, nY: int, nZ: int) -> Vec3:
		fPhiRatio = float(nZ) / float(self.m_nNumberInZ)
		fHeightRatio = float(nX) / float(self.m_nNumberInX)
		fRadiusRatio = float(nY) / float(self.m_nNumberInY)
		return oLens.vecGetSurfacePoint(fHeightRatio, fPhiRatio, fRadiusRatio)

	def vecGetInternalSegmentPt(self, oSegment: BasePipeSegment, nX: int, nY: int, nZ: int) -> Vec3:
		fPhiRatio = float(nZ) / float(self.m_nNumberInZ)
		fLengthRatio = float(nX) / float(self.m_nNumberInX)
		fRadiusRatio = float(nY) / float(self.m_nNumberInY)
		return oSegment.vecGetSurfacePoint(fLengthRatio, fPhiRatio, fRadiusRatio)

	def aGetUnitCells(self) -> list[IUnitCell]:
		return self.m_aUnitCells


class ConformalShowcaseShapes:
	@staticmethod
	def oGetBox_01() -> BaseBox:
		oBox = BaseBox.from_frame(LocalFrame(), fLength=100.0)
		oBox.SetDepth(LineModulation(ConformalShowcaseShapes.fGetDepth_01))
		oBox.SetWidth(LineModulation(ConformalShowcaseShapes.fGetWidth_01))
		return oBox

	@staticmethod
	def fGetWidth_01(fLengthRatio: float) -> float:
		return 60.0 + 20.0 * math.cos(5.0 * float(fLengthRatio))

	@staticmethod
	def fGetDepth_01(fLengthRatio: float) -> float:
		return 80.0 - 40.0 * math.cos(3.0 * float(fLengthRatio))

	@staticmethod
	def oGetLens_01() -> BaseLens:
		oLens = BaseLens(LocalFrame(), 1.0, 20.0, 40.0)
		oLens.SetHeight(
			SurfaceModulation(ConformalShowcaseShapes.fGetLowerLens_01),
			SurfaceModulation(ConformalShowcaseShapes.fGetUpperLens_01),
		)
		return oLens

	@staticmethod
	def fGetLowerLens_01(fPhi: float, fRadiusRatio: float) -> float:
		return -20.0 + 20.0 * float(fRadiusRatio)

	@staticmethod
	def fGetUpperLens_01(fPhi: float, fRadiusRatio: float) -> float:
		return 20.0 + 5.0 * math.cos(2.0 * float(fRadiusRatio))

	@staticmethod
	def oGetSegment_01() -> BasePipeSegment:
		oSegment = BasePipeSegment.from_frame(
			LocalFrame(),
			100.0,
			20.0,
			40.0,
			LineModulation(0.0),
			LineModulation(ConformalShowcaseShapes.fGetPhiRange_01),
			BasePipeSegment.EMethod.MID_RANGE,
		)
		oSegment.SetRadius(
			SurfaceModulation(ConformalShowcaseShapes.fGetInnerRadius_01),
			SurfaceModulation(ConformalShowcaseShapes.fGetOuterRadius_01),
		)
		return oSegment

	@staticmethod
	def fGetPhiRange_01(fLengthRatio: float) -> float:
		return math.pi - 0.45 * math.pi * math.cos(3.0 * float(fLengthRatio))

	@staticmethod
	def fGetInnerRadius_01(fPhi: float, fLengthRatio: float) -> float:
		return 20.0 + 10.0 * float(fLengthRatio)

	@staticmethod
	def fGetOuterRadius_01(fPhi: float, fLengthRatio: float) -> float:
		return ConformalShowcaseShapes.fGetInnerRadius_01(fPhi, fLengthRatio) + 15.0 + 5.0 * math.cos(4.0 * float(fPhi))


__all__ = ["ConformalCellArray", "ConformalShowcaseShapes"]