from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

@dataclass
class _TimeLapseState:
    interval_ms: float
    path: Path
    file_name: str
    current_frame: int
    paused: bool
    next_due_ms: float

    @classmethod
    def create(
        cls,
        fIntervalInMilliseconds: float,
        strPath: str,
        strFileName: str,
        nStartFrame: int,
        bPaused: bool,
    ) -> "_TimeLapseState":
        now = time.perf_counter() * 1000.0
        path = Path(strPath)
        path.mkdir(parents=True, exist_ok=True)
        return cls(
            interval_ms=float(fIntervalInMilliseconds),
            path=path,
            file_name=strFileName,
            current_frame=int(nStartFrame),
            paused=bool(bPaused),
            next_due_ms=now + float(fIntervalInMilliseconds),
        )

    def Pause(self) -> None:
        self.paused = True

    def Resume(self) -> None:
        self.paused = False
        self.next_due_ms = (time.perf_counter() * 1000.0) + self.interval_ms

    def bDue(self) -> tuple[bool, str]:
        if self.paused:
            return False, ""
        now = time.perf_counter() * 1000.0
        if now < self.next_due_ms:
            return False, ""
        frame_path = self.path / f"{self.file_name}{self.current_frame:05d}.png"
        self.current_frame += 1
        self.next_due_ms = now + self.interval_ms
        return True, str(frame_path)



