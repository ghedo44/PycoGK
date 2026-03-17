from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from picogk import Voxels
from shape_kernel._types import Vector3Like

if TYPE_CHECKING:
	from ..unit_cells.i_unit_cell import IUnitCell


class IBeamThickness(ABC):
	@abstractmethod
	def fGetBeamThickness(self, vecPt: Vector3Like) -> float:
		raise NotImplementedError

	@abstractmethod
	def UpdateCell(self, xCell: IUnitCell) -> None:
		raise NotImplementedError

	@abstractmethod
	def SetBoundingVoxels(self, voxBounding: Voxels) -> None:
		raise NotImplementedError


__all__ = ["IBeamThickness"]