#!/usr/bin/env python3
"""Re-grade completed runs of one task against the current hidden test.

Every run keeps its work directory, so a corrected grader can be replayed
without spending another token. Used after the h3 synthetic case was found to
sit on a Decimal rounding knife-edge, which failed correct solutions.

  ./regrade.py h3_bigcontext          # show what would change
  ./regrade.py h3_bigcontext --write  # rewrite results_hard.csv
"""
import csv
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ROOT, "results_hard.csv")


def grade(task, work):
    hidden = os.path.join(ROOT, "hidden", f"{task}_test.py")
    shutil.copy(hidden, os.path.join(work, "_hidden_test.py"))
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "_hidden_test", "-v"],
        cwd=work, capture_output=True, text=True)
    failed = len(re.findall(r"^(?:FAIL|ERROR):", proc.stdout + proc.stderr,
                            re.M))
    return (1 if proc.returncode == 0 else 0), failed, proc.stdout + proc.stderr


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    task = sys.argv[1]
    write = "--write" in sys.argv

    rows = list(csv.DictReader(open(RESULTS)))
    fields = rows[0].keys() if rows else []
    changed = 0

    for row in rows:
        if row["task"] != task:
            continue
        work = os.path.join(ROOT, "work",
                            f"{row['model']}_{task}_t{row['trial']}")
        if not os.path.isdir(work):
            print(f"  skip {row['model']} t{row['trial']}: no work dir")
            continue
        passed, failed, output = grade(task, work)
        note = ""
        if (str(passed) != row["passed"]
                or str(failed) != row["tests_failed"]):
            note = (f"  <-- was passed={row['passed']} "
                    f"failed={row['tests_failed']}")
            changed += 1
        print(f"  {row['model']:<9} t{row['trial']}  passed={passed} "
              f"failed={failed}{note}")
        row["passed"], row["tests_failed"] = str(passed), str(failed)
        gradelog = os.path.join(
            ROOT, "runs", f"{row['model']}_{task}_t{row['trial']}.grade")
        if write:
            with open(gradelog, "w") as fh:
                fh.write(output)

    print(f"\n{changed} row(s) would change" if not write
          else f"\n{changed} row(s) changed")
    if write:
        with open(RESULTS, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(fields))
            writer.writeheader()
            writer.writerows(rows)
        print(f"rewrote {RESULTS}")


if __name__ == "__main__":
    main()
