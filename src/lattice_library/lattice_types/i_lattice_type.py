from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from picogk import Lattice

if TYPE_CHECKING:
	from ..beam_thickness.i_beam_thickness import IBeamThickness
	from ..unit_cells.i_unit_cell import IUnitCell


class ILatticeType(ABC):
	@abstractmethod
	def AddCell(self, oLattice: Lattice, xCell: IUnitCell, xBeamThickness: IBeamThickness, nSubSamples: int) -> None:
		raise NotImplementedError


__all__ = ["ILatticeType"]