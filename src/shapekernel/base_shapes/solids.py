from __future__ import annotations

import math
import numpy as np

from picogk import Mesh, Voxels

from .._types import Vec3, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import GenericContour, LineModulation, SurfaceModulation
from ..utils import VecOperations
from .basics import BaseCylinder, BaseShape

class BaseSphere(BaseShape):
    def __init__(self, oFrame: LocalFrame, fRadius: float = 10.0) -> None:
        super().__init__()
        self.SetAzimuthalSteps(360)
        self.SetPolarSteps(180)
        self.m_oFrame = oFrame
        self.m_oRadiusModulation = SurfaceModulation(fRadius)

    def SetRadius(self, oModulation: SurfaceModulation) -> None:
        self.m_oRadiusModulation = oModulation

    def SetAzimuthalSteps(self, nAzimuthalSteps: int) -> None:
        self.m_nAzimuthalSteps = int(nAzimuthalSteps)

    def SetPolarSteps(self, nPolarSteps: int) -> None:
        self.m_nPolarSteps = int(nPolarSteps)

    def voxConstruct(self) -> Voxels:
        return Voxels.from_mesh(self.mshConstruct())

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        rr = 1.0
        for it in range(1, self.m_nAzimuthalSteps):
            t1 = (1.0 / (self.m_nAzimuthalSteps - 1)) * (it - 1)
            t2 = (1.0 / (self.m_nAzimuthalSteps - 1)) * it
            for ip in range(1, self.m_nPolarSteps):
                p1 = (1.0 / (self.m_nPolarSteps - 1)) * (ip - 1)
                p2 = (1.0 / (self.m_nPolarSteps - 1)) * ip
                mesh.nAddTriangle(self.vecGetSurfacePoint(t1, p1, rr), self.vecGetSurfacePoint(t2, p1, rr), self.vecGetSurfacePoint(t2, p2, rr))
                mesh.nAddTriangle(self.vecGetSurfacePoint(t1, p1, rr), self.vecGetSurfacePoint(t2, p2, rr), self.vecGetSurfacePoint(t1, p2, rr))
        return mesh

    def fGetRadius(self, fPhi: float, fLengthRatio: float) -> float:
        return self.m_oRadiusModulation.fGetModulation(fPhi, fLengthRatio)

    def vecGetSurfacePoint(self, fPhiRatio: float, fThetaRatio: float, fRadiusRatio: float) -> Vec3:
        theta = math.pi * fThetaRatio
        phi = 2.0 * math.pi * fPhiRatio
        fRadius = fRadiusRatio * self.fGetRadius(phi, theta)
        fx = fRadius * math.cos(phi) * math.sin(theta)
        fy = fRadius * math.sin(phi) * math.sin(theta)
        fz = fRadius * math.cos(theta)
        pos = as_np3(self.m_oFrame.vecGetPosition())
        lx = as_np3(self.m_oFrame.vecGetLocalX())
        ly = as_np3(self.m_oFrame.vecGetLocalY())
        lz = as_np3(self.m_oFrame.vecGetLocalZ())
        return self.m_fnTrafo(as_vec3(pos + fx * lx + fy * ly + fz * lz))


