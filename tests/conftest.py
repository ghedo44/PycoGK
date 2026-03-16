from __future__ import annotations

import sys
from pathlib import Path

# Keep helper imports stable across pytest import modes and CI runners.
_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent

for _path in (_REPO_ROOT, _TESTS_DIR):
    path_str = str(_path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
