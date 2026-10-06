# word-counter

A tiny zero-dependency Python CLI that counts **lines, words, and characters** in files (or stdin) and can print the **top-N word frequencies** — like `wc` with a frequency table.

## Usage

    python word_counter.py [options] [FILE ...]

With no `FILE` (or with `-`), input is read from stdin. Multiple files are aggregated into a single summary.

    $ printf 'the cat and the hat\n' | python word_counter.py --top 2
    lines=1 words=5 chars=20 unique=4
         2  the
         1  and

### Options

| option             | meaning                                                              |
| ------------------ | -------------------------------------------------------------------- |
| `--top N`          | print the N most frequent words (sorted by count, then alphabetically) |
| `--min-length N`   | ignore words shorter than N chars in the frequency table              |
| `--case-sensitive` | don't fold case when counting word frequencies                        |
| `--json`           | machine-readable output                                               |
| `--version`        | print version                                                         |

Word definition: a run of Unicode letters/digits joined by internal apostrophes (`don't` and `rock’n’roll` count as one word each); underscores and other punctuation separate words. `--min-length` filters the frequency table only — the `words` total counts every token.

## Tests

    python -m unittest -v test_word_counter.py

Covers tokenization (apostrophes, Unicode, underscores), case folding, tie-break ordering, min-length filtering, multi-input aggregation, and the CLI contract (stdin, files, `--json`, missing-file errors).

## License

MIT — see [LICENSE](LICENSE).
