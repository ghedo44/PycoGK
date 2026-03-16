from _common.types import ColorLike, clamp01

def _to_rgba(color: ColorLike) -> tuple[float, float, float, float]:
    if len(color) == 4:
        return (clamp01(color[0]), clamp01(color[1]), clamp01(color[2]), clamp01(color[3]))
    if len(color) == 3:
        return (clamp01(color[0]), clamp01(color[1]), clamp01(color[2]), 1.0)
    if len(color) == 1:
        c = clamp01(color[0])
        return (c, c, c, 1.0)
    raise ValueError("Color must have 1, 3, or 4 channels")



