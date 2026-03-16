
from enum import IntEnum
import time
from typing import Callable, Protocol

class IAction(Protocol):
    def bAnimate(self, fTimeStamp: float) -> bool:
        ...


class Animation:
    class EType(IntEnum):
        ONCE = 0
        REPEAT = 1
        WIGGLE = 2

    def __init__(self, action: Callable[[float], None], duration_seconds: float, eType: "Animation.EType" = EType.ONCE) -> None:
        if duration_seconds <= 0.0:
            raise ValueError("duration_seconds must be > 0")
        self._action = action
        self._duration = float(duration_seconds)
        self._type = eType
        self._start_time = time.perf_counter()

    def bAnimate(self, fTimeStamp: float) -> bool:
        dt = max(0.0, float(fTimeStamp) - self._start_time)
        finished = dt >= self._duration
        t = dt / self._duration
        if self._type == Animation.EType.ONCE:
            if finished:
                t = 1.0
        elif self._type == Animation.EType.REPEAT:
            t = t % 1.0
            finished = False
        else:
            oscillation = t % 2.0
            t = oscillation if oscillation <= 1.0 else 2.0 - oscillation
            finished = False
        self._action(float(t))
        return not finished

    def End(self) -> None:
        self._action(1.0)


class AnimationQueue:
    def __init__(self) -> None:
        self._queue: list[IAction] = []

    def Clear(self) -> None:
        for action in self._queue:
            end_fn = getattr(action, "End", None)
            if callable(end_fn):
                end_fn()
        self._queue.clear()

    def Add(self, action: IAction) -> None:
        self._queue.append(action)

    def bIsIdle(self) -> bool:
        return len(self._queue) == 0

    def bPulse(self) -> bool:
        if not self._queue:
            return False
        now = time.perf_counter()
        to_remove: list[int] = []
        for i, action in enumerate(self._queue):
            if not action.bAnimate(now):
                to_remove.append(i)
        for idx in reversed(to_remove):
            self._queue.pop(idx)
        return len(self._queue) > 0
