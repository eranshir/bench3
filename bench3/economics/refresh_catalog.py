#!/usr/bin/env python3
"""Snapshot current OpenRouter and LunaRoute model catalogs."""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone

from common import ECON, load_config, load_credentials


def get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url)
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def main() -> int:
    config = load_config()
    creds = load_credentials()
    openrouter = get_json("https://openrouter.ai/api/v1/models").get("data", [])
    lunaroute = []
    lunaroute_images = []
    lunaroute_embeddings = []
    lunaroute_rerank = []
    lr_key = creds.get("LUNAROUTE_API_KEY")
    if lr_key:
        headers = {"LUNAROUTE-API-KEY": lr_key}
        lunaroute = get_json("https://gw.lunaroute.com/v1/models", headers).get("data", [])
        lunaroute_images = get_json(
            "https://gw.lunaroute.com/v1/images/models", headers
        ).get("data", [])
        lunaroute_embeddings = get_json(
            "https://gw.lunaroute.com/v1/embeddings/models", headers
        ).get("data", [])
        lunaroute_rerank = get_json(
            "https://gw.lunaroute.com/v1/rerank/models", headers
        ).get("data", [])

    configured = {route["model"] for route in config["routes"].values()}
    selected_or = [model for model in openrouter if model.get("id") in configured]
    snapshot = {
        "schema_version": "bench3.economics.catalog.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "configured_catalog_as_of": config["catalog_as_of"],
        "openrouter": selected_or,
        "lunaroute": lunaroute,
        "lunaroute_images": lunaroute_images,
        "lunaroute_embeddings": lunaroute_embeddings,
        "lunaroute_rerank": lunaroute_rerank,
    }
    out = ECON / "catalog_snapshot.json"
    out.write_text(json.dumps(snapshot, indent=1))
    print(
        "wrote %s: %d selected OpenRouter, %d LunaRoute main, %d image, %d embedding, %d rerank models"
        % (
            out, len(selected_or), len(lunaroute), len(lunaroute_images),
            len(lunaroute_embeddings), len(lunaroute_rerank),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

