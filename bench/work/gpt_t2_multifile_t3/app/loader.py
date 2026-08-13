import os

from .config import DEFAULTS, Config, coerce_env_value


def load_config(overrides=None):
    values = dict(DEFAULTS)
    for key, default in DEFAULTS.items():
        env_name = f"APP_{key.upper()}"
        if env_name in os.environ:
            values[key] = coerce_env_value(os.environ[env_name], default)
    if overrides:
        values.update(overrides)
    return Config(values)
