"""Unit tests for word_counter (library + CLI)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import word_counter as wc

SCRIPT = str(Path(__file__).with_name("word_counter.py"))


def run_cli(*argv, stdin_text=None):
    return subprocess.run(
        [sys.executable, SCRIPT, *argv],
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(Path(SCRIPT).parent),
    )


class TokenizeTests(unittest.TestCase):
    def test_basic_words(self):
        self.assertEqual(wc.tokenize("Hello, world! 42"), ["Hello", "world", "42"])

    def test_apostrophes_join(self):
        self.assertEqual(wc.tokenize("don't stop"), ["don't", "stop"])
        self.assertEqual(
            wc.tokenize("rock\u2019n\u2019roll baby"), ["rock\u2019n\u2019roll", "baby"]
        )

    def test_underscore_is_separator(self):
        self.assertEqual(wc.tokenize("foo_bar baz"), ["foo", "bar", "baz"])

    def test_leading_apostrophe_dropped(self):
        self.assertEqual(wc.tokenize("'tis the season"), ["tis", "the", "season"])

    def test_unicode_words(self):
        self.assertEqual(wc.tokenize("caf\u00e9 na\u00efve"), ["caf\u00e9", "na\u00efve"])


class AnalyseTests(unittest.TestCase):
    def test_counts(self):
        text = "one two three\nfour five\n"
        stats = wc.analyse([text])
        self.assertEqual(stats["lines"], 2)
        self.assertEqual(stats["words"], 5)
        self.assertEqual(stats["chars"], 24)
        self.assertEqual(stats["unique"], 5)
        self.assertIsNone(stats["top"])

    def test_no_trailing_newline(self):
        stats = wc.analyse(["abc"])
        self.assertEqual((stats["lines"], stats["words"], stats["chars"]), (1, 1, 3))

    def test_empty_input(self):
        stats = wc.analyse([""])
        self.assertEqual(
            (stats["lines"], stats["words"], stats["chars"], stats["unique"]),
            (0, 0, 0, 0),
        )

    def test_case_folding_default(self):
        stats = wc.analyse(["The the THE"], top=10)
        self.assertEqual(stats["top"], [("the", 3)])

    def test_case_sensitive(self):
        stats = wc.analyse(["The The the THE"], case_sensitive=True, top=10)
        self.assertEqual(stats["top"], [("The", 2), ("THE", 1), ("the", 1)])

    def test_min_length_filters_frequency_only(self):
        stats = wc.analyse(["a bb ccc"], min_length=2, top=10)
        self.assertEqual(stats["top"], [("bb", 1), ("ccc", 1)])
        self.assertEqual(stats["words"], 3)
        self.assertEqual(stats["unique"], 2)

    def test_top_ties_sorted_alphabetically(self):
        stats = wc.analyse(["b a c b a"], top=10)
        self.assertEqual(stats["top"], [("a", 2), ("b", 2), ("c", 1)])

    def test_top_limit(self):
        stats = wc.analyse(["b a c b a"], top=2)
        self.assertEqual(stats["top"], [("a", 2), ("b", 2)])

    def test_multiple_texts_aggregate(self):
        stats = wc.analyse(["ab", "cd\nef"])
        self.assertEqual(
            (stats["lines"], stats["words"], stats["chars"], stats["unique"]),
            (3, 3, 7, 3),
        )


class CliTests(unittest.TestCase):
    def test_stdin_summary(self):
        res = run_cli(stdin_text="one two\nthree\n")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            res.stdout.strip().splitlines()[0], "lines=2 words=3 chars=14 unique=3"
        )

    def test_json_output(self):
        res = run_cli("--json", "--top", "2", stdin_text="the cat the hat the\n")
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["words"], 5)
        self.assertEqual(
            payload["top"],
            [{"word": "the", "count": 3}, {"word": "cat", "count": 1}],
        )

    def test_json_min_length(self):
        res = run_cli(
            "--json", "--min-length", "4", "--top", "10",
            stdin_text="the quick brown fox jumps\n",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["words"], 5)
        self.assertEqual(payload["unique"], 3)
        self.assertEqual(
            [item["word"] for item in payload["top"]],
            ["brown", "jumps", "quick"],
        )

    def test_file_input(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.txt"
            path.write_text("alpha beta\nbeta\n", encoding="utf-8")
            res = run_cli("--top", "1", str(path))
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = res.stdout.strip().splitlines()
        self.assertEqual(lines[0], "lines=2 words=3 chars=16 unique=2")
        self.assertIn("beta", lines[1])

    def test_dash_reads_stdin(self):
        res = run_cli("-", "--json", stdin_text="hi there\n")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(json.loads(res.stdout)["words"], 2)

    def test_missing_file_errors(self):
        res = run_cli("definitely-missing.txt")
        self.assertEqual(res.returncode, 1)
        self.assertIn("definitely-missing.txt", res.stderr)

    def test_unicode_roundtrip(self):
        res = run_cli("--json", "--top", "10", stdin_text="caf\u00e9 CAF\u00c9 na\u00efve\n")
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(
            payload["top"],
            [
                {"word": "caf\u00e9", "count": 2},
                {"word": "na\u00efve", "count": 1},
            ],
        )

    def test_version(self):
        res = run_cli("--version")
        self.assertEqual(res.returncode, 0)
        self.assertIn("1.0.0", res.stdout)


if __name__ == "__main__":
    unittest.main()
