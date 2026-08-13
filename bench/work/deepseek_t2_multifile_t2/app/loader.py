import os

from .config import DEFAULTS, Config, coerce_value


def _env_overrides():
    values = {}
    for key in DEFAULTS:
        raw_value = os.environ.get(f"APP_{key.upper()}")
        if raw_value is not None:
            values[key] = coerce_value(key, raw_value)
    return values


def load_config(overrides=None):
    values = dict(DEFAULTS)
    values.update(_env_overrides())
    if overrides:
        values.update(overrides)
    return Config(values)
