from __future__ import annotations

from pathlib import Path

from picogk import LogFile, TempFolder, Utils, Vector3Ext

"""
Example 10: Utils, TempFolder, LogFile, Vector3Ext
"""


def main() -> None:
    with TempFolder() as tmp:
        p = Path(tmp.strFolder)
        f = p / "data.txt"
        f.write_text("hello", encoding="utf-8")

        print("file exists:", Utils.bFileExists(f))
        print("folder exists:", Utils.bFolderExists(p))
        print("short path:", Utils.strShorten(str(f), 30))

    n = Vector3Ext.vecNormalized((2.0, 0.0, 0.0))
    m = Vector3Ext.vecMirrored((1.0, 2.0, 3.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    print("normalized:", n)
    print("mirrored:", m)

    with LogFile("example.log", bOutputToConsole=True) as log:
        log.Log("Custom log row: value={0}", 42)
        log.LogTime()


if __name__ == "__main__":
    main()
