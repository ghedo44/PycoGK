from __future__ import annotations


import threading
from typing import Callable

from .._core import Library
from .vedo_viewer import VedoViewer

def go(
    voxel_size_mm: float,
    task: Callable[[], None],
    *,
    end_on_task_completion: bool = False,
    viewer: VedoViewer | None = None,
) -> None:
    """Initialize runtime, execute task in worker thread, then clean up."""

    errors: list[BaseException] = []

    def _runner() -> None:
        try:
            task()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    Library.init(float(voxel_size_mm))
    try:
        Library.SetViewer(viewer)
        # For interactive viewer mode we render on the main thread after task completion.
        # Starting the background loop in that mode can race window lifetime on some backends.
        if viewer is not None and end_on_task_completion:
            viewer.start()

        worker = threading.Thread(target=_runner, daemon=True)
        worker.start()

        worker.join()

        if errors:
            raise errors[0]

        if viewer is not None and not end_on_task_completion:
            viewer.interact()
    finally:
        if viewer is not None:
            viewer.close()
        Library.ClearViewer()
        Library.destroy()

