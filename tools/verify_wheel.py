from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python tools/verify_wheel.py <wheel-path>")
        return 2

    wheel_path = Path(sys.argv[1])
    if not wheel_path.is_file():
        print(f"Wheel not found: {wheel_path}")
        return 2

    with zipfile.ZipFile(wheel_path, "r") as whl:
        names = whl.namelist()

    native_payload = [n for n in names if n.startswith("picogk/native/")]
    runtime_bins = [n for n in native_payload if n.endswith((".dll", ".dylib", ".so"))]

    if not native_payload:
        print("FAIL: wheel does not include picogk/native payload")
        return 1

    if not runtime_bins:
        print("FAIL: wheel includes picogk/native but no runtime binaries")
        return 1

    has_windows = any("/win-x64/" in n and n.endswith(".dll") for n in runtime_bins)
    has_macos_arm64 = any("/osx-arm64/" in n and n.endswith(".dylib") for n in runtime_bins)

    print(f"OK: found {len(native_payload)} native payload files")
    print(f"OK: found {len(runtime_bins)} runtime binaries")
    print(f"Windows runtime present: {has_windows}")
    print(f"macOS arm64 runtime present: {has_macos_arm64}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
