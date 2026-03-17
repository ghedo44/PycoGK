from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

from picogk import Library, Mesh, VedoViewer

from .._types import Vec3, as_np3
from .color_scale_2d import IColorScale


class MeshPainter:
	ColorScaleFunc = Callable[[Vec3, Vec3, Vec3], float]

	@staticmethod
	def _build_submesh_classes(oMesh: Mesh, nClasses: int) -> list[Mesh]:
		return [Mesh() for _ in range(int(nClasses))]

	@staticmethod
	def _emit_preview_groups(
		segments: list[tuple[Mesh, tuple[float, float, float, float]]],
		oViewer: VedoViewer | None = None,
	) -> None:
		viewer = oViewer if oViewer is not None else Library.oViewer()
		if viewer is None:
			return
		from ..functions import Sh

		for msh, clr in segments:
			if msh.nTriangleCount() <= 0:
				continue
			Sh.PreviewMesh(msh, clr, oViewer=viewer)

	@staticmethod
	def PreviewOverhangAngle(
		oMesh: Mesh,
		xScale: IColorScale,
		bShowOnlyDownFacing: bool,
		nClasses: int = 30,
		oViewer: VedoViewer | None = None,
	) -> list[tuple[Mesh, tuple[float, float, float, float]]]:
		sub_meshes = MeshPainter._build_submesh_classes(oMesh, nClasses)
		fMinAngle = xScale.fGetMinValue()
		fMaxAngle = xScale.fGetMaxValue()
		dAngle = (fMaxAngle - fMinAngle) / (nClasses - 1.0)

		n_triangles = oMesh.nTriangleCount()
		for i in range(n_triangles):
			vecA, vecB, vecC = oMesh.GetTriangle(i)
			a = as_np3(vecA)
			b = as_np3(vecB)
			c = as_np3(vecC)
			normal = np.cross(a - b, c - b)
			n_norm = float(np.linalg.norm(normal))
			if n_norm <= 1e-12:
				continue
			normal = normal / n_norm

			dR = math.sqrt(float(normal[0] * normal[0] + normal[1] * normal[1]))
			dZ = abs(float(normal[2]))
			overhang = math.atan2(dZ, dR) / math.pi * 180.0
			overhang = min(max(overhang, 0.0), 90.0)

			if bShowOnlyDownFacing and normal[2] < 0.0:
				overhang = 0.0

			ratio = (overhang - fMinAngle) / (fMaxAngle - fMinAngle)
			index = int(min(max(ratio, 0.0), 1.0) * (nClasses - 1))
			sub_meshes[index].nAddTriangle(vecA, vecB, vecC)

		segments = [(sub_meshes[i], xScale.clrGetColor(fMinAngle + i * dAngle)) for i in range(nClasses)]
		MeshPainter._emit_preview_groups(segments, oViewer)
		return segments

	@staticmethod
	def PreviewCustomProperty(
		oMesh: Mesh,
		xScale: IColorScale,
		oColorFunc: ColorScaleFunc,
		nClasses: int = 30,
		oViewer: VedoViewer | None = None,
	) -> list[tuple[Mesh, tuple[float, float, float, float]]]:
		sub_meshes = MeshPainter._build_submesh_classes(oMesh, nClasses)
		fMinValue = xScale.fGetMinValue()
		fMaxValue = xScale.fGetMaxValue()
		dValue = (fMaxValue - fMinValue) / (nClasses - 1.0)

		n_triangles = oMesh.nTriangleCount()
		for i in range(n_triangles):
			vecA, vecB, vecC = oMesh.GetTriangle(i)
			value = float(oColorFunc(vecA, vecB, vecC))
			ratio = min(max((value - fMinValue) / (fMaxValue - fMinValue), 0.0), 1.0)
			index = int(ratio * (nClasses - 1))
			sub_meshes[index].nAddTriangle(vecA, vecB, vecC)

		segments = [(sub_meshes[i], xScale.clrGetColor(fMinValue + i * dValue)) for i in range(nClasses)]
		MeshPainter._emit_preview_groups(segments, oViewer)
		return segments

	@staticmethod
	def PreviewCustomDeformation(
		oMesh: Mesh,
		xScale: IColorScale,
		oColorFunc: ColorScaleFunc,
		fnTrafo: Callable[[Vec3], Vec3],
		nClasses: int = 30,
		oViewer: VedoViewer | None = None,
	) -> list[tuple[Mesh, tuple[float, float, float, float]]]:
		sub_meshes = MeshPainter._build_submesh_classes(oMesh, nClasses)
		fMinValue = xScale.fGetMinValue()
		fMaxValue = xScale.fGetMaxValue()
		dValue = (fMaxValue - fMinValue) / (nClasses - 1.0)

		n_triangles = oMesh.nTriangleCount()
		for i in range(n_triangles):
			vecA, vecB, vecC = oMesh.GetTriangle(i)
			value = float(oColorFunc(vecA, vecB, vecC))
			ratio = min(max((value - fMinValue) / (fMaxValue - fMinValue), 0.0), 1.0)
			index = int(ratio * (nClasses - 1))
			sub_meshes[index].nAddTriangle(fnTrafo(vecA), fnTrafo(vecB), fnTrafo(vecC))

		segments = [(sub_meshes[i], xScale.clrGetColor(fMinValue + i * dValue)) for i in range(nClasses)]
		MeshPainter._emit_preview_groups(segments, oViewer)
		return segments


__all__ = ["MeshPainter"]
