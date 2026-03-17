from __future__ import annotations

import math

import numpy as np

from shape_kernel import Cp, LocalFrame, VecOperations
from shape_kernel._types import as_np3, as_vec3, normalized

from .icosahedral_face import IcosehedralFace
from .quasi_tile import QuasiTile


class QuasiTile_03(QuasiTile):
    def __init__(self, oFrame0c: LocalFrame, fFaceSide: float = 20.0) -> None:
        super().__init__()
        self.m_clr = Cp.clrCrystal

        f_rot_angle = (360.0 / 5.0) / 180.0 * math.pi

        s_ref_face = IcosehedralFace(oFrame0c, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.LINE, fFaceSide)
        f_long_axis = float(np.linalg.norm(as_np3(s_ref_face.vecPt3) - as_np3(s_ref_face.vecPt1)))
        f_short_axis = float(np.linalg.norm(as_np3(s_ref_face.vecPt4) - as_np3(s_ref_face.vecPt2)))
        f_dome_pentagon_side = f_short_axis
        f_dome_pentagon_height = f_dome_pentagon_side / (2.0 * math.sqrt(5.0 - math.sqrt(20.0)))
        f_tilt_angle_rad = math.asin(f_dome_pentagon_height / (0.5 * f_long_axis))
        f_tilt_angle_deg = 90.0 - (f_tilt_angle_rad / math.pi * 180.0)
        f_tilt_angle = (-f_tilt_angle_deg) / 180.0 * math.pi

        a_lower_centre_faces: list[IcosehedralFace] = []
        for i in range(5):
            o_frame_1b = LocalFrame.oGetRotatedFrame(oFrame0c, i * f_rot_angle, oFrame0c.vecGetLocalZ())
            o_frame_1b = LocalFrame.oGetRotatedFrame(o_frame_1b, f_tilt_angle, o_frame_1b.vecGetLocalY())

            s_face_1b = IcosehedralFace(o_frame_1b, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.TRIANGLE, fFaceSide)
            a_lower_centre_faces.append(s_face_1b)

        a_lower_side_faces: list[IcosehedralFace] = []
        for i in range(5):
            i_lower_index = i - 1
            if i_lower_index < 0:
                i_lower_index += 5
            i_upper_index = i

            s_face_1b = a_lower_centre_faces[i_lower_index]
            s_face_2b = a_lower_centre_faces[i_upper_index]

            vec_tip_1b = s_face_1b.vecPt3
            vec_tip_2b = s_face_2b.vecPt3
            vec_long_1s = as_vec3(normalized(as_np3(vec_tip_2b) - as_np3(vec_tip_1b)))
            vec_centre_1s = as_vec3(as_np3(vec_tip_1b) + 0.5 * (as_np3(vec_tip_2b) - as_np3(vec_tip_1b)))
            vec_short_1s = as_vec3(normalized(as_np3(s_face_1b.vecPt4) - as_np3(vec_centre_1s)))
            vec_normal_1s = as_vec3(np.cross(as_np3(vec_long_1s), as_np3(vec_short_1s)))
            o_frame_1s = LocalFrame(vec_tip_1b, vec_normal_1s, vec_long_1s)

            s_face_1s = IcosehedralFace(o_frame_1s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.ARROW, fFaceSide)
            a_lower_side_faces.append(s_face_1s)

        f_lower_z = VecOperations.vecExpressPointInFrame(oFrame0c, a_lower_side_faces[0].vecPt1)[2]
        f_upper_z = VecOperations.vecExpressPointInFrame(oFrame0c, a_lower_side_faces[0].vecPt2)[2]
        f_max_z = f_lower_z + f_upper_z
        o_frame_1c = LocalFrame.oGetTranslatedFrame(oFrame0c, tuple(f_max_z * x for x in oFrame0c.vecGetLocalZ()))
        o_frame_1c = LocalFrame.oGetInvertFrame(o_frame_1c, True, True)

        a_upper_centre_faces: list[IcosehedralFace] = []
        for i in range(5):
            o_frame_1t = LocalFrame.oGetRotatedFrame(o_frame_1c, i * f_rot_angle, o_frame_1c.vecGetLocalZ())
            o_frame_1t = LocalFrame.oGetRotatedFrame(o_frame_1t, f_tilt_angle, o_frame_1t.vecGetLocalY())

            s_face_1t = IcosehedralFace(o_frame_1t, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.LINE, fFaceSide)
            a_upper_centre_faces.append(s_face_1t)

        a_upper_side_faces: list[IcosehedralFace] = []
        for i in range(5):
            i_lower_index = i - 1
            if i_lower_index < 0:
                i_lower_index += 5
            i_upper_index = i

            s_face_1b = a_upper_centre_faces[i_lower_index]
            s_face_2b = a_upper_centre_faces[i_upper_index]

            vec_tip_1b = s_face_1b.vecPt3
            vec_tip_2b = s_face_2b.vecPt3
            vec_long_1s = as_vec3(normalized(as_np3(vec_tip_2b) - as_np3(vec_tip_1b)))
            vec_centre_1s = as_vec3(as_np3(vec_tip_1b) + 0.5 * (as_np3(vec_tip_2b) - as_np3(vec_tip_1b)))
            vec_short_1s = as_vec3(normalized(as_np3(s_face_1b.vecPt4) - as_np3(vec_centre_1s)))
            vec_normal_1s = as_vec3(np.cross(as_np3(vec_long_1s), as_np3(vec_short_1s)))
            o_frame_1s = LocalFrame(vec_tip_1b, vec_normal_1s, vec_long_1s)

            s_face_1s = IcosehedralFace(o_frame_1s, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.LINE, fFaceSide)
            a_upper_side_faces.append(s_face_1s)

        self.m_aFaces = []
        self.m_aFaces.extend(a_lower_centre_faces)
        self.m_aFaces.extend(a_lower_side_faces)
        self.m_aFaces.extend(a_upper_side_faces)
        self.m_aFaces.extend(a_upper_centre_faces)


__all__ = ["QuasiTile_03"]
