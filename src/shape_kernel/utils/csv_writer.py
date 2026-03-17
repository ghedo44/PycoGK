from __future__ import annotations


class CSVWriter:
	def __init__(self, strFilename: str) -> None:
		self._filename = str(strFilename)
		self._writer = open(self._filename, "w", newline="", encoding="utf-8")

	def AddLine(self, strLine: str) -> None:
		self._writer.write(str(strLine) + "\n")

	def ExportCSVFile(self) -> None:
		try:
			self._writer.flush()
		except Exception as exc:
			print(f"Could not save CSV: {exc}")

	def __del__(self) -> None:
		try:
			self._writer.close()
		except Exception:
			pass


__all__ = ["CSVWriter"]
