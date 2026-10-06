#!/usr/bin/env python3
"""word-counter -- count lines, words, and characters, with word frequencies.

A tiny, zero-dependency CLI in the spirit of wc(1), plus a top-N word
frequency table.  Reads from files, or from stdin when no files are given.

Examples:
    python word_counter.py notes.txt
    cat notes.txt | python word_counter.py --top 10
    python word_counter.py --json --min-length 4 a.txt b.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

__version__ = "1.0.0"

# A "word" is a run of Unicode letters/digits joined by internal
# apostrophes: "don't" and "rock’n’roll" are single words, while
# underscores act as separators.
_WORD_RE = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*")


def tokenize(text: str) -> list[str]:
    """Split *text* into word tokens."""
    return _WORD_RE.findall(text)


def analyse(texts, min_length: int = 1, case_sensitive: bool = False, top=None):
    """Aggregate statistics over an iterable of text chunks.

    Returns a dict with keys ``lines``, ``words``, ``chars``, ``unique``
    and ``top``.  ``top`` is ``None`` unless the *top* argument is not
    ``None``; otherwise it is a list of ``(word, count)`` pairs sorted by
    count (descending) and then alphabetically, limited to *top* entries.

    ``min_length`` filters which tokens enter the frequency table
    (``unique`` / ``top``); the ``words`` total counts every token.
    """
    lines = words = chars = 0
    freq: Counter[str] = Counter()
    for text in texts:
        lines += len(text.splitlines())
        chars += len(text)
        tokens = tokenize(text)
        words += len(tokens)
        for token in tokens:
            if len(token) >= min_length:
                freq[token if case_sensitive else token.lower()] += 1
    top_pairs = None
    if top is not None:
        top_pairs = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return {
        "lines": lines,
        "words": words,
        "chars": chars,
        "unique": len(freq),
        "top": top_pairs,
    }


def read_inputs(files) -> list[str]:
    """Return one text chunk per input; an empty *files* list means stdin."""
    if not files:
        return [sys.stdin.read()]
    chunks = []
    for name in files:
        if name == "-":
            chunks.append(sys.stdin.read())
            continue
        try:
            with open(name, "r", encoding="utf-8", errors="replace") as fh:
                chunks.append(fh.read())
        except OSError as exc:
            raise OSError(f"cannot read {name!r}: {exc.strerror or exc}") from exc
    return chunks


def format_summary(stats) -> str:
    return (
        f"lines={stats['lines']} words={stats['words']} "
        f"chars={stats['chars']} unique={stats['unique']}"
    )


def emit(stats, *, as_json: bool) -> None:
    if as_json:
        payload = {key: stats[key] for key in ("lines", "words", "chars", "unique")}
        if stats["top"] is not None:
            payload["top"] = [
                {"word": word, "count": count} for word, count in stats["top"]
            ]
        print(json.dumps(payload))
        return
    print(format_summary(stats))
    if stats["top"] is not None:
        for word, count in stats["top"]:
            print(f"{count:>6}  {word}")


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:  # pragma: no cover - stream not reconfigurable
            pass

    parser = argparse.ArgumentParser(
        prog="word-counter",
        description="Count lines, words, and characters; show top word frequencies.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="files to read ('-' for stdin); default: stdin",
    )
    parser.add_argument(
        "--top", type=int, metavar="N", help="print the N most frequent words"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=1,
        metavar="N",
        help="ignore words shorter than N characters in the frequency table",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="do not fold case when counting word frequencies",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args(argv)

    if args.top is not None and args.top < 0:
        parser.error("--top must be >= 0")
    if args.min_length < 1:
        parser.error("--min-length must be >= 1")

    try:
        texts = read_inputs(args.files)
    except OSError as exc:
        print(f"word-counter: error: {exc}", file=sys.stderr)
        return 1

    emit(
        analyse(
            texts,
            min_length=args.min_length,
            case_sensitive=args.case_sensitive,
            top=args.top,
        ),
        as_json=args.json,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
