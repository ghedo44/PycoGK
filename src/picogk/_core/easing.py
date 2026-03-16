
from enum import IntEnum
import math


class Easing:
    class EEasing(IntEnum):
        LINEAR = 0
        SINE_IN = 1
        SINE_OUT = 2
        SINE_INOUT = 3
        QUAD_IN = 4
        QUAD_OUT = 5
        QUAD_INOUT = 6
        CUBIC_IN = 7
        CUBIC_OUT = 8
        CUBIC_INOUT = 9

    @staticmethod
    def fEaseSineIn(x: float) -> float:
        return 1.0 - math.cos((x * math.pi) / 2.0)

    @staticmethod
    def fEaseSineOut(x: float) -> float:
        return math.sin((x * math.pi) / 2.0)

    @staticmethod
    def fEaseSineInOut(x: float) -> float:
        return -(math.cos(math.pi * x) - 1.0) / 2.0

    @staticmethod
    def fEaseQuadIn(x: float) -> float:
        return x * x

    @staticmethod
    def fEaseQuadOut(x: float) -> float:
        return 1.0 - (1.0 - x) * (1.0 - x)

    @staticmethod
    def fEaseQuadInOut(x: float) -> float:
        return 2.0 * x * x if x < 0.5 else 1.0 - ((-2.0 * x + 2.0) ** 2.0) / 2.0

    @staticmethod
    def fEaseCubicIn(x: float) -> float:
        return x * x * x

    @staticmethod
    def fEaseCubicOut(x: float) -> float:
        return 1.0 - ((1.0 - x) ** 3.0)

    @staticmethod
    def fEaseCubicInOut(x: float) -> float:
        return 4.0 * x * x * x if x < 0.5 else 1.0 - ((-2.0 * x + 2.0) ** 3.0) / 2.0

    @staticmethod
    def fEasingFunction(x: float, easing: "Easing.EEasing") -> float:
        mapping = {
            Easing.EEasing.LINEAR: lambda y: y,
            Easing.EEasing.SINE_IN: Easing.fEaseSineIn,
            Easing.EEasing.SINE_OUT: Easing.fEaseSineOut,
            Easing.EEasing.SINE_INOUT: Easing.fEaseSineInOut,
            Easing.EEasing.QUAD_IN: Easing.fEaseQuadIn,
            Easing.EEasing.QUAD_OUT: Easing.fEaseQuadOut,
            Easing.EEasing.QUAD_INOUT: Easing.fEaseQuadInOut,
            Easing.EEasing.CUBIC_IN: Easing.fEaseCubicIn,
            Easing.EEasing.CUBIC_OUT: Easing.fEaseCubicOut,
            Easing.EEasing.CUBIC_INOUT: Easing.fEaseCubicInOut,
        }
        try:
            return float(mapping[easing](x))
        except KeyError as exc:
            raise ValueError("Unknown easing function") from exc

