#!/usr/bin/env python3
"""Rewrite the agent-default-model section of the bench DSH home settings.
Preserves the llm-pi-ai section. Usage: write_settings.py <provider> <model> <effort>"""
import sys
from pathlib import Path

import yaml

HOME = Path(__file__).resolve().parent.parent.parent / ".dsh-home"
settings_path = HOME / "settings.yaml"


def main():
    provider, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(settings_path) as f:
        doc = yaml.safe_load(f) or {}
    doc["agent-default-model"] = {"provider": provider, "model": model, "reasoningEffort": effort}
    with open(settings_path, "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False)
    print(f"agent-default-model -> {provider}/{model} effort={effort}")


if __name__ == "__main__":
    main()
