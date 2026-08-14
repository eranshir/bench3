#!/usr/bin/env python3
"""Shows a case where schedule() returns a suboptimal answer.
Run: python3 stress.py
"""
from scheduler import schedule

# The classic counterexample for start-time greedy:
# picking the interval that starts first blocks two later intervals.
intervals = [(0, 10), (1, 2), (2, 3)]
got = schedule(intervals)
print("case 1: expected 2, got", got, "->", "OK" if got == 2 else "WRONG")

# A second case: a long early interval blocks several short ones.
intervals2 = [(0, 8), (1, 2), (2, 3), (3, 4), (4, 5)]
got2 = schedule(intervals2)
print("case 2: expected 4, got", got2, "->", "OK" if got2 == 4 else "WRONG")
