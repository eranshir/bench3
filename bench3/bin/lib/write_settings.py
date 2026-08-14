#!/usr/bin/env python3
"""Rewrite the agent-default-model section of the bench DSH home settings.
Preserves the llm-pi-ai section. Usage: write_settings.py <provider> <model> <effort>

Uses a YAML 1.2 loader: PyYAML's default YAML 1.1 treats bare off/on/yes/no
as booleans, so a reasoningEfforts key like `off:` would round-trip as
`false:` and break the pi-ai route registration (all-or-nothing).
"""
import sys
from pathlib import Path

import yaml


class NoBoolLoader(yaml.SafeLoader):
    pass


# strip the implicit bool resolver so off/on/yes/no stay strings
NoBoolLoader.yaml_implicit_resolvers = {
    k: [v for v in vals if v[0] != 'tag:yaml.org,2002:bool']
    for k, vals in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

HOME = Path(__file__).resolve().parent.parent.parent / '.dsh-home'
settings_path = HOME / 'settings.yaml'


def main():
    provider, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(settings_path) as f:
        doc = yaml.load(f, Loader=NoBoolLoader) or {}
    doc["agent-default-model"] = {"provider": provider, "model": model, "reasoningEffort": effort}
    with open(settings_path, "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False)
    print("agent-default-model -> %s/%s effort=%s" % (provider, model, effort))


if __name__ == "__main__":
    main()
