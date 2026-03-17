from __future__ import annotations

import math
from abc import ABC, abstractmethod

from shape_kernel._types import Vec3, as_np3, as_vec3

from .robinson_triangle import RobinsonTriangle


class ISubDTile(ABC):
    @abstractmethod
    def aGetInflatedSubTiles(self) -> list["ISubDTile"]:
        raise NotImplementedError

    @abstractmethod
    def aGetTileVertices(self) -> list[Vec3]:
        raise NotImplementedError


class RhombicTile(ISubDTile):
    m_fPsi = (math.sqrt(5.0) - 1.0) / 2.0

    def __init__(self, oTri: RobinsonTriangle) -> None:
        self.m_oTri_01 = oTri
        self.m_oTri_02 = oTri.oGetFlippedTriangle()

    @abstractmethod
    def aGetInflatedSubTiles(self) -> list[ISubDTile]:
        raise NotImplementedError

    def aGetTileVertices(self) -> list[Vec3]:
        return [
            self.m_oTri_01.m_vecA,
            self.m_oTri_01.m_vecB,
            self.m_oTri_01.m_vecC,
            self.m_oTri_02.m_vecB,
        ]


class SmallRhombicTile(RhombicTile):
    def aGetInflatedSubTiles(self) -> list[ISubDTile]:
        vec_d = as_np3(self.m_oTri_01.m_vecB) + self.m_fPsi * (as_np3(self.m_oTri_01.m_vecA) - as_np3(self.m_oTri_01.m_vecB))
        o_sub_tile_1: ISubDTile = SmallRhombicTile(RobinsonTriangle(as_vec3(vec_d), self.m_oTri_01.m_vecC, self.m_oTri_01.m_vecA))
        o_sub_tile_2: ISubDTile = LargeRhombicTile(RobinsonTriangle(self.m_oTri_01.m_vecC, as_vec3(vec_d), self.m_oTri_01.m_vecB))

        vec_d = as_np3(self.m_oTri_02.m_vecB) + self.m_fPsi * (as_np3(self.m_oTri_02.m_vecA) - as_np3(self.m_oTri_02.m_vecB))
        o_sub_tile_11: ISubDTile = SmallRhombicTile(RobinsonTriangle(as_vec3(vec_d), self.m_oTri_02.m_vecC, self.m_oTri_02.m_vecA))
        o_sub_tile_22: ISubDTile = LargeRhombicTile(RobinsonTriangle(self.m_oTri_02.m_vecC, as_vec3(vec_d), self.m_oTri_02.m_vecB))

        return [o_sub_tile_1, o_sub_tile_2, o_sub_tile_11, o_sub_tile_22]


class LargeRhombicTile(RhombicTile):
    def aGetInflatedSubTiles(self) -> list[ISubDTile]:
        vec_d = as_np3(self.m_oTri_01.m_vecA) + self.m_fPsi * (as_np3(self.m_oTri_01.m_vecB) - as_np3(self.m_oTri_01.m_vecA))
        vec_e = as_np3(self.m_oTri_01.m_vecA) + self.m_fPsi * (as_np3(self.m_oTri_01.m_vecC) - as_np3(self.m_oTri_01.m_vecA))
        o_sub_tile_1: ISubDTile = LargeRhombicTile(RobinsonTriangle(as_vec3(vec_e), as_vec3(vec_d), self.m_oTri_01.m_vecA))
        o_sub_tile_2: ISubDTile = SmallRhombicTile(RobinsonTriangle(as_vec3(vec_d), as_vec3(vec_e), self.m_oTri_01.m_vecB))
        o_sub_tile_3: ISubDTile = LargeRhombicTile(RobinsonTriangle(self.m_oTri_01.m_vecC, as_vec3(vec_e), self.m_oTri_01.m_vecB))

        vec_d = as_np3(self.m_oTri_02.m_vecA) + self.m_fPsi * (as_np3(self.m_oTri_02.m_vecB) - as_np3(self.m_oTri_02.m_vecA))
        vec_e = as_np3(self.m_oTri_02.m_vecA) + self.m_fPsi * (as_np3(self.m_oTri_02.m_vecC) - as_np3(self.m_oTri_02.m_vecA))
        o_sub_tile_11: ISubDTile = LargeRhombicTile(RobinsonTriangle(as_vec3(vec_e), as_vec3(vec_d), self.m_oTri_02.m_vecA))
        o_sub_tile_22: ISubDTile = SmallRhombicTile(RobinsonTriangle(as_vec3(vec_d), as_vec3(vec_e), self.m_oTri_02.m_vecB))
        o_sub_tile_33: ISubDTile = LargeRhombicTile(RobinsonTriangle(self.m_oTri_02.m_vecC, as_vec3(vec_e), self.m_oTri_02.m_vecB))

        return [o_sub_tile_1, o_sub_tile_2, o_sub_tile_3, o_sub_tile_11, o_sub_tile_22, o_sub_tile_33]


__all__ = ["ISubDTile", "RhombicTile", "SmallRhombicTile", "LargeRhombicTile"]
