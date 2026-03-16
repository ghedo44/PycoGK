from __future__ import annotations

import math
import numpy as np

from enum import Enum
from pathlib import Path
from typing import Callable, Sequence, cast

from picogk import BBox3, Lattice, Library, Mesh, PolyLine, VedoViewer, Voxels
from picogk._types import ColorFloat

from .._types import ColorLike, Vec3, Vector3Like, as_np3, as_vec3
from ..utils.utils import GridOperations, LocalFrame, VecOperations
class Measure:
    @staticmethod
    def fGetVolume(oVoxels: Voxels) -> float:
        volume, _bbox = oVoxels.calculate_properties()
        return float(volume)

    @staticmethod
    def fGetSurfaceArea(oVoxels_or_mesh: Voxels | Mesh) -> float:
        if isinstance(oVoxels_or_mesh, Voxels):
            with Mesh.from_voxels(oVoxels_or_mesh) as msh:
                return Measure.fGetSurfaceArea(msh)
        msh = oVoxels_or_mesh
        total = 0.0
        for i in range(msh.triangle_count()):
            a, b, c = msh.get_triangle_vertices(i)
            total += Measure.fGetTriangleArea(a, b, c)
        return total

    @staticmethod
    def fGetTriangleArea(vecA: Vector3Like, vecB: Vector3Like, vecC: Vector3Like) -> float:
        ab = as_np3(vecB) - as_np3(vecA)
        ac = as_np3(vecC) - as_np3(vecA)
        return float(0.5 * np.linalg.norm(np.cross(ab, ac)))

    @staticmethod
    def vecGetCentreOfGravity(oVoxels: Voxels) -> Vec3:
        _volume, (box_min, box_max) = oVoxels.calculate_properties()
        step = Library.voxel_size_mm
        bmin = np.array(box_min, dtype=np.float64) - step
        bmax = np.array(box_max, dtype=np.float64) + step
        cog  = np.zeros(3, dtype=np.float64)
        count = 0
        xs = np.arange(float(bmin[0]), float(bmax[0]), step)
        ys = np.arange(float(bmin[1]), float(bmax[1]), step)
        zs = np.arange(float(bmin[2]), float(bmax[2]), step)
        for x in xs:
            for y in ys:
                for z in zs:
                    pt = (float(x), float(y), float(z))
                    if oVoxels.is_inside(pt):
                        cog += np.array([x, y, z])
                        count += 1
        if count > 0:
            cog /= count
        return as_vec3(cog)

    @staticmethod
    def matGetMomentOfInertia(oVoxels: Voxels, oRefFrame: LocalFrame, fDensity: float) -> list[list[float]]:
        volume, (box_min, box_max) = oVoxels.calculate_properties()
        step       = Library.voxel_size_mm
        bmin       = np.array(box_min, dtype=np.float64) - step
        bmax       = np.array(box_max, dtype=np.float64) + step
        dv         = step ** 3
        mat        = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        vox_count  = 0
        xs = np.arange(float(bmin[0]), float(bmax[0]), step)
        ys = np.arange(float(bmin[1]), float(bmax[1]), step)
        zs = np.arange(float(bmin[2]), float(bmax[2]), step)
        for x in xs:
            for y in ys:
                for z in zs:
                    pt = (float(x), float(y), float(z))
                    if oVoxels.is_inside(pt):
                        vox_count += 1
        vox_vol    = float(vox_count) * dv
        vol_factor = float(volume) / max(vox_vol, 1e-30)
        for x in xs:
            for y in ys:
                for z in zs:
                    pt = (float(x), float(y), float(z))
                    if oVoxels.is_inside(pt):
                        dm  = float(fDensity) * vol_factor * dv / 1e9
                        rel = VecOperations.vecExpressPointInFrame(oRefFrame, pt)
                        rx, ry, rz = float(rel[0]), float(rel[1]), float(rel[2])
                        mat[0][0] += dm * (ry * ry + rz * rz)
                        mat[1][1] += dm * (rx * rx + rz * rz)
                        mat[2][2] += dm * (rx * rx + ry * ry)
                        mat[0][1] += dm * (-rx * ry)
                        mat[0][2] += dm * (-rx * rz)
                        mat[1][0] += dm * (-ry * rx)
                        mat[1][2] += dm * (-ry * rz)
                        mat[2][0] += dm * (-rz * rx)
                        mat[2][1] += dm * (-rz * ry)
        return mat


