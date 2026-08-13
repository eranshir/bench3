DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}

_TRUE_STRINGS = ("1", "true", "True", "yes")
_FALSE_STRINGS = ("0", "false", "False", "no")


def coerce_value(key, raw_value):
    default = DEFAULTS[key]
    if isinstance(default, bool):
        if raw_value in _TRUE_STRINGS:
            return True
        if raw_value in _FALSE_STRINGS:
            return False
        raise ValueError(
            f"Invalid boolean for APP_{key.upper()}: {raw_value!r}"
        )
    return type(default)(raw_value)


class Config:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values[key]

    def as_dict(self):
        return dict(self._values)
