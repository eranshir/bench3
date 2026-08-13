DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}

ENV_PREFIX = "APP_"


def env_name(key):
    return f"{ENV_PREFIX}{key.upper()}"


def coerce_env_value(value, default):
    if isinstance(default, bool):
        if value in {"1", "true", "True", "yes"}:
            return True
        if value in {"0", "false", "False", "no"}:
            return False
        raise ValueError(f"Invalid boolean environment value: {value!r}")

    return type(default)(value)


class Config:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values[key]

    def as_dict(self):
        return dict(self._values)
