# Publishing pycogk

This package publishes through GitHub Actions using trusted publishing.

## References

1. Official PicoGK: https://github.com/leap71/PicoGK
2. pycogk repository: https://github.com/ghedo44/PycoGK

## Workflow

Publishing workflow file:

`/.github/workflows/publish-pypi.yml`

Targets:

1. TestPyPI (recommended first)
2. PyPI

## Trusted Publisher Setup

Configure trusted publisher in TestPyPI and PyPI:

1. Owner: your GitHub owner
2. Repository: `PycoGK` (or current repository name)
3. Workflow: `publish-pypi.yml`
4. Environment: `testpypi` or `pypi`

## Automated Validation

Before publish, workflow validates:

1. package version from `pyproject.toml`
2. tag/version match for real PyPI publishes
3. duplicate version existence on target index

Validator script:

`tools/validate_publish.py`

## Local Preflight

```bash
python -m build
python tools/verify_wheel.py dist/*.whl
pytest -q
```

## Install Validation

From TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pycogk
```

From PyPI:

```bash
pip install pycogk
```

## Import Name

```python
import picogk
```
