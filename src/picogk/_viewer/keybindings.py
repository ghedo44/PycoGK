from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .vedo_viewer import VedoViewer


class IViewerAction(Protocol):
    def Do(self, viewer: "VedoViewer") -> None:
        ...


class IKeyHandler(Protocol):
    def bHandleEvent(
        self,
        viewer: "VedoViewer",
        eKey: str,
        bPressed: bool,
        bShift: bool,
        bCtrl: bool,
        bAlt: bool,
        bCmd: bool,
    ) -> bool:
        ...


class KeyAction:
    def __init__(
        self,
        xAction: IViewerAction,
        eKey: str,
        bPressed: bool = False,
        bShift: bool = False,
        bCtrl: bool = False,
        bAlt: bool = False,
        bCmd: bool = False,
    ) -> None:
        self._action = xAction
        self._key = str(eKey).lower()
        self._pressed = bool(bPressed)
        self._shift = bool(bShift)
        self._ctrl = bool(bCtrl)
        self._alt = bool(bAlt)
        self._cmd = bool(bCmd)

    def bKeyEquals(
        self,
        eKey: str,
        bPressed: bool,
        bShift: bool,
        bCtrl: bool,
        bAlt: bool,
        bCmd: bool,
    ) -> bool:
        return (
            self._key == str(eKey).lower()
            and self._pressed == bool(bPressed)
            and self._shift == bool(bShift)
            and self._ctrl == bool(bCtrl)
            and self._alt == bool(bAlt)
            and self._cmd == bool(bCmd)
        )

    def Do(self, viewer: "VedoViewer") -> None:
        self._action.Do(viewer)


class KeyHandler:
    def __init__(self) -> None:
        self._actions: list[KeyAction] = []

    def AddAction(self, action: KeyAction) -> None:
        self._actions.insert(0, action)

    def bHandleEvent(
        self,
        viewer: "VedoViewer",
        eKey: str,
        bPressed: bool,
        bShift: bool,
        bCtrl: bool,
        bAlt: bool,
        bCmd: bool,
    ) -> bool:
        for action in self._actions:
            if action.bKeyEquals(eKey, bPressed, bShift, bCtrl, bAlt, bCmd):
                action.Do(viewer)
                return True
        return False


class RotateToNextRoundAngleAction:
    class EDir(IntEnum):
        Dir_Down = 0
        Dir_Up = 1
        Dir_Left = 2
        Dir_Right = 3

    def __init__(self, eDir: "RotateToNextRoundAngleAction.EDir") -> None:
        self._dir = eDir

    def Do(self, viewer: "VedoViewer") -> None:
        step = 15.0
        if self._dir == self.EDir.Dir_Left:
            viewer.AdjustViewAngles(-step, 0.0)
        elif self._dir == self.EDir.Dir_Right:
            viewer.AdjustViewAngles(step, 0.0)
        elif self._dir == self.EDir.Dir_Up:
            viewer.AdjustViewAngles(0.0, step)
        else:
            viewer.AdjustViewAngles(0.0, -step)



