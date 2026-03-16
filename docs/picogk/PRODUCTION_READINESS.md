# Production Readiness

This document summarizes practical gates for shipping pycogk in production.

## Scope

pycogk is an unofficial Python package around the official PicoGK runtime.

1. Official PicoGK: https://github.com/leap71/PicoGK
2. pycogk repository: https://github.com/ghedo44/PycoGK

## Required Gates

1. API surface gate
- Public symbols required by the package contract are exported.
- Automated by tests in `tests/test_production_readiness.py`.

2. Runtime discovery gate
- Runtime candidate list is non-empty.
- Automated by `tests/test_production_readiness.py`.

3. Bundled runtime gate
- If platform runtime folders exist, they include files.
- Automated by `tests/test_production_readiness.py`.

4. Functional regression gate
- Runtime/utility/parity tests pass.
- Automated by `pytest -q`.

5. Package artifact gate
- Wheel includes runtime payload.
- Automated by `tools/verify_wheel.py`.

## Operational Constraints

1. Viewer backend is vedo-based and adapted, not identical to C# native viewer.
2. Bundled runtime coverage may not include every OS/arch.
3. Offscreen viewer stress behavior can vary by backend/driver.

