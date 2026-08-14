import unittest

from csvish import parse_rows


class TestParser(unittest.TestCase):
    def test_quoted_fields(self):
        self.assertEqual(parse_rows('a,"b,c",d\n'), [["a", "b,c", "d"]])

    def test_embedded_newlines(self):
        self.assertEqual(parse_rows('a,"x\ny",b\n'), [["a", "x\ny", "b"]])

    def test_escaped_quotes(self):
        self.assertEqual(parse_rows('"say ""hi""",z\n'), [["say \"hi\"", "z"]])

    def test_empty_fields(self):
        self.assertEqual(parse_rows("a,,,\n"), [["a", "", "", ""]])

    def test_trailing_newline(self):
        self.assertEqual(parse_rows("a,b\n"), [["a", "b"]])


if __name__ == "__main__":
    unittest.main()
