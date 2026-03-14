from __future__ import annotations

import csv
import datetime
import math
import struct
import tempfile
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol, Sequence, cast

import numpy as np

from ._api import Mesh, PolyLine, ScalarField, VectorField, Voxels


Vector2Like = Sequence[float]
Vector3Like = Sequence[float]
ColorLike = Sequence[float]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _to_rgba(color: ColorLike) -> tuple[float, float, float, float]:
    if len(color) == 4:
        return (_clamp01(color[0]), _clamp01(color[1]), _clamp01(color[2]), _clamp01(color[3]))
    if len(color) == 3:
        return (_clamp01(color[0]), _clamp01(color[1]), _clamp01(color[2]), 1.0)
    if len(color) == 1:
        c = _clamp01(color[0])
        return (c, c, c, 1.0)
    raise ValueError("Color must have 1, 3, or 4 channels")


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


class IAction(Protocol):
    def bAnimate(self, fTimeStamp: float) -> bool:
        ...


class Animation:
    class EType(IntEnum):
        ONCE = 0
        REPEAT = 1
        WIGGLE = 2

    def __init__(self, action: Callable[[float], None], duration_seconds: float, eType: "Animation.EType" = EType.ONCE) -> None:
        if duration_seconds <= 0.0:
            raise ValueError("duration_seconds must be > 0")
        self._action = action
        self._duration = float(duration_seconds)
        self._type = eType
        self._start_time = time.perf_counter()

    def bAnimate(self, fTimeStamp: float) -> bool:
        dt = max(0.0, float(fTimeStamp) - self._start_time)
        finished = dt >= self._duration
        t = dt / self._duration
        if self._type == Animation.EType.ONCE:
            if finished:
                t = 1.0
        elif self._type == Animation.EType.REPEAT:
            t = t % 1.0
            finished = False
        else:
            oscillation = t % 2.0
            t = oscillation if oscillation <= 1.0 else 2.0 - oscillation
            finished = False
        self._action(float(t))
        return not finished


class AnimationQueue:
    def __init__(self) -> None:
        self._queue: list[IAction] = []

    def Clear(self) -> None:
        self._queue.clear()

    def Add(self, action: IAction) -> None:
        self._queue.append(action)

    def bIsIdle(self) -> bool:
        return len(self._queue) == 0

    def bPulse(self) -> bool:
        if not self._queue:
            return False
        now = time.perf_counter()
        to_remove: list[int] = []
        for i, action in enumerate(self._queue):
            if not action.bAnimate(now):
                to_remove.append(i)
        for idx in reversed(to_remove):
            self._queue.pop(idx)
        return len(self._queue) > 0


class IDataTable(Protocol):
    def nRowCount(self) -> int:
        ...

    def nMaxColumnCount(self) -> int:
        ...

    def strGetAt(self, nRow: int, nCol: int) -> str:
        ...


