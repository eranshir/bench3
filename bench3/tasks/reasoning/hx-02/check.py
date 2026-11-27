import json
import re
import sys
from pathlib import Path

expected = int(Path(__file__).with_name("reference.txt").read_text())
got = None
try:
    response = json.loads(Path(sys.argv[1]).read_text())
    content = response["choices"][0]["message"]["content"]
    match = re.search(r"FINAL ANSWER:\s*([0-9]+)", content)
    if match:
        got = int(match.group(1))
except (OSError, ValueError, KeyError, IndexError, TypeError):
    pass
print(json.dumps({"passed": got == expected, "expected": expected, "got": got}))
