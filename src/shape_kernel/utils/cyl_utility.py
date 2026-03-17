from __future__ import annotations

from typing import TYPE_CHECKING

from picogk import Voxels

from .._types import as_np3, as_vec3

if TYPE_CHECKING:
    from ..frames.local_frames import LocalFrame


class CylUtility:
    @staticmethod
    def voxGetCyl(fStartZ_or_frame: float | LocalFrame, fEndZ_or_startZ: float = 0.0, fRadius_or_endZ: float = 0.0, fRadius: float | None = None) -> Voxels:
        from ..base_shapes import BaseCylinder
        from ..frames.local_frames import LocalFrame
        if isinstance(fStartZ_or_frame, LocalFrame):
            oRefFrame = fStartZ_or_frame
            fStartZ   = float(fEndZ_or_startZ)
            fEndZ     = float(fRadius_or_endZ)
            fR        = float(fRadius) if fRadius is not None else 1.0
            lz        = as_np3(oRefFrame.vecGetLocalZ())
            oFrame    = oRefFrame.oTranslate(as_vec3(lz * fStartZ))
            length    = fEndZ - fStartZ
        else:
            fStartZ = float(fStartZ_or_frame)
            fEndZ   = float(fEndZ_or_startZ)
            fR      = float(fRadius_or_endZ)
            oFrame  = LocalFrame((0.0, 0.0, fStartZ))
            length  = fEndZ - fStartZ
        return BaseCylinder.from_frame(oFrame, length, fR).voxConstruct()

    @staticmethod
    def voxGetCone(fStartZ_or_frame: float | LocalFrame, fEndZ_or_startZ: float, fStartRadius_or_endZ: float, fEndRadius_or_startR: float, fEndRadius: float | None = None) -> Voxels:
        from ..base_shapes import BaseCone
        from ..frames.local_frames import LocalFrame
        if isinstance(fStartZ_or_frame, LocalFrame):
            oRefFrame = fStartZ_or_frame
            fStartZ   = float(fEndZ_or_startZ)
            fEndZ     = float(fStartRadius_or_endZ)
            fStartR   = float(fEndRadius_or_startR)
            fEndR     = float(fEndRadius) if fEndRadius is not None else fStartR
            lz        = as_np3(oRefFrame.vecGetLocalZ())
            oFrame    = oRefFrame.oTranslate(as_vec3(lz * fStartZ))
            length    = fEndZ - fStartZ
        else:
            fStartZ = float(fStartZ_or_frame)
            fEndZ   = float(fEndZ_or_startZ)
            fStartR = float(fStartRadius_or_endZ)
            fEndR   = float(fEndRadius_or_startR)
            oFrame  = LocalFrame((0.0, 0.0, fStartZ))
            length  = fEndZ - fStartZ
        return BaseCone(oFrame, length, fStartR, fEndR).voxConstruct()

    @staticmethod
    def voxGetPipe(fStartZ_or_frame: float | LocalFrame, fEndZ_or_startZ: float, fInnerRadius_or_endZ: float, fOuterRadius_or_innerR: float, fOuterRadius: float | None = None) -> Voxels:
        from ..base_shapes import BasePipe
        from ..frames.local_frames import LocalFrame
        if isinstance(fStartZ_or_frame, LocalFrame):
            oRefFrame = fStartZ_or_frame
            fStartZ   = float(fEndZ_or_startZ)
            fEndZ     = float(fInnerRadius_or_endZ)
            fInnerR   = float(fOuterRadius_or_innerR)
            fOuterR   = float(fOuterRadius) if fOuterRadius is not None else fInnerR
            lz        = as_np3(oRefFrame.vecGetLocalZ())
            oFrame    = oRefFrame.oTranslate(as_vec3(lz * fStartZ))
            length    = fEndZ - fStartZ
        else:
            fStartZ = float(fStartZ_or_frame)
            fEndZ   = float(fEndZ_or_startZ)
            fInnerR = float(fInnerRadius_or_endZ)
            fOuterR = float(fOuterRadius_or_innerR)
            oFrame  = LocalFrame((0.0, 0.0, fStartZ))
            length  = fEndZ - fStartZ
        return BasePipe.from_frame(oFrame, length, fInnerR, fOuterR).voxConstruct()

