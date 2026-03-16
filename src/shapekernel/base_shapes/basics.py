from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable

from picogk import BBox3, Mesh, Voxels

from .._types import Vec3, Vector3Like, as_np3, as_vec3
from ..frames import Frames
from ..modulations import LineModulation, SurfaceModulation
from ..utils.utils import LocalFrame

class BaseShape(ABC):
    fnVertexTransformation = Callable[[Vec3], Vec3]

    def __init__(self) -> None:
        self.m_fnTrafo: BaseShape.fnVertexTransformation = self.vecNoTransform

    def SetTransformation(self, fnTrafo: fnVertexTransformation) -> None:
        self.m_fnTrafo = fnTrafo

    def set_transformation(self, fnTrafo: fnVertexTransformation) -> None:
        self.SetTransformation(fnTrafo)

    @staticmethod
    def vecNoTransform(vecPt: Vec3) -> Vec3:
        return vecPt

    @abstractmethod
    def voxConstruct(self) -> Voxels:
        raise NotImplementedError


class BaseBox(BaseShape):
    """Axis-aligned box swept along a spine.

    Construct with a :class:`LocalFrame` (straight spine) or a pre-built
    :class:`Frames` (arbitrary spine) using the matching class-method:

    .. code-block:: python

        BaseBox.from_frame(frame, fLength=20, fWidth=20, fDepth=20)
        BaseBox.from_frames(frames, fWidth=20, fDepth=20)
    """

    def __init__(
        self,
        aFrames: Frames,
        fWidth: float,
        fDepth: float,
        *,
        _length_steps: int,
    ) -> None:
        """Internal – use :meth:`from_frame` or :meth:`from_frames`."""
        super().__init__()
        self.m_aFrames = aFrames
        self.SetWidthSteps(5)
        self.SetDepthSteps(5)
        self.SetLengthSteps(_length_steps)
        self.m_oWidthModulation = LineModulation(fWidth)
        self.m_oDepthModulation = LineModulation(fDepth)

    @classmethod
    def from_frame(
        cls,
        oFrame: LocalFrame,
        fLength: float = 20.0,
        fWidth: float = 20.0,
        fDepth: float = 20.0,
    ) -> "BaseBox":
        """Create a box from a :class:`LocalFrame` and three scalar dimensions."""
        return cls(Frames.from_length(fLength, oFrame), fWidth, fDepth, _length_steps=5)

    @classmethod
    def from_frames(
        cls,
        aFrames: Frames,
        fWidth: float = 20.0,
        fDepth: float = 20.0,
    ) -> "BaseBox":
        """Create a box whose spine is driven by a :class:`Frames` object."""
        return cls(aFrames, fWidth, fDepth, _length_steps=500)

    @classmethod
    def from_bbox(
        cls,
        oBBox: BBox3 | tuple[Vector3Like, Vector3Like],
    ) -> "BaseBox":
        """Create a box from a PicoGK bbox or a ``(min_xyz, max_xyz)`` tuple."""
        if isinstance(oBBox, BBox3):
            box_min = (float(oBBox.min.x), float(oBBox.min.y), float(oBBox.min.z))
            box_max = (float(oBBox.max.x), float(oBBox.max.y), float(oBBox.max.z))
        else:
            box_min, box_max = oBBox

        bmin = as_np3(box_min)
        bmax = as_np3(box_max)
        centre = 0.5 * (bmin + bmax)
        centre[2] = bmin[2]
        return cls.from_frame(
            LocalFrame(as_vec3(centre), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
            fLength=float(bmax[2] - bmin[2]),
            fWidth=float(bmax[0] - bmin[0]),
            fDepth=float(bmax[1] - bmin[1]),
        )

    def SetWidth(self, oModulation: LineModulation) -> None:
        self.m_oWidthModulation = oModulation
        self.SetWidthSteps(500)
        self.SetLengthSteps(500)

    def SetDepth(self, oModulation: LineModulation) -> None:
        self.m_oDepthModulation = oModulation
        self.SetDepthSteps(500)
        self.SetLengthSteps(500)

    def SetWidthSteps(self, nWidthSteps: int) -> None:
        self.m_nWidthSteps = max(5, int(nWidthSteps))

    def SetDepthSteps(self, nDepthSteps: int) -> None:
        self.m_nDepthSteps = max(5, int(nDepthSteps))

    def SetLengthSteps(self, nLengthSteps: int) -> None:
        self.m_nLengthSteps = max(5, int(nLengthSteps))

    def voxConstruct(self) -> Voxels:
        return Voxels.from_mesh(self.mshConstruct())

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        self._add_top_surface(mesh, True)
        self._add_bottom_surface(mesh)
        self._add_front_surface(mesh, True)
        self._add_back_surface(mesh)
        self._add_right_surface(mesh, True)
        self._add_left_surface(mesh)
        return mesh

    def _add_rect(self, mesh: Mesh, pts: tuple[Vec3, Vec3, Vec3, Vec3], flip: bool) -> None:
        p0, p1, p2, p3 = pts
        if not flip:
            mesh.nAddTriangle(p0, p1, p2)
            mesh.nAddTriangle(p0, p2, p3)
        else:
            mesh.nAddTriangle(p0, p2, p1)
            mesh.nAddTriangle(p0, p3, p2)

    def _add_top_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
        lr = self._length_ratio(self.m_nLengthSteps - 1)
        for iw in range(1, self.m_nWidthSteps):
            w1 = self._width_ratio(iw - 1)
            w2 = self._width_ratio(iw)
            for idepth in range(1, self.m_nDepthSteps):
                d1 = self._depth_ratio(idepth - 1)
                d2 = self._depth_ratio(idepth)
                self._add_rect(
                    mesh,
                    (
                        self.vecGetSurfacePoint(w1, d1, lr),
                        self.vecGetSurfacePoint(w1, d2, lr),
                        self.vecGetSurfacePoint(w2, d2, lr),
                        self.vecGetSurfacePoint(w2, d1, lr),
                    ),
                    bFlip,
                )

    def _add_bottom_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
        lr = self._length_ratio(0)
        for iw in range(1, self.m_nWidthSteps):
            w1 = self._width_ratio(iw - 1)
            w2 = self._width_ratio(iw)
            for idepth in range(1, self.m_nDepthSteps):
                d1 = self._depth_ratio(idepth - 1)
                d2 = self._depth_ratio(idepth)
                self._add_rect(
                    mesh,
                    (
                        self.vecGetSurfacePoint(w1, d1, lr),
                        self.vecGetSurfacePoint(w1, d2, lr),
                        self.vecGetSurfacePoint(w2, d2, lr),
                        self.vecGetSurfacePoint(w2, d1, lr),
                    ),
                    bFlip,
                )

    def _add_front_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
        wr = self._width_ratio(0)
        for il in range(1, self.m_nLengthSteps):
            lr1 = self._length_ratio(il - 1)
            lr2 = self._length_ratio(il)
            for idepth in range(1, self.m_nDepthSteps):
                d1 = self._depth_ratio(idepth - 1)
                d2 = self._depth_ratio(idepth)
                self._add_rect(mesh, (self.vecGetSurfacePoint(wr, d1, lr1), self.vecGetSurfacePoint(wr, d2, lr1), self.vecGetSurfacePoint(wr, d2, lr2), self.vecGetSurfacePoint(wr, d1, lr2)), bFlip)

    def _add_back_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
        wr = self._width_ratio(self.m_nWidthSteps - 1)
        for il in range(1, self.m_nLengthSteps):
            lr1 = self._length_ratio(il - 1)
            lr2 = self._length_ratio(il)
            for idepth in range(1, self.m_nDepthSteps):
                d1 = self._depth_ratio(idepth - 1)
                d2 = self._depth_ratio(idepth)
                self._add_rect(mesh, (self.vecGetSurfacePoint(wr, d1, lr1), self.vecGetSurfacePoint(wr, d2, lr1), self.vecGetSurfacePoint(wr, d2, lr2), self.vecGetSurfacePoint(wr, d1, lr2)), bFlip)

    def _add_right_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
        dr = self._depth_ratio(self.m_nDepthSteps - 1)
        for il in range(1, self.m_nLengthSteps):
            lr1 = self._length_ratio(il - 1)
            lr2 = self._length_ratio(il)
            for iw in range(1, self.m_nWidthSteps):
                w1 = self._width_ratio(iw - 1)
                w2 = self._width_ratio(iw)
                self._add_rect(mesh, (self.vecGetSurfacePoint(w1, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr2), self.vecGetSurfacePoint(w1, dr, lr2)), bFlip)

    def _add_left_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
        dr = self._depth_ratio(0)
        for il in range(1, self.m_nLengthSteps):
            lr1 = self._length_ratio(il - 1)
            lr2 = self._length_ratio(il)
            for iw in range(1, self.m_nWidthSteps):
                w1 = self._width_ratio(iw - 1)
                w2 = self._width_ratio(iw)
                self._add_rect(mesh, (self.vecGetSurfacePoint(w1, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr2), self.vecGetSurfacePoint(w1, dr, lr2)), bFlip)

    def _width_ratio(self, step: int) -> float:
        return -1.0 + (2.0 / float(self.m_nWidthSteps - 1)) * float(step)

    def _depth_ratio(self, step: int) -> float:
        return -1.0 + (2.0 / float(self.m_nDepthSteps - 1)) * float(step)

    def _length_ratio(self, step: int) -> float:
        return (1.0 / float(self.m_nLengthSteps - 1)) * float(step)

    def fGetWidth(self, fLengthRatio: float) -> float:
        return self.m_oWidthModulation.fGetModulation(fLengthRatio)

    def fGetDepth(self, fLengthRatio: float) -> float:
        return self.m_oDepthModulation.fGetModulation(fLengthRatio)

    def vecGetSurfacePoint(self, fWidthRatio: float, fDepthRatio: float, fLengthRatio: float) -> Vec3:
        spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
        lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
        ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
        x = 0.5 * fWidthRatio * self.fGetWidth(fLengthRatio)
        y = 0.5 * fDepthRatio * self.fGetDepth(fLengthRatio)
        return self.m_fnTrafo(as_vec3(spine + x * lx + y * ly))


class BaseCylinder(BaseShape):
    """Solid cylinder swept along a spine.

    .. code-block:: python

        BaseCylinder.from_frame(frame, fLength=20, fRadius=10)
        BaseCylinder.from_frames(frames, fRadius=10)
    """

    def __init__(
        self,
        aFrames: Frames,
        fRadius: float,
        *,
        _length_steps: int,
    ) -> None:
        """Internal – use :meth:`from_frame` or :meth:`from_frames`."""
        super().__init__()
        self.m_aFrames = aFrames
        self.SetLengthSteps(_length_steps)
        self.SetPolarSteps(360)
        self.SetRadialSteps(5)
        self.m_oRadiusModulation = SurfaceModulation(fRadius)

    @classmethod
    def from_frame(
        cls,
        oFrame: LocalFrame,
        fLength: float = 20.0,
        fRadius: float = 10.0,
    ) -> "BaseCylinder":
        """Create a cylinder from a :class:`LocalFrame`, length, and radius."""
        return cls(Frames.from_length(fLength, oFrame), fRadius, _length_steps=5)

    @classmethod
    def from_frames(
        cls,
        aFrames: Frames,
        fRadius: float = 10.0,
    ) -> "BaseCylinder":
        """Create a cylinder whose spine is driven by a :class:`Frames` object."""
        return cls(aFrames, fRadius, _length_steps=500)

    def SetRadius(self, oModulation: SurfaceModulation) -> None:
        self.m_oRadiusModulation = oModulation
        self.SetLengthSteps(500)

    def SetRadialSteps(self, nRadialSteps: int) -> None:
        self.m_nRadialSteps = max(5, int(nRadialSteps))

    def SetPolarSteps(self, nPolarSteps: int) -> None:
        self.m_nPolarSteps = max(5, int(nPolarSteps))

    def SetLengthSteps(self, nLengthSteps: int) -> None:
        self.m_nLengthSteps = max(5, int(nLengthSteps))

    def voxConstruct(self) -> Voxels:
        return Voxels.from_mesh(self.mshConstruct())

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        self._add_top_surface(mesh)
        self._add_outer_mantle(mesh)
        self._add_bottom_surface(mesh)
        return mesh

    def _add_top_surface(self, mesh: Mesh) -> None:
        lr = self._length_ratio(self.m_nLengthSteps - 1)
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for ir in range(1, self.m_nRadialSteps):
                r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
                mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p1, r2), self.vecGetSurfacePoint(lr, p2, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p2, r2), self.vecGetSurfacePoint(lr, p2, r1))

    def _add_bottom_surface(self, mesh: Mesh) -> None:
        lr = self._length_ratio(0)
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for ir in range(1, self.m_nRadialSteps):
                r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
                mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p2, r2), self.vecGetSurfacePoint(lr, p1, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(lr, p1, r1), self.vecGetSurfacePoint(lr, p2, r1), self.vecGetSurfacePoint(lr, p2, r2))

    def _add_outer_mantle(self, mesh: Mesh) -> None:
        rr = self._radius_ratio(self.m_nRadialSteps - 1)
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for il in range(1, self.m_nLengthSteps):
                l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p2, rr), self.vecGetSurfacePoint(l2, p1, rr))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l1, p2, rr), self.vecGetSurfacePoint(l2, p2, rr))

    def _radius_ratio(self, step: int) -> float:
        return (1.0 / float(self.m_nRadialSteps - 1)) * float(step)

    def _phi_ratio(self, step: int) -> float:
        return (1.0 / float(self.m_nPolarSteps - 1)) * float(step)

    def _length_ratio(self, step: int) -> float:
        return (1.0 / float(self.m_nLengthSteps - 1)) * float(step)

    def fGetRadius(self, fPhi: float, fLengthRatio: float) -> float:
        return self.m_oRadiusModulation.fGetModulation(fPhi, fLengthRatio)

    def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
        phi = 2.0 * math.pi * fPhiRatio
        spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
        lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
        ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
        radius = fRadiusRatio * self.fGetRadius(phi, fLengthRatio)
        pt = spine + (radius * math.cos(phi)) * lx + (radius * math.sin(phi)) * ly
        return self.m_fnTrafo(as_vec3(pt))


