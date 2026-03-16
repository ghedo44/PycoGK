

from pathlib import Path
import struct

from _common.types import clamp01

from .image import Image, ImageColor, ImageGrayScale


class TgaIo:
    @staticmethod
    def bYAxisFlipped(image_desc: int) -> bool:
        return (int(image_desc) & 0x20) != 0

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
                        handle.write(bytes((int(clamp01(b) * 255), int(clamp01(g) * 255), int(clamp01(r) * 255))))
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
                    iy = y if TgaIo.bYAxisFlipped(image_desc) else (height - y - 1)
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
                    iy = y if TgaIo.bYAxisFlipped(image_desc) else (height - y - 1)
                    for x in range(width):
                        value = handle.read(1)
                        if len(value) != 1:
                            raise ValueError("Unexpected EOF in TGA payload")
                        img.SetValue(x, iy, value[0] / 255.0)
                return img
        raise ValueError("Unsupported TGA format")


