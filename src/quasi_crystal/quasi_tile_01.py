from __future__ import annotations

import math

import numpy as np

from shape_kernel import Cp, LocalFrame, VecOperations
from shape_kernel._types import as_np3

from .icosahedral_face import IcosehedralFace
from .quasi_tile import QuasiTile


class QuasiTile_01(QuasiTile):
    def __init__(self, oFrame0c: LocalFrame, fFaceSide: float = 20.0) -> None:
        super().__init__()
        self.m_clr = Cp.clrRed

        f_rot_angle = (360.0 / 3.0) / 180.0 * math.pi

        s_ref_face = IcosehedralFace(oFrame0c, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.LINE, fFaceSide)
        f_long_axis = float(np.linalg.norm(as_np3(s_ref_face.vecPt3) - as_np3(s_ref_face.vecPt1)))
        f_short_axis = float(np.linalg.norm(as_np3(s_ref_face.vecPt4) - as_np3(s_ref_face.vecPt2)))
        f_dome_triangle_side = f_short_axis
        f_dome_triangle_height = f_dome_triangle_side / (2.0 * math.sqrt(3.0))
        f_tilt_angle_rad = math.asin(f_dome_triangle_height / (0.5 * f_long_axis))
        f_tilt_angle_deg = 90.0 - (f_tilt_angle_rad / math.pi * 180.0)
        f_tilt_angle = (-f_tilt_angle_deg) / 180.0 * math.pi

        a_lower_centre_faces: list[IcosehedralFace] = []
        for i in range(3):
            o_frame_1b = LocalFrame.oGetRotatedFrame(oFrame0c, i * f_rot_angle, oFrame0c.vecGetLocalZ())
            o_frame_1b = LocalFrame.oGetRotatedFrame(o_frame_1b, f_tilt_angle, o_frame_1b.vecGetLocalY())

            s_face_1b = IcosehedralFace(o_frame_1b, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.TRIANGLE, fFaceSide)
            a_lower_centre_faces.append(s_face_1b)

        f_lower_z = VecOperations.vecExpressPointInFrame(oFrame0c, a_lower_centre_faces[0].vecPt2)[2]
        f_upper_z = VecOperations.vecExpressPointInFrame(oFrame0c, a_lower_centre_faces[0].vecPt3)[2]
        f_max_z = f_lower_z + f_upper_z
        o_frame_1c = LocalFrame.oGetTranslatedFrame(oFrame0c, tuple(f_max_z * x for x in oFrame0c.vecGetLocalZ()))
        o_frame_1c = LocalFrame.oGetInvertFrame(o_frame_1c, True, True)

        a_upper_centre_faces: list[IcosehedralFace] = []
        for i in range(3):
            o_frame_1t = LocalFrame.oGetRotatedFrame(o_frame_1c, i * f_rot_angle, o_frame_1c.vecGetLocalZ())
            o_frame_1t = LocalFrame.oGetRotatedFrame(o_frame_1t, f_tilt_angle, o_frame_1t.vecGetLocalY())

            s_face_1t = IcosehedralFace(o_frame_1t, IcosehedralFace.EDef.LONG_AXIS, IcosehedralFace.EConnector.LINE, fFaceSide)
            a_upper_centre_faces.append(s_face_1t)

        for i in range(3):
            a_lower_centre_faces[i].FlipAroundShortAxis()
            a_lower_centre_faces[i].FlipAroundLongAxis()

        self.m_aFaces = []
        self.m_aFaces.extend(a_lower_centre_faces)
        self.m_aFaces.extend(a_upper_centre_faces)

__all__ = ["QuasiTile_01"]
