#!/bin/bash
# Assemble FINAL_REPORT.md: narrative + generated tables.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 bin/report.py > /dev/null
{
  echo '# Three-provider coding-agent benchmark — final report'
  echo
  cat NARRATIVE.md
  echo
  cat FINDINGS.md
  echo
  echo '## Full results'
  echo
  cat REPORT3.md
} > FINAL_REPORT.md
echo 'wrote FINAL_REPORT.md'
