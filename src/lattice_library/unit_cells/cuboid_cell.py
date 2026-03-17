from __future__ import annotations

import numpy as np

from picogk import BBox3
from shape_kernel import Cp, Sh
from shape_kernel._types import Vec3, Vector3Like, as_np3, as_vec3
from .i_unit_cell import IUnitCell


class CuboidCell(IUnitCell):
	def __init__(
		self,
		vecCorner_01: Vector3Like,
		vecCorner_02: Vector3Like,
		vecCorner_03: Vector3Like,
		vecCorner_04: Vector3Like,
		vecCorner_05: Vector3Like,
		vecCorner_06: Vector3Like,
		vecCorner_07: Vector3Like,
		vecCorner_08: Vector3Like,
	) -> None:
		self.m_aCornerPoints: list[Vec3] = [
			as_vec3(vecCorner_01),
			as_vec3(vecCorner_02),
			as_vec3(vecCorner_03),
			as_vec3(vecCorner_04),
			as_vec3(vecCorner_05),
			as_vec3(vecCorner_06),
			as_vec3(vecCorner_07),
			as_vec3(vecCorner_08),
		]

		corners = np.stack([as_np3(vecCorner) for vecCorner in self.m_aCornerPoints], axis=0)
		self.m_vecCentre = as_vec3(np.mean(corners, axis=0))
		self.m_oBBox = BBox3(as_vec3(np.min(corners, axis=0)), as_vec3(np.max(corners, axis=0)))

	def vecGetCellCentre(self) -> Vec3:
		return self.m_vecCentre

	def oGetCellBounding(self) -> BBox3:
		return self.m_oBBox

	def aGetCornerPoints(self) -> list[Vec3]:
		return self.m_aCornerPoints

	def PreviewUnitCell(self) -> None:
		Sh.PreviewLine([self.m_aCornerPoints[0], self.m_aCornerPoints[1], self.m_aCornerPoints[2], self.m_aCornerPoints[3], self.m_aCornerPoints[0]], Cp.clrBlack)
		Sh.PreviewLine([self.m_aCornerPoints[4], self.m_aCornerPoints[5], self.m_aCornerPoints[6], self.m_aCornerPoints[7], self.m_aCornerPoints[4]], Cp.clrBlack)
		Sh.PreviewLine([self.m_aCornerPoints[0], self.m_aCornerPoints[4]], Cp.clrBlack)
		Sh.PreviewLine([self.m_aCornerPoints[1], self.m_aCornerPoints[5]], Cp.clrBlack)
		Sh.PreviewLine([self.m_aCornerPoints[2], self.m_aCornerPoints[6]], Cp.clrBlack)
		Sh.PreviewLine([self.m_aCornerPoints[3], self.m_aCornerPoints[7]], Cp.clrBlack)


__all__ = ["CuboidCell"]