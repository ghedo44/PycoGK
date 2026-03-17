from __future__ import annotations

import math

from _shared import run_mesh_example
from shape_kernel import BaseLens, LocalFrame, SurfaceModulation


if __name__ == "__main__":
    run_mesh_example("BaseLens basic", lambda: BaseLens(LocalFrame((0.0, 0.0, 0.0)), 6.0, 2.0, 10.0))
    run_mesh_example(
        "BaseLens modulated",
        lambda: (lambda shape: (shape.SetHeight(SurfaceModulation(lambda phi, rr: -1.0 - rr), SurfaceModulation(lambda phi, rr: 4.0 + 0.8 * math.cos(4.0 * phi) * (1.0 - rr))), shape)[1])(BaseLens(LocalFrame((24.0, 0.0, 0.0)), 5.0, 1.0, 8.0)),
    )
