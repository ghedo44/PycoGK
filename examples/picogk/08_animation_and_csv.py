from __future__ import annotations

from pathlib import Path

from picogk import Animation, AnimationQueue, CsvTable, Easing

"""
Example 08: Animation/Easing and CsvTable
"""



OUT = Path("example_table.csv")


def main() -> None:
    q = AnimationQueue()

    def tick(t: float) -> None:
        eased = Easing.fEasingFunction(t, Easing.EEasing.SINE_INOUT)
        print(f"t={t:.2f}, eased={eased:.2f}")

    q.Add(Animation(tick, 0.5, Animation.EType.ONCE))
    while q.bPulse():
        pass

    table = CsvTable()
    table.SetColumnIds(["id", "name", "score"])
    table.SetKeyColumn(0)
    table.AddRow(["1", "alice", "98"])
    table.AddRow(["2", "bob", "87"])
    table.Save(OUT)

    loaded = CsvTable(OUT)
    loaded.SetColumnIds(["id", "name", "score"])
    loaded.SetKeyColumn(0)
    print("rows:", loaded.nRowCount())
    print("bob score:", loaded.bGetAt("2", "score"))


if __name__ == "__main__":
    main()
