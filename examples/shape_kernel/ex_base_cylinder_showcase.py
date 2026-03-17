from __future__ import annotations

import math

from _shared import example_frames, run_mesh_example
from shape_kernel import BaseCylinder, LocalFrame, SurfaceModulation


if __name__ == "__main__":
    run_mesh_example("BaseCylinder basic", lambda: BaseCylinder.from_frame(LocalFrame((-40.0, 0.0, 0.0)), 24.0, 8.0))
    run_mesh_example(
        "BaseCylinder modulated",
        lambda: (lambda shape: (shape.SetRadius(SurfaceModulation(lambda phi, lr: 5.0 + 1.2 * math.cos(6.0 * lr) + 0.5 * math.sin(3.0 * phi))), shape)[1])(BaseCylinder.from_frame(LocalFrame((40.0, 0.0, 0.0)), 24.0, 6.0)),
    )
    run_mesh_example(
        "BaseCylinder spined",
        lambda: (lambda shape: (shape.SetRadius(SurfaceModulation(lambda phi, lr: 4.0 + 1.5 * math.sin(2.0 * math.pi * lr))), shape)[1])(BaseCylinder.from_frames(example_frames(), 5.0)),
    )
