from .config import DEFAULTS, Config, env_overrides


def load_config(overrides=None):
    values = dict(DEFAULTS)
    values.update(env_overrides())
    if overrides:
        values.update(overrides)
    return Config(values)
