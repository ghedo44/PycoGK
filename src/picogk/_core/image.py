
from enum import IntEnum
import math
from typing import Sequence

import numpy as np

from _common.types import ColorLike, clamp01
from picogk._extras import _to_rgba


class Image:
    class EType(IntEnum):
        BW = 0
        GRAY = 1
        COLOR = 2

    def __init__(self, width: int, height: int, eType: "Image.EType") -> None:
        if width < 1 or height < 1:
            raise ValueError("Image width and height must be larger than 0")
        self.nWidth = int(width)
        self.nHeight = int(height)
        self.eType = eType

    def clrValue(self, x: int, y: int) -> tuple[float, float, float, float]:
        if not (0 <= x < self.nWidth and 0 <= y < self.nHeight):
            return (0.0, 0.0, 0.0, 1.0)
        data = getattr(self, "_data", None)
        if data is None:
            f = self.fValue(x, y)
            return (f, f, f, 1.0)
        if self.eType == Image.EType.COLOR and len(data.shape) == 3 and data.shape[2] >= 4:
            px = data[y, x, :]
            return (float(px[0]), float(px[1]), float(px[2]), float(px[3]))
        f = float(data[y, x])
        return (f, f, f, 1.0)

    def fValue(self, x: int, y: int) -> float:
        if not (0 <= x < self.nWidth and 0 <= y < self.nHeight):
            return 0.0
        data = getattr(self, "_data", None)
        if data is None:
            clr = self.clrValue(x, y)
            return float((clr[0] + clr[1] + clr[2]) / 3.0)
        if self.eType == Image.EType.COLOR and len(data.shape) == 3 and data.shape[2] >= 3:
            px = data[y, x, :]
            return float((px[0] + px[1] + px[2]) / 3.0)
        if self.eType == Image.EType.BW:
            return 1.0 if bool(data[y, x]) else 0.0
        return float(data[y, x])

    def bValue(self, x: int, y: int) -> bool:
        return self.fValue(x, y) > 0.5

    def SetValue(self, x: int, y: int, value: bool | float | ColorLike) -> None:
        if not (0 <= x < self.nWidth and 0 <= y < self.nHeight):
            return
        data = getattr(self, "_data", None)
        if data is None:
            raise RuntimeError("Image subclass must define _data or override SetValue")
        if self.eType == Image.EType.BW:
            if isinstance(value, bool):
                data[y, x] = value
            elif isinstance(value, (float, int)):
                data[y, x] = float(value) > 0.5
            else:
                rgba = _to_rgba(value)
                data[y, x] = ((rgba[0] + rgba[1] + rgba[2]) / 3.0) > 0.5
            return
        if self.eType == Image.EType.GRAY:
            if isinstance(value, bool):
                data[y, x] = 1.0 if value else 0.0
            elif isinstance(value, (float, int)):
                data[y, x] = float(value)
            else:
                rgba = _to_rgba(value)
                data[y, x] = (rgba[0] + rgba[1] + rgba[2]) / 3.0
            return
        if isinstance(value, bool):
            c = 1.0 if value else 0.0
            data[y, x, :] = np.array([c, c, c, 1.0], dtype=np.float32)
        elif isinstance(value, (float, int)):
            c = float(value)
            data[y, x, :] = np.array([c, c, c, 1.0], dtype=np.float32)
        else:
            data[y, x, :] = np.array(_to_rgba(value), dtype=np.float32)

    def byGetValue(self, x: int, y: int) -> int:
        return int(round(clamp01(self.fValue(x, y)) * 255.0))

    def SetValueByte(self, x: int, y: int, byValue: int) -> None:
        self.SetValue(x, y, float(int(byValue) & 0xFF) / 255.0)

    def sGetBgr24(self, x: int, y: int) -> tuple[int, int, int]:
        r, g, b, _ = self.clrValue(x, y)
        return (
            int(round(clamp01(b) * 255.0)),
            int(round(clamp01(g) * 255.0)),
            int(round(clamp01(r) * 255.0)),
        )

    def SetBgr24(self, x: int, y: int, clr: Sequence[int] | ColorLike) -> None:
        if len(clr) < 3:
            raise ValueError("BGR color must contain at least 3 channels")
        b = float(clr[0])
        g = float(clr[1])
        r = float(clr[2])
        if max(abs(b), abs(g), abs(r)) > 1.0:
            self.SetValue(x, y, (r / 255.0, g / 255.0, b / 255.0, 1.0))
        else:
            self.SetValue(x, y, (r, g, b, 1.0))

    def sGetBgra32(self, x: int, y: int) -> tuple[int, int, int, int]:
        r, g, b, a = self.clrValue(x, y)
        return (
            int(round(clamp01(b) * 255.0)),
            int(round(clamp01(g) * 255.0)),
            int(round(clamp01(r) * 255.0)),
            int(round(clamp01(a) * 255.0)),
        )

    def SetBgra32(self, x: int, y: int, clr: Sequence[int] | ColorLike) -> None:
        if len(clr) < 4:
            raise ValueError("BGRA color must contain 4 channels")
        b = float(clr[0])
        g = float(clr[1])
        r = float(clr[2])
        a = float(clr[3])
        if max(abs(b), abs(g), abs(r), abs(a)) > 1.0:
            self.SetValue(x, y, (r / 255.0, g / 255.0, b / 255.0, a / 255.0))
        else:
            self.SetValue(x, y, (r, g, b, a))

    def sGetRgb24(self, x: int, y: int) -> tuple[int, int, int]:
        r, g, b, _ = self.clrValue(x, y)
        return (
            int(round(clamp01(r) * 255.0)),
            int(round(clamp01(g) * 255.0)),
            int(round(clamp01(b) * 255.0)),
        )

    def sGetRgba32(self, x: int, y: int) -> tuple[int, int, int, int]:
        r, g, b, a = self.clrValue(x, y)
        return (
            int(round(clamp01(r) * 255.0)),
            int(round(clamp01(g) * 255.0)),
            int(round(clamp01(b) * 255.0)),
            int(round(clamp01(a) * 255.0)),
        )

    def SetRgb24(self, x: int, y: int, clr: Sequence[int] | ColorLike) -> None:
        if len(clr) < 3:
            raise ValueError("RGB color must contain at least 3 channels")
        r = float(clr[0])
        g = float(clr[1])
        b = float(clr[2])
        if max(abs(r), abs(g), abs(b)) > 1.0:
            self.SetValue(x, y, (r / 255.0, g / 255.0, b / 255.0, 1.0))
        else:
            self.SetValue(x, y, (r, g, b, 1.0))

    def SetRgba32(self, x: int, y: int, clr: Sequence[int] | ColorLike) -> None:
        if len(clr) < 4:
            raise ValueError("RGBA color must contain 4 channels")
        r = float(clr[0])
        g = float(clr[1])
        b = float(clr[2])
        a = float(clr[3])
        if max(abs(r), abs(g), abs(b), abs(a)) > 1.0:
            self.SetValue(x, y, (r / 255.0, g / 255.0, b / 255.0, a / 255.0))
        else:
            self.SetValue(x, y, (r, g, b, a))

    def clrGetAtNormalized(self, tx: float, ty: float) -> tuple[float, float, float, float]:
        fx = (tx * self.nWidth) - 1.0
        fy = (ty * self.nHeight) - 1.0
        x0 = max(0, min(self.nWidth - 1, int(math.floor(fx))))
        y0 = max(0, min(self.nHeight - 1, int(math.floor(fy))))
        x1 = max(0, min(self.nWidth - 1, x0 + 1))
        y1 = max(0, min(self.nHeight - 1, y0 + 1))
        dx = fx - x0
        dy = fy - y0
        c00 = self.clrValue(x0, y0)
        c10 = self.clrValue(x1, y0)
        c01 = self.clrValue(x0, y1)
        c11 = self.clrValue(x1, y1)

        def lerp(ca: tuple[float, float, float, float], cb: tuple[float, float, float, float], t: float) -> tuple[float, float, float, float]:
            return tuple(float(ca[i] + (cb[i] - ca[i]) * t) for i in range(4))  # type: ignore[return-value]

        c0 = lerp(c00, c10, dx)
        c1 = lerp(c01, c11, dx)
        return lerp(c0, c1, dy)

    def DrawLine(self, x0: int, y0: int, x1: int, y1: int, value: bool | float | ColorLike) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.SetValue(x0, y0, value)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy


