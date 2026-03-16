from __future__ import annotations

from pathlib import Path

from picogk import go
from picogk._errors import PicoGKLoadError


ROOT = Path(__file__).resolve().parents[1]


def runtime_available() -> bool:
    try:
        go(0.5, lambda: None, end_on_task_completion=True)
        return True
    except PicoGKLoadError:
        return False
