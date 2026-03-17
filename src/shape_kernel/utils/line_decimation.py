from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from .._types import Vec3, Vector3Like, as_np3, as_vec3
from .vec_operations import VecOperations


class LineDecimation:
	def __init__(self, aPoints: Sequence[Vector3Like], fMaxError: float) -> None:
		self._pts = [as_np3(p) for p in aPoints]
		i_start = 0
		indices: list[int] = [0]
		while i_start < len(self._pts) - 1:
			i_end = self._iGetNextIndex(i_start, float(fMaxError))
			i_start = i_end
			indices.append(i_start)
		self._decimated: list[Vec3] = [as_vec3(self._pts[i]) for i in indices]

	def _iGetNextIndex(self, i_start: int, fMaxError: float) -> int:
		if i_start > len(self._pts) - 2:
			return len(self._pts) - 1
		i_end = i_start + 1
		line_pts = list(self._pts[i_start : i_start + 2])
		for i_idx in range(i_start + 2, len(self._pts)):
			line_pts.append(self._pts[i_idx])
			if LineDecimation._fGetMaxError(line_pts) > fMaxError:
				break
			i_end = i_idx
		return i_end

	@staticmethod
	def _fGetMaxError(line_pts: list[np.ndarray]) -> float:
		line_dir = line_pts[-1] - line_pts[0]
		max_err = 0.0
		for i in range(1, len(line_pts) - 1):
			pointer = line_pts[i] - line_pts[0]
			angle = VecOperations.fGetAngleBetween(pointer, line_dir)
			err = math.sin(angle) * float(np.linalg.norm(pointer))
			if err > max_err:
				max_err = err
		return max_err

	def aGetDecimatedPoints(self) -> list[Vec3]:
		return list(self._decimated)


__all__ = ["LineDecimation"]
