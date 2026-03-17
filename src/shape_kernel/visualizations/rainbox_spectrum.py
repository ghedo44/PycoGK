from __future__ import annotations

from abc import ABC, abstractmethod

from .._types import Vec3


class ISpectrum(ABC):
	@abstractmethod
	def aGetRawRGBList(self) -> list[Vec3]:
		raise NotImplementedError


class RainboxSpectrum(ISpectrum):
	def aGetRawRGBList(self) -> list[Vec3]:
		return [
			(0.0, 0.0, 255.0),
			(0.0, 255.0, 0.0),
			(255.0, 255.0, 0.0),
			(255.0, 130.0, 0.0),
			(255.0, 0.0, 0.0),
		]


__all__ = ["ISpectrum", "RainboxSpectrum"]
