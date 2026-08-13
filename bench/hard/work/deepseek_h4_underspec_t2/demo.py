"""The three cases from the ticket. Run: python3 demo.py"""
from filterlang import evaluate

CASES = [
    ("age > 30 and city == 'NY'", {"age": 41, "city": "NY"}, True),
    ("not banned or score >= 4.5", {"banned": True, "score": 4.9}, True),
    ("tags contains 'vip'", {"tags": ["vip", "beta"]}, True),
]

if __name__ == "__main__":
    for expr, rec, want in CASES:
        got = evaluate(expr, rec)
        print(f"{'ok ' if got == want else 'BAD'} {expr!r} -> {got} "
              f"(want {want})")