class ImageBW(Image):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height, Image.EType.BW)
        self._data = np.zeros((height, width), dtype=np.bool_)

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.nWidth and 0 <= y < self.nHeight

    def bValue(self, x: int, y: int) -> bool:
        if not self._in_bounds(x, y):
            return False
        return bool(self._data[y, x])

    def fValue(self, x: int, y: int) -> float:
        return 1.0 if self.bValue(x, y) else 0.0

    def clrValue(self, x: int, y: int) -> tuple[float, float, float, float]:
        f = self.fValue(x, y)
        return (f, f, f, 1.0)

    def SetValue(self, x: int, y: int, value: bool | float | ColorLike) -> None:
        if not self._in_bounds(x, y):
            return
        if isinstance(value, bool):
            self._data[y, x] = value
            return
        if isinstance(value, (float, int)):
            self._data[y, x] = float(value) > 0.5
            return
        rgba = _to_rgba(value)
        self._data[y, x] = ((rgba[0] + rgba[1] + rgba[2]) / 3.0) > 0.5


class ImageGrayScale(Image):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height, Image.EType.GRAY)
        self._data = np.zeros((height, width), dtype=np.float32)

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.nWidth and 0 <= y < self.nHeight

    def fValue(self, x: int, y: int) -> float:
        if not self._in_bounds(x, y):
            return 0.0
        return float(self._data[y, x])

    def bValue(self, x: int, y: int) -> bool:
        return self.fValue(x, y) > 0.5

    def clrValue(self, x: int, y: int) -> tuple[float, float, float, float]:
        f = self.fValue(x, y)
        return (f, f, f, 1.0)

    def SetValue(self, x: int, y: int, value: bool | float | ColorLike) -> None:
        if not self._in_bounds(x, y):
            return
        if isinstance(value, bool):
            self._data[y, x] = 1.0 if value else 0.0
            return
        if isinstance(value, (float, int)):
            self._data[y, x] = float(value)
            return
        rgba = _to_rgba(value)
        self._data[y, x] = (rgba[0] + rgba[1] + rgba[2]) / 3.0

    def bContainsActivePixels(self, fThreshold: float = 0.0) -> bool:
        return bool(np.any(self._data <= float(fThreshold)))


