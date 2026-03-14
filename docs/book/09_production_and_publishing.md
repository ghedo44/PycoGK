# Chapter 9: Production and Publishing

## Production Checklist

Before release:

1. Run test suite (`pytest -q`).
2. Build package (`python -m build`).
3. Verify wheel payload (`python tools/verify_wheel.py dist/*.whl`).
4. Review readiness gates in [Production Readiness](../PRODUCTION_READINESS.md).

## Versioning Strategy

1. Use semantic versioning where possible.
2. Update `project.version` for every release.
3. Tag releases with `vX.Y.Z`.

## PyPI Publishing

Use GitHub trusted publishing workflow documented in [Publishing Guide](../PUBLISHING.md).

Key guardrails:

1. Tag/version validation before publish.
2. Duplicate-version check against target index.
3. Manual TestPyPI smoke before PyPI release.

## Cross-Platform Reality

Current bundled runtimes are limited to selected targets.

For wider production deployment:

1. Expand bundled runtime set.
2. Run CI matrix validation across all supported targets.
3. Keep fallback runtime path documented for edge deployments.

## Long-Term Maintenance

1. Track parity against official PicoGK changes.
2. Add regression tests for each newly exposed API.
3. Keep examples aligned with runtime behavior.
4. Review viewer backend risks when updating vedo/VTK.

## Final Advice

Treat pycogk as an engineering toolchain component:

1. Make builds reproducible.
2. Keep test evidence per release.
3. Log metadata into exported artifacts.

This approach makes production incidents easier to diagnose and fix.
