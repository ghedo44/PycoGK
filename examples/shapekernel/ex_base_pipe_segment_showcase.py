from __future__ import annotations

import math

from _shared import example_frames, run_mesh_example
from shapekernel import BasePipeSegment, LineModulation, LocalFrame


if __name__ == "__main__":
    run_mesh_example(
        "BasePipeSegment basic",
        lambda: BasePipeSegment.from_frame(
            LocalFrame((0.0, 0.0, 0.0)),
            28.0,
            2.0,
            7.0,
            LineModulation(0.0),
            LineModulation(1.2 * math.pi),
            BasePipeSegment.EMethod.START_END,
        ),
    )
    run_mesh_example(
        "BasePipeSegment spined",
        lambda: BasePipeSegment.from_frames(
            example_frames(),
            1.5,
            5.0,
            LineModulation(lambda lr: 0.5 * math.pi * lr),
            LineModulation(lambda lr: math.pi * (0.4 + 0.1 * math.sin(6.0 * lr))),
            BasePipeSegment.EMethod.MID_RANGE,
        ),
    )
