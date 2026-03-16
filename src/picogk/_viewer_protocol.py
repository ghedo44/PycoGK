"""Leaf module – defines the IViewer structural protocol.

This module has *no* imports from the rest of the picogk package, so it can be
imported by both the ``data`` layer (Library) and the ``viewer`` layer
(VedoViewer) without creating any circular dependency.
"""
from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable


@runtime_checkable
class IViewer(Protocol):
    """Structural interface that any viewer object passed to Library must satisfy.

    VedoViewer (and any future viewer implementation) satisfies this protocol
    through duck-typing – no explicit inheritance is required.
    """

    def Add(self, xObject: object, nGroupID: int = 0) -> int: ...
    def RequestUpdate(self) -> None: ...
    def RequestScreenShot(self, strScreenShotPath: str) -> None: ...
    def SetGroupVisible(self, nGroupID: int, bVisible: bool) -> None: ...
    def SetGroupStatic(self, nGroupID: int, bStatic: bool) -> None: ...
    def SetGroupMaterial(
        self,
        nGroupID: int,
        clr: Sequence[float],
        fMetallic: float,
        fRoughness: float,
    ) -> None: ...
    def SetGroupMatrix(self, nGroupID: int, mat: Sequence[float]) -> None: ...
    def SetViewAngles(self, fOrbit: float, fElevation: float) -> None: ...
    def AdjustViewAngles(
        self, fOrbitRelative: float, fElevationRelative: float
    ) -> None: ...
    def AddKeyHandler(self, xKeyHandler: Any) -> None: ...
    def AddAnimation(self, oAnim: Any) -> None: ...
