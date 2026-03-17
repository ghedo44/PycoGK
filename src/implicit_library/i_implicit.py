from __future__ import annotations

from abc import ABC, abstractmethod

from shape_kernel._types import Vector3Like


class IImplicit(ABC):
	@abstractmethod
	def fSignedDistance(self, vecPt: Vector3Like) -> float:
		raise NotImplementedError


__all__ = ["IImplicit"]
