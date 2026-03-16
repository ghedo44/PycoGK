from __future__ import annotations

import math
import numpy as np

from picogk import BBox3, Lattice, Mesh, Voxels

from .._types import Vec3, Vector3Like, as_np3, as_vec3
from ..frames import Frames
from ..modulations import LineModulation
from ..utils.utils import LocalFrame
from .basics import BaseShape

class LatticePipe(BaseShape):
    """Lattice-based round pipe.

    .. code-block:: python

        LatticePipe.from_frame(frame, fLength=20, fRadius=10)
        LatticePipe.from_frames(frames, fRadius=10)
    """

    def __init__(
        self,
        aFrames: Frames,
        fRadius: float,
        *,
        _length_steps: int,
    ) -> None:
        """Internal – use :meth:`from_frame` or :meth:`from_frames`."""
        super().__init__()
        self.m_aFrames = aFrames
        self.SetLengthSteps(_length_steps)
        self.m_oRadiusModulation = LineModulation(fRadius)

    @classmethod
    def from_frame(
        cls,
        oFrame: LocalFrame,
        fLength: float = 20.0,
        fRadius: float = 10.0,
    ) -> "LatticePipe":
        """Create a lattice pipe from a :class:`LocalFrame`, length, and radius."""
        return cls(Frames.from_length(fLength, oFrame), fRadius, _length_steps=100)

    @classmethod
    def from_frames(
        cls,
        aFrames: Frames,
        fRadius: float = 10.0,
    ) -> "LatticePipe":
        """Create a lattice pipe whose spine is driven by a :class:`Frames` object."""
        return cls(aFrames, fRadius, _length_steps=500)

    def SetRadius(self, oModulation: LineModulation) -> None:
        self.m_oRadiusModulation = oModulation

    def SetLengthSteps(self, nLengthSteps: int) -> None:
        self.m_nLengthSteps = int(nLengthSteps)

    def voxConstruct(self) -> Voxels:
        return Voxels.from_lattice(self.latConstruct())

    def latConstruct(self) -> Lattice:
        lattice = Lattice()
        for iz in range(1, self.m_nLengthSteps):
            lr0 = (1.0 / self.m_nLengthSteps) * (iz - 1)
            lr1 = (1.0 / self.m_nLengthSteps) * iz
            p0 = self.vecGetSpinePoint(lr0)
            p1 = self.vecGetSpinePoint(lr1)
            b0 = self.fGetRadius(lr0)
            b1 = self.fGetRadius(lr1)
            lattice.add_beam(p0, p1, b0, b1)
        return lattice

    def vecGetSpinePoint(self, fLengthRatio: float) -> Vec3:
        return self.m_fnTrafo(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))

    def fGetRadius(self, fLengthRatio: float) -> float:
        return self.m_oRadiusModulation.fGetModulation(fLengthRatio)


class LatticeManifold(LatticePipe):
    """Lattice pipe with teardrop-shaped cross-sections to improve printability.

    The overhang angle drives the teardrop geometry; the extension flag controls
    whether the teardrop points upward only or in both ±Z directions.

    .. code-block:: python

        LatticeManifold.from_frame(
            frame, fLength=30, fRadius=4,
            fMaxOverhangAngle=45, bExtendBothSides=True, fMinPrintableRadius=0.1,
        )
        LatticeManifold.from_frames(
            frames, fRadius=4,
            fMaxOverhangAngle=45, bExtendBothSides=False, fMinPrintableRadius=0.1,
        )
    """

    def __init__(
        self,
        aFrames: Frames,
        fRadius: float,
        fMaxOverhangAngle: float,
        bExtendBothSides: bool,
        fMinPrintableRadius: float,
        *,
        _length_steps: int,
    ) -> None:
        """Internal – use :meth:`from_frame` or :meth:`from_frames`."""
        super().__init__(aFrames, fRadius, _length_steps=_length_steps)
        self.m_fMaxPrintableRadius = fMinPrintableRadius
        self.m_fLimitAngle = fMaxOverhangAngle
        self.m_bExtendBothSides = bExtendBothSides

    @classmethod
    def from_frame(
        cls,
        oFrame: LocalFrame,
        fLength: float = 20.0,
        fRadius: float = 10.0,
        fMaxOverhangAngle: float = 45.0,
        bExtendBothSides: bool = False,
        fMinPrintableRadius: float = 0.1,
    ) -> "LatticeManifold":
        """Create a manifold pipe from a :class:`LocalFrame`."""
        return cls(
            Frames.from_length(fLength, oFrame),
            fRadius,
            fMaxOverhangAngle,
            bExtendBothSides,
            fMinPrintableRadius,
            _length_steps=100,
        )

    @classmethod
    def from_frames(
        cls,
        aFrames: Frames,
        fRadius: float = 10.0,
        fMaxOverhangAngle: float = 45.0,
        bExtendBothSides: bool = False,
        fMinPrintableRadius: float = 0.1,
    ) -> "LatticeManifold":
        """Create a manifold pipe whose spine is driven by a :class:`Frames` object."""
        return cls(
            aFrames,
            fRadius,
            fMaxOverhangAngle,
            bExtendBothSides,
            fMinPrintableRadius,
            _length_steps=500,
        )

    def latConstruct(self) -> Lattice:
        lattice = Lattice()
        for iz in range(self.m_nLengthSteps):
            lr = (1.0 / self.m_nLengthSteps) * iz
            p = self.vecGetSpinePoint(lr)
            beam = self.fGetRadius(lr)
            lattice.add_beam(p, p, beam, beam)
            self._add_tip(lattice, p, beam, True)
            if self.m_bExtendBothSides:
                self._add_tip(lattice, p, beam, False)
        return lattice

    def _add_tip(self, lattice: Lattice, vecPt: Vector3Like, fBeam: float, bZPositive: bool = True) -> None:
        half_alpha = 90.0 - self.m_fLimitAngle
        r = fBeam
        h = r * (1.0 - math.cos(math.radians(half_alpha)))
        s = 2.0 * r * math.sin(math.radians(half_alpha))
        tip_length = math.tan(math.radians(half_alpha)) * (0.5 * s - self.m_fMaxPrintableRadius)
        p = as_np3(vecPt)

        if bZPositive:
            mid = p + (r - h) * np.array([0.0, 0.0, 1.0], dtype=np.float64)
            tip = mid + tip_length * np.array([0.0, 0.0, 1.0], dtype=np.float64)
        else:
            mid = p - (r - h) * np.array([0.0, 0.0, 1.0], dtype=np.float64)
            tip = mid - tip_length * np.array([0.0, 0.0, 1.0], dtype=np.float64)

        lattice.add_beam(as_vec3(mid), as_vec3(tip), 0.5 * s, self.m_fMaxPrintableRadius, False)

