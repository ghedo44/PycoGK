from __future__ import annotations

from _shared import example_frames, run_lattice_example
from shapekernel import LatticeManifold


if __name__ == "__main__":
    run_lattice_example("LatticeManifold showcase", lambda: LatticeManifold.from_frames(example_frames(), 10.0, 45.0, True, 0.3))