class ImageColor(Image):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height, Image.EType.COLOR)
        self._data = np.zeros((height, width, 4), dtype=np.float32)
        self._data[:, :, 3] = 1.0

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.nWidth and 0 <= y < self.nHeight

    def clrValue(self, x: int, y: int) -> tuple[float, float, float, float]:
        if not self._in_bounds(x, y):
            return (0.0, 0.0, 0.0, 1.0)
        px = self._data[y, x, :]
        return (float(px[0]), float(px[1]), float(px[2]), float(px[3]))

    def fValue(self, x: int, y: int) -> float:
        r, g, b, _ = self.clrValue(x, y)
        return (r + g + b) / 3.0

    def bValue(self, x: int, y: int) -> bool:
        return self.fValue(x, y) > 0.5

    def SetValue(self, x: int, y: int, value: bool | float | ColorLike) -> None:
        if not self._in_bounds(x, y):
            return
        if isinstance(value, bool):
            c = 1.0 if value else 0.0
            self._data[y, x, :] = np.array([c, c, c, 1.0], dtype=np.float32)
            return
        if isinstance(value, (float, int)):
            c = float(value)
            self._data[y, x, :] = np.array([c, c, c, 1.0], dtype=np.float32)
            return
        self._data[y, x, :] = np.array(_to_rgba(value), dtype=np.float32)


class ImageRgb24(ImageColor):
    def __init__(self, width_or_source: int | Image, height: int | None = None) -> None:
        if isinstance(width_or_source, Image):
            src = width_or_source
            super().__init__(src.nWidth, src.nHeight)
            for x in range(self.nWidth):
                for y in range(self.nHeight):
                    self.SetRgb24(x, y, src.sGetRgb24(x, y))
            return
        if height is None:
            raise ValueError("height is required when width is an integer")
        super().__init__(int(width_or_source), int(height))

    def clrValue(self, x: int, y: int) -> tuple[float, float, float, float]:
        r, g, b, _ = super().clrValue(x, y)
        return (r, g, b, 1.0)

    def SetValue(self, x: int, y: int, value: bool | float | ColorLike) -> None:
        if isinstance(value, Sequence) and len(value) >= 3:
            super().SetValue(x, y, (float(value[0]), float(value[1]), float(value[2]), 1.0))
            return
        super().SetValue(x, y, value)
        if 0 <= x < self.nWidth and 0 <= y < self.nHeight:
            self._data[y, x, 3] = 1.0


class ImageRgba32(ImageColor):
    def __init__(self, width_or_source: int | Image, height: int | None = None) -> None:
        if isinstance(width_or_source, Image):
            src = width_or_source
            super().__init__(src.nWidth, src.nHeight)
            for x in range(self.nWidth):
                for y in range(self.nHeight):
                    self.SetRgba32(x, y, src.sGetRgba32(x, y))
            return
        if height is None:
            raise ValueError("height is required when width is an integer")
        super().__init__(int(width_or_source), int(height))
