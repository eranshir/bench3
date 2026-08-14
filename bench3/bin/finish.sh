#!/bin/bash
# Post-pilot finishing pipeline: judge subjective runs, rebuild webapp data,
# regenerate REPORT3.md. Run after the pilot completes.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/bin"
echo '=== judging subjective runs (deepseek-v4-pro, blind) ==='
python3 judge.py
echo '=== cross-check sample with gpt-5.6-sol ==='
python3 judge.py --judge openai
echo '=== rebuilding webapp data ==='
python3 build_webdata.py
echo '=== generating REPORT3.md ==='
python3 report.py
echo '=== done ==='
echo "view the webapp:  cd bench3 && python3 -m http.server 8931  ->  http://127.0.0.1:8931/webapp/"