class BasePipe(BaseCylinder):
    """Hollow annular pipe swept along a spine.

    .. code-block:: python

        BasePipe.from_frame(frame, fLength=20, fInnerRadius=10, fOuterRadius=20)
        BasePipe.from_frames(frames, fInnerRadius=10, fOuterRadius=20)
    """

    def __init__(
        self,
        aFrames: Frames,
        fInnerRadius: float,
        fOuterRadius: float,
        *,
        _length_steps: int,
    ) -> None:
        """Internal – use :meth:`from_frame` or :meth:`from_frames`."""
        super().__init__(aFrames, fOuterRadius, _length_steps=_length_steps)
        self.m_oInnerRadiusModulation = SurfaceModulation(fInnerRadius)
        self.m_oOuterRadiusModulation = SurfaceModulation(fOuterRadius)

    @classmethod
    def from_frame(
        cls,
        oFrame: LocalFrame,
        fLength: float = 20.0,
        fInnerRadius: float = 10.0,
        fOuterRadius: float = 20.0,
    ) -> "BasePipe":
        """Create a pipe from a :class:`LocalFrame`, length, and radii."""
        return cls(Frames.from_length(fLength, oFrame), fInnerRadius, fOuterRadius, _length_steps=5)

    @classmethod
    def from_frames(
        cls,
        aFrames: Frames,
        fInnerRadius: float = 10.0,
        fOuterRadius: float = 20.0,
    ) -> "BasePipe":
        """Create a pipe whose spine is driven by a :class:`Frames` object."""
        return cls(aFrames, fInnerRadius, fOuterRadius, _length_steps=500)

    def SetRadius(self, oInnerRadiusOverCylinder: SurfaceModulation, oOuterRadiusOverCylinder: SurfaceModulation) -> None:
        self.m_oInnerRadiusModulation = oInnerRadiusOverCylinder
        self.m_oOuterRadiusModulation = oOuterRadiusOverCylinder
        self.SetLengthSteps(500)

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        self._add_top_surface(mesh)
        self._add_bottom_surface(mesh)
        self._add_inner_mantle(mesh)
        self._add_outer_mantle(mesh)
        return mesh

    def _add_outer_mantle(self, mesh: Mesh) -> None:
        rr = self._radius_ratio(self.m_nRadialSteps - 1)
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for il in range(1, self.m_nLengthSteps):
                l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p2, rr), self.vecGetSurfacePoint(l2, p1, rr))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l1, p2, rr), self.vecGetSurfacePoint(l2, p2, rr))

    def _add_inner_mantle(self, mesh: Mesh) -> None:
        rr = self._radius_ratio(0)
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for il in range(1, self.m_nLengthSteps):
                l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p1, rr), self.vecGetSurfacePoint(l2, p2, rr))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, rr), self.vecGetSurfacePoint(l2, p2, rr), self.vecGetSurfacePoint(l1, p2, rr))

    def fGetInnerRadius(self, fPhi: float, fLengthRatio: float) -> float:
        return self.m_oInnerRadiusModulation.fGetModulation(fPhi, fLengthRatio)

    def fGetOuterRadius(self, fPhi: float, fLengthRatio: float) -> float:
        return self.m_oOuterRadiusModulation.fGetModulation(fPhi, fLengthRatio)

    def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
        phi = 2.0 * math.pi * fPhiRatio
        spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
        lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
        ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
        outer = self.fGetOuterRadius(phi, fLengthRatio)
        inner = self.fGetInnerRadius(phi, fLengthRatio)
        radius = fRadiusRatio * (outer - inner) + inner
        pt = spine + (radius * math.cos(phi)) * lx + (radius * math.sin(phi)) * ly
        return self.m_fnTrafo(as_vec3(pt))


