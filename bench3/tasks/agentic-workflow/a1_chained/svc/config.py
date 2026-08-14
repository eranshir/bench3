"""Service configuration. BUG 1: the default DB path points at a
non-writable location, so a bare run fails before any query."""
import os

# BUG 1: default should be a writable dev path, not the prod path
DB_PATH = os.environ.get("SVC_DB", "/var/svc-prod/data.db")
