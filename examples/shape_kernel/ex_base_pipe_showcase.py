from __future__ import annotations

import math

from _shared import example_frames, run_mesh_example
from shape_kernel import BasePipe, LocalFrame, SurfaceModulation


if __name__ == "__main__":
    run_mesh_example("BasePipe basic", lambda: BasePipe.from_frame(LocalFrame((-30.0, 0.0, 0.0)), 24.0, 2.0, 7.0))
    run_mesh_example(
        "BasePipe modulated",
        lambda: (lambda shape: (shape.SetRadius(SurfaceModulation(lambda phi, lr: 1.0 + 0.5 * math.sin(2.0 * math.pi * lr)), SurfaceModulation(lambda phi, lr: 6.0 + 0.8 * math.cos(3.0 * phi))), shape)[1])(BasePipe.from_frame(LocalFrame((30.0, 0.0, 0.0)), 24.0, 2.0, 7.0)),
    )
    run_mesh_example(
        "BasePipe spined",
        lambda: BasePipe.from_frames(example_frames(), 1.5, 4.0),
    )
