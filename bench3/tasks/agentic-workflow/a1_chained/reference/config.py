"""Service configuration. Fixed: default points at a writable dev path."""
import os
from pathlib import Path

# FIX 1: writable dev default
DB_PATH = os.environ.get("SVC_DB", str(Path(__file__).resolve().parent / "dev.db"))
