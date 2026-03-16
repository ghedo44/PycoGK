from __future__ import annotations

from _shared import run_lattice_example
from shapekernel import LatticeManifold, LatticePipe, LocalFrame


if __name__ == "__main__":
    run_lattice_example("LatticePipe basic", lambda: LatticePipe.from_frame(LocalFrame((0.0, 0.0, 0.0)), 30.0, 4.0))
    run_lattice_example("LatticeManifold basic", lambda: LatticeManifold.from_frame(LocalFrame((20.0, 0.0, 0.0)), 30.0, 4.0, 45.0, True, 0.4))