class MeshUtility:
    @staticmethod
    def mshFromGrid(aGrid: Sequence[Sequence[Vector3Like]]) -> Mesh:
        msh = Mesh()
        for i in range(1, len(aGrid)):
            for j in range(1, len(aGrid[i])):
                p1 = aGrid[i - 1][j - 1]
                p2 = aGrid[i - 1][j]
                p3 = aGrid[i][j]
                p4 = aGrid[i][j - 1]
                msh.nAddTriangle(p4, p1, p2)
                msh.nAddTriangle(p2, p3, p4)
        return msh

    @staticmethod
    def mshFromQuad(vecPt1: Vector3Like, vecPt2: Vector3Like, vecPt3: Vector3Like, vecPt4: Vector3Like) -> Mesh:
        msh = Mesh()
        msh.nAddTriangle(vecPt4, vecPt1, vecPt2)
        msh.nAddTriangle(vecPt2, vecPt3, vecPt4)
        return msh

    @staticmethod
    def AddQuad(msh: Mesh, vecPt1: Vector3Like, vecPt2: Vector3Like, vecPt3: Vector3Like, vecPt4: Vector3Like) -> None:
        msh.nAddTriangle(vecPt4, vecPt1, vecPt2)
        msh.nAddTriangle(vecPt2, vecPt3, vecPt4)

    @staticmethod
    def mshApplyTransformation(msh: Mesh, fnTrafo: Callable[[Vec3], Vec3]) -> Mesh:
        new_msh = Mesh()
        for i in range(msh.triangle_count()):
            a, b, c = msh.get_triangle_vertices(i)
            new_msh.nAddTriangle(fnTrafo(a), fnTrafo(b), fnTrafo(c))
        return new_msh

    @staticmethod
    def voxApplyTransformation(vox: Voxels, fnTrafo: Callable[[Vec3], Vec3]) -> Voxels:
        with Mesh.from_voxels(vox) as msh:
            new_msh = MeshUtility.mshApplyTransformation(msh, fnTrafo)
        return Voxels.from_mesh(new_msh)

    @staticmethod
    def mshTranslateMeshOntoFrame(msh: Mesh, oInputFrame: LocalFrame, oOutputFrame: LocalFrame) -> Mesh:
        def trafo(pt: Vec3) -> Vec3:
            rel = VecOperations.vecExpressPointInFrame(oInputFrame, pt)
            return VecOperations.vecTranslatePointOntoFrame(oOutputFrame, rel)
        return MeshUtility.mshApplyTransformation(msh, trafo)

    @staticmethod
    def Append(msh1: Mesh, msh2: Mesh) -> Mesh:
        return msh1.append(msh2)


class CylUtility:
    @staticmethod
    def voxGetCyl(fStartZ_or_frame: float | LocalFrame, fEndZ_or_startZ: float = 0.0, fRadius_or_endZ: float = 0.0, fRadius: float | None = None) -> Voxels:
        from ..base_shapes import BaseCylinder
        if isinstance(fStartZ_or_frame, LocalFrame):
            oRefFrame = fStartZ_or_frame
            fStartZ   = float(fEndZ_or_startZ)
            fEndZ     = float(fRadius_or_endZ)
            fR        = float(fRadius) if fRadius is not None else 1.0
            lz        = as_np3(oRefFrame.vecGetLocalZ())
            oFrame    = oRefFrame.oTranslate(as_vec3(lz * fStartZ))
            length    = fEndZ - fStartZ
        else:
            fStartZ = float(fStartZ_or_frame)
            fEndZ   = float(fEndZ_or_startZ)
            fR      = float(fRadius_or_endZ)
            oFrame  = LocalFrame((0.0, 0.0, fStartZ))
            length  = fEndZ - fStartZ
        return BaseCylinder.from_frame(oFrame, length, fR).voxConstruct()

    @staticmethod
    def voxGetCone(fStartZ_or_frame: float | LocalFrame, fEndZ_or_startZ: float, fStartRadius_or_endZ: float, fEndRadius_or_startR: float, fEndRadius: float | None = None) -> Voxels:
        from ..base_shapes import BaseCone
        if isinstance(fStartZ_or_frame, LocalFrame):
            oRefFrame = fStartZ_or_frame
            fStartZ   = float(fEndZ_or_startZ)
            fEndZ     = float(fStartRadius_or_endZ)
            fStartR   = float(fEndRadius_or_startR)
            fEndR     = float(fEndRadius) if fEndRadius is not None else fStartR
            lz        = as_np3(oRefFrame.vecGetLocalZ())
            oFrame    = oRefFrame.oTranslate(as_vec3(lz * fStartZ))
            length    = fEndZ - fStartZ
        else:
            fStartZ = float(fStartZ_or_frame)
            fEndZ   = float(fEndZ_or_startZ)
            fStartR = float(fStartRadius_or_endZ)
            fEndR   = float(fEndRadius_or_startR)
            oFrame  = LocalFrame((0.0, 0.0, fStartZ))
            length  = fEndZ - fStartZ
        return BaseCone(oFrame, length, fStartR, fEndR).voxConstruct()

    @staticmethod
    def voxGetPipe(fStartZ_or_frame: float | LocalFrame, fEndZ_or_startZ: float, fInnerRadius_or_endZ: float, fOuterRadius_or_innerR: float, fOuterRadius: float | None = None) -> Voxels:
        from ..base_shapes import BasePipe
        if isinstance(fStartZ_or_frame, LocalFrame):
            oRefFrame = fStartZ_or_frame
            fStartZ   = float(fEndZ_or_startZ)
            fEndZ     = float(fInnerRadius_or_endZ)
            fInnerR   = float(fOuterRadius_or_innerR)
            fOuterR   = float(fOuterRadius) if fOuterRadius is not None else fInnerR
            lz        = as_np3(oRefFrame.vecGetLocalZ())
            oFrame    = oRefFrame.oTranslate(as_vec3(lz * fStartZ))
            length    = fEndZ - fStartZ
        else:
            fStartZ = float(fStartZ_or_frame)
            fEndZ   = float(fEndZ_or_startZ)
            fInnerR = float(fInnerRadius_or_endZ)
            fOuterR = float(fOuterRadius_or_innerR)
            oFrame  = LocalFrame((0.0, 0.0, fStartZ))
            length  = fEndZ - fStartZ
        return BasePipe.from_frame(oFrame, length, fInnerR, fOuterR).voxConstruct()

