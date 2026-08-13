from .config import DEFAULTS, Config


def load_config(overrides=None):
    values = dict(DEFAULTS)
    if overrides:
        values.update(overrides)
    return Config(values)