class BaseLens(BaseShape):
    def __init__(self, oFrame: LocalFrame, fHeight: float, fInnerRadius: float, fOuterRadius: float) -> None:
        super().__init__()
        self.m_oFrame = oFrame
        self.SetRadialSteps(5)
        self.SetPolarSteps(360)
        self.SetHeightSteps(5)
        self.m_fInnerRadius = fInnerRadius
        self.m_fOuterRadius = fOuterRadius
        self.m_oLowerModulation = SurfaceModulation(0.0)
        self.m_oUpperModulation = SurfaceModulation(fHeight)

    def SetHeight(self, oLowerModulation: SurfaceModulation, oUpperModulation: SurfaceModulation) -> None:
        self.m_oLowerModulation = oLowerModulation
        self.m_oUpperModulation = oUpperModulation
        self.SetRadialSteps(500)

    def SetRadialSteps(self, nRadialSteps: int) -> None:
        self.m_nRadialSteps = max(5, int(nRadialSteps))

    def SetPolarSteps(self, nPolarSteps: int) -> None:
        self.m_nPolarSteps = max(5, int(nPolarSteps))

    def SetHeightSteps(self, nHeightSteps: int) -> None:
        self.m_nHeightSteps = max(5, int(nHeightSteps))

    def voxConstruct(self) -> Voxels:
        return Voxels.from_mesh(self.mshConstruct())

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for ir in range(1, self.m_nRadialSteps):
                r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
                mesh.nAddTriangle(self.vecGetSurfacePoint(1.0, p1, r1), self.vecGetSurfacePoint(1.0, p1, r2), self.vecGetSurfacePoint(1.0, p2, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(1.0, p1, r1), self.vecGetSurfacePoint(1.0, p2, r2), self.vecGetSurfacePoint(1.0, p2, r1))
                mesh.nAddTriangle(self.vecGetSurfacePoint(0.0, p1, r1), self.vecGetSurfacePoint(0.0, p2, r2), self.vecGetSurfacePoint(0.0, p1, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(0.0, p1, r1), self.vecGetSurfacePoint(0.0, p2, r1), self.vecGetSurfacePoint(0.0, p2, r2))
            for ih in range(1, self.m_nHeightSteps):
                h1, h2 = self._height_ratio(ih - 1), self._height_ratio(ih)
                r_in = self._radius_ratio(0)
                r_out = self._radius_ratio(self.m_nRadialSteps - 1)
                mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_in), self.vecGetSurfacePoint(h2, p1, r_in), self.vecGetSurfacePoint(h2, p2, r_in))
                mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_in), self.vecGetSurfacePoint(h2, p2, r_in), self.vecGetSurfacePoint(h1, p2, r_in))
                mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_out), self.vecGetSurfacePoint(h2, p2, r_out), self.vecGetSurfacePoint(h2, p1, r_out))
                mesh.nAddTriangle(self.vecGetSurfacePoint(h1, p1, r_out), self.vecGetSurfacePoint(h1, p2, r_out), self.vecGetSurfacePoint(h2, p2, r_out))
        return mesh

    def _radius_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nRadialSteps - 1)) * float(step)

    def _phi_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nPolarSteps - 1)) * float(step)

    def _height_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nHeightSteps - 1)) * float(step)

    def fGetHeight(self, fHeightRatio: float, fPhi: float, fRadiusRatio: float) -> float:
        low = self.m_oLowerModulation.fGetModulation(fPhi, fRadiusRatio)
        high = self.m_oUpperModulation.fGetModulation(fPhi, fRadiusRatio)
        return low + fHeightRatio * (high - low)

    def vecGetSurfacePoint(self, fHeightRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
        phi = 2.0 * math.pi * fPhiRatio
        radius = (self.m_fOuterRadius - self.m_fInnerRadius) * fRadiusRatio + self.m_fInnerRadius
        z = self.fGetHeight(fHeightRatio, phi, fRadiusRatio)
        x = radius * math.cos(phi)
        y = radius * math.sin(phi)
        pos = as_np3(self.m_oFrame.vecGetPosition())
        lx = as_np3(self.m_oFrame.vecGetLocalX())
        ly = as_np3(self.m_oFrame.vecGetLocalY())
        lz = as_np3(self.m_oFrame.vecGetLocalZ())
        return self.m_fnTrafo(as_vec3(pos + x * lx + y * ly + z * lz))


class BaseRing(BaseShape):
    def __init__(self, oFrame: LocalFrame, fRingRadius: float = 50.0, fRadius: float = 5.0) -> None:
        super().__init__()
        self.SetRadialSteps(360)
        self.SetPolarSteps(360)
        self.m_oFrame = oFrame
        self.m_fRingRadius = fRingRadius
        self.m_oRadiusModulation = SurfaceModulation(fRadius)

    def SetRadius(self, oModulation: SurfaceModulation) -> None:
        self.m_oRadiusModulation = oModulation

    def SetRadialSteps(self, nRadialSteps: int) -> None:
        self.m_nRadialSteps = max(5, int(nRadialSteps))

    def SetPolarSteps(self, nPolarSteps: int) -> None:
        self.m_nPolarSteps = max(5, int(nPolarSteps))

    def voxConstruct(self) -> Voxels:
        return Voxels.from_mesh(self.mshConstruct())

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        rr = 1.0
        for ia in range(self.m_nRadialSteps):
            lower = ia - 1
            if lower < 0:
                lower += self.m_nRadialSteps
            a1 = self._alpha_ratio(lower)
            a2 = self._alpha_ratio(ia)
            for ip in range(1, self.m_nPolarSteps):
                p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
                mesh.nAddTriangle(self.vecGetSurfacePoint(a1, p1, rr), self.vecGetSurfacePoint(a2, p1, rr), self.vecGetSurfacePoint(a2, p2, rr))
                mesh.nAddTriangle(self.vecGetSurfacePoint(a1, p1, rr), self.vecGetSurfacePoint(a2, p2, rr), self.vecGetSurfacePoint(a1, p2, rr))
        return mesh

    def _alpha_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nRadialSteps - 1)) * float(step)

    def _phi_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nPolarSteps - 1)) * float(step)

    def fGetRadius(self, fPhi: float, fLengthRatio: float) -> float:
        return self.m_oRadiusModulation.fGetModulation(fPhi, fLengthRatio)

    def vecGetSurfacePoint(self, fAlphaRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
        alpha = 2.0 * math.pi * fAlphaRatio
        phi = 2.0 * math.pi * fPhiRatio
        x = self.m_fRingRadius * math.cos(alpha)
        y = self.m_fRingRadius * math.sin(alpha)
        frame_pos = as_np3(self.m_oFrame.vecGetPosition())
        frame_x = as_np3(self.m_oFrame.vecGetLocalX())
        frame_y = as_np3(self.m_oFrame.vecGetLocalY())
        frame_z = as_np3(self.m_oFrame.vecGetLocalZ())
        spine = frame_pos + x * frame_x + y * frame_y
        local_x = spine - frame_pos
        norm = float(np.linalg.norm(local_x))
        if norm > 1e-12:
            local_x = local_x / norm
        local_y = frame_z
        radius = fRadiusRatio * self.fGetRadius(phi, alpha)
        pt = spine + (radius * math.cos(phi)) * local_x + (radius * math.sin(phi)) * local_y
        return self.m_fnTrafo(as_vec3(pt))


class BaseCone(BaseShape):
    def __init__(self, oFrame: LocalFrame, fLength: float, fStartRadius: float, fEndRadius: float) -> None:
        super().__init__()
        self.m_fStartRadius = fStartRadius
        self.m_fEndRadius = fEndRadius
        self.m_oCyl = BaseCylinder.from_frame(oFrame, fLength=fLength)
        self.m_oCyl.SetRadius(SurfaceModulation(self.fGetLinearRadius))

    def fGetLinearRadius(self, fPhi: float, fLengthRatio: float) -> float:
        lr = max(0.0, min(1.0, fLengthRatio))
        return self.m_fStartRadius + lr * (self.m_fEndRadius - self.m_fStartRadius)

    def voxConstruct(self) -> Voxels:
        self.m_oCyl.SetTransformation(self.m_fnTrafo)
        return self.m_oCyl.voxConstruct()

    def oGetBaseCylinder(self) -> BaseCylinder:
        return self.m_oCyl


class BaseRevolve(BaseShape):
    def __init__(self, oFrame: LocalFrame, aFrames: Frames, fInwardRadius: float = 3.0, fOutwardRadius: float = 3.0) -> None:
        super().__init__()
        self.m_oFrame = oFrame
        self.m_aFrames = aFrames
        self.SetRadialSteps(100)
        self.SetPolarSteps(360)
        self.SetLengthSteps(500)
        self.m_oOuterRadiusModulation = LineModulation(fOutwardRadius)
        self.m_oInnerRadiusModulation = LineModulation(fInwardRadius)

    def SetRadius(self, oInnerRadiusOverCylinder: LineModulation, oOuterRadiusOverCylinder: LineModulation) -> None:
        self.m_oInnerRadiusModulation = oInnerRadiusOverCylinder
        self.m_oOuterRadiusModulation = oOuterRadiusOverCylinder

    def SetRadialSteps(self, nRadialSteps: int) -> None:
        self.m_nRadialSteps = max(5, int(nRadialSteps))

    def SetPolarSteps(self, nPolarSteps: int) -> None:
        self.m_nPolarSteps = max(5, int(nPolarSteps))

    def SetLengthSteps(self, nLengthSteps: int) -> None:
        self.m_nLengthSteps = max(5, int(nLengthSteps))

    def fGetInnerRadius(self, fLengthRatio: float) -> float:
        return self.m_oInnerRadiusModulation.fGetModulation(fLengthRatio)

    def fGetOuterRadius(self, fLengthRatio: float) -> float:
        return self.m_oOuterRadiusModulation.fGetModulation(fLengthRatio)

    def voxConstruct(self) -> Voxels:
        return Voxels.from_mesh(self.mshConstruct())

    def mshConstruct(self) -> Mesh:
        mesh = Mesh()
        for ip in range(1, self.m_nPolarSteps):
            p1, p2 = self._phi_ratio(ip - 1), self._phi_ratio(ip)
            for ir in range(1, self.m_nRadialSteps):
                r1, r2 = self._radius_ratio(ir - 1), self._radius_ratio(ir)
                l0, lN = self._length_ratio(0), self._length_ratio(self.m_nLengthSteps - 1)
                mesh.nAddTriangle(self.vecGetSurfacePoint(lN, p1, r1), self.vecGetSurfacePoint(lN, p1, r2), self.vecGetSurfacePoint(lN, p2, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(lN, p1, r1), self.vecGetSurfacePoint(lN, p2, r2), self.vecGetSurfacePoint(lN, p2, r1))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l0, p1, r1), self.vecGetSurfacePoint(l0, p2, r2), self.vecGetSurfacePoint(l0, p1, r2))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l0, p1, r1), self.vecGetSurfacePoint(l0, p2, r1), self.vecGetSurfacePoint(l0, p2, r2))
            for il in range(1, self.m_nLengthSteps):
                l1, l2 = self._length_ratio(il - 1), self._length_ratio(il)
                r_in = self._radius_ratio(0)
                r_out = self._radius_ratio(self.m_nRadialSteps - 1)
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_in), self.vecGetSurfacePoint(l2, p1, r_in), self.vecGetSurfacePoint(l2, p2, r_in))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_in), self.vecGetSurfacePoint(l2, p2, r_in), self.vecGetSurfacePoint(l1, p2, r_in))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_out), self.vecGetSurfacePoint(l2, p2, r_out), self.vecGetSurfacePoint(l2, p1, r_out))
                mesh.nAddTriangle(self.vecGetSurfacePoint(l1, p1, r_out), self.vecGetSurfacePoint(l1, p2, r_out), self.vecGetSurfacePoint(l2, p2, r_out))
        return mesh

    def _radius_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nRadialSteps - 1)) * float(step)

    def _phi_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nPolarSteps - 1)) * float(step)

    def _length_ratio(self, step: int) -> float:
        return (1.0 / (self.m_nLengthSteps - 1)) * float(step)

    def vecGetSurfacePoint(self, fLengthRatio: float, fPhiRatio: float, fRadiusRatio: float) -> Vec3:
        spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
        lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
        phi = (2.0 * math.pi) * fPhiRatio
        outward = self.fGetOuterRadius(fLengthRatio)
        inward = -self.fGetInnerRadius(fLengthRatio)
        radius = fRadiusRatio * (outward - inward) + inward
        pt = spine + radius * lx
        rotated = VecOperations.vecRotateAroundAxis(pt, phi, self.m_oFrame.vecGetLocalZ(), self.m_oFrame.vecGetPosition())
        return self.m_fnTrafo(rotated)

    @staticmethod
    def aGetFramesFromContour(oContour: GenericContour, oFrame: LocalFrame | None = None) -> Frames:
        frame = oFrame if oFrame is not None else LocalFrame()
        samples = 500
        points: list[Vec3] = []
        for i in range(samples):
            lr = float(i) / float(samples - 1)
            z = lr * oContour.m_fTotalLength
            radius = oContour.m_oModulation.fGetModulation(lr)
            rel = (radius, 0.0, z)
            points.append(VecOperations.vecTranslatePointOntoFrame(frame, rel))
        return Frames.from_points_and_frame_type(points, Frames.EFrameType.CYLINDRICAL, 0.5)

