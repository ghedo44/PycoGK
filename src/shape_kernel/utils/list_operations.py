from __future__ import annotations


class ListOperations:
	@staticmethod
	def aOverSampleList(aList: list[float], iSamplesPerStep: int) -> list[float]:
		out: list[float] = []
		for i in range(1, len(aList)):
			for j in range(int(iSamplesPerStep)):
				t = float(j) / float(iSamplesPerStep)
				out.append(float(aList[i - 1]) + t * (float(aList[i]) - float(aList[i - 1])))
		out.append(float(aList[-1]))
		return out

	@staticmethod
	def aSubsampleList(aList: list[float], iSampleSize: int) -> list[float]:
		out: list[float] = []
		step = max(1, int(iSampleSize))
		i = 0
		while i < len(aList):
			out.append(float(aList[i]))
			i += step
		if out[-1] != float(aList[-1]):
			out.append(float(aList[-1]))
		return out

	@staticmethod
	def iGetIndexOfMaxValue(aList: list[float]) -> int:
		max_val = float("-inf")
		idx = -1
		for i, v in enumerate(aList):
			if float(v) > max_val:
				max_val = float(v)
				idx = i
		return idx

	@staticmethod
	def iGetIndexOfMinValue(aList: list[float]) -> int:
		min_val = float("inf")
		idx = -1
		for i, v in enumerate(aList):
			if float(v) < min_val:
				min_val = float(v)
				idx = i
		return idx


__all__ = ["ListOperations"]
