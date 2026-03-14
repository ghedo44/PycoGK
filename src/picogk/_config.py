from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Iterable

DEFAULT_RUNTIME_NAME = "picogk.1.7"
STRING_LENGTH = 255


def _platform_suffixes() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return [".dll"]
    if system == "darwin":
        return [".dylib", ".so"]
    return [".so", ".dylib"]


def runtime_candidates(runtime_name: str = DEFAULT_RUNTIME_NAME) -> list[str]:
    suffixes = _platform_suffixes()
    candidates: list[str] = [runtime_name]
    for suffix in suffixes:
        candidates.append(f"{runtime_name}{suffix}")
        if not runtime_name.startswith("lib"):
            candidates.append(f"lib{runtime_name}{suffix}")
    return candidates


def _platform_native_subdirs() -> list[str]:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return ["win-x64"]

    if system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            return ["osx-arm64"]
        return ["osx-x64", "osx-arm64"]

    if "arm" in machine or "aarch64" in machine:
        return ["linux-arm64", "linux-x64"]
    return ["linux-x64", "linux-arm64"]


def _bundled_native_dirs() -> Iterable[Path]:
    base = Path(__file__).resolve().parent / "native"
    if not base.exists():
        return

    yielded = False
    for subdir in _platform_native_subdirs():
        p = base / subdir
        if p.exists():
            yielded = True
            yield p

    if not yielded:
        for p in base.iterdir():
            if p.is_dir():
                yield p


def candidate_library_paths(runtime_name: str = DEFAULT_RUNTIME_NAME) -> list[str]:
    env = os.getenv("PICOGK_RUNTIME_PATH")
    if env:
        return [env]

    candidates = runtime_candidates(runtime_name)
    paths = list(candidates)

    for native_dir in _bundled_native_dirs():
        for child in native_dir.rglob("*"):
            if not child.is_file():
                continue
            if child.name in candidates:
                paths.append(str(child))

    return paths
