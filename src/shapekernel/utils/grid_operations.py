from __future__ import annotations

from collections.abc import Sequence

from .._types import Vec3, Vector3Like, as_vec3


class GridOperations:
	@staticmethod
	def aGetListInX(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[Vec3]:
		return [as_vec3(p) for p in aGrid[int(index)]]

	@staticmethod
	def aGetListInY(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[Vec3]:
		idx = int(index)
		return [as_vec3(row[idx]) for row in aGrid]

	@staticmethod
	def aAddListInX(aGrid: Sequence[Sequence[Vector3Like]], aList: Sequence[Vector3Like]) -> list[list[Vec3]]:
		out = [[as_vec3(p) for p in row] for row in aGrid]
		out.append([as_vec3(p) for p in aList])
		return out

	@staticmethod
	def aAddListInY(aGrid: Sequence[Sequence[Vector3Like]], aList: Sequence[Vector3Like]) -> list[list[Vec3]]:
		out = [[as_vec3(p) for p in row] for row in aGrid]
		col = [as_vec3(p) for p in aList]
		if len(out) != len(col):
			raise ValueError("Column length must match grid height")
		for i in range(len(out)):
			out[i].append(col[i])
		return out

	@staticmethod
	def aRemoveListInX(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[list[Vec3]]:
		idx = int(index)
		out = [[as_vec3(p) for p in row] for row in aGrid]
		if idx < 0 or idx >= len(out):
			raise IndexError(idx)
		del out[idx]
		return out

	@staticmethod
	def aRemoveListInY(aGrid: Sequence[Sequence[Vector3Like]], index: int) -> list[list[Vec3]]:
		idx = int(index)
		out = [[as_vec3(p) for p in row] for row in aGrid]
		for row in out:
			if idx < 0 or idx >= len(row):
				raise IndexError(idx)
			del row[idx]
		return out

	@staticmethod
	def aGetInverseGrid(aGrid: Sequence[Sequence[Vector3Like]]) -> list[list[Vec3]]:
		if not aGrid:
			return []
		h = len(aGrid)
		w = len(aGrid[0])
		return [[as_vec3(aGrid[i][j]) for i in range(h)] for j in range(w)]


__all__ = ["GridOperations"]
