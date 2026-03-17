from __future__ import annotations

import numpy as np

from shape_kernel import Cp, LocalFrame
from shape_kernel._types import as_np3, as_vec3, normalized

from .icosahedral_face import IcosehedralFace
from .quasi_tile import QuasiTile


class QuasiTile_02(QuasiTile):
    def __init__(self, oFrame0c: LocalFrame, fFaceSide: float = 20.0) -> None:
        super().__init__()
        self.m_clr = Cp.clrLemongrass

        s_ref_face = IcosehedralFace(oFrame0c, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.LINE, fFaceSide)
        f_long_axis = float(np.linalg.norm(as_np3(s_ref_face.vecPt3) - as_np3(s_ref_face.vecPt1)))

        o_frame_1b = oFrame0c
        o_frame_1t = LocalFrame.oGetTranslatedFrame(oFrame0c, tuple(f_long_axis * x for x in oFrame0c.vecGetLocalZ()))
        o_frame_1t = LocalFrame.oGetInvertFrame(o_frame_1t, True, True)

        s_face_1b = IcosehedralFace(o_frame_1b, IcosehedralFace.EDef.CENTRE, IcosehedralFace.EConnector.LINE, fFaceSide)
        s_face_1t = IcosehedralFace(o_frame_1t, IcosehedralFace.EDef.CENTRE, IcosehedralFace.EConnector.LINE, fFaceSide)

        a_side_faces: list[IcosehedralFace] = []
        a_angled_faces: list[IcosehedralFace] = []

        for vec_side_1b, vec_side_1t in ((s_face_1b.vecPt2, s_face_1t.vecPt2), (s_face_1b.vecPt4, s_face_1t.vecPt4)):
            vec_long_1s = as_vec3(normalized(as_np3(vec_side_1t) - as_np3(vec_side_1b)))
            vec_short_1s = as_vec3(normalized(as_np3(s_face_1b.vecPt3) - as_np3(s_face_1b.vecPt1)))
            vec_normal_1s = as_vec3(np.cross(as_np3(vec_long_1s), as_np3(vec_short_1s)))
            o_frame_1s = LocalFrame(vec_side_1b, vec_normal_1s, vec_long_1s)
            s_face_1s = IcosehedralFace(o_frame_1s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.TRIANGLE, fFaceSide)
            a_side_faces.append(s_face_1s)

            vec_centre_2s = as_vec3(0.5 * (as_np3(s_face_1b.vecPt1) + as_np3(s_face_1s.vecPt2)))
            vec_long_2s = as_vec3(normalized(as_np3(vec_centre_2s) - as_np3(vec_side_1b)))
            vec_short_2s = as_vec3(normalized(as_np3(vec_centre_2s) - as_np3(s_face_1b.vecPt1)))
            vec_normal_2s = as_vec3(np.cross(as_np3(vec_long_2s), as_np3(vec_short_2s)))
            o_frame_2s = LocalFrame(vec_side_1b, vec_normal_2s, vec_long_2s)
            s_face_2s = IcosehedralFace(o_frame_2s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.ARROW, fFaceSide)

            vec_centre_3s = as_vec3(0.5 * (as_np3(s_face_1b.vecPt3) + as_np3(s_face_1s.vecPt4)))
            vec_long_3s = as_vec3(normalized(as_np3(vec_centre_3s) - as_np3(vec_side_1b)))
            vec_short_3s = as_vec3(normalized(as_np3(vec_centre_3s) - as_np3(s_face_1b.vecPt3)))
            vec_normal_3s = as_vec3(np.cross(as_np3(vec_long_3s), as_np3(vec_short_3s)))
            o_frame_3s = LocalFrame(vec_side_1b, vec_normal_3s, vec_long_3s)
            s_face_3s = IcosehedralFace(o_frame_3s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.ARROW, fFaceSide)

            a_angled_faces.extend([s_face_2s, s_face_3s])

            vec_centre_2s = as_vec3(0.5 * (as_np3(s_face_1t.vecPt1) + as_np3(s_face_1s.vecPt4)))
            vec_long_2s = as_vec3(normalized(as_np3(vec_centre_2s) - as_np3(vec_side_1t)))
            vec_short_2s = as_vec3(normalized(as_np3(vec_centre_2s) - as_np3(s_face_1t.vecPt1)))
            vec_normal_2s = as_vec3(np.cross(as_np3(vec_long_2s), as_np3(vec_short_2s)))
            o_frame_2s = LocalFrame(vec_side_1t, vec_normal_2s, vec_long_2s)
            s_face_2s = IcosehedralFace(o_frame_2s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.TRIANGLE, fFaceSide)

            vec_centre_3s = as_vec3(0.5 * (as_np3(s_face_1t.vecPt3) + as_np3(s_face_1s.vecPt2)))
            vec_long_3s = as_vec3(normalized(as_np3(vec_centre_3s) - as_np3(vec_side_1t)))
            vec_short_3s = as_vec3(normalized(as_np3(vec_centre_3s) - as_np3(s_face_1t.vecPt3)))
            vec_normal_3s = as_vec3(np.cross(as_np3(vec_long_3s), as_np3(vec_short_3s)))
            o_frame_3s = LocalFrame(vec_side_1t, vec_normal_3s, vec_long_3s)
            s_face_3s = IcosehedralFace(o_frame_3s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.TRIANGLE, fFaceSide)

            a_angled_faces.extend([s_face_2s, s_face_3s])

        for i in range(len(a_side_faces)):
            a_side_faces[i].FlipAroundShortAxis()
            a_side_faces[i].FlipAroundLongAxis()

        self.m_aFaces = [s_face_1b, s_face_1t]
        self.m_aFaces.extend(a_side_faces)
        self.m_aFaces.extend(a_angled_faces)


__all__ = ["QuasiTile_02"]
