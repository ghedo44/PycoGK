from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING

from picogk import Library, Mesh, Voxels

from .._types import Vec3, Vector3Like, as_np3, as_vec3

if TYPE_CHECKING:
    from ..frames.local_frames import LocalFrame
    
from .vec_operations import VecOperations


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


