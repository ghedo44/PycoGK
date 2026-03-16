from __future__ import annotations

import math

from _shared import run_mesh_example
from shapekernel import BaseRing, LocalFrame, SurfaceModulation


if __name__ == "__main__":
    run_mesh_example("BaseRing basic", lambda: BaseRing(LocalFrame((0.0, 0.0, 0.0)), 20.0, 4.0))
    run_mesh_example(
        "BaseRing modulated",
        lambda: (lambda shape: (shape.SetRadius(SurfaceModulation(lambda phi, alpha: 3.5 + 0.8 * math.cos(5.0 * phi) * (0.5 + alpha / (2.0 * math.pi)))), shape)[1])(BaseRing(LocalFrame((28.0, 0.0, 0.0)), 18.0, 4.0)),
    )
