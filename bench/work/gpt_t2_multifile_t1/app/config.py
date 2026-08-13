DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}

TRUE_VALUES = {"1", "true", "yes"}
FALSE_VALUES = {"0", "false", "no"}


def coerce_env_value(key, value):
    """Coerce an environment value to the type of its default."""
    default = DEFAULTS[key]

    if isinstance(default, bool):
        normalized = value.strip().lower()
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False
        raise ValueError(f"Invalid boolean value for APP_{key.upper()}: {value!r}")

    return type(default)(value)


class Config:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values[key]

    def as_dict(self):
        return dict(self._values)
