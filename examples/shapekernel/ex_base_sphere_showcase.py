from __future__ import annotations

import math

from _shared import run_mesh_example
from shapekernel import BaseSphere, LocalFrame, SurfaceModulation


if __name__ == "__main__":
    run_mesh_example("BaseSphere basic", lambda: BaseSphere(LocalFrame((-16.0, 0.0, 0.0)), 6.0))
    run_mesh_example(
        "BaseSphere modulated",
        lambda: (lambda shape: (shape.SetRadius(SurfaceModulation(lambda phi, theta: 5.0 + 0.6 * math.cos(6.0 * phi) * math.sin(theta))), shape)[1])(BaseSphere(LocalFrame((16.0, 0.0, 0.0)), 5.0)),
    )
