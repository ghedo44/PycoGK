from __future__ import annotations

import math

from picogk import Library
from shape_kernel import Cp, Sh, VecOperations
from shape_kernel._types import Vec3, as_np3, as_vec3

from .rhombic_tile import ISubDTile, LargeRhombicTile
from .robinson_triangle import RobinsonTriangle


class PenrosePattern:
    def __init__(self, nGenerations: int, fInitialSide: float = 20.0) -> None:
        self.m_nGenerations = int(nGenerations)
        self.m_aTileGenerations: list[list[ISubDTile]] = [[] for _ in range(self.m_nGenerations)]
        self.m_fInitialSide = float(fInitialSide)
        self.m_aTileGenerations[0] = self.aGetDefaultInitialTiles()

        for i in range(1, self.m_nGenerations):
            a_inflated_sub_tiles: list[ISubDTile] = []
            for x_tile in self.m_aTileGenerations[i - 1]:
                a_inflated_sub_tiles.extend(x_tile.aGetInflatedSubTiles())

            a_inflated_sub_tiles = self.aGetDeduplicatedSubTiles(a_inflated_sub_tiles)
            self.m_aTileGenerations[i] = a_inflated_sub_tiles

    def aGetDeduplicatedSubTiles(self, aSubTiles: list[ISubDTile]) -> list[ISubDTile]:
        a_ref_centres: list[Vec3] = []
        a_deduplicated_sub_tiles: list[ISubDTile] = []

        for x_sub_tile in aSubTiles:
            a_vertices = x_sub_tile.aGetTileVertices()
            vec_centre = sum((as_np3(v) for v in a_vertices), start=as_np3((0.0, 0.0, 0.0))) / float(len(a_vertices))
            vec_rounded_centre = as_vec3((round(float(vec_centre[0]), 2), round(float(vec_centre[1]), 2), round(float(vec_centre[2]), 2)))

            if vec_rounded_centre not in a_ref_centres:
                a_ref_centres.append(vec_rounded_centre)
                a_deduplicated_sub_tiles.append(x_sub_tile)

        return a_deduplicated_sub_tiles

    def aGetDefaultInitialTiles(self) -> list[ISubDTile]:
        a_initial_tiles: list[ISubDTile] = []
        f_theta = 108.0 / 180.0 * math.pi
        n_symmetry = 5

        for i in range(n_symmetry):
            f_alpha = (2.0 * math.pi) / float(n_symmetry) * float(i)
            vec_a: Vec3 = (0.0, 0.0, 0.0)
            vec_b = VecOperations.vecRotateAroundZ((self.m_fInitialSide, 0.0, 0.0), f_alpha)
            vec_c = VecOperations.vecRotateAroundZ(vec_a, f_theta, vec_b)

            o_tri = RobinsonTriangle(vec_a, vec_b, vec_c)
            o_tile: ISubDTile = LargeRhombicTile(o_tri)
            a_initial_tiles.append(o_tile)

        return a_initial_tiles

    def PreviewGeneration(self, nGen: int) -> None:
        try:
            a_tiles = self.m_aTileGenerations[int(nGen)]
            Library.Log(f"Number of Tiles = {len(a_tiles)}.")
            for x_tile in a_tiles:
                a_vertices = x_tile.aGetTileVertices()
                a_vertices.append(a_vertices[0])
                Sh.PreviewLine(a_vertices, Cp.clrBlack)
        except Exception as exc:
            raise Exception("Generation not found.") from exc


__all__ = ["PenrosePattern"]
