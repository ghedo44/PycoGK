from abc import ABC, abstractmethod

from .._types import Vec3

class ISpline(ABC):
    @abstractmethod
    def aGetPoints(self, nSamples: int | None = 500) -> list[Vec3]:
        raise NotImplementedError

