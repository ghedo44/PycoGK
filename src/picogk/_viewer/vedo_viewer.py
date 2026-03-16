from __future__ import annotations

import io
import math
import threading
import time
import zipfile
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Optional, Sequence, cast

import numpy as np
import vedo
from vedo import Mesh as VedoMesh

from .._types import ColorFloat
from .._core import Mesh, PolyLine, Voxels
from .keybindings import IKeyHandler, KeyAction, KeyHandler, RotateToNextRoundAngleAction
from .timelapse import _TimeLapseState

class VedoViewer:
    """C#-style viewer facade adapted to vedo with a thread-safe command queue."""

    def __init__(self, title: str = "PicoGK", offscreen: bool = False) -> None:
        self._plotter = vedo.Plotter(title=title, interactive=False, offscreen=offscreen)
        self._queue: Queue[tuple[str, object]] = Queue()
        self._running = False
        self._closed = False
        self._thread: Optional[threading.Thread] = None
        self._actors: dict[int, object] = {}
        self._groups: dict[int, set[int]] = {}
        self._object_to_actor: dict[int, int] = {}
        self._group_visible: dict[int, bool] = {}
        self._group_static: dict[int, bool] = {}
        self._group_material: dict[int, tuple[tuple[float, float, float, float], float, float]] = {}
        self._group_matrix: dict[int, tuple[float, ...]] = {}
        self._next_actor_id = 1
        self._idle = True
        self._light_setup_raw: tuple[bytes, bytes] | None = None
        self._timelapse: _TimeLapseState | None = None
        self._animations: list[Any] = []
        self._key_handlers: list[IKeyHandler] = []
        self._key_callback_handle: object | None = None

        self.m_fElevation = 30.0
        self.m_fOrbit = 45.0
        self.m_fFov = 45.0
        self.m_fZoom = 1.0
        self.m_bPerspective = True

        self._default_key_handler = KeyHandler()
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Down), "Down"))
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Up), "Up"))
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Left), "Left"))
        self._default_key_handler.AddAction(KeyAction(RotateToNextRoundAngleAction(RotateToNextRoundAngleAction.EDir.Dir_Right), "Right"))
        self.AddKeyHandler(self._default_key_handler)

    def _enqueue(self, cmd: str, payload: object = None) -> None:
        self._idle = False
        self._queue.put((cmd, payload))

    def _stop_loop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _is_visible(self, actor: object) -> bool:
        visible_fn = getattr(actor, "is_visible", None)
        if callable(visible_fn):
            try:
                return bool(visible_fn())
            except Exception:
                return True
        return True

    def _set_actor_visible(self, actor: object, visible: bool) -> None:
        if visible:
            on_fn = getattr(actor, "on", None)
            if callable(on_fn):
                on_fn()
                return
        else:
            off_fn = getattr(actor, "off", None)
            if callable(off_fn):
                off_fn()
                return

        set_vis = getattr(actor, "SetVisibility", None)
        if callable(set_vis):
            set_vis(bool(visible))

    def _set_actor_pickable(self, actor: object, pickable: bool) -> None:
        pickable_fn = getattr(actor, "pickable", None)
        if callable(pickable_fn):
            try:
                pickable_fn(bool(pickable))
                return
            except Exception:
                pass
        set_pickable = getattr(actor, "SetPickable", None)
        if callable(set_pickable):
            set_pickable(bool(pickable))

    def _apply_matrix_points(self, actor: object, mat: tuple[float, ...]) -> None:
        if len(mat) != 16:
            raise ValueError("mat must contain 16 values")
        pts_fn = getattr(actor, "points", None)
        if not callable(pts_fn):
            return
        try:
            points = np.asarray(pts_fn(), dtype=np.float64)
        except Exception:
            return
        if points.ndim != 2 or points.shape[0] == 0 or points.shape[1] != 3:
            return
        m = np.array(mat, dtype=np.float64).reshape((4, 4))
        homo = np.hstack([points, np.ones((points.shape[0], 1), dtype=np.float64)])
        transformed = (homo @ m.T)[:, :3]
        pts_fn(transformed.astype(np.float32))

    def _apply_group_style_to_actor(self, actor_id: int) -> None:
        actor = self._actors.get(actor_id)
        if actor is None:
            return
        group_id = None
        for gid, members in self._groups.items():
            if actor_id in members:
                group_id = gid
                break
        if group_id is None:
            return

        visible = self._group_visible.get(group_id)
        if visible is not None:
            self._set_actor_visible(actor, visible)

        static = self._group_static.get(group_id)
        if static is not None:
            self._set_actor_pickable(actor, not static)

        material = self._group_material.get(group_id)
        if material is not None:
            clr, _metallic, _roughness = material
            color_fn = getattr(actor, "c", None)
            if callable(color_fn):
                color_fn((clr[0], clr[1], clr[2]))
            alpha_fn = getattr(actor, "alpha", None)
            if callable(alpha_fn):
                alpha_fn(clr[3])

        matrix = self._group_matrix.get(group_id)
        if matrix is not None:
            self._apply_matrix_points(actor, matrix)

    def _active_bounds(self) -> tuple[float, float, float, float, float, float] | None:
        items: list[tuple[float, float, float, float, float, float]] = []
        for actor in self._actors.values():
            if not self._is_visible(actor):
                continue
            bounds_fn = getattr(actor, "bounds", None)
            if not callable(bounds_fn):
                continue
            try:
                raw_bounds = cast(Sequence[object], bounds_fn())
                b = tuple(float(cast(Any, v)) for v in raw_bounds)
            except Exception:
                continue
            if len(b) == 6:
                items.append(cast(tuple[float, float, float, float, float, float], b))
        if not items:
            return None
        xmin = min(v[0] for v in items)
        xmax = max(v[1] for v in items)
        ymin = min(v[2] for v in items)
        ymax = max(v[3] for v in items)
        zmin = min(v[4] for v in items)
        zmax = max(v[5] for v in items)
        return (xmin, xmax, ymin, ymax, zmin, zmax)

    def _update_camera(self) -> None:
        bounds = self._active_bounds()
        if bounds is None:
            return
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        cx = (xmin + xmax) * 0.5
        cy = (ymin + ymax) * 0.5
        cz = (zmin + zmax) * 0.5
        rx = max(1e-3, xmax - xmin)
        ry = max(1e-3, ymax - ymin)
        rz = max(1e-3, zmax - zmin)
        radius = max(rx, ry, rz) * 1.5 * max(1e-3, self.m_fZoom)

        orbit = math.radians(self.m_fOrbit)
        elev = math.radians(self.m_fElevation)
        cos_e = math.cos(elev)
        ex = cx + (math.cos(orbit) * cos_e * radius)
        ey = cy + (math.sin(orbit) * cos_e * radius)
        ez = cz + (math.sin(elev) * radius)

        cam = self._plotter.camera
        cam.SetPosition(ex, ey, ez)
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetViewUp(0.0, 0.0, 1.0)
        cam.SetViewAngle(float(self.m_fFov))
        if self.m_bPerspective:
            cam.ParallelProjectionOff()
        else:
            cam.ParallelProjectionOn()

    def _pulse_animations(self) -> bool:
        if not self._animations:
            return False
        current = time.perf_counter() - self._anim_start
        keep: list[Any] = []
        changed = False
        for anim in self._animations:
            try:
                alive = bool(anim.bAnimate(float(current)))
            except Exception:
                alive = False
            changed = True
            if alive:
                keep.append(anim)
        self._animations = keep
        return changed

    def _capture_timelapse_if_due(self) -> bool:
        if self._timelapse is None:
            return False
        due, path = self._timelapse.bDue()
        if not due:
            return False
        self._plotter.screenshot(path)
        return True

    def _render(self) -> None:
        self._update_camera()
        self._plotter.render(resetcam=False)

    def _next_id(self) -> int:
        out = self._next_actor_id
        self._next_actor_id += 1
        return out

    def _process_command(self, cmd: str, payload: object) -> None:
        if cmd == "close":
            self._running = False
            self._closed = True
            return

        if cmd == "add_actor":
            actor_id, actor, group_id, object_key = cast(tuple[int, object, int, int], payload)
            self._actors[actor_id] = self._plotter.add(actor)
            self._groups.setdefault(group_id, set()).add(actor_id)
            if object_key >= 0:
                self._object_to_actor[object_key] = actor_id
            self._apply_group_style_to_actor(actor_id)
            self._render()
            return

        if cmd == "remove_actor":
            actor_id = int(cast(int, payload))
            actor = self._actors.pop(actor_id, None)
            if actor is not None:
                self._plotter.remove(actor)
            for members in self._groups.values():
                members.discard(actor_id)
            keys = [k for k, v in self._object_to_actor.items() if v == actor_id]
            for k in keys:
                self._object_to_actor.pop(k, None)
            self._render()
            return

        if cmd == "remove_object":
            object_key = int(cast(int, payload))
            actor_id = self._object_to_actor.pop(object_key, None)
            if actor_id is not None:
                self._process_command("remove_actor", actor_id)
            return

        if cmd == "remove_all":
            for actor in list(self._actors.values()):
                self._plotter.remove(actor)
            self._actors.clear()
            self._groups.clear()
            self._object_to_actor.clear()
            self._render()
            return

        if cmd == "render":
            self._render()
            return

        if cmd == "set_group_visible":
            group_id, visible = cast(tuple[int, bool], payload)
            self._group_visible[group_id] = bool(visible)
            for actor_id in self._groups.get(group_id, set()):
                actor = self._actors.get(actor_id)
                if actor is not None:
                    self._set_actor_visible(actor, visible)
            self._render()
            return

        if cmd == "set_group_static":
            group_id, static = cast(tuple[int, bool], payload)
            self._group_static[group_id] = bool(static)
            for actor_id in self._groups.get(group_id, set()):
                actor = self._actors.get(actor_id)
                if actor is not None:
                    self._set_actor_pickable(actor, not static)
            return

        if cmd == "set_group_material":
            group_id, clr, metallic, roughness = cast(tuple[int, tuple[float, float, float, float], float, float], payload)
            self._group_material[group_id] = (clr, metallic, roughness)
            for actor_id in self._groups.get(group_id, set()):
                self._apply_group_style_to_actor(actor_id)
            self._render()
            return

        if cmd == "set_group_matrix":
            group_id, mat = cast(tuple[int, tuple[float, ...]], payload)
            self._group_matrix[group_id] = mat
            for actor_id in self._groups.get(group_id, set()):
                self._apply_group_style_to_actor(actor_id)
            self._render()
            return

        if cmd == "set_background":
            r, g, b = cast(tuple[float, float, float], payload)
            self._plotter.background((r, g, b))
            self._render()
            return

        if cmd == "set_view":
            orbit, elevation = cast(tuple[float, float], payload)
            self.m_fOrbit = float(orbit)
            self.m_fElevation = float(max(-89.9, min(89.9, elevation)))
            self._render()
            return

        if cmd == "set_fov":
            self.m_fFov = float(cast(float, payload))
            self._render()
            return

        if cmd == "set_zoom":
            self.m_fZoom = float(max(0.05, cast(float, payload)))
            self._render()
            return

        if cmd == "set_perspective":
            self.m_bPerspective = bool(cast(bool, payload))
            self._render()
            return

        if cmd == "screenshot":
            path = str(cast(str, payload))
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._plotter.screenshot(path)
            return

        if cmd == "log_stats":
            bounds = self._active_bounds()
            print(f"Viewer stats: actors={len(self._actors)} groups={len(self._groups)} queue={self._queue.qsize()} idle={self._idle}")
            if bounds is not None:
                print(f"Bounds: x[{bounds[0]:.3f},{bounds[1]:.3f}] y[{bounds[2]:.3f},{bounds[3]:.3f}] z[{bounds[4]:.3f},{bounds[5]:.3f}]")
            return

        if cmd == "light_setup":
            self._light_setup_raw = cast(tuple[bytes, bytes], payload)
            return

    def _drain_queue(self) -> None:
        drained = False
        while True:
            try:
                cmd, payload = self._queue.get_nowait()
            except Empty:
                break
            drained = True
            self._process_command(cmd, payload)
        if drained:
            self._idle = self._queue.empty()

    def _loop(self) -> None:
        while self._running:
            updated = False
            try:
                cmd, payload = self._queue.get(timeout=0.03)
                self._process_command(cmd, payload)
                updated = True
            except Empty:
                pass
            if self._pulse_animations():
                updated = True
            if self._capture_timelapse_if_due():
                updated = True
            if updated:
                self._render()
            self._idle = self._queue.empty()

    def _color_tuple(self, clr: ColorFloat | Sequence[float]) -> tuple[float, float, float, float]:
        if isinstance(clr, ColorFloat):
            return (float(clr.r), float(clr.g), float(clr.b), float(clr.a))
        if len(clr) == 3:
            return (float(clr[0]), float(clr[1]), float(clr[2]), 1.0)
        if len(clr) == 4:
            return (float(clr[0]), float(clr[1]), float(clr[2]), float(clr[3]))
        raise ValueError("Color must be (r,g,b) or (r,g,b,a)")

    def _make_mesh_actor(self, mesh: Mesh, color: str | Sequence[float] = "lightgray") -> object:
        vertices, triangles = mesh.to_numpy()
        # vedo expects plain triangle connectivity [v0, v1, v2] per face.
        # Passing VTK-style [3, v0, v1, v2] corrupts topology in rendering.
        faces = np.ascontiguousarray(triangles, dtype=np.int32)
        actor = VedoMesh([vertices, faces])
        # Do not force a normals recomputation here: runtime meshes may contain
        # local winding inconsistencies, and averaging normals can produce
        # severe shading artifacts (striping / cone-like appearance).
        phong_fn = getattr(actor, "phong", None)
        if callable(phong_fn):
            phong_fn()
        if isinstance(color, str):
            actor.c(color)
        else:
            clr = self._color_tuple(cast(Sequence[float], color))
            actor.c((clr[0], clr[1], clr[2])).alpha(clr[3])
        return actor

    def _make_polyline_actor(self, poly: PolyLine) -> object:
        n = poly.vertex_count()
        color = poly.get_color()
        if n <= 0:
            actor = vedo.Points(np.array([[0.0, 0.0, 0.0]], dtype=np.float32), c=(color[0], color[1], color[2]), r=1)
            alpha_fn = getattr(actor, "alpha", None)
            if callable(alpha_fn):
                alpha_fn(color[3])
            return actor
        pts = np.array([poly.get_vertex(i) for i in range(n)], dtype=np.float32)
        if n == 1:
            actor = vedo.Points(pts, c=(color[0], color[1], color[2]), r=8)
            alpha_fn = getattr(actor, "alpha", None)
            if callable(alpha_fn):
                alpha_fn(color[3])
            return actor
        actor = vedo.Line(pts, lw=2)
        color_fn = getattr(actor, "c", None)
        if callable(color_fn):
            color_fn((color[0], color[1], color[2]))
        alpha_fn = getattr(actor, "alpha", None)
        if callable(alpha_fn):
            alpha_fn(color[3])
        return actor

    def Add(self, xObject: object, nGroupID: int = 0) -> int:
        if isinstance(xObject, Mesh):
            return self.add_mesh(xObject, nGroupID=nGroupID)
        if isinstance(xObject, Voxels):
            return self.add_voxels(xObject, nGroupID=nGroupID)
        if isinstance(xObject, PolyLine):
            return self.add_polyline(xObject, nGroupID=nGroupID)
        raise TypeError("Add expects Mesh, Voxels, or PolyLine")

    def add_mesh(self, mesh: Mesh, color: str | Sequence[float] = "lightgray", nGroupID: int = 0) -> int:
        actor_id = self._next_id()
        actor = self._make_mesh_actor(mesh, color)
        self._enqueue("add_actor", (actor_id, actor, int(nGroupID), id(mesh)))
        return actor_id

    def add_voxels(self, vox: Voxels, nGroupID: int = 0, color: str | Sequence[float] = "lightgray") -> int:
        with Mesh.from_voxels(vox) as mesh:
            actor = self._make_mesh_actor(mesh, color)
        actor_id = self._next_id()
        self._enqueue("add_actor", (actor_id, actor, int(nGroupID), id(vox)))
        return actor_id

    def add_polyline(self, poly: PolyLine, nGroupID: int = 0) -> int:
        actor_id = self._next_id()
        actor = self._make_polyline_actor(poly)
        self._enqueue("add_actor", (actor_id, actor, int(nGroupID), id(poly)))
        return actor_id

    def Remove(self, xObject: object) -> None:
        if isinstance(xObject, int):
            self._enqueue("remove_actor", int(xObject))
            return
        self._enqueue("remove_object", id(xObject))

    def remove(self, actor_id: int) -> None:
        self.Remove(actor_id)

    def RemoveAllObjects(self) -> None:
        self._enqueue("remove_all")

    def RequestUpdate(self) -> None:
        self._enqueue("render")

    def request_render(self) -> None:
        self.RequestUpdate()

    def RequestScreenShot(self, strScreenShotPath: str) -> None:
        self._enqueue("screenshot", str(strScreenShotPath))

    def SetGroupVisible(self, nGroupID: int, bVisible: bool) -> None:
        self._enqueue("set_group_visible", (int(nGroupID), bool(bVisible)))

    def SetGroupStatic(self, nGroupID: int, bStatic: bool) -> None:
        self._enqueue("set_group_static", (int(nGroupID), bool(bStatic)))

    def SetGroupMaterial(self, nGroupID: int, clr: ColorFloat | Sequence[float], fMetallic: float, fRoughness: float) -> None:
        self._enqueue("set_group_material", (int(nGroupID), self._color_tuple(clr), float(fMetallic), float(fRoughness)))

    def SetGroupMatrix(self, nGroupID: int, mat: Sequence[float]) -> None:
        if len(mat) != 16:
            raise ValueError("mat must contain 16 values (row-major 4x4)")
        self._enqueue("set_group_matrix", (int(nGroupID), tuple(float(v) for v in mat)))

    def SetBackgroundColor(self, clr: ColorFloat | Sequence[float]) -> None:
        rgba = self._color_tuple(clr)
        self._enqueue("set_background", (rgba[0], rgba[1], rgba[2]))

    def AdjustViewAngles(self, fOrbitRelative: float, fElevationRelative: float) -> None:
        self.SetViewAngles(self.m_fOrbit + float(fOrbitRelative), self.m_fElevation + float(fElevationRelative))

    def SetViewAngles(self, fOrbit: float, fElevation: float) -> None:
        orbit = float(fOrbit)
        while orbit >= 360.0:
            orbit -= 360.0
        while orbit < 0.0:
            orbit += 360.0
        elev = max(-89.9, min(89.9, float(fElevation)))
        self._enqueue("set_view", (orbit, elev))

    def SetFov(self, fAngle: float) -> None:
        self._enqueue("set_fov", float(fAngle))

    def SetZoom(self, fZoom: float) -> None:
        self._enqueue("set_zoom", float(fZoom))

    def SetPerspective(self, bPerspective: bool) -> None:
        self._enqueue("set_perspective", bool(bPerspective))

    def LogStatistics(self) -> None:
        self._enqueue("log_stats")

    def LoadLightSetup(self, source: str | bytes | io.BytesIO) -> None:
        if isinstance(source, str):
            blob = Path(source).read_bytes()
        elif isinstance(source, io.BytesIO):
            blob = source.getvalue()
        else:
            blob = bytes(source)

        with zipfile.ZipFile(io.BytesIO(blob), "r") as zf:
            diffuse = zf.read("Diffuse.dds")
            specular = zf.read("Specular.dds")
        self._enqueue("light_setup", (diffuse, specular))

    def AddKeyHandler(self, xKeyHandler: IKeyHandler) -> None:
        self._key_handlers.insert(0, xKeyHandler)

    def _ensure_key_callback(self) -> None:
        if self._key_callback_handle is not None:
            return

        def _on_key(event: object) -> None:
            key = str(getattr(event, "keypress", getattr(event, "keyPressed", "")))
            if not key:
                return
            shift = bool(getattr(event, "shift", False))
            ctrl = bool(getattr(event, "ctrl", False))
            alt = bool(getattr(event, "alt", False))
            cmd = bool(getattr(event, "cmd", False))
            for handler in self._key_handlers:
                if handler.bHandleEvent(self, key, False, shift, ctrl, alt, cmd):
                    self.RequestUpdate()
                    break

        self._key_callback_handle = self._plotter.add_callback("KeyPress", _on_key)

    def AddAnimation(self, oAnim: Any) -> None:
        if not hasattr(self, "_anim_start"):
            self._anim_start = time.perf_counter()
        self._animations.append(oAnim)
        self.RequestUpdate()

    def RemoveAllAnimations(self) -> None:
        for anim in self._animations:
            end_fn = getattr(anim, "End", None)
            if callable(end_fn):
                end_fn()
        self._animations.clear()

    def StartTimeLapse(
        self,
        fIntervalInMilliseconds: float,
        strPath: str,
        strFileName: str = "frame_",
        nStartFrame: int = 0,
        bPaused: bool = False,
    ) -> None:
        self._timelapse = _TimeLapseState.create(
            fIntervalInMilliseconds,
            strPath,
            strFileName,
            nStartFrame,
            bPaused,
        )

    def PauseTimeLapse(self) -> None:
        if self._timelapse is not None:
            self._timelapse.Pause()

    def ResumeTimeLapse(self) -> None:
        if self._timelapse is not None:
            self._timelapse.Resume()

    def StopTimeLapse(self) -> None:
        self._timelapse = None

    def bPoll(self) -> bool:
        self._drain_queue()
        changed = self._pulse_animations()
        changed = self._capture_timelapse_if_due() or changed
        if changed:
            self._render()
        self._idle = self._queue.empty()
        return not self._closed

    def bIsIdle(self) -> bool:
        self._idle = self._idle and self._queue.empty()
        return self._idle

    def interact(self) -> None:
        self._stop_loop()
        self._drain_queue()
        self._ensure_key_callback()
        # Phase 1: open the VTK window non-interactively so the render window
        # and camera object actually exist.  resetcam=True lets vedo fit the
        # scene so the object is always visible before we reposition.
        self._plotter.show(interactive=False, resetcam=True)
        # Phase 2: now that the window is live, apply our computed camera
        # position (respecting m_fZoom, m_fOrbit, m_fElevation, m_fFov) on
        # the real VTK camera, then re-render without resetting.
        self._update_camera()
        self._plotter.render(resetcam=False)
        # Phase 3: hand off to the VTK interactive event loop.
        if getattr(self._plotter, "interactor", None) is not None:
            self._plotter.interactor.Start()
        else:
            self._plotter.show(interactive=True, resetcam=False)

    def close(self) -> None:
        if self._closed:
            return
        self._enqueue("close")
        self._stop_loop()
        self._drain_queue()
        self._plotter.close()



