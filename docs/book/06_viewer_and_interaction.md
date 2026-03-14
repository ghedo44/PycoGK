# Chapter 6: Viewer and Interaction

## Viewer Model

pycogk includes a vedo-backed viewer (`VedoViewer`) with C#-style control methods.

Important: this is an adaptation, not the exact official C# native viewer backend.

## Basic Viewer Usage

```python
from picogk import Lattice, Voxels, VedoViewer, go

viewer = VedoViewer(title="demo", offscreen=False)


def task() -> None:
    with Lattice() as lat:
        lat.AddSphere((0, 0, 0), 10)
        with Voxels.from_lattice(lat) as vox:
            viewer.Add(vox, nGroupID=1)
            viewer.SetViewAngles(45.0, 25.0)
            viewer.RequestUpdate()


go(0.5, task, end_on_task_completion=False, viewer=viewer)
```

## Groups and Styling

Group-oriented controls:

1. `SetGroupVisible`
2. `SetGroupStatic`
3. `SetGroupMaterial`
4. `SetGroupMatrix`

Use groups to separate objects by function (base part, tools, references).

## Camera and Output

1. `SetViewAngles`, `AdjustViewAngles`
2. `SetFov`, `SetZoom`, `SetPerspective`
3. `RequestScreenShot`
4. `StartTimeLapse` / `StopTimeLapse`

## Practical Caveats

1. Offscreen backends can behave differently across environments.
2. Long render loops should be validated on target machines.
3. For CI/headless systems, keep viewer tests optional or controlled by env vars.

## Chapter Summary

You can now use the viewer effectively while understanding its backend limits.
