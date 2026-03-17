from __future__ import annotations

import numpy as np

from picogk import BBox3, Library
from shape_kernel import BaseBox, Cp, LocalFrame, Sh, Uf
from shape_kernel._types import Vec3, Vector3Like, as_np3, as_vec3


class RandomDeformationField:
	def __init__(self, oBoundingBox: BBox3, fResolution: float, fMinValue: float, fMaxValue: float) -> None:
		self.m_oBBox = oBoundingBox
		fXSize, fYSize, fZSize = self.m_oBBox.vecSize()
		self.m_nXSamples = int(fXSize / float(fResolution)) + 1
		self.m_nYSamples = int(fYSize / float(fResolution)) + 1
		self.m_nZSamples = int(fZSize / float(fResolution)) + 1

		self.m_aGridPoints = np.zeros((self.m_nXSamples + 1, self.m_nYSamples + 1, self.m_nZSamples + 1, 3), dtype=np.float64)
		self.m_aNoiseVectors = np.zeros_like(self.m_aGridPoints)

		self._preview_field(fXSize, fYSize, fZSize)

		for iX in range(0, self.m_nXSamples + 1):
			for iY in range(0, self.m_nYSamples + 1):
				for iZ in range(0, self.m_nZSamples + 1):
					fX = fXSize / float(self.m_nXSamples) * float(iX) + float(self.m_oBBox.vecMin.x)
					fY = fYSize / float(self.m_nYSamples) * float(iY) + float(self.m_oBBox.vecMin.y)
					fZ = fZSize / float(self.m_nZSamples) * float(iZ) + float(self.m_oBBox.vecMin.z)
					vecPt = np.array([fX, fY, fZ], dtype=np.float64)
					self.m_aGridPoints[iX, iY, iZ] = vecPt

					if Library.oViewer() is not None:
						Sh.PreviewPoint(as_vec3(vecPt), 1.0, Cp().clrRandom())

					self.m_aNoiseVectors[iX, iY, iZ] = np.array(
						[
							Uf.fGetRandomLinear(fMinValue, fMaxValue),
							Uf.fGetRandomLinear(fMinValue, fMaxValue),
							Uf.fGetRandomLinear(fMinValue, fMaxValue),
						],
						dtype=np.float64,
					)

	def _preview_field(self, fXSize: float, fYSize: float, fZSize: float) -> None:
		if Library.oViewer() is None:
			return

		Sh.PreviewPoint((0.0, 0.0, 0.0), 0.5, Cp.clrRed)
		Sh.PreviewBoxWireframe(self.m_oBBox, Cp.clrRed)

		for iX in range(1, self.m_nXSamples + 1):
			for iY in range(1, self.m_nYSamples + 1):
				for iZ in range(1, self.m_nZSamples + 1):
					fMinX = float(self.m_oBBox.vecMin.x) + 1.0 / float(self.m_nXSamples) * (float(iX) - 1.0) * fXSize
					fMaxX = float(self.m_oBBox.vecMin.x) + 1.0 / float(self.m_nXSamples) * float(iX) * fXSize
					fMinY = float(self.m_oBBox.vecMin.y) + 1.0 / float(self.m_nYSamples) * (float(iY) - 1.0) * fYSize
					fMaxY = float(self.m_oBBox.vecMin.y) + 1.0 / float(self.m_nYSamples) * float(iY) * fYSize
					fMinZ = float(self.m_oBBox.vecMin.z) + 1.0 / float(self.m_nZSamples) * (float(iZ) - 1.0) * fZSize
					fMaxZ = float(self.m_oBBox.vecMin.z) + 1.0 / float(self.m_nZSamples) * float(iZ) * fZSize

					vecFramePos = (0.5 * (fMinX + fMaxX), 0.5 * (fMinY + fMaxY), fMinZ)
					dX = fMaxX - fMinX
					dY = fMaxY - fMinY
					dZ = fMaxZ - fMinZ
					oSubCube = BaseBox.from_frame(LocalFrame(vecFramePos), fLength=dZ, fWidth=dX, fDepth=dY)
					Sh.PreviewBoxWireframe(oSubCube, Cp.clrBlack)

	def vecGetData(self, vecPt: Vector3Like) -> Vec3:
		pt = as_np3(vecPt)
		fX = min(max(float(pt[0]), float(self.m_oBBox.vecMin.x)), float(self.m_oBBox.vecMax.x))
		fY = min(max(float(pt[1]), float(self.m_oBBox.vecMin.y)), float(self.m_oBBox.vecMax.y))
		fZ = min(max(float(pt[2]), float(self.m_oBBox.vecMin.z)), float(self.m_oBBox.vecMax.z))

		dX = float(self.m_oBBox.vecSize()[0]) / float(self.m_nXSamples)
		dY = float(self.m_oBBox.vecSize()[1]) / float(self.m_nYSamples)
		dZ = float(self.m_oBBox.vecSize()[2]) / float(self.m_nZSamples)

		iLowerX = int((fX - float(self.m_oBBox.vecMin.x)) / dX)
		iLowerY = int((fY - float(self.m_oBBox.vecMin.y)) / dY)
		iLowerZ = int((fZ - float(self.m_oBBox.vecMin.z)) / dZ)
		iLowerX = min(max(iLowerX, 0), self.m_nXSamples - 1)
		iLowerY = min(max(iLowerY, 0), self.m_nYSamples - 1)
		iLowerZ = min(max(iLowerZ, 0), self.m_nZSamples - 1)
		iUpperX = iLowerX + 1
		iUpperY = iLowerY + 1
		iUpperZ = iLowerZ + 1

		vecPt000 = self.m_aGridPoints[iLowerX, iLowerY, iLowerZ]

		vecDir000 = self.m_aNoiseVectors[iLowerX, iLowerY, iLowerZ]
		vecDir100 = self.m_aNoiseVectors[iUpperX, iLowerY, iLowerZ]
		vecDir110 = self.m_aNoiseVectors[iUpperX, iUpperY, iLowerZ]
		vecDir010 = self.m_aNoiseVectors[iLowerX, iUpperY, iLowerZ]
		vecDir001 = self.m_aNoiseVectors[iLowerX, iLowerY, iUpperZ]
		vecDir101 = self.m_aNoiseVectors[iUpperX, iLowerY, iUpperZ]
		vecDir111 = self.m_aNoiseVectors[iUpperX, iUpperY, iUpperZ]
		vecDir011 = self.m_aNoiseVectors[iLowerX, iUpperY, iUpperZ]

		fXRatio = (fX - float(vecPt000[0])) / dX
		fYRatio = (fY - float(vecPt000[1])) / dY
		fZRatio = (fZ - float(vecPt000[2])) / dZ

		vecDir00 = self.vecGetInter(vecDir000, vecDir100, fXRatio)
		vecDir10 = self.vecGetInter(vecDir010, vecDir110, fXRatio)
		vecDir01 = self.vecGetInter(vecDir001, vecDir101, fXRatio)
		vecDir11 = self.vecGetInter(vecDir011, vecDir111, fXRatio)
		vecDir0 = self.vecGetInter(vecDir00, vecDir10, fYRatio)
		vecDir1 = self.vecGetInter(vecDir01, vecDir11, fYRatio)
		vecDir = self.vecGetInter(vecDir0, vecDir1, fZRatio)
		return as_vec3(vecDir)

	def vecGetInter(self, vecMin: np.ndarray, vecMax: np.ndarray, fRatio: float) -> np.ndarray:
		ratio = min(max(float(fRatio), 0.0), 1.0)
		return vecMin + ratio * (vecMax - vecMin)


__all__ = ["RandomDeformationField"]