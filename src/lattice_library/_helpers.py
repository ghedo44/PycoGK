from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from picogk import BBox3, Lattice
from shape_kernel._types import Vec3, Vector3Like, as_np3, as_vec3

if TYPE_CHECKING:
	from .beam_thickness.i_beam_thickness import IBeamThickness


class _BBoxMinMax(Protocol):
	x: float
	y: float
	z: float


class _BBoxWithVecMinMax(Protocol):
	vecMin: Vector3Like
	vecMax: Vector3Like


class _BBoxWithMinMax(Protocol):
	min: _BBoxMinMax
	max: _BBoxMinMax


BBox3Like = BBox3 | tuple[Vector3Like, Vector3Like] | _BBoxWithVecMinMax | _BBoxWithMinMax


def _coerce_bbox3(box: BBox3Like) -> BBox3:
	if isinstance(box, BBox3):
		return box
	if isinstance(box, tuple) and len(box) == 2:
		return BBox3(as_vec3(box[0]), as_vec3(box[1]))
	if hasattr(box, "vecMin") and hasattr(box, "vecMax"):
		return BBox3(as_vec3(getattr(box, "vecMin")), as_vec3(getattr(box, "vecMax")))
	if hasattr(box, "min") and hasattr(box, "max"):
		return BBox3(
			(float(box.min.x), float(box.min.y), float(box.min.z)), # type: ignore
			(float(box.max.x), float(box.max.y), float(box.max.z)), # type: ignore
		)
	raise TypeError("Unsupported bounding box representation")


def _interpolate_point(vecPt1: Vector3Like, vecPt2: Vector3Like, ratio: float) -> Vec3:
	pt1 = as_np3(vecPt1)
	pt2 = as_np3(vecPt2)
	return as_vec3(pt1 + float(ratio) * (pt2 - pt1))


def _add_sampled_beam(oLattice: Lattice, vecPt1: Vector3Like, vecPt2: Vector3Like, xBeamThickness: IBeamThickness, nSamples: int = 2) -> None:
	n_samples = max(2, int(nSamples))
	if n_samples == 2:
		fRadius1 = 0.5 * float(xBeamThickness.fGetBeamThickness(vecPt1))
		fRadius2 = 0.5 * float(xBeamThickness.fGetBeamThickness(vecPt2))
		oLattice.AddBeam(vecPt1, vecPt2, fRadius1, fRadius2)
		return

	for i in range(1, n_samples):
		vecPt11 = _interpolate_point(vecPt1, vecPt2, float(i - 1) / float(n_samples - 1))
		vecPt22 = _interpolate_point(vecPt1, vecPt2, float(i) / float(n_samples - 1))
		fRadius11 = 0.5 * float(xBeamThickness.fGetBeamThickness(vecPt11))
		fRadius22 = 0.5 * float(xBeamThickness.fGetBeamThickness(vecPt22))
		oLattice.AddBeam(vecPt11, vecPt22, fRadius11, fRadius22)


def _add_polyline_beam(oLattice: Lattice, aPoints: list[Vec3], xBeamThickness: IBeamThickness) -> None:
	for i in range(1, len(aPoints)):
		vecPt11 = aPoints[i - 1]
		vecPt22 = aPoints[i]
		fRadius11 = 0.5 * float(xBeamThickness.fGetBeamThickness(vecPt11))
		fRadius22 = 0.5 * float(xBeamThickness.fGetBeamThickness(vecPt22))
		oLattice.AddBeam(vecPt11, vecPt22, fRadius11, fRadius22)


__all__ = ["_add_polyline_beam", "_add_sampled_beam", "_coerce_bbox3"]