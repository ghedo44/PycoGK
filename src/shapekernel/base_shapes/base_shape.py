from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from picogk import Voxels

from .._types import Vec3


class BaseShape(ABC):
	fnVertexTransformation = Callable[[Vec3], Vec3]

	def __init__(self) -> None:
		self.m_fnTrafo: BaseShape.fnVertexTransformation = self.vecNoTransform

	def SetTransformation(self, fnTrafo: fnVertexTransformation) -> None:
		self.m_fnTrafo = fnTrafo

	def set_transformation(self, fnTrafo: fnVertexTransformation) -> None:
		self.SetTransformation(fnTrafo)

	@staticmethod
	def vecNoTransform(vecPt: Vec3) -> Vec3:
		return vecPt

	@abstractmethod
	def voxConstruct(self) -> Voxels:
		raise NotImplementedError


__all__ = ["BaseShape"]
