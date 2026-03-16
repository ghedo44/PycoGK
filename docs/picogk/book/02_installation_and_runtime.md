# Chapter 2: Installation and Runtime

## Install Options

Install from PyPI:

```bash
pip install pycogk
```

Install from GitHub repository:

```bash
pip install "git+https://github.com/ghedo44/PycoGK.git"
```


## Import Name

The package is published as `pycogk`, but imported as:

```python
import picogk
```

## Runtime Loading

pycogk loads a PicoGK native library through `ctypes`.

Search strategy:

1. Bundled runtime files inside the package.
2. Candidate library names for the current platform.
3. Optional explicit path via environment variable.

## For Unsupported Platforms

Set `PICOGK_RUNTIME_PATH` to a compatible runtime file.

PowerShell:

```powershell
$env:PICOGK_RUNTIME_PATH = "C:\path\to\picogk.1.7.dll"
python your_script.py
```

Bash:

```bash
export PICOGK_RUNTIME_PATH="/path/to/picogk.1.7.dylib"
python your_script.py
```

## Validate Installation

Minimal validation script:

```python
from picogk import go, Library

def task() -> None:
    print(Library.strName())
    print(Library.strVersion())

go(0.5, task, end_on_task_completion=True)
```

## Common Runtime Errors

1. Missing library file: check package install and `PICOGK_RUNTIME_PATH`.
2. Missing symbols: runtime binary version mismatch.
3. Architecture mismatch: x64 package with arm runtime (or inverse).

## Chapter Summary

You now have a repeatable install and runtime validation process.

Next: first real project.
