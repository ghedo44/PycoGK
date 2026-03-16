from __future__ import annotations


from typing import Callable, Sequence, TYPE_CHECKING

from picogk import Mesh, Voxels

from .._types import Vec3, Vector3Like

if TYPE_CHECKING:
    from ..frames.local_frames import LocalFrame
from .utils import VecOperations


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

