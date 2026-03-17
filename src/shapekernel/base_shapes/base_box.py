from __future__ import annotations

from picogk import BBox3, Mesh, Voxels

from .._types import Vec3, Vector3Like, as_np3, as_vec3
from ..frames import Frames
from ..frames.local_frames import LocalFrame
from ..modulations import LineModulation
from .base_shape import BaseShape


class BaseBox(BaseShape):
	def __init__(
		self,
		aFrames: Frames,
		fWidth: float,
		fDepth: float,
		*,
		_length_steps: int,
	) -> None:
		super().__init__()
		self.m_aFrames = aFrames
		self.SetWidthSteps(5)
		self.SetDepthSteps(5)
		self.SetLengthSteps(_length_steps)
		self.m_oWidthModulation = LineModulation(fWidth)
		self.m_oDepthModulation = LineModulation(fDepth)

	@classmethod
	def from_frame(
		cls,
		oFrame: LocalFrame,
		fLength: float = 20.0,
		fWidth: float = 20.0,
		fDepth: float = 20.0,
	) -> "BaseBox":
		return cls(Frames.from_length(fLength, oFrame), fWidth, fDepth, _length_steps=5)

	@classmethod
	def from_frames(
		cls,
		aFrames: Frames,
		fWidth: float = 20.0,
		fDepth: float = 20.0,
	) -> "BaseBox":
		return cls(aFrames, fWidth, fDepth, _length_steps=500)

	@classmethod
	def from_bbox(
		cls,
		oBBox: BBox3 | tuple[Vector3Like, Vector3Like],
	) -> "BaseBox":
		if isinstance(oBBox, BBox3):
			box_min = (float(oBBox.min.x), float(oBBox.min.y), float(oBBox.min.z))
			box_max = (float(oBBox.max.x), float(oBBox.max.y), float(oBBox.max.z))
		else:
			box_min, box_max = oBBox

		bmin = as_np3(box_min)
		bmax = as_np3(box_max)
		centre = 0.5 * (bmin + bmax)
		centre[2] = bmin[2]
		return cls.from_frame(
			LocalFrame(as_vec3(centre), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
			fLength=float(bmax[2] - bmin[2]),
			fWidth=float(bmax[0] - bmin[0]),
			fDepth=float(bmax[1] - bmin[1]),
		)

	def SetWidth(self, oModulation: LineModulation) -> None:
		self.m_oWidthModulation = oModulation
		self.SetWidthSteps(500)
		self.SetLengthSteps(500)

	def SetDepth(self, oModulation: LineModulation) -> None:
		self.m_oDepthModulation = oModulation
		self.SetDepthSteps(500)
		self.SetLengthSteps(500)

	def SetWidthSteps(self, nWidthSteps: int) -> None:
		self.m_nWidthSteps = max(5, int(nWidthSteps))

	def SetDepthSteps(self, nDepthSteps: int) -> None:
		self.m_nDepthSteps = max(5, int(nDepthSteps))

	def SetLengthSteps(self, nLengthSteps: int) -> None:
		self.m_nLengthSteps = max(5, int(nLengthSteps))

	def voxConstruct(self) -> Voxels:
		return Voxels.from_mesh(self.mshConstruct())

	def mshConstruct(self) -> Mesh:
		mesh = Mesh()
		self._add_top_surface(mesh, True)
		self._add_bottom_surface(mesh)
		self._add_front_surface(mesh, True)
		self._add_back_surface(mesh)
		self._add_right_surface(mesh, True)
		self._add_left_surface(mesh)
		return mesh

	def _add_rect(self, mesh: Mesh, pts: tuple[Vec3, Vec3, Vec3, Vec3], flip: bool) -> None:
		p0, p1, p2, p3 = pts
		if not flip:
			mesh.nAddTriangle(p0, p1, p2)
			mesh.nAddTriangle(p0, p2, p3)
		else:
			mesh.nAddTriangle(p0, p2, p1)
			mesh.nAddTriangle(p0, p3, p2)

	def _add_top_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
		lr = self._length_ratio(self.m_nLengthSteps - 1)
		for iw in range(1, self.m_nWidthSteps):
			w1 = self._width_ratio(iw - 1)
			w2 = self._width_ratio(iw)
			for idepth in range(1, self.m_nDepthSteps):
				d1 = self._depth_ratio(idepth - 1)
				d2 = self._depth_ratio(idepth)
				self._add_rect(
					mesh,
					(
						self.vecGetSurfacePoint(w1, d1, lr),
						self.vecGetSurfacePoint(w1, d2, lr),
						self.vecGetSurfacePoint(w2, d2, lr),
						self.vecGetSurfacePoint(w2, d1, lr),
					),
					bFlip,
				)

	def _add_bottom_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
		lr = self._length_ratio(0)
		for iw in range(1, self.m_nWidthSteps):
			w1 = self._width_ratio(iw - 1)
			w2 = self._width_ratio(iw)
			for idepth in range(1, self.m_nDepthSteps):
				d1 = self._depth_ratio(idepth - 1)
				d2 = self._depth_ratio(idepth)
				self._add_rect(
					mesh,
					(
						self.vecGetSurfacePoint(w1, d1, lr),
						self.vecGetSurfacePoint(w1, d2, lr),
						self.vecGetSurfacePoint(w2, d2, lr),
						self.vecGetSurfacePoint(w2, d1, lr),
					),
					bFlip,
				)

	def _add_front_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
		wr = self._width_ratio(0)
		for il in range(1, self.m_nLengthSteps):
			lr1 = self._length_ratio(il - 1)
			lr2 = self._length_ratio(il)
			for idepth in range(1, self.m_nDepthSteps):
				d1 = self._depth_ratio(idepth - 1)
				d2 = self._depth_ratio(idepth)
				self._add_rect(mesh, (self.vecGetSurfacePoint(wr, d1, lr1), self.vecGetSurfacePoint(wr, d2, lr1), self.vecGetSurfacePoint(wr, d2, lr2), self.vecGetSurfacePoint(wr, d1, lr2)), bFlip)

	def _add_back_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
		wr = self._width_ratio(self.m_nWidthSteps - 1)
		for il in range(1, self.m_nLengthSteps):
			lr1 = self._length_ratio(il - 1)
			lr2 = self._length_ratio(il)
			for idepth in range(1, self.m_nDepthSteps):
				d1 = self._depth_ratio(idepth - 1)
				d2 = self._depth_ratio(idepth)
				self._add_rect(mesh, (self.vecGetSurfacePoint(wr, d1, lr1), self.vecGetSurfacePoint(wr, d2, lr1), self.vecGetSurfacePoint(wr, d2, lr2), self.vecGetSurfacePoint(wr, d1, lr2)), bFlip)

	def _add_right_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
		dr = self._depth_ratio(self.m_nDepthSteps - 1)
		for il in range(1, self.m_nLengthSteps):
			lr1 = self._length_ratio(il - 1)
			lr2 = self._length_ratio(il)
			for iw in range(1, self.m_nWidthSteps):
				w1 = self._width_ratio(iw - 1)
				w2 = self._width_ratio(iw)
				self._add_rect(mesh, (self.vecGetSurfacePoint(w1, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr2), self.vecGetSurfacePoint(w1, dr, lr2)), bFlip)

	def _add_left_surface(self, mesh: Mesh, bFlip: bool = False) -> None:
		dr = self._depth_ratio(0)
		for il in range(1, self.m_nLengthSteps):
			lr1 = self._length_ratio(il - 1)
			lr2 = self._length_ratio(il)
			for iw in range(1, self.m_nWidthSteps):
				w1 = self._width_ratio(iw - 1)
				w2 = self._width_ratio(iw)
				self._add_rect(mesh, (self.vecGetSurfacePoint(w1, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr1), self.vecGetSurfacePoint(w2, dr, lr2), self.vecGetSurfacePoint(w1, dr, lr2)), bFlip)

	def _width_ratio(self, step: int) -> float:
		return -1.0 + (2.0 / float(self.m_nWidthSteps - 1)) * float(step)

	def _depth_ratio(self, step: int) -> float:
		return -1.0 + (2.0 / float(self.m_nDepthSteps - 1)) * float(step)

	def _length_ratio(self, step: int) -> float:
		return (1.0 / float(self.m_nLengthSteps - 1)) * float(step)

	def fGetWidth(self, fLengthRatio: float) -> float:
		return self.m_oWidthModulation.fGetModulation(fLengthRatio)

	def fGetDepth(self, fLengthRatio: float) -> float:
		return self.m_oDepthModulation.fGetModulation(fLengthRatio)

	def vecGetSurfacePoint(self, fWidthRatio: float, fDepthRatio: float, fLengthRatio: float) -> Vec3:
		spine = as_np3(self.m_aFrames.vecGetSpineAlongLength(fLengthRatio))
		lx = as_np3(self.m_aFrames.vecGetLocalXAlongLength(fLengthRatio))
		ly = as_np3(self.m_aFrames.vecGetLocalYAlongLength(fLengthRatio))
		x = 0.5 * fWidthRatio * self.fGetWidth(fLengthRatio)
		y = 0.5 * fDepthRatio * self.fGetDepth(fLengthRatio)
		return self.m_fnTrafo(as_vec3(spine + x * lx + y * ly))


__all__ = ["BaseBox"]
