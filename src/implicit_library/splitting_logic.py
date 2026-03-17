from __future__ import annotations

from abc import ABC, abstractmethod


class ISplittingLogic(ABC):
	@abstractmethod
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		raise NotImplementedError


class FullWallLogic(ISplittingLogic):
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		return abs(float(fSignedDistance)) - 0.5 * float(fWallThickness)


class FullVoidLogic(ISplittingLogic):
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		return -(abs(float(fSignedDistance)) - 0.5 * float(fWallThickness))


class PositiveHalfWallLogic(ISplittingLogic):
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		fSD = float(fSignedDistance)
		return max(fSD, abs(fSD) - 0.5 * float(fWallThickness))


class NegativeHalfWallLogic(ISplittingLogic):
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		fSD = float(fSignedDistance)
		return max(-fSD, abs(fSD) - 0.5 * float(fWallThickness))


class PositiveVoidLogic(ISplittingLogic):
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		fFinalDist = max(0.0, float(fSignedDistance)) - 0.5 * float(fWallThickness)
		return -fFinalDist


class NegativeVoidLogic(ISplittingLogic):
	def fGetAdvancedSignedDistance(self, fSignedDistance: float, fWallThickness: float) -> float:
		fFinalDist = max(0.0, -float(fSignedDistance)) - 0.5 * float(fWallThickness)
		return -fFinalDist


__all__ = [
	"ISplittingLogic",
	"FullWallLogic",
	"FullVoidLogic",
	"PositiveHalfWallLogic",
	"NegativeHalfWallLogic",
	"PositiveVoidLogic",
	"NegativeVoidLogic",
]