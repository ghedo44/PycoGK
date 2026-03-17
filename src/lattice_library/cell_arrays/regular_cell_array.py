from __future__ import annotations

import random

from picogk import Voxels
from shape_kernel._types import Vec3, as_vec3

from .._helpers import _coerce_bbox3
from ..unit_cells import CuboidCell, IUnitCell
from .i_cell_array import ICellArray


class RegularCellArray(ICellArray):
	def __init__(self, oVoxels: Voxels, dX: float, dY: float, dZ: float, fNoiseLevel: float = 0.0) -> None:
		self.m_dX = float(dX)
		self.m_dY = float(dY)
		self.m_dZ = float(dZ)
		self.m_fNoiseLevel = min(max(abs(float(fNoiseLevel)), 0.0), 0.3)
		self.m_oRandom = random.Random()
		self.m_oVoxels = oVoxels
		_, oBBox = self.m_oVoxels.CalculateProperties()
		bbox = _coerce_bbox3(oBBox)

		self.m_aUnitCells: list[IUnitCell] = []
		fX = float(bbox.vecMin.x - 0.5 * self.m_dX)
		fXEnd = float(bbox.vecMax.x + 0.5 * self.m_dX)
		while fX <= fXEnd:
			fY = float(bbox.vecMin.y - 0.5 * self.m_dY)
			fYEnd = float(bbox.vecMax.y + 0.5 * self.m_dY)
			while fY <= fYEnd:
				fZ = float(bbox.vecMin.z - 0.5 * self.m_dZ)
				fZEnd = float(bbox.vecMax.z + 0.5 * self.m_dZ)
				while fZ <= fZEnd:
					self.m_aUnitCells.append(
						CuboidCell(
							self.vecGetCorner(fX, fY, fZ),
							self.vecGetCorner(fX, fY + self.m_dY, fZ),
							self.vecGetCorner(fX + self.m_dX, fY + self.m_dY, fZ),
							self.vecGetCorner(fX + self.m_dX, fY, fZ),
							self.vecGetCorner(fX, fY, fZ + self.m_dZ),
							self.vecGetCorner(fX, fY + self.m_dY, fZ + self.m_dZ),
							self.vecGetCorner(fX + self.m_dX, fY + self.m_dY, fZ + self.m_dZ),
							self.vecGetCorner(fX + self.m_dX, fY, fZ + self.m_dZ),
						)
					)
					fZ += self.m_dZ
				fY += self.m_dY
			fX += self.m_dX

	def vecGetCorner(self, fX: float, fY: float, fZ: float) -> Vec3:
		iX = int(fX * 1000.0)
		iY = int(fY * 1000.0)
		iZ = int(fZ * 1000.0)
		iIndex = iX * iY * iZ
		self.m_oRandom = random.Random(iIndex)
		vecNoise = self.vecGetNoise()
		return as_vec3((fX + vecNoise[0], fY + vecNoise[1], fZ + vecNoise[2]))

	def vecGetNoise(self) -> Vec3:
		return (
			self.fGetRandomLinear(-self.m_fNoiseLevel * self.m_dX, self.m_fNoiseLevel * self.m_dX),
			self.fGetRandomLinear(-self.m_fNoiseLevel * self.m_dY, self.m_fNoiseLevel * self.m_dY),
			self.fGetRandomLinear(-self.m_fNoiseLevel * self.m_dZ, self.m_fNoiseLevel * self.m_dZ),
		)

	def fGetRandomLinear(self, fMin: float, fMax: float, oRandom: random.Random | None = None) -> float:
		rng = self.m_oRandom if oRandom is None else oRandom
		return float(fMin) + (float(fMax) - float(fMin)) * rng.random()

	def aGetUnitCells(self) -> list[IUnitCell]:
		return self.m_aUnitCells


__all__ = ["RegularCellArray"]