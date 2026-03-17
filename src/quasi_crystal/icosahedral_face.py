from __future__ import annotations

import math
from enum import Enum

import numpy as np

from picogk import Lattice
from shape_kernel import Cp, LocalFrame, Sh, VecOperations
from shape_kernel._types import as_np3, as_vec3, normalized


class IcosehedralFace:
    class EConnector(Enum):
        ARROW = "ARROW"
        TRIANGLE = "TRIANGLE"
        LINE = "LINE"

    class EDef(Enum):
        CENTRE = "CENTRE"
        SHORT_AXIS = "SHORT_AXIS"
        LONG_AXIS = "LONG_AXIS"

    m_fPsi = math.acos(1.0 / math.sqrt(5.0))

    def __init__(
        self,
        oFrame: LocalFrame,
        eDef: "IcosehedralFace.EDef",
        eConnector: "IcosehedralFace.EConnector",
        fSide: float = 20.0,
    ) -> None:
        self.eConnector = eConnector

        vec_pointer = float(fSide) * np.array((1.0, 0.0, 0.0), dtype=np.float64)
        vec_pointer_01 = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(vec_pointer), -0.5 * self.m_fPsi, (0.0, 0.0, 1.0)))
        vec_pointer_02 = as_np3(VecOperations.vecRotateAroundAxis(as_vec3(vec_pointer), +0.5 * self.m_fPsi, (0.0, 0.0, 1.0)))

        self.vecPt1 = as_vec3((0.0, 0.0, 0.0))
        self.vecPt2 = as_vec3(as_np3(self.vecPt1) + vec_pointer_01)
        self.vecPt3 = as_vec3(as_np3(self.vecPt2) + vec_pointer_02)
        self.vecPt4 = as_vec3(as_np3(self.vecPt3) - vec_pointer_01)

        if eDef == self.EDef.CENTRE:
            vec_centre = as_np3(self.vecPt1) + 0.5 * (as_np3(self.vecPt3) - as_np3(self.vecPt1))
            self.vecPt1 = as_vec3(as_np3(self.vecPt1) - vec_centre)
            self.vecPt2 = as_vec3(as_np3(self.vecPt2) - vec_centre)
            self.vecPt3 = as_vec3(as_np3(self.vecPt3) - vec_centre)
            self.vecPt4 = as_vec3(as_np3(self.vecPt4) - vec_centre)

            self.vecPt1 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt1)
            self.vecPt2 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt2)
            self.vecPt3 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt3)
            self.vecPt4 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt4)
        elif eDef == self.EDef.LONG_AXIS:
            vec_shift = as_np3(self.vecPt1)
            self.vecPt1 = as_vec3(as_np3(self.vecPt1) - vec_shift)
            self.vecPt2 = as_vec3(as_np3(self.vecPt2) - vec_shift)
            self.vecPt3 = as_vec3(as_np3(self.vecPt3) - vec_shift)
            self.vecPt4 = as_vec3(as_np3(self.vecPt4) - vec_shift)

            self.vecPt1 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt1)
            self.vecPt2 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt2)
            self.vecPt3 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt3)
            self.vecPt4 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt4)
        elif eDef == self.EDef.SHORT_AXIS:
            vec_centre = as_np3(self.vecPt1) + 0.5 * (as_np3(self.vecPt3) - as_np3(self.vecPt1))
            self.vecPt1 = as_vec3(as_np3(self.vecPt1) - vec_centre)
            self.vecPt2 = as_vec3(as_np3(self.vecPt2) - vec_centre)
            self.vecPt3 = as_vec3(as_np3(self.vecPt3) - vec_centre)
            self.vecPt4 = as_vec3(as_np3(self.vecPt4) - vec_centre)

            self.vecPt1 = VecOperations.vecRotateAroundZ(self.vecPt1, -90.0 / 180.0 * math.pi)
            self.vecPt2 = VecOperations.vecRotateAroundZ(self.vecPt2, -90.0 / 180.0 * math.pi)
            self.vecPt3 = VecOperations.vecRotateAroundZ(self.vecPt3, -90.0 / 180.0 * math.pi)
            self.vecPt4 = VecOperations.vecRotateAroundZ(self.vecPt4, -90.0 / 180.0 * math.pi)

            vec_shift = as_np3(self.vecPt2)
            self.vecPt1 = as_vec3(as_np3(self.vecPt1) - vec_shift)
            self.vecPt2 = as_vec3(as_np3(self.vecPt2) - vec_shift)
            self.vecPt3 = as_vec3(as_np3(self.vecPt3) - vec_shift)
            self.vecPt4 = as_vec3(as_np3(self.vecPt4) - vec_shift)

            self.vecPt1 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt1)
            self.vecPt2 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt2)
            self.vecPt3 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt3)
            self.vecPt4 = VecOperations.vecTranslatePointOntoFrame(oFrame, self.vecPt4)

        self.vecCentre = as_vec3(as_np3(self.vecPt1) + 0.5 * (as_np3(self.vecPt3) - as_np3(self.vecPt1)))
        self.vecLongAxis = as_vec3(normalized(as_np3(self.vecPt3) - as_np3(self.vecPt1)))
        self.vecShortAxis = as_vec3(normalized(as_np3(self.vecPt4) - as_np3(self.vecPt2)))

    def FlipAroundShortAxis(self) -> None:
        vec_temp1 = self.vecPt1
        vec_temp2 = self.vecPt2
        vec_temp3 = self.vecPt3
        vec_temp4 = self.vecPt4

        self.vecPt1 = vec_temp3
        self.vecPt2 = vec_temp2
        self.vecPt3 = vec_temp1
        self.vecPt4 = vec_temp4

    def FlipAroundLongAxis(self) -> None:
        vec_temp1 = self.vecPt1
        vec_temp2 = self.vecPt2
        vec_temp3 = self.vecPt3
        vec_temp4 = self.vecPt4

        self.vecPt1 = vec_temp1
        self.vecPt2 = vec_temp4
        self.vecPt3 = vec_temp3
        self.vecPt4 = vec_temp2

    def Preview(self, bShowConnector: bool) -> None:
        a_boundary = [self.vecPt1, self.vecPt2, self.vecPt3, self.vecPt4, self.vecPt1]
        a_long_axis = [self.vecPt1, self.vecPt3]
        a_short_axis = [self.vecPt2, self.vecPt4]
        Sh.PreviewLine(a_boundary, Cp.clrBlack)
        Sh.PreviewLine(a_long_axis, Cp.clrGreen)
        Sh.PreviewLine(a_short_axis, Cp.clrRed)

        if bShowConnector:
            lat_connector = Lattice()
            if self.eConnector == self.EConnector.LINE:
                vec_start = as_vec3(as_np3(self.vecPt1) + 0.2 * (as_np3(self.vecPt3) - as_np3(self.vecPt1)))
                vec_end = as_vec3(as_np3(self.vecPt1) + 0.8 * (as_np3(self.vecPt3) - as_np3(self.vecPt1)))
                lat_connector.AddBeam(vec_start, vec_end, 0.5, 0.5, True)
                Sh.PreviewLattice(lat_connector, Cp.clrBlue)
            elif self.eConnector == self.EConnector.ARROW:
                vec_start = as_vec3(as_np3(self.vecPt2) + 0.2 * (as_np3(self.vecPt4) - as_np3(self.vecPt2)))
                vec_end = as_vec3(as_np3(self.vecPt2) + 0.8 * (as_np3(self.vecPt4) - as_np3(self.vecPt2)))
                lat_connector.AddBeam(vec_start, vec_end, 0.5, 0.5, True)

                vec_arrow1 = as_vec3(
                    as_np3(self.vecPt2)
                    + 0.4 * (as_np3(self.vecPt4) - as_np3(self.vecPt2))
                    + 0.2 * (as_np3(self.vecPt3) - as_np3(self.vecPt1))
                )
                vec_arrow2 = as_vec3(
                    as_np3(self.vecPt2)
                    + 0.4 * (as_np3(self.vecPt4) - as_np3(self.vecPt2))
                    - 0.2 * (as_np3(self.vecPt3) - as_np3(self.vecPt1))
                )
                lat_connector.AddBeam(vec_start, vec_arrow1, 0.5, 0.5, True)
                lat_connector.AddBeam(vec_start, vec_arrow2, 0.5, 0.5, True)
                Sh.PreviewLattice(lat_connector, Cp.clrRed)
            elif self.eConnector == self.EConnector.TRIANGLE:
                vec_start = as_vec3(as_np3(self.vecPt2) + 0.2 * (as_np3(self.vecPt4) - as_np3(self.vecPt2)))
                vec_end = as_vec3(as_np3(self.vecPt2) + 0.8 * (as_np3(self.vecPt4) - as_np3(self.vecPt2)))
                lat_connector.AddBeam(vec_start, vec_end, 0.5, 0.5, True)

                vec_tri = as_vec3(
                    as_np3(self.vecPt2)
                    + 0.5 * (as_np3(self.vecPt4) - as_np3(self.vecPt2))
                    + 0.25 * (as_np3(self.vecPt3) - as_np3(self.vecPt1))
                )
                lat_connector.AddBeam(vec_start, vec_tri, 0.5, 0.5, True)
                lat_connector.AddBeam(vec_end, vec_tri, 0.5, 0.5, True)
                Sh.PreviewLattice(lat_connector, Cp.clrBillie)


__all__ = ["IcosehedralFace"]
