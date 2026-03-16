from __future__ import annotations

from _shared import example_frames


if __name__ == "__main__":
    frames = example_frames()
    points = frames.aGetPoints(12)
    for index, point in enumerate(points[:5]):
        print(index, point)
    print("samples", len(points))
