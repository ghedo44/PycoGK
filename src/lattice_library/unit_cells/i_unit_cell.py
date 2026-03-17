from __future__ import annotations

from abc import ABC, abstractmethod

from picogk import BBox3
from shape_kernel._types import Vec3


class IUnitCell(ABC):
	@abstractmethod
	def aGetCornerPoints(self) -> list[Vec3]:
		raise NotImplementedError

	@abstractmethod
	def vecGetCellCentre(self) -> tuple[float, float, float]:
		raise NotImplementedError

	@abstractmethod
	def oGetCellBounding(self) -> BBox3:
		raise NotImplementedError

	@abstractmethod
	def PreviewUnitCell(self) -> None:
		raise NotImplementedError


__all__ = ["IUnitCell"]