class CsvTable(IDataTable):
    def __init__(self, source: str | Path | IDataTable | None = None) -> None:
        self._rows: list[list[str]] = []
        self._key_column = -1
        self._col_ids: dict[str, int] = {}
        if source is None:
            return
        if isinstance(source, (str, Path)):
            with open(source, "r", newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                self._rows = [list(row) for row in reader]
        else:
            for r in range(source.nRowCount()):
                row = [source.strGetAt(r, c) for c in range(source.nMaxColumnCount())]
                self._rows.append(row)

    def Save(self, file_path: str | Path) -> None:
        with open(file_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(self._rows)

    def nRowCount(self) -> int:
        return len(self._rows)

    def nMaxColumnCount(self) -> int:
        return max((len(r) for r in self._rows), default=0)

    def strGetAt(self, nRow: int, nCol: int) -> str:
        if nRow < 0 or nRow >= len(self._rows):
            return ""
        row = self._rows[nRow]
        if nCol < 0 or nCol >= len(row):
            return ""
        return row[nCol]

    def SetKeyColumn(self, nColumn: int) -> None:
        self._key_column = int(nColumn)

    def bGetAt(self, key_or_row: str | int, col_or_idx: str | int) -> tuple[bool, str]:
        if isinstance(key_or_row, int) and isinstance(col_or_idx, int):
            value = self.strGetAt(key_or_row, col_or_idx)
            return (value != "", value)
        if not isinstance(key_or_row, str) or not isinstance(col_or_idx, str):
            return (False, "")
        if self._key_column < 0:
            return (False, "")
        ok_col, col = self.bFindColumn(col_or_idx)
        if not ok_col:
            return (False, "")
        for row in self._rows:
            if self._key_column < len(row) and row[self._key_column] == key_or_row:
                if col < len(row):
                    return (True, row[col])
                return (False, "")
        return (False, "")

    def bFindColumn(self, strColumnID: str) -> tuple[bool, int]:
        idx = self._col_ids.get(strColumnID)
        if idx is None:
            return (False, -1)
        return (True, idx)

    def strColumnId(self, nColumn: int) -> str:
        for key, val in self._col_ids.items():
            if val == nColumn:
                return key
        return ""

    def SetColumnIds(self, ids: Sequence[str]) -> None:
        self._col_ids = {str(col): i for i, col in enumerate(ids)}

    def AddRow(self, values: Sequence[str]) -> None:
        self._rows.append([str(v) for v in values])


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
        return int(round(_clamp01(self.fValue(x, y)) * 255.0))

    def SetValueByte(self, x: int, y: int, byValue: int) -> None:
        self.SetValue(x, y, float(int(byValue) & 0xFF) / 255.0)

    def sGetBgr24(self, x: int, y: int) -> tuple[int, int, int]:
        r, g, b, _ = self.clrValue(x, y)
        return (
            int(round(_clamp01(b) * 255.0)),
            int(round(_clamp01(g) * 255.0)),
            int(round(_clamp01(r) * 255.0)),
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
            int(round(_clamp01(b) * 255.0)),
            int(round(_clamp01(g) * 255.0)),
            int(round(_clamp01(r) * 255.0)),
            int(round(_clamp01(a) * 255.0)),
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
            int(round(_clamp01(r) * 255.0)),
            int(round(_clamp01(g) * 255.0)),
            int(round(_clamp01(b) * 255.0)),
        )

    def sGetRgba32(self, x: int, y: int) -> tuple[int, int, int, int]:
        r, g, b, a = self.clrValue(x, y)
        return (
            int(round(_clamp01(r) * 255.0)),
            int(round(_clamp01(g) * 255.0)),
            int(round(_clamp01(b) * 255.0)),
            int(round(_clamp01(a) * 255.0)),
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


class TgaIo:
    @staticmethod
    def SaveTga(file_path: str | Path, img: Image) -> None:
        width = img.nWidth
        height = img.nHeight
        is_color = img.eType == Image.EType.COLOR
        image_type = 2 if is_color else 3
        pixel_depth = 24 if is_color else 8
        header = struct.pack(
            "<BBBHHBHHHHBB",
            0,
            0,
            image_type,
            0,
            0,
            0,
            0,
            0,
            width,
            height,
            pixel_depth,
            32,
        )
        with open(file_path, "wb") as handle:
            handle.write(header)
            for y in range(height):
                for x in range(width):
                    if is_color:
                        r, g, b, _ = img.clrValue(x, y)
                        handle.write(bytes((int(_clamp01(b) * 255), int(_clamp01(g) * 255), int(_clamp01(r) * 255))))
                    else:
                        handle.write(bytes((img.byGetValue(x, y),)))

    @staticmethod
    def GetFileInfo(file_path: str | Path) -> tuple[Image.EType, int, int]:
        with open(file_path, "rb") as handle:
            header = handle.read(18)
        if len(header) != 18:
            raise ValueError("TGA header too short")
        _, _, image_type, _, _, _, _, _, width, height, _, _ = struct.unpack("<BBBHHBHHHHBB", header)
        eType = Image.EType.COLOR if image_type == 2 else Image.EType.GRAY
        return (eType, int(width), int(height))

    @staticmethod
    def LoadTga(file_path: str | Path) -> Image:
        with open(file_path, "rb") as handle:
            header = handle.read(18)
            if len(header) != 18:
                raise ValueError("TGA header too short")
            _, _, image_type, _, _, _, _, _, width, height, pixel_depth, image_desc = struct.unpack("<BBBHHBHHHHBB", header)
            if image_type == 2 and pixel_depth == 24:
                img: Image = ImageColor(width, height)
                for y in range(height):
                    iy = height - y - 1 if (image_desc & 0x20) == 0 else y
                    for x in range(width):
                        bgr = handle.read(3)
                        if len(bgr) != 3:
                            raise ValueError("Unexpected EOF in TGA payload")
                        b, g, r = bgr[0], bgr[1], bgr[2]
                        img.SetValue(x, iy, (r / 255.0, g / 255.0, b / 255.0, 1.0))
                return img
            if image_type == 3 and pixel_depth == 8:
                img = ImageGrayScale(width, height)
                for y in range(height):
                    iy = height - y - 1 if (image_desc & 0x20) == 0 else y
                    for x in range(width):
                        value = handle.read(1)
                        if len(value) != 1:
                            raise ValueError("Unexpected EOF in TGA payload")
                        img.SetValue(x, iy, value[0] / 255.0)
                return img
        raise ValueError("Unsupported TGA format")


@dataclass
class BBox2:
    vecMin: tuple[float, float] = (float("inf"), float("inf"))
    vecMax: tuple[float, float] = (float("-inf"), float("-inf"))

    def Include(self, point: Vector2Like | "BBox2") -> None:
        if isinstance(point, BBox2):
            self.Include(point.vecMin)
            self.Include(point.vecMax)
            return
        x, y = float(point[0]), float(point[1])
        self.vecMin = (min(self.vecMin[0], x), min(self.vecMin[1], y))
        self.vecMax = (max(self.vecMax[0], x), max(self.vecMax[1], y))


class PolyContour:
    class EWinding(IntEnum):
        UNKNOWN = 0
        CLOCKWISE = 1
        COUNTERCLOCKWISE = 2

    @staticmethod
    def strWindingAsString(eWinding: "PolyContour.EWinding") -> str:
        if eWinding == PolyContour.EWinding.COUNTERCLOCKWISE:
            return "[counter-clockwise]"
        if eWinding == PolyContour.EWinding.CLOCKWISE:
            return "[clockwise]"
        return "[unknown/degenerate]"

    def __init__(self, vertices: Iterable[Vector2Like], eWinding: "PolyContour.EWinding" = EWinding.UNKNOWN) -> None:
        self._vertices = [(float(v[0]), float(v[1])) for v in vertices]
        if len(self._vertices) < 3:
            raise ValueError("Polyline with less than 3 points makes no sense")
        self._bbox = BBox2()
        for v in self._vertices:
            self._bbox.Include(v)
        self._winding = self.eDetectWinding(self._vertices) if eWinding == self.EWinding.UNKNOWN else eWinding

    @staticmethod
    def eDetectWinding(vertices: Sequence[Vector2Like]) -> "PolyContour.EWinding":
        if len(vertices) < 3:
            return PolyContour.EWinding.UNKNOWN
        area = 0.0
        for i in range(len(vertices)):
            j = (i + 1) % len(vertices)
            area += (vertices[j][0] - vertices[i][0]) * (vertices[j][1] + vertices[i][1])
        if area > 0:
            return PolyContour.EWinding.CLOCKWISE
        if area < 0:
            return PolyContour.EWinding.COUNTERCLOCKWISE
        return PolyContour.EWinding.UNKNOWN

    def AddVertex(self, vec: Vector2Like) -> None:
        v = (float(vec[0]), float(vec[1]))
        self._vertices.append(v)
        self._bbox.Include(v)

    def DetectWinding(self) -> None:
        self._winding = self.eDetectWinding(self._vertices)

    def eWinding(self) -> "PolyContour.EWinding":
        return self._winding

    def oVertices(self) -> list[tuple[float, float]]:
        return list(self._vertices)

    def Close(self) -> None:
        if not self._vertices:
            return
        if self._vertices[0] != self._vertices[-1]:
            self._vertices.append(self._vertices[0])

    def AsSvgPolyline(self) -> str:
        pts = " ".join(f"{x},{y}" for x, y in self._vertices + [self._vertices[0]])
        stroke = "red"
        if self._winding == self.EWinding.CLOCKWISE:
            stroke = "blue"
        elif self._winding == self.EWinding.COUNTERCLOCKWISE:
            stroke = "black"
        return f"<polyline points='{pts}' stroke='{stroke}' fill='none' stroke-width='0.1' />\n"

    def AsSvgPath(self) -> str:
        parts: list[str] = []
        for i, (x, y) in enumerate(self._vertices):
            if i == 0:
                parts.append(f"M{x},{y}")
            else:
                parts.append(f"L{x},{y}")
        parts.append("Z")
        return " ".join(parts)

    def oBBox(self) -> BBox2:
        return self._bbox

    def nCount(self) -> int:
        return len(self._vertices)

    def vecVertex(self, n: int) -> tuple[float, float]:
        return self._vertices[n]


class PolySlice:
    def __init__(self, fZPos: float) -> None:
        self.m_fZPos = float(fZPos)
        self._contours: list[PolyContour] = []
        self._bbox = BBox2()

    def fZPos(self) -> float:
        return self.m_fZPos

    def AddContour(self, contour: PolyContour) -> None:
        self._contours.append(contour)
        self._bbox.Include(contour.oBBox())

    def nContours(self) -> int:
        return len(self._contours)

    def oContourAt(self, index: int) -> PolyContour:
        return self._contours[index]

    def oBBox(self) -> BBox2:
        return self._bbox

    def bIsEmpty(self) -> bool:
        return len(self._contours) == 0

    def Close(self) -> None:
        for c in self._contours:
            c.Close()

    def SaveToSvgFile(self, strPath: str | Path, bSolid: bool, oBBoxToUse: BBox2 | None = None) -> None:
        bbox = oBBoxToUse or self._bbox
        sx = bbox.vecMax[0] - bbox.vecMin[0]
        sy = bbox.vecMax[1] - bbox.vecMin[1]
        with open(strPath, "w", encoding="utf-8") as handle:
            handle.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
            handle.write("<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n")
            handle.write(
                f"<svg xmlns='http://www.w3.org/2000/svg' version='1.1' viewBox='{bbox.vecMin[0]} {bbox.vecMin[1]} {sx} {sy}' width='{sx}mm' height='{sy}mm'>\n"
            )
            handle.write("<g>\n")
            if not bSolid:
                for c in self._contours:
                    handle.write(c.AsSvgPolyline())
            else:
                path = " ".join(c.AsSvgPath() for c in self._contours)
                handle.write(f"<path d='{path}' fill='black'/>\n")
            handle.write("</g>\n</svg>\n")

    @staticmethod
    def _zero_crossing(a: float, b: float) -> float:
        den = a - b
        if abs(den) < 1e-8:
            return 0.5
        return float(np.clip(a / den, 0.0, 1.0))

    @staticmethod
    def oFromSdf(img: Image, fZPos: float, vecOffset: Vector2Like, fScale: float) -> "PolySlice":
        slice_obj = PolySlice(fZPos)
        if img.nWidth < 2 or img.nHeight < 2:
            return slice_obj
        ox, oy = float(vecOffset[0]), float(vecOffset[1])

        segs: list[tuple[tuple[float, float], tuple[float, float]]] = []
        edge_map = {
            1: ((3, 0),),
            2: ((0, 1),),
            3: ((3, 1),),
            4: ((1, 2),),
            5: ((3, 2), (0, 1)),
            6: ((0, 2),),
            7: ((3, 2),),
            8: ((2, 3),),
            9: ((0, 2),),
            10: ((0, 1), (2, 3)),
            11: ((1, 2),),
            12: ((1, 3),),
            13: ((0, 1),),
            14: ((0, 3),),
        }
        for y in range(img.nHeight - 1):
            for x in range(img.nWidth - 1):
                corners = [img.fValue(x, y), img.fValue(x + 1, y), img.fValue(x + 1, y + 1), img.fValue(x, y + 1)]
                idx = 0
                if corners[0] < 0.0:
                    idx |= 1
                if corners[1] < 0.0:
                    idx |= 2
                if corners[2] < 0.0:
                    idx |= 4
                if corners[3] < 0.0:
                    idx |= 8
                if idx == 0 or idx == 15:
                    continue
                cross: dict[int, tuple[float, float]] = {}
                if idx in edge_map:
                    if any(e in (0, 1, 2, 3) for pair in edge_map[idx] for e in pair):
                        cross[0] = (x + PolySlice._zero_crossing(corners[0], corners[1]), y)
                        cross[1] = (x + 1, y + PolySlice._zero_crossing(corners[1], corners[2]))
                        cross[2] = (x + PolySlice._zero_crossing(corners[3], corners[2]), y + 1)
                        cross[3] = (x, y + PolySlice._zero_crossing(corners[0], corners[3]))
                    for e0, e1 in edge_map[idx]:
                        p0 = cross[e0]
                        p1 = cross[e1]
                        segs.append(((ox + p0[0] * fScale, oy + p0[1] * fScale), (ox + p1[0] * fScale, oy + p1[1] * fScale)))

        remaining = segs[:]
        while remaining:
            a, b = remaining.pop()
            contour = [a, b]
            changed = True
            while changed and remaining:
                changed = False
                for i, (s0, s1) in enumerate(remaining):
                    if np.hypot(contour[-1][0] - s0[0], contour[-1][1] - s0[1]) < 1e-3:
                        contour.append(s1)
                        remaining.pop(i)
                        changed = True
                        break
                    if np.hypot(contour[-1][0] - s1[0], contour[-1][1] - s1[1]) < 1e-3:
                        contour.append(s0)
                        remaining.pop(i)
                        changed = True
                        break
            if len(contour) >= 3:
                try:
                    slice_obj.AddContour(PolyContour(contour))
                except ValueError:
                    pass
        return slice_obj


class PolySliceStack:
    def __init__(self, slices: Sequence[PolySlice] | None = None) -> None:
        self._slices = list(slices or [])
        self._bbox = BBox2()
        for sl in self._slices:
            self._bbox.Include(sl.oBBox())

    def AddSlice(self, poly_slice: PolySlice) -> None:
        self._slices.append(poly_slice)
        self._bbox.Include(poly_slice.oBBox())

    def AddSlices(self, slices: Sequence[PolySlice]) -> None:
        for sl in slices:
            self.AddSlice(sl)

    def nCount(self) -> int:
        return len(self._slices)

    def oSliceAt(self, index: int) -> PolySlice:
        return self._slices[index]

    def oBBox(self) -> BBox2:
        return self._bbox

    def oSlices(self) -> list[PolySlice]:
        return list(self._slices)


class Cli:
    class EFormat(IntEnum):
        UseEmptyFirstLayer = 0
        FirstLayerWithContent = 1

    @dataclass
    class Result:
        oSlices: PolySliceStack
        oBBoxFile: tuple[tuple[float, float, float], tuple[float, float, float]]
        bBinary: bool
        fUnitsHeader: float
        b32BitAlign: bool
        nVersion: int
        strHeaderDate: str
        nLayers: int
        strWarnings: str

    @staticmethod
    def _extract_parameter(line: str) -> tuple[bool, str, str]:
        if not line:
            return (False, "", line)
        if line[0] not in "/,":
            return (False, "", line)
        line = line[1:]
        end = len(line)
        for i, ch in enumerate(line):
            if ch in "$/,":
                end = i
                break
        param = line[:end]
        rest = line[end:]
        return (True, param, rest)

    @staticmethod
    def _safe_float(text: str, context: str) -> float:
        try:
            return float(text)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid parameter for {context}: {text}") from exc

    @staticmethod
    def _safe_uint(text: str, context: str) -> int:
        try:
            value = int(text)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid parameter for {context}: {text}") from exc
        if value < 0:
            raise ValueError(f"Invalid parameter for {context}: {text}")
        return value

    @staticmethod
    def WriteSlicesToCliFile(
        oSlices: PolySliceStack | Sequence[PolySlice],
        strFilePath: str | Path,
        eFormat: "Cli.EFormat" = EFormat.FirstLayerWithContent,
        strDate: str = "",
        fUnitsInMM: float = 0.0,
    ) -> None:
        stack = oSlices if isinstance(oSlices, PolySliceStack) else PolySliceStack(oSlices)

        if stack.nCount() < 1 or (math.isinf(stack.oBBox().vecMin[0]) and math.isinf(stack.oBBox().vecMin[1])):
            raise ValueError("No valid slices detected (empty)")

        if fUnitsInMM <= 0.0:
            fUnitsInMM = 1.0
        if not strDate:
            strDate = time.strftime("%Y-%m-%d")

        bbox = stack.oBBox()
        nSliceCount = stack.nCount() + (1 if eFormat == Cli.EFormat.UseEmptyFirstLayer else 0)
        strDim = (
            f"{bbox.vecMin[0]:08.5f},{bbox.vecMin[1]:08.5f},{0.0:08.5f},"
            f"{bbox.vecMax[0]:08.5f},{bbox.vecMax[1]:08.5f},{stack.oSliceAt(stack.nCount() - 1).fZPos():08.5f}"
        )

        with open(strFilePath, "w", encoding="ascii", newline="\n") as handle:
            handle.write("$$HEADERSTART\n")
            handle.write("$$ASCII\n")
            handle.write(f"$$UNITS/{fUnitsInMM}\n")
            handle.write("$$VERSION/200\n")
            handle.write("$$LABEL/1,default\n")
            handle.write(f"$$DATE/{strDate}\n")
            handle.write(f"$$DIMENSION/{strDim}\n")
            handle.write(f"$$LAYERS/{nSliceCount:05d}\n")
            handle.write("$$HEADEREND\n")
            handle.write("$$GEOMETRYSTART\n")

            if eFormat == Cli.EFormat.UseEmptyFirstLayer:
                handle.write("$$LAYER/0.0\n")

            for nLayer in range(stack.nCount()):
                sl = stack.oSliceAt(nLayer)
                handle.write(f"$$LAYER/{(sl.fZPos() / fUnitsInMM):0.5f}\n")

                for nPass in range(3):
                    for nPolyline in range(sl.nContours()):
                        poly = sl.oContourAt(nPolyline)
                        if nPass == 0 and poly.eWinding() != PolyContour.EWinding.COUNTERCLOCKWISE:
                            continue
                        if nPass == 1 and poly.eWinding() != PolyContour.EWinding.CLOCKWISE:
                            continue
                        if nPass == 2 and poly.eWinding() != PolyContour.EWinding.UNKNOWN:
                            continue

                        nWinding = 2
                        if poly.eWinding() == PolyContour.EWinding.CLOCKWISE:
                            nWinding = 0
                        elif poly.eWinding() == PolyContour.EWinding.COUNTERCLOCKWISE:
                            nWinding = 1

                        entries = ["$$POLYLINE/1", str(nWinding), str(poly.nCount())]
                        for nVertex in range(poly.nCount()):
                            vx, vy = poly.vecVertex(nVertex)
                            entries.append(f"{(vx / fUnitsInMM):0.5f}")
                            entries.append(f"{(vy / fUnitsInMM):0.5f}")
                        handle.write(",".join(entries) + "\n")

            handle.write("$$GEOMETRYEND\n")

    @staticmethod
    def oSlicesFromCliFile(strFilePath: str | Path) -> "Cli.Result":
        with open(strFilePath, "r", encoding="ascii", errors="ignore") as handle:
            raw_lines = handle.readlines()

        warnings: list[str] = []
        in_comment = False
        n_label = None
        n_header_layer_numbers = 0
        b_binary = False
        f_units_header = 0.0
        b_32bit_align = False
        n_version = 0
        str_header_date = ""
        bbox_file = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        i = 0
        b_header_started = False
        b_header_ended = False
        while i < len(raw_lines) and not b_header_ended:
            line = raw_lines[i]
            i += 1

            while line != "":
                line = line.strip()
                if line.startswith("//"):
                    in_comment = True
                    line = line[2:]

                if in_comment:
                    end = line.find("//")
                    if end == -1:
                        line = ""
                        continue
                    line = line[end + 2 :].strip()
                    in_comment = False

                if not b_header_started:
                    idx = line.find("$$HEADERSTART")
                    if idx == -1:
                        break
                    line = line[idx + len("$$HEADERSTART") :].strip()
                    b_header_started = True
                    continue

                if not line.startswith("$$"):
                    break

                if line.startswith("$$BINARY"):
                    line = line[len("$$BINARY") :]
                    b_binary = True
                    continue
                if line.startswith("$$ASCII"):
                    line = line[len("$$ASCII") :]
                    b_binary = False
                    continue
                if line.startswith("$$ALIGN"):
                    line = line[len("$$ALIGN") :]
                    b_32bit_align = True
                    continue
                if line.startswith("$$UNITS"):
                    line = line[len("$$UNITS") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$UNITS")
                    f_units_header = Cli._safe_float(param, "$$UNITS")
                    if f_units_header <= 0.0:
                        raise ValueError(f"Invalid parameter for $$UNITS: {param}")
                    continue
                if line.startswith("$$VERSION"):
                    line = line[len("$$VERSION") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$VERSION")
                    n_version = Cli._safe_uint(param, "$$VERSION")
                    continue
                if line.startswith("$$LABEL"):
                    line = line[len("$$LABEL") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LABEL")
                    if n_label is not None:
                        raise NotImplementedError("Currently we do not support multiple labels and objects in one CLI file")
                    n_label = Cli._safe_uint(param, "$$LABEL")
                    ok, _, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LABEL (text)")
                    continue
                if line.startswith("$$DATE"):
                    line = line[len("$$DATE") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$DATE")
                    str_header_date = param.strip()
                    continue
                if line.startswith("$$DIMENSION"):
                    line = line[len("$$DIMENSION") :]
                    values: list[float] = []
                    for _ in range(6):
                        ok, param, line = Cli._extract_parameter(line)
                        if not ok:
                            raise ValueError("Missing parameter after $$DIMENSION")
                        values.append(Cli._safe_float(param, "$$DIMENSION"))
                    bbox_file[0] = [values[0], values[1], values[2]]
                    bbox_file[1] = [values[3], values[4], values[5]]
                    continue
                if line.startswith("$$LAYERS"):
                    line = line[len("$$LAYERS") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LAYERS")
                    n_header_layer_numbers = Cli._safe_uint(param, "$$LAYERS")
                    continue
                if line.startswith("$$HEADEREND"):
                    b_header_ended = True
                    break

                break

        if not b_header_ended:
            raise ValueError("End of file while searching for valid header")

        if b_binary:
            raise NotImplementedError("Binary CLI Files are not yet supported")

        b_geometry_started = False
        b_geometry_ended = False
        o_current_slice: PolySlice | None = None
        slices: list[PolySlice] = []
        f_prev_z = float("-inf")

        while i < len(raw_lines) and not b_geometry_ended:
            line = raw_lines[i]
            i += 1
            while line != "":
                line = line.strip()
                if line.startswith("//"):
                    in_comment = True
                    line = line[2:]

                if in_comment:
                    end = line.find("//")
                    if end == -1:
                        line = ""
                        continue
                    line = line[end + 2 :].strip()
                    in_comment = False

                if not b_geometry_started:
                    idx = line.find("$$GEOMETRYSTART")
                    if idx == -1:
                        break
                    line = line[idx + len("$$GEOMETRYSTART") :].strip()
                    b_geometry_started = True
                    continue

                if line.startswith("$$LAYER"):
                    line = line[len("$$LAYER") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LAYER")
                    f_z = Cli._safe_float(param, "$$LAYER") * f_units_header

                    if f_prev_z != float("-inf") and f_z < f_prev_z:
                        raise ValueError(f"Z position in current layer is smaller than in previous {param}")

                    if f_z > 0.0:
                        if o_current_slice is not None:
                            slices.append(o_current_slice)
                        o_current_slice = PolySlice(f_z)
                        f_prev_z = f_z
                    continue

                if line.startswith("$$POLYLINE"):
                    if o_current_slice is None:
                        raise ValueError("There should not be contours at z position 0")

                    line = line[len("$$POLYLINE") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$POLYLINE")
                    n_id = Cli._safe_uint(param, "$$POLYLINE")

                    if n_label is None:
                        n_label = n_id
                    if n_id != n_label:
                        raise NotImplementedError("We do not support CLI labels and multiple models yet")

                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$POLYLINE")
                    n_winding = Cli._safe_uint(param, "$$POLYLINE direction")
                    if n_winding == 0:
                        declared = PolyContour.EWinding.CLOCKWISE
                    elif n_winding == 1:
                        declared = PolyContour.EWinding.COUNTERCLOCKWISE
                    elif n_winding == 2:
                        declared = PolyContour.EWinding.UNKNOWN
                    else:
                        raise ValueError(f"Invalid parameter for $$POLYLINE direction: {param}")

                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter polygon count after $$POLYLINE")
                    n_count = Cli._safe_uint(param, "$$POLYLINE polygon count")

                    vertices: list[tuple[float, float]] = []
                    while n_count > 0:
                        ok, param, line = Cli._extract_parameter(line)
                        if not ok:
                            raise ValueError("Missing vertices in $$POLYLINE")
                        fx = Cli._safe_float(param, "$$POLYLINE vertex X") * f_units_header
                        ok, param, line = Cli._extract_parameter(line)
                        if not ok:
                            raise ValueError("Missing vertices in $$POLYLINE")
                        fy = Cli._safe_float(param, "$$POLYLINE vertex Y") * f_units_header
                        vertices.append((fx, fy))
                        n_count -= 1

                    if len(vertices) < 3:
                        warnings.append(f"Line: {i} Discarding POLYLINE with {len(vertices)} vertices which is degenerate")
                        continue

                    poly = PolyContour(vertices)
                    actual = poly.eWinding()
                    if actual == PolyContour.EWinding.UNKNOWN:
                        warnings.append(
                            f"Line: {i} Discarding POLYLINE with area 0 (degenerate) - defined with winding {PolyContour.strWindingAsString(declared)}"
                        )
                        continue
                    if actual != declared:
                        warnings.append(
                            f"Line: {i} POLYLINE defined with winding {PolyContour.strWindingAsString(declared)} actual winding is {PolyContour.strWindingAsString(actual)} (using actual)"
                        )
                    o_current_slice.AddContour(poly)
                    continue

                if line.startswith("$$GEOMETRYEND"):
                    b_geometry_ended = True
                    break

                if line.startswith("$$"):
                    warnings.append(f"Line: {i} Unsupported command {Utils.strShorten(line, 20)}")
                    line = ""
                    continue

                line = ""

        if o_current_slice is not None:
            slices.append(o_current_slice)

        result_stack = PolySliceStack(slices)
        return Cli.Result(
            oSlices=result_stack,
            oBBoxFile=((bbox_file[0][0], bbox_file[0][1], bbox_file[0][2]), (bbox_file[1][0], bbox_file[1][1], bbox_file[1][2])),
            bBinary=b_binary,
            fUnitsHeader=f_units_header,
            b32BitAlign=b_32bit_align,
            nVersion=n_version,
            strHeaderDate=str_header_date,
            nLayers=n_header_layer_numbers,
            strWarnings="\n".join(warnings),
        )


class CliIo(Cli):
    @staticmethod
    def WriteSlicesToCliFile(
        oSlices: PolySliceStack | Sequence[PolySlice],
        strFilePath: str | Path,
        eFormat: "Cli.EFormat" = Cli.EFormat.FirstLayerWithContent,
        strDate: str = "",
        fUnitsInMM: float = 0.0,
    ) -> None:
        Cli.WriteSlicesToCliFile(oSlices, strFilePath, eFormat, strDate, fUnitsInMM)

    @staticmethod
    def oSlicesFromCliFile(strFilePath: str | Path) -> "Cli.Result":
        return Cli.oSlicesFromCliFile(strFilePath)


class MeshMath:
    @staticmethod
    def bPointLiesOnTriangle(vecP: Vector3Like, vecA: Vector3Like, vecB: Vector3Like, vecC: Vector3Like) -> bool:
        p = np.array(vecP, dtype=np.float64)
        a = np.array(vecA, dtype=np.float64) - p
        b = np.array(vecB, dtype=np.float64) - p
        c = np.array(vecC, dtype=np.float64) - p
        u = np.cross(b, c)
        v = np.cross(c, a)
        w = np.cross(a, b)
        return float(np.dot(u, v)) >= 0.0 and float(np.dot(u, w)) >= 0.0

    @staticmethod
    def bFindTriangleFromSurfacePoint(mesh: Mesh, vecSurfacePoint: Vector3Like) -> tuple[bool, int]:
        for i in range(mesh.nTriangleCount()):
            a, b, c = mesh.GetTriangle(i)
            if MeshMath.bPointLiesOnTriangle(vecSurfacePoint, a, b, c):
                return (True, i)
        return (False, (2**31) - 1)


class EStlUnit(IntEnum):
    AUTO = 0
    MM = 1
    CM = 2
    M = 3
    FT = 4
    IN = 5


def _stl_unit_scale_to_mm(unit: EStlUnit) -> float:
    return {
        EStlUnit.MM: 1.0,
        EStlUnit.CM: 10.0,
        EStlUnit.M: 1000.0,
        EStlUnit.FT: 304.8,
        EStlUnit.IN: 25.4,
    }.get(unit, 1.0)


class MeshIo:
    @staticmethod
    def mshFromStlFile(strFilePath: str, eLoadUnit: EStlUnit = EStlUnit.AUTO, fPostScale: float = 1.0, vecPostOffsetMM: Vector3Like | None = None) -> Mesh:
        path = Path(strFilePath)
        raw = path.read_bytes()
        if len(raw) < 84:
            raise ValueError("Failed to read STL file, header too short")
        header = raw[:80].decode("ascii", errors="ignore")
        offset = np.array(vecPostOffsetMM if vecPostOffsetMM is not None else (0.0, 0.0, 0.0), dtype=np.float64)

        load_unit = eLoadUnit
        if load_unit == EStlUnit.AUTO:
            h = header.lower()
            if "units=cm" in h:
                load_unit = EStlUnit.CM
            elif "units= m" in h:
                load_unit = EStlUnit.M
            elif "units=ft" in h:
                load_unit = EStlUnit.FT
            elif "units=in" in h:
                load_unit = EStlUnit.IN
            else:
                load_unit = EStlUnit.MM

        scale = _stl_unit_scale_to_mm(load_unit) * float(fPostScale)
        msh = Mesh()
        cast(Any, msh).m_strLoadHeaderData = header.strip()
        cast(Any, msh).m_eLoadUnits = load_unit

        is_ascii = raw.startswith(b"solid") and (b"vertex" in raw[:2048])
        if is_ascii:
            text = raw.decode("ascii", errors="ignore")
            verts: list[tuple[float, float, float]] = []
            for line in text.splitlines():
                line = line.strip().lower()
                if line.startswith("vertex "):
                    parts = line.split()
                    if len(parts) >= 4:
                        v = np.array((float(parts[1]), float(parts[2]), float(parts[3])), dtype=np.float64)
                        v = (v * scale) + offset
                        verts.append((float(v[0]), float(v[1]), float(v[2])))
                        if len(verts) == 3:
                            msh.nAddTriangle(verts[0], verts[1], verts[2])
                            verts.clear()
        else:
            tri_count = struct.unpack("<I", raw[80:84])[0]
            cursor = 84
            for _ in range(tri_count):
                if cursor + 50 > len(raw):
                    break
                data = raw[cursor : cursor + 50]
                cursor += 50
                v0 = np.array(struct.unpack("<3f", data[12:24]), dtype=np.float64)
                v1 = np.array(struct.unpack("<3f", data[24:36]), dtype=np.float64)
                v2 = np.array(struct.unpack("<3f", data[36:48]), dtype=np.float64)
                v0 = (v0 * scale) + offset
                v1 = (v1 * scale) + offset
                v2 = (v2 * scale) + offset
                msh.nAddTriangle(tuple(v0.tolist()), tuple(v1.tolist()), tuple(v2.tolist()))

        if msh.nTriangleCount() == 0:
            msh.close()
            raise ValueError("Imported STL mesh is empty (zero triangles), failed to load")
        return msh

    @staticmethod
    def SaveToStlFile(mesh: Mesh, strFilePath: str, eUnit: EStlUnit = EStlUnit.AUTO, vecOffsetMM: Vector3Like | None = None, fScale: float = 1.0) -> None:
        unit = eUnit
        if unit == EStlUnit.AUTO:
            unit = getattr(mesh, "m_eLoadUnits", EStlUnit.MM)
        unit_tag = {
            EStlUnit.CM: "UNITS=cm",
            EStlUnit.M: "UNITS= m",
            EStlUnit.FT: "UNITS=ft",
            EStlUnit.IN: "UNITS=in",
        }.get(unit, "UNITS=mm")
        header = f"PicoGK {unit_tag}".ljust(80, " ").encode("ascii", errors="ignore")
        conv = 1.0 / _stl_unit_scale_to_mm(unit)
        offset = np.array(vecOffsetMM if vecOffsetMM is not None else (0.0, 0.0, 0.0), dtype=np.float64)

        with open(strFilePath, "wb") as handle:
            handle.write(header)
            handle.write(struct.pack("<I", mesh.nTriangleCount()))
            for i in range(mesh.nTriangleCount()):
                a, b, c = mesh.GetTriangle(i)
                va = (np.array(a, dtype=np.float64) + offset) * fScale * conv
                vb = (np.array(b, dtype=np.float64) + offset) * fScale * conv
                vc = (np.array(c, dtype=np.float64) + offset) * fScale * conv
                normal = np.cross(vb - va, vc - va)
                nlen = np.linalg.norm(normal)
                if nlen > 1e-12:
                    normal = normal / nlen
                else:
                    normal = np.array((0.0, 0.0, 1.0), dtype=np.float64)
                handle.write(struct.pack("<3f", float(normal[0]), float(normal[1]), float(normal[2])))
                handle.write(struct.pack("<3f", float(va[0]), float(va[1]), float(va[2])))
                handle.write(struct.pack("<3f", float(vb[0]), float(vb[1]), float(vb[2])))
                handle.write(struct.pack("<3f", float(vc[0]), float(vc[1]), float(vc[2])))
                handle.write(struct.pack("<H", 0))


class SdfVisualizer:
    @staticmethod
    def imgEncodeFromSdf(
        oField: ScalarField,
        fBackgroundValue: float,
        nSlice: int,
        _clrBackground: ColorLike | None = None,
        _clrSurface: ColorLike | None = None,
        _clrInside: ColorLike | None = None,
        _clrOutside: ColorLike | None = None,
        _clrDefect: ColorLike | None = None,
    ) -> ImageColor:
        dims = oField.GetVoxelDimensions()
        img = ImageColor(dims.x_size, dims.y_size)
        if nSlice >= dims.z_size:
            return img
        colors = {
            "bg": _to_rgba(_clrBackground or (0.0, 0.4, 1.0, 1.0)),
            "surf": _to_rgba(_clrSurface or (1.0, 1.0, 1.0, 1.0)),
            "in": _to_rgba(_clrInside or (0.8, 0.2, 1.0, 1.0)),
            "out": _to_rgba(_clrOutside or (0.2, 0.8, 0.2, 1.0)),
            "def": _to_rgba(_clrDefect or (1.0, 0.33, 0.0, 1.0)),
        }
        sdf = oField.GetVoxelSlice(nSlice)
        for y in range(dims.y_size):
            for x in range(dims.x_size):
                f = float(sdf[y, x])
                if not math.isfinite(f):
                    clr = colors["def"]
                elif abs(f) < np.finfo(np.float32).eps:
                    clr = colors["surf"]
                elif abs(f - fBackgroundValue) < np.finfo(np.float32).eps:
                    clr = colors["bg"]
                elif f < 0.0:
                    t = min(1.0, abs(f) / max(abs(fBackgroundValue), 1e-6))
                    base = colors["in"]
                    clr = (base[0] * (1.0 - 0.35 * t), base[1] * (1.0 - 0.35 * t), base[2] * (1.0 - 0.35 * t), base[3])
                else:
                    t = min(1.0, abs(f) / max(abs(fBackgroundValue), 1e-6))
                    base = colors["out"]
                    clr = (base[0] * (1.0 - 0.35 * t), base[1] * (1.0 - 0.35 * t), base[2] * (1.0 - 0.35 * t), base[3])
                img.SetValue(x, y, clr)
        return img

    @staticmethod
    def bDoesSliceContainDefect(oField: ScalarField, nSlice: int) -> bool:
        dims = oField.GetVoxelDimensions()
        if nSlice >= dims.z_size:
            return False
        sdf = oField.GetVoxelSlice(nSlice)
        return bool(np.any(~np.isfinite(sdf)))

    @staticmethod
    def bVisualizeSdfSlicesAsTgaStack(
        oField: ScalarField,
        fBackgroundValue: float,
        strPath: str,
        strFilePrefix: str = "Sdf_",
        bOnlyDefective: bool = False,
        _clrBackground: ColorLike | None = None,
        _clrSurface: ColorLike | None = None,
        _clrInside: ColorLike | None = None,
        _clrOutside: ColorLike | None = None,
        _clrDefect: ColorLike | None = None,
    ) -> bool:
        path = Path(strPath)
        path.mkdir(parents=True, exist_ok=True)
        dims = oField.GetVoxelDimensions()
        found_defect = False
        for s in range(dims.z_size):
            has_defect = SdfVisualizer.bDoesSliceContainDefect(oField, s)
            found_defect = found_defect or has_defect
            if bOnlyDefective and not has_defect:
                continue
            img = SdfVisualizer.imgEncodeFromSdf(
                oField,
                fBackgroundValue,
                s,
                _clrBackground,
                _clrSurface,
                _clrInside,
                _clrOutside,
                _clrDefect,
            )
            TgaIo.SaveTga(path / f"{strFilePrefix}{s:05d}.tga", img)
        return found_defect


class ActiveVoxelCounterScalar:
    @staticmethod
    def nCount(oField: ScalarField) -> int:
        count = 0

        def _visit(_: tuple[float, float, float], __: float) -> None:
            nonlocal count
            count += 1

        oField.TraverseActive(_visit)
        return count


class SurfaceNormalFieldExtractor:
    @staticmethod
    def oExtract(
        vox: Voxels,
        fSurfaceThresholdVx: float = 0.5,
        vecDirectionFilter: Vector3Like | None = None,
        fDirectionFilterTolerance: float = 0.0,
        vecScaleBy: Vector3Like | None = None,
    ) -> VectorField:
        direction = np.array(vecDirectionFilter if vecDirectionFilter is not None else (0.0, 0.0, 0.0), dtype=np.float64)
        if np.linalg.norm(direction) > 1e-12:
            direction = direction / np.linalg.norm(direction)
        scale_by = np.array(vecScaleBy if vecScaleBy is not None else (1.0, 1.0, 1.0), dtype=np.float64)

        src = ScalarField.from_voxels(vox)
        dst = VectorField()

        def _visit(pos: tuple[float, float, float], value: float) -> None:
            if abs(value) > fSurfaceThresholdVx:
                return
            normal = np.array(vox.vecSurfaceNormal(pos), dtype=np.float64)
            nlen = np.linalg.norm(normal)
            if nlen <= 1e-12:
                return
            normal = normal / nlen
            if np.linalg.norm(direction) > 1e-12:
                dev = abs(1.0 - float(np.dot(normal, direction)))
                if dev > float(fDirectionFilterTolerance):
                    return
            v = normal * scale_by
            dst.SetValue(pos, (float(v[0]), float(v[1]), float(v[2])))

        src.TraverseActive(_visit)
        src.close()
        return dst


class VectorFieldMerge:
    @staticmethod
    def Merge(oSource: VectorField, oTarget: VectorField) -> None:
        def _visit(p: tuple[float, float, float], v: tuple[float, float, float]) -> None:
            oTarget.SetValue(p, v)

        oSource.TraverseActive(_visit)


class FieldUtils:
    SdfVisualizer = SdfVisualizer
    ActiveVoxelCounterScalar = ActiveVoxelCounterScalar
    SurfaceNormalFieldExtractor = SurfaceNormalFieldExtractor
    VectorFieldMerge = VectorFieldMerge


class ImplicitTriangle:
    def __init__(self, vecA: Vector3Like, vecB: Vector3Like, vecC: Vector3Like, fThickness: float) -> None:
        self.A = np.array(vecA, dtype=np.float64)
        self.B = np.array(vecB, dtype=np.float64)
        self.C = np.array(vecC, dtype=np.float64)
        self._thickness = float(fThickness)
        mins = np.minimum(np.minimum(self.A, self.B), self.C) - self._thickness
        maxs = np.maximum(np.maximum(self.A, self.B), self.C) + self._thickness
        self.oBounds = (tuple(mins.tolist()), tuple(maxs.tolist()))

    @staticmethod
    def _closest_point_on_triangle(point: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        ab = b - a
        ac = c - a
        ap = point - a
        d1 = np.dot(ab, ap)
        d2 = np.dot(ac, ap)
        if d1 <= 0.0 and d2 <= 0.0:
            return a
        bp = point - b
        d3 = np.dot(ab, bp)
        d4 = np.dot(ac, bp)
        if d3 >= 0.0 and d4 <= d3:
            return b
        vc = d1 * d4 - d3 * d2
        if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
            v = d1 / (d1 - d3)
            return a + (v * ab)
        cp = point - c
        d5 = np.dot(ab, cp)
        d6 = np.dot(ac, cp)
        if d6 >= 0.0 and d5 <= d6:
            return c
        vb = d5 * d2 - d1 * d6
        if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
            w = d2 / (d2 - d6)
            return a + (w * ac)
        va = d3 * d6 - d5 * d4
        if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
            w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
            return b + (w * (c - b))
        denom = 1.0 / (va + vb + vc)
        v_ab = vb * denom
        v_ac = vc * denom
        return a + (v_ab * ab) + (v_ac * ac)

    def fSignedDistance(self, vec: Vector3Like) -> float:
        p = np.array(vec, dtype=np.float64)
        cp = self._closest_point_on_triangle(p, self.A, self.B, self.C)
        return float(np.linalg.norm(p - cp) - self._thickness)


class ImplicitMesh:
    def __init__(self, msh: Mesh, fThickness: float) -> None:
        self._triangles: list[ImplicitTriangle] = []
        bounds_min = np.array((float("inf"), float("inf"), float("inf")), dtype=np.float64)
        bounds_max = np.array((float("-inf"), float("-inf"), float("-inf")), dtype=np.float64)
        for i in range(msh.nTriangleCount()):
            a, b, c = msh.GetTriangle(i)
            tri = ImplicitTriangle(a, b, c, fThickness)
            self._triangles.append(tri)
            tmin = np.array(tri.oBounds[0], dtype=np.float64)
            tmax = np.array(tri.oBounds[1], dtype=np.float64)
            bounds_min = np.minimum(bounds_min, tmin)
            bounds_max = np.maximum(bounds_max, tmax)
        self.oBounds = (tuple(bounds_min.tolist()), tuple(bounds_max.tolist()))

    def fSignedDistance(self, vec: Vector3Like) -> float:
        return min((tri.fSignedDistance(vec) for tri in self._triangles), default=1e9)


class TriangleVoxelization:
    @staticmethod
    def voxVoxelizeHollow(mesh: Mesh, fThickness: float) -> Voxels:
        implicit = ImplicitMesh(mesh, fThickness)
        vox = Voxels()
        bmin, bmax = implicit.oBounds
        vox.RenderImplicit(bmin, bmax, implicit.fSignedDistance)
        return vox


class Utils:
    @staticmethod
    def bFileExists(path: str | Path) -> bool:
        return Path(path).is_file()

    @staticmethod
    def bFolderExists(path: str | Path) -> bool:
        return Path(path).is_dir()

    @staticmethod
    def strGetFullPath(path: str | Path) -> str:
        return str(Path(path).resolve())

    @staticmethod
    def strGetFileName(path: str | Path) -> str:
        return Path(path).name

    @staticmethod
    def strGetFileNameWithoutExtension(path: str | Path) -> str:
        return Path(path).stem

    @staticmethod
    def strGetFolderName(path: str | Path) -> str:
        return Path(path).parent.name

    @staticmethod
    def strGetFileExtension(path: str | Path) -> str:
        return Path(path).suffix

    @staticmethod
    def strGetFileNameWithOtherExtension(path: str | Path, extension: str) -> str:
        p = Path(path)
        if extension and not extension.startswith("."):
            extension = "." + extension
        return str(p.with_suffix(extension))

    @staticmethod
    def strReplaceFileName(path: str | Path, new_name: str) -> str:
        return str(Path(path).with_name(new_name))

    @staticmethod
    def strShorten(text: str, max_len: int = 48) -> str:
        if max_len < 6:
            max_len = 6
        if len(text) <= max_len:
            return text
        lead = max_len // 2 - 1
        trail = max_len - lead - 3
        return text[:lead] + "..." + text[-trail:]


class TempFolder:
    def __init__(self) -> None:
        self.strFolder = tempfile.mkdtemp(prefix="picogk_")
        self._disposed = False

    def dispose(self) -> None:
        if self._disposed:
            return
        try:
            for file_path in Path(self.strFolder).glob("*"):
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)
            Path(self.strFolder).rmdir()
        except Exception:
            pass
        self._disposed = True

    def __enter__(self) -> "TempFolder":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.dispose()


class LogFile:
    def __init__(self, strFileName: str = "", bOutputToConsole: bool = True) -> None:
        self._output_to_console = bool(bOutputToConsole)
        self._start = time.perf_counter()
        self._last = 0.0
        if not strFileName:
            docs = Path.home() / "Documents"
            docs.mkdir(parents=True, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            strFileName = str(docs / f"PicoGK_{stamp}.log")
        self._path = strFileName
        self._writer = open(strFileName, "w", encoding="utf-8")
        self.Log(f"Opened {strFileName}")

    def Log(self, strFormat: str, *args: object) -> None:
        now = time.perf_counter() - self._start
        diff = now - self._last
        msg = strFormat.format(*args) if args else strFormat
        prefix = f"{now:7.0f}s {diff:6.1f}+ "
        for line in msg.split("\n"):
            row = prefix + line
            if self._output_to_console:
                print(row)
            self._writer.write(row + "\n")
        self._writer.flush()
        self._last = now

    def LogTime(self) -> None:
        self.Log("Current time (UTC): {0}", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)"))
        self.Log("Current local time: {0}", datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S (%z)"))

    def dispose(self) -> None:
        if self._writer.closed:
            return
        self.Log("Closing log file.")
        self.LogTime()
        self._writer.close()

    def __enter__(self) -> "LogFile":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.dispose()


class Vector3Ext:
    @staticmethod
    def vecNormalized(vec: Vector3Like) -> tuple[float, float, float]:
        v = np.array(vec, dtype=np.float64)
        n = np.linalg.norm(v)
        if n <= 1e-12:
            return (0.0, 0.0, 0.0)
        v = v / n
        return (float(v[0]), float(v[1]), float(v[2]))

    @staticmethod
    def vecMirrored(vec: Vector3Like, vecPlanePoint: Vector3Like, vecPlaneNormalUnitVector: Vector3Like) -> tuple[float, float, float]:
        v = np.array(vec, dtype=np.float64)
        p = np.array(vecPlanePoint, dtype=np.float64)
        n = np.array(vecPlaneNormalUnitVector, dtype=np.float64)
        ln = np.linalg.norm(n)
        if ln <= 1e-12:
            raise ValueError("vecPlaneNormalUnitVector must be non-zero")
        n = n / ln
        out = v - (2.0 * np.dot(v - p, n) * n)
        return (float(out[0]), float(out[1]), float(out[2]))

    @staticmethod
    def vecTransformed(vec: Vector3Like, mat: Sequence[float]) -> tuple[float, float, float]:
        if len(mat) != 16:
            raise ValueError("mat must have 16 values (row-major 4x4)")
        m = np.array(mat, dtype=np.float64).reshape((4, 4))
        v = np.array((float(vec[0]), float(vec[1]), float(vec[2]), 1.0), dtype=np.float64)
        out = m @ v
        return (float(out[0]), float(out[1]), float(out[2]))


class ESliceMode(IntEnum):
    SignedDistance = 0
    Antialiased = 1
    BlackWhite = 2


class AddVectorFieldToViewer:
    @staticmethod
    def AddToViewer(oViewer: object, oField: VectorField, clr: ColorLike, nStep: int = 10, fArrow: float = 1.0, nGroup: int = 0) -> None:
        if nStep <= 0:
            raise ValueError("nStep must be > 0")
        color = _to_rgba(clr)
        count = 0

        def _visit(pos: tuple[float, float, float], vec: tuple[float, float, float]) -> None:
            nonlocal count
            count += 1
            if count < nStep:
                return
            count = 0

            poly = PolyLine(color)
            poly.nAddVertex(pos)
            if abs(vec[0]) < 1e-12 and abs(vec[1]) < 1e-12 and abs(vec[2]) < 1e-12:
                poly.AddCross(fArrow)
            else:
                poly.nAddVertex((pos[0] + vec[0], pos[1] + vec[1], pos[2] + vec[2]))
                poly.AddArrow(fArrow)

            add_fn = getattr(oViewer, "Add", None)
            if callable(add_fn):
                add_fn(poly, nGroup)

        oField.TraverseActive(_visit)


