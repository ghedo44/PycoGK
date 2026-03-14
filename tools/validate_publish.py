from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def read_project_meta() -> tuple[str, str]:
    try:
        import tomllib  # py311+
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    name = str(project.get("name", "")).strip()
    version = str(project.get("version", "")).strip()
    if not name or not version:
        raise RuntimeError("project.name and project.version must be set in pyproject.toml")
    return name, version


def normalize_tag(tag: str) -> str:
    out = tag.strip()
    if out.startswith("refs/tags/"):
        out = out[len("refs/tags/") :]
    if out.startswith("v"):
        out = out[1:]
    return out


def version_exists(index_host: str, package_name: str, version: str) -> bool:
    url = f"https://{index_host}/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise RuntimeError(f"Failed to query package index: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to query package index: {exc}") from exc

    releases = data.get("releases", {})
    files = releases.get(version, [])
    return bool(files)


def main() -> int:
    target = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "testpypi"
    if target not in {"testpypi", "pypi"}:
        print("Target must be one of: testpypi, pypi")
        return 2

    package_name, version = read_project_meta()
    ref_name = str(__import__("os").environ.get("GITHUB_REF_NAME", "")).strip()

    print(f"Package: {package_name}")
    print(f"Version: {version}")
    print(f"Target: {target}")

    # Strict rule for real PyPI publishes: publish only from matching tag.
    if target == "pypi":
        if not ref_name:
            print("ERROR: GITHUB_REF_NAME is empty; PyPI publish must run from a tag")
            return 1
        normalized = normalize_tag(ref_name)
        if normalized != version:
            print(
                "ERROR: tag/version mismatch: "
                f"ref '{ref_name}' -> '{normalized}', project version '{version}'"
            )
            print("Use a release tag like v<version> or <version>.")
            return 1

    host = "pypi.org" if target == "pypi" else "test.pypi.org"
    if version_exists(host, package_name, version):
        print(f"ERROR: version {version} already exists on {host} for {package_name}")
        return 1

    print("Publish validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
