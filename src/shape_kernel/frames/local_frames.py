
import numpy as np
from dataclasses import dataclass

from ..utils import VecOperations

from .._types import Vec3, Vector3Like, as_np3, as_vec3, normalized

@dataclass
class LocalFrame:
    _position: np.ndarray
    _local_x: np.ndarray
    _local_y: np.ndarray
    _local_z: np.ndarray

    def __init__(
        self,
        vecPos: Vector3Like = (0.0, 0.0, 0.0),
        vecLocalZ: Vector3Like = (0.0, 0.0, 1.0),
        vecLocalX: Vector3Like | None = None,
    ) -> None:
        pos = as_np3(vecPos)
        local_z = normalized(vecLocalZ)
        if float(np.linalg.norm(local_z)) <= 1e-12:
            raise ValueError("Local Z Coordinate has a length of Zero!")
        if vecLocalX is None:
            local_x = VecOperations.vecGetOrthogonalDir(local_z)
        else:
            local_x = normalized(vecLocalX)
            if float(np.linalg.norm(local_x)) <= 1e-12:
                raise ValueError("Local X Coordinate has a length of Zero!")
        local_y = LocalFrame.vecBuildLocalY(local_z, local_x)

        self._position = pos
        self._local_x = normalized(local_x)
        self._local_y = normalized(local_y)
        self._local_z = normalized(local_z)

    def vecGetPosition(self) -> Vec3:
        return as_vec3(self._position)

    def vec_get_position(self) -> Vec3:
        return self.vecGetPosition()

    def vecGetLocalX(self) -> Vec3:
        return as_vec3(self._local_x)

    def vec_get_local_x(self) -> Vec3:
        return self.vecGetLocalX()

    def vecGetLocalY(self) -> Vec3:
        return as_vec3(self._local_y)

    def vec_get_local_y(self) -> Vec3:
        return self.vecGetLocalY()

    def vecGetLocalZ(self) -> Vec3:
        return as_vec3(self._local_z)

    def vec_get_local_z(self) -> Vec3:
        return self.vecGetLocalZ()

    def oInvert(self, bMirrorZ: bool, bMirrorX: bool) -> "LocalFrame":
        z = -self._local_z if bMirrorZ else self._local_z
        x = -self._local_x if bMirrorX else self._local_x
        return LocalFrame(self._position, z, x)

    def oTranslate(self, vecTranslate: Vector3Like) -> "LocalFrame":
        return LocalFrame(self._position + as_np3(vecTranslate), self._local_z, self._local_x)

    def oRotate(self, dPhi: float, vecAxis: Vector3Like) -> "LocalFrame":
        x = VecOperations.vecRotateAroundAxis(self._local_x, dPhi, vecAxis)
        z = VecOperations.vecRotateAroundAxis(self._local_z, dPhi, vecAxis)
        return LocalFrame(self._position, z, x)

    @staticmethod
    def oGetInvertFrame(oFrame: "LocalFrame", bMirrorZ: bool, bMirrorX: bool) -> "LocalFrame":
        return oFrame.oInvert(bMirrorZ, bMirrorX)

    @staticmethod
    def oGetTranslatedFrame(oFrame: "LocalFrame", vecTranslate: Vector3Like) -> "LocalFrame":
        return oFrame.oTranslate(vecTranslate)

    @staticmethod
    def oGetRotatedFrame(oFrame: "LocalFrame", dPhi: float, vecAxis: Vector3Like) -> "LocalFrame":
        return oFrame.oRotate(dPhi, vecAxis)

    @staticmethod
    def vecBuildLocalY(vecLocalZ: Vector3Like, vecLocalX: Vector3Like) -> Vec3:
        z = as_np3(vecLocalZ)
        x = as_np3(vecLocalX)
        return as_vec3(np.cross(z, x))


