DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}


class Config:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values[key]

    def as_dict(self):
        return dict(self._values)
