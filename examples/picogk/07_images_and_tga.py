from __future__ import annotations


from pathlib import Path

from picogk import ImageColor, ImageGrayScale, TgaIo

"""
Example 07: Image classes and TGA IO
"""

OUT_GRAY = Path("example_gray.tga")
OUT_COLOR = Path("example_color.tga")


def main() -> None:
    gray = ImageGrayScale(64, 64)
    for y in range(64):
        for x in range(64):
            gray.SetValue(x, y, x / 63.0)
    gray.DrawLine(0, 0, 63, 63, 0.0)
    TgaIo.SaveTga(OUT_GRAY, gray)

    color = ImageColor(64, 64)
    for y in range(64):
        for x in range(64):
            color.SetValue(x, y, (x / 63.0, y / 63.0, 0.4, 1.0))
    color.DrawLine(0, 63, 63, 0, (1.0, 1.0, 1.0, 1.0))
    TgaIo.SaveTga(OUT_COLOR, color)

    e, w, h = TgaIo.GetFileInfo(OUT_COLOR)
    loaded = TgaIo.LoadTga(OUT_COLOR)
    print("type:", e, "size:", w, h, "sample:", loaded.clrValue(10, 10))


if __name__ == "__main__":
    main()
