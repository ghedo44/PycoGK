from __future__ import annotations

from picogk import Lattice, Library, Voxels
from shape_kernel import LocalFrame

from .icosahedral_face import IcosehedralFace
from .quasi_tile import QuasiTile
from .quasi_tile_01 import QuasiTile_01
from .quasi_tile_04 import QuasiTile_04
from .quasi_tile_inflation import QuasiTileInflation


class QuasiCrystal:
    def __init__(
        self,
        nGenerations: int,
        aInitialTiles: list[QuasiTile] | None = None,
        sInitialFace: IcosehedralFace | None = None,
    ) -> None:
        self.m_nGenerations = int(nGenerations)
        self.m_aTileGenerations: list[list[QuasiTile]] = [[] for _ in range(self.m_nGenerations)]

        if aInitialTiles is not None:
            self.m_aTileGenerations[0] = list(aInitialTiles)
        elif sInitialFace is not None:
            self.m_aTileGenerations[0] = QuasiTileInflation.aGetInflatedFace(sInitialFace)
        else:
            raise ValueError("Provide either aInitialTiles or sInitialFace.")

        for i in range(1, self.m_nGenerations):
            a_inflated_sub_tiles: list[QuasiTile] = []
            for o_tile in self.m_aTileGenerations[i - 1]:
                a_faces = o_tile.aGetFaces()
                for s_face in a_faces:
                    a_inflated_sub_tiles.extend(QuasiTileInflation.aGetInflatedFace(s_face))

            a_inflated_sub_tiles = self.aGetDeduplicatedSubTiles(a_inflated_sub_tiles)
            self.m_aTileGenerations[i] = a_inflated_sub_tiles

    def aGetDeduplicatedSubTiles(self, aSubTiles: list[QuasiTile]) -> list[QuasiTile]:
        a_ref_centres: list[tuple[float, float, float]] = []
        a_deduplicated_sub_tiles: list[QuasiTile] = []

        for o_sub_tile in aSubTiles:
            vec_rounded_centre = o_sub_tile.vecGetRoundedCentre()
            if vec_rounded_centre not in a_ref_centres:
                a_ref_centres.append(vec_rounded_centre)
                a_deduplicated_sub_tiles.append(o_sub_tile)

        return a_deduplicated_sub_tiles

    @staticmethod
    def aGetFirstGenerationTiles() -> list[QuasiTile]:
        a_tiles: list[QuasiTile] = []

        o_tile_000 = QuasiTile_01(LocalFrame())
        o_tile_001 = QuasiTile_01(LocalFrame())
        o_tile_002 = QuasiTile_01(LocalFrame())
        o_tile_003 = QuasiTile_01(LocalFrame())
        o_tile_004 = QuasiTile_01(LocalFrame())

        o_tile_001.AttachToOtherQuasiTile(0, o_tile_000, 1)
        o_tile_002.AttachToOtherQuasiTile(0, o_tile_001, 1)
        o_tile_003.AttachToOtherQuasiTile(0, o_tile_002, 1)
        o_tile_004.AttachToOtherQuasiTile(1, o_tile_000, 0)

        o_tile_005 = QuasiTile_01(LocalFrame())
        o_tile_006 = QuasiTile_01(LocalFrame())
        o_tile_007 = QuasiTile_01(LocalFrame())
        o_tile_008 = QuasiTile_01(LocalFrame())
        o_tile_009 = QuasiTile_01(LocalFrame())

        o_tile_005.AttachToOtherQuasiTile(0, o_tile_000, 2)
        o_tile_006.AttachToOtherQuasiTile(0, o_tile_001, 2)
        o_tile_007.AttachToOtherQuasiTile(0, o_tile_002, 2)
        o_tile_008.AttachToOtherQuasiTile(0, o_tile_003, 2)
        o_tile_009.AttachToOtherQuasiTile(0, o_tile_004, 2)

        o_tile_010 = QuasiTile_01(LocalFrame())
        o_tile_011 = QuasiTile_01(LocalFrame())
        o_tile_012 = QuasiTile_01(LocalFrame())
        o_tile_013 = QuasiTile_01(LocalFrame())
        o_tile_014 = QuasiTile_01(LocalFrame())

        o_tile_010.AttachToOtherQuasiTile(0, o_tile_005, 1)
        o_tile_011.AttachToOtherQuasiTile(0, o_tile_006, 1)
        o_tile_012.AttachToOtherQuasiTile(0, o_tile_007, 1)
        o_tile_013.AttachToOtherQuasiTile(0, o_tile_008, 1)
        o_tile_014.AttachToOtherQuasiTile(0, o_tile_009, 1)

        o_tile_015 = QuasiTile_01(LocalFrame())
        o_tile_016 = QuasiTile_01(LocalFrame())
        o_tile_017 = QuasiTile_01(LocalFrame())
        o_tile_018 = QuasiTile_01(LocalFrame())
        o_tile_019 = QuasiTile_01(LocalFrame())

        o_tile_015.AttachToOtherQuasiTile(0, o_tile_010, 2)
        o_tile_016.AttachToOtherQuasiTile(0, o_tile_011, 2)
        o_tile_017.AttachToOtherQuasiTile(0, o_tile_012, 2)
        o_tile_018.AttachToOtherQuasiTile(0, o_tile_013, 2)
        o_tile_019.AttachToOtherQuasiTile(0, o_tile_014, 2)

        a_tiles.extend([
            o_tile_000,
            o_tile_001,
            o_tile_002,
            o_tile_003,
            o_tile_004,
            o_tile_005,
            o_tile_006,
            o_tile_007,
            o_tile_008,
            o_tile_009,
            o_tile_010,
            o_tile_011,
            o_tile_012,
            o_tile_013,
            o_tile_014,
            o_tile_015,
            o_tile_016,
            o_tile_017,
            o_tile_018,
            o_tile_019,
        ])
        return a_tiles

    @staticmethod
    def aGetSecondGenerationTiles() -> list[QuasiTile]:
        a_first_generation_tiles = QuasiCrystal.aGetFirstGenerationTiles()
        a_tiles: list[QuasiTile] = []

        o_tile_100 = QuasiTile_04(LocalFrame())
        o_tile_101 = QuasiTile_04(LocalFrame())
        o_tile_102 = QuasiTile_04(LocalFrame())
        o_tile_103 = QuasiTile_04(LocalFrame())
        o_tile_104 = QuasiTile_04(LocalFrame())
        o_tile_105 = QuasiTile_04(LocalFrame())
        o_tile_106 = QuasiTile_04(LocalFrame())
        o_tile_107 = QuasiTile_04(LocalFrame())
        o_tile_108 = QuasiTile_04(LocalFrame())
        o_tile_109 = QuasiTile_04(LocalFrame())
        o_tile_110 = QuasiTile_04(LocalFrame())
        o_tile_111 = QuasiTile_04(LocalFrame())

        o_tile_100.AttachToOtherQuasiTile(1, a_first_generation_tiles[0], 4)
        o_tile_101.AttachToOtherQuasiTile(1, a_first_generation_tiles[0], 5)
        o_tile_102.AttachToOtherQuasiTile(1, a_first_generation_tiles[1], 5)
        o_tile_103.AttachToOtherQuasiTile(1, a_first_generation_tiles[2], 5)
        o_tile_104.AttachToOtherQuasiTile(1, a_first_generation_tiles[3], 5)
        o_tile_105.AttachToOtherQuasiTile(1, a_first_generation_tiles[4], 5)
        o_tile_106.AttachToOtherQuasiTile(1, a_first_generation_tiles[15], 5)
        o_tile_107.AttachToOtherQuasiTile(1, a_first_generation_tiles[16], 5)
        o_tile_108.AttachToOtherQuasiTile(1, a_first_generation_tiles[17], 5)
        o_tile_109.AttachToOtherQuasiTile(1, a_first_generation_tiles[18], 5)
        o_tile_110.AttachToOtherQuasiTile(1, a_first_generation_tiles[19], 5)
        o_tile_111.AttachToOtherQuasiTile(1, a_first_generation_tiles[19], 3)

        a_tiles.extend([
            o_tile_100,
            o_tile_101,
            o_tile_102,
            o_tile_103,
            o_tile_104,
            o_tile_105,
            o_tile_106,
            o_tile_107,
            o_tile_108,
            o_tile_109,
            o_tile_110,
            o_tile_111,
        ])
        return a_tiles

    def PreviewGeneration(self, nGen: int, ePreviewFace: QuasiTile.EPreviewFace) -> None:
        try:
            a_tiles = self.m_aTileGenerations[int(nGen)]
            Library.Log(f"Number of Tiles = {len(a_tiles)}.")
            for o_tile in a_tiles:
                o_tile.Preview(ePreviewFace)
        except Exception as exc:
            raise Exception("Generation not found.") from exc

    def aGetTileGeneration(self, nGen: int) -> list[QuasiTile]:
        try:
            return self.m_aTileGenerations[int(nGen)]
        except Exception as exc:
            raise Exception("Generation not found.") from exc

    def voxGetWireframe(self, nGen: int, fBeamR: float) -> Voxels:
        try:
            a_quasi_tiles = self.m_aTileGenerations[int(nGen)]
            o_lattice = Lattice()

            for o_tile in a_quasi_tiles:
                for s_face in o_tile.aGetFaces():
                    vec_pt1 = s_face.vecPt1
                    vec_pt2 = s_face.vecPt2
                    vec_pt3 = s_face.vecPt3
                    vec_pt4 = s_face.vecPt4

                    o_lattice.AddBeam(vec_pt1, vec_pt2, fBeamR, fBeamR, True)
                    o_lattice.AddBeam(vec_pt2, vec_pt3, fBeamR, fBeamR, True)
                    o_lattice.AddBeam(vec_pt3, vec_pt4, fBeamR, fBeamR, True)
                    o_lattice.AddBeam(vec_pt4, vec_pt1, fBeamR, fBeamR, True)

            return Voxels.from_lattice(o_lattice)
        except Exception as exc:
            raise Exception("Generation not found.") from exc


__all__ = ["QuasiCrystal"]
