import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from csvish import parse_rows


class T(unittest.TestCase):
    def test_quoted_delimiter(self):
        self.assertEqual(parse_rows('a,"b,c",d\n'), [["a", "b,c", "d"]])

    def test_quoted_newline(self):
        self.assertEqual(parse_rows('a,"line1\nline2",b\n'), [["a", "line1\nline2", "b"]])

    def test_escaped_quotes(self):
        self.assertEqual(parse_rows('"he said ""hi""",x\n'), [["he said \"hi\"", "x"]])

    def test_empty_fields(self):
        self.assertEqual(parse_rows("a,,c,\n"), [["a", "", "c", ""]])

    def test_trailing_newline_and_blank_rows(self):
        self.assertEqual(parse_rows("a,b\n\n"), [["a", "b"]])
        self.assertEqual(parse_rows("a,b\n"), [["a", "b"]])

    def test_multiple_rows(self):
        self.assertEqual(parse_rows("1,2\n3,4\n"), [["1", "2"], ["3", "4"]])

    def test_custom_delimiter(self):
        self.assertEqual(parse_rows("x;y;z\n", delimiter=";"), [["x", "y", "z"]])

    def test_model_wrote_tests(self):
        """The model must deliver its own tests covering the five cases."""
        test_path = Path(__file__).parent / 'test_csvish.py'
        self.assertTrue(test_path.exists(), 'test_csvish.py missing')
        content = test_path.read_text().lower()
        for probe in ('quoted', 'newline', 'escape', 'empty', 'trailing'):
            self.assertIn(probe, content, 'test_csvish.py lacks coverage of %s' % probe)


if __name__ == "__main__":
    unittest.main()
