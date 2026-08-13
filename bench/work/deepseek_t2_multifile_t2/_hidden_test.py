import os
import unittest
from app.loader import load_config


class T(unittest.TestCase):
    def setUp(self):
        for k in list(os.environ):
            if k.startswith("APP_"):
                del os.environ[k]

    tearDown = setUp

    def test_defaults(self):
        c = load_config()
        self.assertEqual(c.get("host"), "localhost")
        self.assertEqual(c.get("port"), 8000)
        self.assertIs(c.get("debug"), False)

    def test_env_override_with_types(self):
        os.environ["APP_PORT"] = "9000"
        os.environ["APP_DEBUG"] = "true"
        c = load_config()
        self.assertEqual(c.get("port"), 9000)
        self.assertIsInstance(c.get("port"), int)
        self.assertIs(c.get("debug"), True)

    def test_bool_falsey_strings(self):
        for s in ("0", "false", "False", "no"):
            os.environ["APP_DEBUG"] = s
            self.assertIs(load_config().get("debug"), False, s)

    def test_explicit_overrides_win(self):
        os.environ["APP_PORT"] = "9000"
        self.assertEqual(load_config({"port": 1234}).get("port"), 1234)

    def test_unknown_env_ignored(self):
        os.environ["APP_NOPE"] = "x"
        self.assertNotIn("nope", load_config().as_dict())

    def test_api_unchanged(self):
        self.assertEqual(
            set(load_config().as_dict()), {"host", "port", "debug"}
        )


if __name__ == "__main__":
    unittest.main()
