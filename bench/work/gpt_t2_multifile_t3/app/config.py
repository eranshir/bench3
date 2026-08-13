DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}

TRUE_VALUES = {"1", "true", "True", "yes"}
FALSE_VALUES = {"0", "false", "False", "no"}


def coerce_env_value(value, default):
    if isinstance(default, bool):
        if value in TRUE_VALUES:
            return True
        if value in FALSE_VALUES:
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
