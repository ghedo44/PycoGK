from __future__ import annotations

import time

from picogk import VedoViewer


class RotationAnimator:
	def __init__(self, oViewer: VedoViewer) -> None:
		self.m_oViewer = oViewer

	def Do(self, fStep: float = 0.5) -> None:
		fElevation = float(self.m_oViewer.m_fElevation)
		fCurrentOrbit = float(self.m_oViewer.m_fOrbit)
		self.m_oViewer.SetViewAngles(fCurrentOrbit + float(fStep), fElevation)

	def Run(self, nSteps: int = 360, fWaitSeconds: float = 0.01, fStep: float = 0.5) -> None:
		for _ in range(int(nSteps)):
			time.sleep(float(fWaitSeconds))
			self.Do(fStep)


__all__ = ["RotationAnimator"]
