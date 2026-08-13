#!/usr/bin/env python3
"""Pull each run's final self-report and pair it with the blind grader verdict.

The point is the V4 failure mode the literature flags: confident claims of
success on longer autonomous runs. `codex exec` prints the agent's closing
message again after the `tokens used` block, so that trailing chunk is the
model's own account of what it did. Setting it beside passed/tests_failed makes
"claimed success but failed the hidden test" directly countable.

Usage:
  ./claims.py            # only runs that FAILED the hidden test
  ./claims.py --all
"""
import csv, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def final_message(log_path):
    if not os.path.exists(log_path):
        return "<no log>"
    text = open(log_path, errors="replace").read()
    # the closing message is re-emitted after "tokens used\n<count>"
    m = list(re.finditer(r"tokens used\n[0-9,]+\n", text))
    tail = text[m[-1].end():] if m else text[-1500:]
    return tail.strip() or "<empty final message>"


def main():
    show_all = "--all" in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    csv_path = paths[0] if paths else os.path.join(ROOT, "results.csv")
    runs_dir = os.path.join(os.path.dirname(os.path.abspath(csv_path)), "runs")
    rows = list(csv.DictReader(open(csv_path)))
    for r in rows:
        if not show_all and r["passed"] == "1":
            continue
        log = os.path.join(runs_dir,
                           f"{r['model']}_{r['task']}_t{r['trial']}.log")
        print("=" * 78)
        print(f"{r['model']} / {r['task']} / trial {r['trial']}  "
              f"passed={r['passed']}  hidden_tests_failed={r['tests_failed']}  "
              f"{r['notes']}")
        print("-" * 78)
        print(final_message(log)[:2500])
        print()


if __name__ == "__main__":
    main()
