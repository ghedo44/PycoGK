from __future__ import annotations

from collections.abc import Callable


class BisectionException(Exception):
	pass


class Bisection:
	Func = Callable[[float], float]

	def __init__(
		self,
		oFunc: Func,
		fMinInput: float,
		fMaxInput: float,
		fTargetOutput: float,
		fEpsilon: float = 0.01,
		nMaxIterations: int = 500,
	) -> None:
		self.m_oFunc = oFunc
		self.m_fEpsilon = float(fEpsilon)
		self.m_fMinInput = float(fMinInput)
		self.m_fMaxInput = float(fMaxInput)
		self.m_fTargetOutput = float(fTargetOutput)
		self.m_nIterations = 0
		self.m_nMaxIterations = int(nMaxIterations)
		self.m_fRemainingDiff = float(self.m_fMaxInput - self.m_fMinInput)
		self.m_fBestGuess = float(self.m_fMinInput)

	def fGetOutputFromFunc(self, fInput: float) -> float:
		return float(self.m_oFunc(float(fInput))) - self.m_fTargetOutput

	def fFindOptimalInput(self) -> float:
		f_min = self.m_fMinInput
		f_max = self.m_fMaxInput
		out_min = self.fGetOutputFromFunc(f_min)
		out_max = self.fGetOutputFromFunc(f_max)
		if out_min * out_max >= 0.0:
			raise BisectionException("No valid limits.")

		mid = f_min
		self.m_fRemainingDiff = f_max - f_min
		while self.m_fRemainingDiff >= self.m_fEpsilon:
			mid = 0.5 * (f_min + f_max)
			out_mid = self.fGetOutputFromFunc(mid)
			if out_mid == 0.0:
				break
			if out_mid * self.fGetOutputFromFunc(f_min) < 0.0:
				f_max = mid
			else:
				f_min = mid

			self.m_fRemainingDiff = f_max - f_min
			self.m_nIterations += 1
			self.m_fBestGuess = mid

			if self.m_nIterations == self.m_nMaxIterations:
				raise BisectionException("No solution reached after max number of interations.")

		return float(mid)

	def nGetIterations(self) -> int:
		return int(self.m_nIterations)

	def fGetRemainingDiff(self) -> float:
		return float(self.m_fRemainingDiff)

	def fGetBestGuess(self) -> float:
		return float(self.m_fBestGuess)


__all__ = ["Bisection", "BisectionException"]
