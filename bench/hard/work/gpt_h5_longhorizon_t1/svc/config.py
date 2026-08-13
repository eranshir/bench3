"""Runtime configuration.

Environments:
  dev   - local sqlite file under ./data, created by seed.py
  prod  - managed volume, only mounted on the settlement hosts
"""
import os

DEFAULTS = {
    "page_size": 25,
    "dev_db_path": "data/service.db",
    "prod_db_path": "/var/lib/svc/service.db",
}


def load():
    """Return the effective config dict."""
    # A checkout must be safe and useful without requiring environment
    # variables.  Production is selected explicitly on settlement hosts.
    env = os.environ.get("SVC_ENV", "dev")
    cfg = {"env": env, "page_size": DEFAULTS["page_size"]}
    if env == "prod":
        cfg["db_path"] = DEFAULTS["prod_db_path"]
    else:
        cfg["db_path"] = DEFAULTS["dev_db_path"]
    return cfg
