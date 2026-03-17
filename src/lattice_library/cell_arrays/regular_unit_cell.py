from __future__ import annotations

import random

from shape_kernel._types import Vec3, as_vec3

from ..unit_cells import CuboidCell, IUnitCell
from .i_cell_array import ICellArray


class RegularUnitCell(ICellArray):
	def __init__(self, dX: float, dY: float, dZ: float, fNoiseLevel: float = 0.0) -> None:
		self.m_dX = float(dX)
		self.m_dY = float(dY)
		self.m_dZ = float(dZ)
		self.m_fNoiseLevel = min(max(abs(float(fNoiseLevel)), 0.0), 0.3)
		self.m_aUnitCells: list[IUnitCell] = []

		fX = -0.5 * self.m_dX
		fY = -0.5 * self.m_dY
		fZ = 0.0
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

	def vecGetCorner(self, fX: float, fY: float, fZ: float) -> Vec3:
		iX = int(fX * 1000.0)
		iY = int(fY * 1000.0)
		iZ = int(fZ * 1000.0)
		iIndex = iX * iY * iZ
		oRandom = random.Random(iIndex)
		vecNoise = self.vecGetNoise(oRandom)
		return as_vec3((fX + vecNoise[0], fY + vecNoise[1], fZ + vecNoise[2]))

	def vecGetNoise(self, oRandom: random.Random) -> Vec3:
		return (
			self.fGetRandomLinear(-self.m_fNoiseLevel * self.m_dX, self.m_fNoiseLevel * self.m_dX, oRandom),
			self.fGetRandomLinear(-self.m_fNoiseLevel * self.m_dY, self.m_fNoiseLevel * self.m_dY, oRandom),
			self.fGetRandomLinear(-self.m_fNoiseLevel * self.m_dZ, self.m_fNoiseLevel * self.m_dZ, oRandom),
		)

	def fGetRandomLinear(self, fMin: float, fMax: float, oRandom: random.Random) -> float:
		return float(fMin) + (float(fMax) - float(fMin)) * oRandom.random()

	def aGetUnitCells(self) -> list[IUnitCell]:
		return self.m_aUnitCells


__all__ = ["RegularUnitCell"]