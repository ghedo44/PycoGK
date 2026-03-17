from __future__ import annotations

import math

import numpy as np

from shape_kernel import LocalFrame, VecOperations
from shape_kernel._types import Vec3, as_np3, as_vec3, normalized

from .icosahedral_face import IcosehedralFace
from .quasi_tile import QuasiTile
from .quasi_tile_01 import QuasiTile_01
from .quasi_tile_03 import QuasiTile_03
from .quasi_tile_04 import QuasiTile_04


class QuasiTileInflation:
    m_oTargetFrame = LocalFrame()
    m_oCurrentFrame = LocalFrame()
    m_oTargetLength = 0.0
    m_oCurrentLength = 1.0

    @staticmethod
    def aGetInflatedFace(sFace: IcosehedralFace) -> list[QuasiTile]:
        vec_face_normal = as_vec3(np.cross(as_np3(sFace.vecLongAxis), as_np3(sFace.vecShortAxis)))
        o_frame = LocalFrame(sFace.vecCentre, vec_face_normal, sFace.vecLongAxis)

        if sFace.eConnector == IcosehedralFace.EConnector.LINE:
            a_inflated_tiles: list[QuasiTile] = []
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt1, sFace.vecPt2, o_frame.vecGetLocalZ(), 0.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt1, sFace.vecPt4, o_frame.vecGetLocalZ(), 1.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt3, sFace.vecPt2, o_frame.vecGetLocalZ(), 1.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt3, sFace.vecPt4, o_frame.vecGetLocalZ(), 0.0 * math.pi / 5.0))
            return a_inflated_tiles
        if sFace.eConnector == IcosehedralFace.EConnector.TRIANGLE:
            a_inflated_tiles = []
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedPurpleLine(sFace.vecPt3, sFace.vecPt4, o_frame.vecGetLocalZ(), 1.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedPurpleLine(sFace.vecPt3, sFace.vecPt2, o_frame.vecGetLocalZ(), 2.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt1, sFace.vecPt4, o_frame.vecGetLocalZ(), 1.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt1, sFace.vecPt2, o_frame.vecGetLocalZ(), 0.0 * math.pi / 5.0))
            return a_inflated_tiles
        if sFace.eConnector == IcosehedralFace.EConnector.ARROW:
            a_inflated_tiles = []
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedPurpleLine(sFace.vecPt3, sFace.vecPt4, o_frame.vecGetLocalZ(), 1.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedPurpleLine(sFace.vecPt1, sFace.vecPt4, o_frame.vecGetLocalZ(), 2.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt3, sFace.vecPt2, o_frame.vecGetLocalZ(), 1.0 * math.pi / 5.0))
            a_inflated_tiles.extend(QuasiTileInflation.aGetInflatedBlackLine(sFace.vecPt1, sFace.vecPt2, o_frame.vecGetLocalZ(), 0.0 * math.pi / 5.0))
            return a_inflated_tiles

        raise Exception("Unknown face connector type. Face cannot get inflated.")

    @staticmethod
    def aGetInflatedBlackLine(vecStart: Vec3, vecEnd: Vec3, vecFaceNormal: Vec3, fCustomAngle: float) -> list[QuasiTile]:
        QuasiTileInflation.m_oTargetLength = float(np.linalg.norm(as_np3(vecEnd) - as_np3(vecStart)))
        vec_target_local_z = as_vec3(normalized(as_np3(vecEnd) - as_np3(vecStart)))
        vec_target_local_x = vecFaceNormal
        QuasiTileInflation.m_oTargetFrame = LocalFrame(vecStart, vec_target_local_z, vec_target_local_x)

        a_inflated_tiles: list[QuasiTile] = []
        o_sub_tile_000 = QuasiTile_01(LocalFrame())
        o_sub_tile_001 = QuasiTile_01(LocalFrame())
        o_sub_tile_002 = QuasiTile_01(LocalFrame())
        o_sub_tile_003 = QuasiTile_01(LocalFrame())
        o_sub_tile_004 = QuasiTile_01(LocalFrame())

        o_sub_tile_001.AttachToOtherQuasiTile(0, o_sub_tile_000, 1)
        o_sub_tile_002.AttachToOtherQuasiTile(0, o_sub_tile_001, 1)
        o_sub_tile_003.AttachToOtherQuasiTile(0, o_sub_tile_002, 1)
        o_sub_tile_004.AttachToOtherQuasiTile(1, o_sub_tile_000, 0)

        o_sub_tile_mid = QuasiTile_03(LocalFrame())
        o_sub_tile_mid.AttachToOtherQuasiTile(17, o_sub_tile_001, 4, True)

        o_sub_tile_005 = QuasiTile_01(LocalFrame())
        o_sub_tile_006 = QuasiTile_01(LocalFrame())
        o_sub_tile_007 = QuasiTile_01(LocalFrame())
        o_sub_tile_008 = QuasiTile_01(LocalFrame())
        o_sub_tile_009 = QuasiTile_01(LocalFrame())

        o_sub_tile_005.AttachToOtherQuasiTile(2, o_sub_tile_mid, 0)
        o_sub_tile_006.AttachToOtherQuasiTile(2, o_sub_tile_mid, 1)
        o_sub_tile_007.AttachToOtherQuasiTile(2, o_sub_tile_mid, 2)
        o_sub_tile_008.AttachToOtherQuasiTile(2, o_sub_tile_mid, 3)
        o_sub_tile_009.AttachToOtherQuasiTile(2, o_sub_tile_mid, 4)

        a_inflated_tiles.extend([
            o_sub_tile_000,
            o_sub_tile_001,
            o_sub_tile_002,
            o_sub_tile_003,
            o_sub_tile_004,
            o_sub_tile_mid,
            o_sub_tile_005,
            o_sub_tile_006,
            o_sub_tile_007,
            o_sub_tile_008,
            o_sub_tile_009,
        ])

        vec_s = o_sub_tile_000.aGetFaces()[2].vecPt3
        vec_e = o_sub_tile_009.aGetFaces()[4].vecPt1
        QuasiTileInflation.m_oCurrentLength = float(np.linalg.norm(as_np3(vec_e) - as_np3(vec_s)))
        vec_current_local_z = as_vec3(normalized(as_np3(vec_e) - as_np3(vec_s)))
        QuasiTileInflation.m_oCurrentFrame = LocalFrame(vec_s, vec_current_local_z)
        vec_ref1 = o_sub_tile_mid.aGetFaces()[-1].vecPt2
        vec_ref2 = o_sub_tile_mid.aGetFaces()[-1].vecPt1
        vec_cross = np.cross(as_np3(vec_current_local_z), normalized(as_np3(vec_ref1) - as_np3(vec_ref2)))
        vec_current_local_x = np.cross(vec_cross, as_np3(vec_current_local_z))
        vec_current_local_x = as_np3(
            VecOperations.vecRotateAroundAxis(
                as_vec3(vec_current_local_x),
                float(fCustomAngle) + math.pi / 10.0,
                vec_current_local_z,
            )
        )
        QuasiTileInflation.m_oCurrentFrame = LocalFrame(vec_s, vec_current_local_z, as_vec3(vec_current_local_x))

        for o_tile in a_inflated_tiles:
            o_tile.ApplyTrafo(QuasiTileInflation.vecTrafo)

        return a_inflated_tiles

    @staticmethod
    def aGetInflatedPurpleLine(vecStart: Vec3, vecEnd: Vec3, vecFaceNormal: Vec3, fCustomAngle: float) -> list[QuasiTile]:
        QuasiTileInflation.m_oTargetLength = float(np.linalg.norm(as_np3(vecEnd) - as_np3(vecStart)))
        vec_target_local_z = as_vec3(normalized(as_np3(vecEnd) - as_np3(vecStart)))
        vec_target_local_x = vecFaceNormal
        QuasiTileInflation.m_oTargetFrame = LocalFrame(vecStart, vec_target_local_z, vec_target_local_x)

        a_inflated_tiles: list[QuasiTile] = []
        o_sub_tile_000 = QuasiTile_01(LocalFrame())
        o_sub_tile_001 = QuasiTile_01(LocalFrame())
        o_sub_tile_002 = QuasiTile_01(LocalFrame())
        o_sub_tile_003 = QuasiTile_01(LocalFrame())
        o_sub_tile_004 = QuasiTile_01(LocalFrame())

        o_sub_tile_001.AttachToOtherQuasiTile(0, o_sub_tile_000, 1)
        o_sub_tile_002.AttachToOtherQuasiTile(0, o_sub_tile_001, 1)
        o_sub_tile_003.AttachToOtherQuasiTile(0, o_sub_tile_002, 1)
        o_sub_tile_004.AttachToOtherQuasiTile(1, o_sub_tile_000, 0)

        o_sub_tile_mid = QuasiTile_04(LocalFrame())
        o_sub_tile_mid.AttachToOtherQuasiTile(17, o_sub_tile_001, 4, True)

        a_inflated_tiles.extend([
            o_sub_tile_000,
            o_sub_tile_001,
            o_sub_tile_002,
            o_sub_tile_003,
            o_sub_tile_004,
            o_sub_tile_mid,
        ])

        vec_s = o_sub_tile_000.aGetFaces()[2].vecPt3
        vec_e = o_sub_tile_mid.aGetFaces()[4].vecPt1
        QuasiTileInflation.m_oCurrentLength = float(np.linalg.norm(as_np3(vec_e) - as_np3(vec_s)))
        vec_current_local_z = as_vec3(normalized(as_np3(vec_e) - as_np3(vec_s)))
        QuasiTileInflation.m_oCurrentFrame = LocalFrame(vec_s, vec_current_local_z)
        vec_ref1 = o_sub_tile_mid.aGetFaces()[2].vecPt2
        vec_ref2 = o_sub_tile_mid.aGetFaces()[2].vecPt1
        vec_cross = np.cross(as_np3(vec_current_local_z), normalized(as_np3(vec_ref1) - as_np3(vec_ref2)))
        vec_current_local_x = np.cross(vec_cross, as_np3(vec_current_local_z))
        vec_current_local_x = as_np3(
            VecOperations.vecRotateAroundAxis(
                as_vec3(vec_current_local_x),
                float(fCustomAngle) + math.pi / 10.0,
                vec_current_local_z,
            )
        )
        QuasiTileInflation.m_oCurrentFrame = LocalFrame(vec_s, vec_current_local_z, as_vec3(vec_current_local_x))

        for o_tile in a_inflated_tiles:
            o_tile.ApplyTrafo(QuasiTileInflation.vecTrafo)

        return a_inflated_tiles

    @staticmethod
    def vecTrafo(vecPt: Vec3) -> Vec3:
        vec_rel = as_np3(VecOperations.vecExpressPointInFrame(QuasiTileInflation.m_oCurrentFrame, vecPt))
        vec_rel *= QuasiTileInflation.m_oTargetLength / QuasiTileInflation.m_oCurrentLength
        vec_new_pt = VecOperations.vecTranslatePointOntoFrame(QuasiTileInflation.m_oTargetFrame, as_vec3(vec_rel))
        return vec_new_pt


__all__ = ["QuasiTileInflation"]
