import os

from .config import DEFAULTS, Config


def _coerce(value, default):
    if isinstance(default, bool):
        return value.strip().lower() in ("1", "true", "yes")
    if isinstance(default, int):
        return int(value)
    return value


def _env_overrides():
    overrides = {}
    for key, default in DEFAULTS.items():
        env_value = os.environ.get(f"APP_{key.upper()}")
        if env_value is not None:
            overrides[key] = _coerce(env_value, default)
    return overrides


def load_config(overrides=None):
    values = dict(DEFAULTS)
    values.update(_env_overrides())
    if overrides:
        values.update(overrides)
    return Config(values)
