import os

DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}


def _coerce_env_value(raw, default):
    """Coerce an env-var string to the type of the matching default."""
    if isinstance(default, bool):
        return raw.strip().lower() in {"1", "true", "yes"}
    if isinstance(default, int):
        return int(raw)
    return raw


def env_overrides():
    """Return typed overrides from APP_<KEY> env vars for known defaults."""
    result = {}
    for key, default in DEFAULTS.items():
        raw = os.environ.get("APP_" + key.upper())
        if raw is not None:
            result[key] = _coerce_env_value(raw, default)
    return result


class Config:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values[key]

    def as_dict(self):
        return dict(self._values)
