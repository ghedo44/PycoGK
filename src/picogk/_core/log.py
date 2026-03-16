

import datetime
from pathlib import Path
import time


class LogFile:
    def __init__(self, strFileName: str = "", bOutputToConsole: bool = True) -> None:
        self._output_to_console = bool(bOutputToConsole)
        self._start = time.perf_counter()
        self._last = 0.0
        if not strFileName:
            docs = Path.home() / "Documents"
            docs.mkdir(parents=True, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            strFileName = str(docs / f"PicoGK_{stamp}.log")
        self._path = strFileName
        self._writer = open(strFileName, "w", encoding="utf-8")
        self.Log(f"Opened {strFileName}")

    def Log(self, strFormat: str, *args: object) -> None:
        now = time.perf_counter() - self._start
        diff = now - self._last
        msg = strFormat.format(*args) if args else strFormat
        prefix = f"{now:7.0f}s {diff:6.1f}+ "
        for line in msg.split("\n"):
            row = prefix + line
            if self._output_to_console:
                print(row)
            self._writer.write(row + "\n")
        self._writer.flush()
        self._last = now

    def LogTime(self) -> None:
        self.Log("Current time (UTC): {0}", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)"))
        self.Log("Current local time: {0}", datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S (%z)"))

    def dispose(self) -> None:
        if self._writer.closed:
            return
        self.Log("Closing log file.")
        self.LogTime()
        self._writer.close()

    def __enter__(self) -> "LogFile":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.dispose()
