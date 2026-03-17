from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..unit_cells.i_unit_cell import IUnitCell


class ICellArray(ABC):
	@abstractmethod
	def aGetUnitCells(self) -> list[IUnitCell]:
		raise NotImplementedError


__all__ = ["ICellArray"]