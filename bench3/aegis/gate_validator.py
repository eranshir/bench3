#!/usr/bin/env python3
"""bench3 Aegis gate validator — validates the workspace Aegis IR.

Mirrors the codex PreToolUse gate's contract (mithran-hq/aegis
scripts/codex_swebench_pro_lima_gate_hook.py): a schema-valid
.bruno/plan.json (with assumption ledger) + .bruno/children/*.json, each
child with id/scope/acceptance/falsifiers[id, description,
check{command, expected_outcome}]/status. "Marker counts are not evidence":
this validates the real artifact contract, not a presence check.

Stdlib only. Exit 0 = valid, 1 = invalid (reasons on stdout as JSON).
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Optional

BRUNO_DIR = ".bruno"
PLAN_FILE = "plan.json"
CHILDREN_DIR = "children"


def _require(d: dict, key: str, what: str, errs: list[str]) -> Any:
    if key not in d:
        errs.append("%s: missing '%s'" % (what, key))
        return None
    return d[key]


def validate_plan(plan: dict, errs: list[str]) -> bool:
    ok = True
    if not isinstance(plan, dict):
        errs.append("plan must be a JSON object")
        return False
    for key in ("id", "goal", "scope", "status"):
        v = _require(plan, key, "plan", errs)
        if v is not None and not isinstance(v, str):
            errs.append("plan.%s must be a string" % key); ok = False
    # Move 2: assumption ledger is mandatory, not optional.
    assumptions = _require(plan, "assumptions", "plan", errs)
    if assumptions is None:
        ok = False
    elif not isinstance(assumptions, list):
        errs.append("plan.assumptions must be a list"); ok = False
    elif not assumptions:
        errs.append("plan.assumptions is empty: the assumption ledger must name what must be true / fail"); ok = False
    for a in assumptions or []:
        if not isinstance(a, dict) or not a.get("statement"):
            errs.append("plan.assumptions entries need a 'statement'"); ok = False
    return ok


def validate_child(child: dict, errs: list[str]) -> bool:
    ok = True
    if not isinstance(child, dict):
        errs.append("child must be a JSON object")
        return False
    for key in ("id", "scope", "acceptance", "status"):
        v = _require(child, key, "child", errs)
        if v is not None and not isinstance(v, str):
            errs.append("child.%s must be a string" % key); ok = False
    falsifiers = _require(child, "falsifiers", "child", errs)
    if falsifiers is None:
        ok = False
    elif not isinstance(falsifiers, list):
        errs.append("child.falsifiers must be a list"); ok = False
    elif not falsifiers:
        errs.append("child.falsifiers is empty: Move 4 requires >=1 falsifier per child"); ok = False
    for f in falsifiers or []:
        if not isinstance(f, dict):
            errs.append("falsifier must be an object"); ok = False; continue
        for key in ("id", "description"):
            if not f.get(key):
                errs.append("falsifier missing '%s'" % key); ok = False
        check = f.get("check")
        if not isinstance(check, dict):
            errs.append("falsifier missing check{command, expected_outcome}"); ok = False; continue
        if not check.get("command") or not check.get("expected_outcome"):
            errs.append("falsifier.check needs 'command' and 'expected_outcome'"); ok = False
    return ok


def validate_workspace(workspace: pathlib.Path) -> dict[str, Any]:
    """Validate the Aegis IR under workspace. Returns {valid, reasons, plan, children}."""
    errs: list[str] = []
    plan_path = workspace / BRUNO_DIR / PLAN_FILE
    children_dir = workspace / BRUNO_DIR / CHILDREN_DIR
    if not plan_path.exists():
        errs.append("no .bruno/plan.json — Move 2/3/4 not satisfied")
    if not children_dir.exists():
        errs.append("no .bruno/children/ — Move 3 requires child slices")
    plan: Optional[dict] = None
    children: list[dict] = []
    if plan_path.exists():
        try:
            plan = json.loads(plan_path.read_text())
            validate_plan(plan, errs)
        except (OSError, json.JSONDecodeError) as exc:
            errs.append("plan.json unparseable: %s" % exc)
    if children_dir.exists():
        for child_path in sorted(children_dir.glob("*.json")):
            try:
                child = json.loads(child_path.read_text())
                children.append(child)
                validate_child(child, errs)
            except (OSError, json.JSONDecodeError) as exc:
                errs.append("%s unparseable: %s" % (child_path.name, exc))
        if not children:
            errs.append(".bruno/children/ has no *.json children")
    valid = not errs
    return {"valid": valid, "reasons": errs, "plan": plan, "children": children,
            "plan_path": str(plan_path), "children_count": len(children)}


def main() -> int:
    workspace = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    result = validate_workspace(workspace)
    print(json.dumps(result, indent=1, default=str))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
