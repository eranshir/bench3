import os

from .config import DEFAULTS, Config, coerce_env_value


def load_config(overrides=None):
    values = dict(DEFAULTS)

    for key in DEFAULTS:
        env_name = f"APP_{key.upper()}"
        if env_name in os.environ:
            values[key] = coerce_env_value(key, os.environ[env_name])

    if overrides:
        values.update(overrides)
    return Config(values)
