from __future__ import annotations

from enum import Enum
from typing import Callable

import numpy as np

from picogk import Mesh
from shape_kernel import LocalFrame, MeshUtility, Sh, VecOperations
from shape_kernel._types import Vec3, as_np3, as_vec3, normalized

from .icosahedral_face import IcosehedralFace


class QuasiTile:
    class EPreviewFace(Enum):
        NONE = "NONE"
        AXIS = "AXIS"
        CONNECTOR = "CONNECTOR"

    def __init__(self) -> None:
        self.m_clr = (1.0, 1.0, 1.0, 1.0)
        self.m_aFaces: list[IcosehedralFace] = []
        self.m_vecRoundedCentre: Vec3 | None = None

    def aGetFaces(self) -> list[IcosehedralFace]:
        return self.m_aFaces

    def ApplyTrafo(self, oTrafoFunc: Callable[[Vec3], Vec3]) -> None:
        for s_face in self.m_aFaces:
            s_face.vecPt1 = oTrafoFunc(s_face.vecPt1)
            s_face.vecPt2 = oTrafoFunc(s_face.vecPt2)
            s_face.vecPt3 = oTrafoFunc(s_face.vecPt3)
            s_face.vecPt4 = oTrafoFunc(s_face.vecPt4)

            s_face.vecCentre = as_vec3(as_np3(s_face.vecPt1) + 0.5 * (as_np3(s_face.vecPt3) - as_np3(s_face.vecPt1)))
            s_face.vecLongAxis = as_vec3(normalized(as_np3(s_face.vecPt3) - as_np3(s_face.vecPt1)))
            s_face.vecShortAxis = as_vec3(normalized(as_np3(s_face.vecPt4) - as_np3(s_face.vecPt2)))

        self.m_vecRoundedCentre = None
        self.vecGetRoundedCentre()

    def vecGetRoundedCentre(self) -> Vec3:
        if self.m_vecRoundedCentre is None:
            a_unique_vertices: list[Vec3] = []
            for s_face in self.m_aFaces:
                a_face_vertices = [s_face.vecPt1, s_face.vecPt2, s_face.vecPt3, s_face.vecPt4]
                for vec in a_face_vertices:
                    vec_rounded = (
                        round(float(vec[0]), 4),
                        round(float(vec[1]), 4),
                        round(float(vec[2]), 4),
                    )
                    if vec_rounded not in a_unique_vertices:
                        a_unique_vertices.append(vec_rounded)

            vec_centre = sum((as_np3(vec) for vec in a_unique_vertices), start=as_np3((0.0, 0.0, 0.0)))
            vec_centre /= float(len(a_unique_vertices))
            self.m_vecRoundedCentre = (
                round(float(vec_centre[0]), 4),
                round(float(vec_centre[1]), 4),
                round(float(vec_centre[2]), 4),
            )
        return self.m_vecRoundedCentre

    def nGetNumberOfFaces(self) -> int:
        return len(self.m_aFaces)

    def Preview(self, ePreviewFace: "QuasiTile.EPreviewFace") -> None:
        msh_tile = Mesh()
        vec_centre = as_np3(self.vecGetRoundedCentre())
        for s_face in self.m_aFaces:
            vec_normal = np.cross(
                normalized(as_np3(s_face.vecPt3) - as_np3(s_face.vecPt1)),
                normalized(as_np3(s_face.vecPt4) - as_np3(s_face.vecPt2)),
            )
            if VecOperations.bCheckAlignment(as_vec3(vec_normal), as_vec3(as_np3(s_face.vecCentre) - vec_centre)):
                MeshUtility.AddQuad(msh_tile, s_face.vecPt1, s_face.vecPt2, s_face.vecPt3, s_face.vecPt4)
            else:
                MeshUtility.AddQuad(msh_tile, s_face.vecPt1, s_face.vecPt4, s_face.vecPt3, s_face.vecPt2)

            if ePreviewFace == self.EPreviewFace.AXIS:
                s_face.Preview(False)
            elif ePreviewFace == self.EPreviewFace.CONNECTOR:
                s_face.Preview(True)

        Sh.PreviewMesh(msh_tile, self.m_clr, 0.9)

    def oGetConnectorFrame(self, iFaceIndex: int, iIndex: int = 0) -> LocalFrame:
        s_face = self.m_aFaces[iFaceIndex]

        vec_pos = s_face.vecCentre
        vec_local_x = as_vec3(normalized(as_np3(s_face.vecPt3) - as_np3(s_face.vecPt1)))
        vec_local_y = as_vec3(normalized(as_np3(s_face.vecPt4) - as_np3(s_face.vecPt2)))
        vec_local_z = as_vec3(np.cross(as_np3(vec_local_x), as_np3(vec_local_y)))
        vec_local_z = as_vec3(VecOperations.vecFlipForAlignment(vec_local_z, as_vec3(as_np3(vec_pos) - as_np3(self.vecGetRoundedCentre()))))

        if iIndex != 0 and s_face.eConnector == IcosehedralFace.EConnector.LINE:
            vec_local_x = as_vec3(-as_np3(vec_local_x))

        return LocalFrame(vec_pos, vec_local_z, vec_local_x)

    def AttachToOtherQuasiTile(self, iThisFaceIndex: int, oOtherTile: "QuasiTile", iOtherFaceIndex: int, bSwitch: bool = False) -> None:
        n_this_faces = self.nGetNumberOfFaces()
        n_other_faces = oOtherTile.nGetNumberOfFaces()

        if iThisFaceIndex < 0 or iThisFaceIndex >= n_this_faces:
            raise QuasiTile.ThisFaceNotFoundException("This face index exceeds number of faces on this quasi tile.")
        if iOtherFaceIndex < 0 or iOtherFaceIndex >= n_other_faces:
            raise QuasiTile.OtherFaceNotFoundException("Other face index exceeds number of faces on other quasi tile.")

        if self.m_aFaces[iThisFaceIndex].eConnector != oOtherTile.m_aFaces[iOtherFaceIndex].eConnector:
            raise QuasiTile.ConnectorMismatchException("Connector types do not match.")

        i_switch = 1 if bSwitch else 0
        o_other_connector_frame = oOtherTile.oGetConnectorFrame(iOtherFaceIndex, i_switch)
        o_this_current_face_frame = LocalFrame.oGetInvertFrame(self.oGetConnectorFrame(iThisFaceIndex), True, False)

        for s_face in self.m_aFaces:
            s_face.vecPt1 = VecOperations.vecExpressPointInFrame(o_this_current_face_frame, s_face.vecPt1)
            s_face.vecPt2 = VecOperations.vecExpressPointInFrame(o_this_current_face_frame, s_face.vecPt2)
            s_face.vecPt3 = VecOperations.vecExpressPointInFrame(o_this_current_face_frame, s_face.vecPt3)
            s_face.vecPt4 = VecOperations.vecExpressPointInFrame(o_this_current_face_frame, s_face.vecPt4)

            s_face.vecPt1 = VecOperations.vecTranslatePointOntoFrame(o_other_connector_frame, s_face.vecPt1)
            s_face.vecPt2 = VecOperations.vecTranslatePointOntoFrame(o_other_connector_frame, s_face.vecPt2)
            s_face.vecPt3 = VecOperations.vecTranslatePointOntoFrame(o_other_connector_frame, s_face.vecPt3)
            s_face.vecPt4 = VecOperations.vecTranslatePointOntoFrame(o_other_connector_frame, s_face.vecPt4)

            s_face.vecCentre = as_vec3(as_np3(s_face.vecPt1) + 0.5 * (as_np3(s_face.vecPt3) - as_np3(s_face.vecPt1)))
            s_face.vecLongAxis = as_vec3(normalized(as_np3(s_face.vecPt3) - as_np3(s_face.vecPt1)))
            s_face.vecShortAxis = as_vec3(normalized(as_np3(s_face.vecPt4) - as_np3(s_face.vecPt2)))

        self.m_vecRoundedCentre = None
        self.vecGetRoundedCentre()

    class ThisFaceNotFoundException(Exception):
        pass

    class OtherFaceNotFoundException(Exception):
        pass

    class ConnectorMismatchException(Exception):
        pass


__all__ = ["QuasiTile"]
