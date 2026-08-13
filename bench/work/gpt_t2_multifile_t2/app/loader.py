import os

from .config import DEFAULTS, Config, coerce_env_value, env_name


def load_config(overrides=None):
    values = dict(DEFAULTS)

    for key, default in DEFAULTS.items():
        name = env_name(key)
        if name in os.environ:
            values[key] = coerce_env_value(os.environ[name], default)

    if overrides:
        values.update(overrides)
    return Config(values)
