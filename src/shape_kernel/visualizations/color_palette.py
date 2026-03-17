
from typing import Optional
import random

def _hex_to_rgba(hex_value: str) -> tuple[float, float, float, float]:
    value = hex_value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("Expected RGB hex color")
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return (r, g, b, 1.0)

class Cp:
    clrBlack = _hex_to_rgba("#000000")
    clrRacingGreen = _hex_to_rgba("#065c35")
    clrGreen = _hex_to_rgba("#00b800")
    clrBillie = _hex_to_rgba("#02f70b")
    clrLemongrass = _hex_to_rgba("#b8e031")
    clrYellow = _hex_to_rgba("#fcd808")
    clrWarning = _hex_to_rgba("#fc6608")
    clrRed = _hex_to_rgba("#ff0000")
    clrRuby = _hex_to_rgba("#b0002c")
    clrOrchid = _hex_to_rgba("#c72483")
    clrPitaya = _hex_to_rgba("#fa2a88")
    clrBubblegum = _hex_to_rgba("#ff66ce")
    clrLavender = _hex_to_rgba("#c966ff")
    clrGray = _hex_to_rgba("#bdbdbd")
    clrRock = _hex_to_rgba("#6b7178")
    clrCrystal = _hex_to_rgba("#0cc1f7")
    clrFrozen = _hex_to_rgba("#6de2fc")
    clrBlueberry = _hex_to_rgba("#4f0dbf")
    clrBlue = _hex_to_rgba("#4287f5")
    clrToothpaste = _hex_to_rgba("#25e6c9")

    def clrRandom(self, j: Optional[int] = None) -> tuple[float, float, float, float]:
        rng = random.Random(j)
        return (float(rng.random()), float(rng.random()), float(rng.random()), 1.0)
