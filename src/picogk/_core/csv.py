
import csv
from pathlib import Path
from typing import Protocol, Sequence


class IDataTable(Protocol):
    def nRowCount(self) -> int:
        ...

    def nMaxColumnCount(self) -> int:
        ...

    def strGetAt(self, nRow: int, nCol: int) -> str:
        ...


class CsvTable(IDataTable):
    def __init__(self, source: str | Path | IDataTable | None = None) -> None:
        self._rows: list[list[str]] = []
        self._key_column = -1
        self._col_ids: dict[str, int] = {}
        if source is None:
            return
        if isinstance(source, (str, Path)):
            with open(source, "r", newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                self._rows = [list(row) for row in reader]
        else:
            for r in range(source.nRowCount()):
                row = [source.strGetAt(r, c) for c in range(source.nMaxColumnCount())]
                self._rows.append(row)

    def Save(self, file_path: str | Path) -> None:
        with open(file_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(self._rows)

    def nRowCount(self) -> int:
        return len(self._rows)

    def nMaxColumnCount(self) -> int:
        return max((len(r) for r in self._rows), default=0)

    def strGetAt(self, nRow: int, nCol: int) -> str:
        if nRow < 0 or nRow >= len(self._rows):
            return ""
        row = self._rows[nRow]
        if nCol < 0 or nCol >= len(row):
            return ""
        return row[nCol]

    def SetKeyColumn(self, nColumn: int) -> None:
        self._key_column = int(nColumn)

    def bGetAt(self, key_or_row: str | int, col_or_idx: str | int) -> tuple[bool, str]:
        if isinstance(key_or_row, int) and isinstance(col_or_idx, int):
            value = self.strGetAt(key_or_row, col_or_idx)
            return (value != "", value)
        if not isinstance(key_or_row, str) or not isinstance(col_or_idx, str):
            return (False, "")
        if self._key_column < 0:
            return (False, "")
        ok_col, col = self.bFindColumn(col_or_idx)
        if not ok_col:
            return (False, "")
        for row in self._rows:
            if self._key_column < len(row) and row[self._key_column] == key_or_row:
                if col < len(row):
                    return (True, row[col])
                return (False, "")
        return (False, "")

    def bFindColumn(self, strColumnID: str) -> tuple[bool, int]:
        idx = self._col_ids.get(strColumnID)
        if idx is None:
            return (False, -1)
        return (True, idx)

    def strColumnId(self, nColumn: int) -> str:
        for key, val in self._col_ids.items():
            if val == nColumn:
                return key
        return ""

    def SetColumnIds(self, ids: Sequence[str]) -> None:
        self._col_ids = {str(col): i for i, col in enumerate(ids)}

    def AddRow(self, values: Sequence[str]) -> None:
        self._rows.append([str(v) for v in values])


