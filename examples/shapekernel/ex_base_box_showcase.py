from __future__ import annotations

import math

from _shared import example_frames, run_mesh_example
from shapekernel import BaseBox, LineModulation, LocalFrame


if __name__ == "__main__":
    run_mesh_example("BaseBox basic", lambda: BaseBox.from_frame(LocalFrame((-50.0, 0.0, 0.0)), 20.0, 10.0, 15.0))
    run_mesh_example(
        "BaseBox modulated",
        lambda: (lambda shape: (shape.SetWidth(LineModulation(lambda lr: 10.0 - 3.0 * math.cos(8.0 * lr))), shape.SetDepth(LineModulation(lambda lr: 8.0 - math.cos(40.0 * lr))), shape)[2])(BaseBox.from_frame(LocalFrame((50.0, 0.0, 0.0)), 20.0)),
    )
    run_mesh_example(
        "BaseBox spined",
        lambda: (lambda shape: (shape.SetWidth(LineModulation(lambda lr: 10.0 - 3.0 * math.cos(8.0 * lr))), shape.SetDepth(LineModulation(lambda lr: 8.0 - math.cos(40.0 * lr))), shape)[2])(BaseBox.from_frames(example_frames())),
    )
