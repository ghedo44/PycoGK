# Chapter 8: Troubleshooting

## Runtime Load Failures

Symptoms:

1. `PicoGKLoadError`
2. Missing DLL/dylib errors

Checklist:

1. Confirm package install succeeded.
2. Confirm architecture matches Python runtime.
3. Set `PICOGK_RUNTIME_PATH` explicitly.
4. Verify dependent native libraries are present.

## Empty Geometry Results

Symptoms:

1. Zero triangles from mesh conversion
2. Empty slices/CLI output

Checklist:

1. Validate initial shape bounds.
2. Check voxel size (too coarse can erase detail).
3. Inspect intermediate results after each operation.
4. Verify layer height relative to model scale.

## Viewer Instability

Symptoms:

1. Window closes unexpectedly
2. Offscreen crashes/hard aborts on specific systems

Checklist:

1. Use interactive mode where possible.
2. Keep repeated viewer stress tests behind env flags.
3. Separate geometry correctness tests from rendering stress tests.

## Symbol/Parity Mismatch

Symptoms:

1. Methods differ from C# examples
2. Runtime-specific unavailable symbols

Checklist:

1. Read [Parity Matrix](../PARITY_MATRIX.md).
2. Confirm runtime version compatibility.
3. Use adapted APIs where marked in docs.

## Chapter Summary

You now have a practical debugging playbook for the most common pycogk issues.