class BasePipeSegment(BasePipe):
    """Circumferentially-limited pipe arc (a 'segment' of a full pipe).

    The angular extent is described by two :class:`LineModulation` objects and
    an :class:`EMethod` selector that governs how they are interpreted:

    * ``EMethod.START_END`` – the two modulations define the start and end
      angles; mid and range are derived automatically.
    * ``EMethod.MID_RANGE`` – the two modulations define the arc midpoint angle
      and total angular span directly.

    .. code-block:: python

        BasePipeSegment.from_frame(
            frame, fLength=20, fInnerRadius=2, fOuterRadius=6,
            oStartOrMidModulation=LineModulation(start_angle),
            oEndOrRangeModulation=LineModulation(range_angle),
            eMethod=BasePipeSegment.EMethod.MID_RANGE,
        )
        BasePipeSegment.from_frames(
            frames, fInnerRadius=2, fOuterRadius=6,
            oStartOrMidModulation=..., oEndOrRangeModulation=...,
            eMethod=BasePipeSegment.EMethod.START_END,
        )
    """

    class EMethod(Enum):
        START_END = "START_END"
        MID_RANGE = "MID_RANGE"

    def __init__(
        self,
        aFrames: Frames,
        fInnerRadius: float,
        fOuterRadius: float,
        oStartOrMidModulation: LineModulation,
        oEndOrRangeModulation: LineModulation,
        eMethod: "BasePipeSegment.EMethod",
        *,
        _length_steps: int,
    ) -> None:
        """Internal – use :meth:`from_frame` or :meth:`from_frames`."""
        super().__init__(aFrames, fInnerRadius, fOuterRadius, _length_steps=_length_steps)
        self.m_eMethod = eMethod
        if self.m_eMethod == self.EMethod.START_END:
            self.m_oMidModulation = 0.5 * (oStartOrMidModulation + oEndOrRangeModulation)
            self.m_oRangeModulation = oEndOrRangeModulation - oStartOrMidModulation
        else:
            self.m_oMidModulation = oStartOrMidModulation
            self.m_oRangeModulation = oEndOrRangeModulation

    @classmethod
    def from_frame(
        cls,
        oFrame: LocalFrame,
        fLength: float,
        fInnerRadius: float,
        fOuterRadius: float,
        oStartOrMidModulation: LineModulation,
        oEndOrRangeModulation: LineModulation,
        eMethod: "BasePipeSegment.EMethod",
    ) -> "BasePipeSegment":
        """Create a pipe segment from a :class:`LocalFrame` and explicit dimensions."""
        return cls(
            Frames.from_length(fLength, oFrame),
            fInnerRadius,
            fOuterRadius,
            oStartOrMidModulation,
            oEndOrRangeModulation,
            eMethod,
            _length_steps=5,
        )

    @classmethod
    def from_frames(
        cls,
        aFrames: Frames,
        fInnerRadius: float,
        fOuterRadius: float,
        oStartOrMidModulation: LineModulation,
        oEndOrRangeModulation: LineModulation,
        eMethod: "BasePipeSegment.EMethod",
    ) -> "BasePipeSegment":
        """Create a pipe segment whose spine is driven by a :class:`Frames` object."""
        return cls(
            aFrames,
            fInnerRadius,
            fOuterRadius,
            oStartOrMidModulation,
            oEndOrRangeModulation,
            eMethod,
            _length_steps=500,
        )

    def mshConstruct(self) -> Mesh:
        mesh = super().mshConstruct()
        self._add_start_surface(mesh)
        self._add_end_surface(mesh)
        return mesh

    def _add_start_surface(self, mesh: Mesh) -> None:
        pr = self._phi_ratio(0)
        for il in range(1, self.m_nLengthSteps):
            l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
            for ir in range(1, self.m_nRadialSteps):
                r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l1, pr, r2), self.vecGetSurfacePoint(l2, pr, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l2, pr, r2), self.vecGetSurfacePoint(l2, pr, r1))

    def _add_end_surface(self, mesh: Mesh) -> None:
        pr = self._phi_ratio(self.m_nPolarSteps - 1)
        for il in range(1, self.m_nLengthSteps):
            l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
            for ir in range(1, self.m_nRadialSteps):
                r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l2, pr, r2), self.vecGetSurfacePoint(l1, pr, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, pr, r1), self.vecGetSurfacePoint(l2, pr, r1), self.vecGetSurfacePoint(l2, pr, r2))

    def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
        spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
        lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
        ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
        phi = self.m_oMidModulation.fGetModulation(fLengthRatio) + (fPhiRatio - 0.5) * self.m_oRangeModulation.fGetModulation(fLengthRatio)
        outer = self.fGetOuterRadius(phi, fLengthRatio)
        inner = self.fGetInnerRadius(phi, fLengthRatio)
        radius = fRadiusRatio * (outer - inner) + inner
        pt = spine + (radius * math.cos(phi)) * lx + (radius * math.sin(phi)) * ly
        return self.m_fnTrafo(as_vec3(pt))

