from __future__ import annotations

from _shared import example_frames, run_lattice_example
from shapekernel import LatticePipe


if __name__ == "__main__":
    run_lattice_example("LatticePipe showcase", lambda: LatticePipe.from_frames(example_frames(), 2.2))
