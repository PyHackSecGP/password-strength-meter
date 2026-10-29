# password-strength-meter — Entropy + pattern + breach-list analyzer

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![tests](https://img.shields.io/badge/tests-6%20passing-brightgreen)
![deps](https://img.shields.io/badge/runtime%20deps-0-success)
![license](https://img.shields.io/badge/license-MIT-informational)
![status](https://img.shields.io/badge/status-educational-orange)

## 60-Second Overview

`pwstrength` scores a password on three axes:

1. **Shannon-style entropy** — `length * log2(charset_size)` where `charset_size` is the sum of character-class sizes present (26 + 26 + 10 + 32 symbols).
2. **Pattern detection** — regex + algorithmic sweeps for dates, keyboard walks (`qwerty`, `asdf`), ascending/descending sequences (`abcd`, `4321`), repeated substrings (`abcabcabc`), repeated characters (`aaaa`), and l33t-normalized dictionary words (`p@ssw0rd` → `password`).
3. **Breach wordlist presence** — a small bundled common-password list acts as the dictionary; a full HIBP/rockyou subset backend is on the roadmap (see Technical Reference → *Breach-list source*).

Each flag penalizes the raw entropy. The adjusted bit-count maps to a 0-4 score. Output is human-readable or JSON.

**This is not a replacement for a password manager.** It is a transparency tool: everything it does is readable in a single ~250-line file (`pwstrength/meter.py`). Use it to teach, demo, or sanity-check — then go generate a 20-character random string in Bitwarden.

## For Interviewers

### Problem Statement

`zxcvbn` is the de-facto strength meter but it ships as a black box: ~35k lines of frequency tables, Markov models, and a graph search most reviewers never crack open. For security workshops and interview demos I wanted something a mid-level engineer can read end-to-end in 20 minutes and extend in an afternoon — without giving up the ideas that make `zxcvbn` useful (penalize patterns, score on log-guesses, give actionable feedback).

### Skills Demonstrated

- **Entropy math** — correct `log2` application over the realized character space, not a naive points-per-class scheme.
- **Regex pattern catalog** — four date formats across `YYYY-MM-DD`, `MM-DD-YYYY`, `DD-MM-YYYY`, and 2-digit years with optional separators.
- **Algorithmic sweeps** — O(n) repeated-char run detection, O(n) monotonic sequence walker, and a divisor-based repeated-substring check (`chunk * k == pw`).
- **Large-wordlist lookup design** — current implementation uses an in-memory `list` for 21 common words (fine); the Technical Reference documents the `set`-backed and Bloom-filter upgrade paths for a 14-million-entry rockyou merge.
- **CLI design** — hidden-input default via `getpass`, `--json` for scripting, `--show` for teaching contexts where echoing is intended.
- **Testing** — six pytest cases cover empty input, leet dictionary, dates, keyboard+sequence combos, repeated substrings, and repeated characters.

### Design Decisions

- **Why not just `zxcvbn`?** You still should in production. This exists to make the ideas inspectable. Every penalty is a single named constant in `_penalize()`; every pattern is one function in `meter.py`.
- **How are patterns detected?** Independent passes, union the flags, penalize additively. Simpler than `zxcvbn`'s DP minimum-guesses graph, demonstrably noisier — the trade is readability.
- **Breach-list storage strategy** — bundled list stays a Python literal (21 entries, zero I/O cost). For rockyou-scale lookups the recommended swap is a `set[str]` loaded once at import or a `pybloom-live` Bloom filter for memory-constrained CLI use. Both are documented below.
- **l33t handling** — single-pass character map (`4→a, @→a, 3→e, 1→l, …`) applied before the dictionary scan. Catches `p@ssw0rd`, misses homoglyph attacks on purpose (out of scope for a CLI).

### Metrics

| Metric | Value |
|-------:|:------|
| Runtime deps | 0 |
| Tests | 6 (all passing) |
| LOC (`pwstrength/`) | ~300 |
| Bundled common-words | 21 |
| Pattern categories | 6 (`repeat`, `repeat-chars`, `sequence`, `keyboard`, `date`, `dictionary`) |
| Entropy formula | `len * log2(charset_size)` |
| Score bands | `<28, <36, <60, <128, 128+` → `0..4` |

## Quick Start

```bash
# install (editable)
cd password-strength-meter
python -m venv .venv && source .venv/bin/activate
pip install -e .

# check one password (hidden prompt)
pwstrength

# check one password (inline — note shell history will store it)
pwstrength 'correct horse battery staple'

# machine-readable
pwstrength --json 'P@ssw0rd!'

# batch check from a file, one password per line
while IFS= read -r pw; do pwstrength --json "$pw"; done < passwords.txt
```

## Features

- Zero runtime dependencies — stdlib only.
- Entropy estimate derived from realized character classes, not fixed point buckets.
- Six pattern detectors: repeated substrings, repeated chars, sequences, keyboard runs, dates, dictionary (with l33t normalization).
- Human feedback: every flag suggests the specific fix.
- JSON output for scripting / batch audits.
- Hidden-prompt mode (`getpass`) when no password argument is given.
- `--show` opt-in echo for workshops / screencasts.
- Readable in one sitting: `meter.py` is ~250 lines.
- Pytest suite covers each pattern class.

## Examples

### Strong passphrase

```
$ pwstrength 'correct horse battery staple'
Length   : 28
Classes  : lower, symbol
Entropy  : 131.6 bits (base 131.6)
Score    : 4 / 4
Flags    : -
```

### Weak with multiple patterns

```
$ pwstrength 'qwerty1234'
Length   : 10
Classes  : lower, digit
Entropy  : 15.72 bits (base 51.7)
Score    : 0 / 4
Flags    :
  - keyboard      [0:6]   qwerty
  - sequence      [6:10]  step +1
Feedback :
  * Use 12+ characters; length boosts entropy.
  * Mix upper/lowercase, digits, and symbols to expand the character space.
  * Avoid sequences like abcd or 1234.
  * Avoid keyboard runs like qwerty or asdf.
  * Consider a passphrase of 4-5 random words.
```

### Breach-list / l33t hit

```
$ pwstrength 'P@ssw0rd!'
Length   : 9
Classes  : lower, upper, digit, symbol
Entropy  : 41.19 bits (base 59.19)
Score    : 2 / 4
Flags    :
  - dictionary    [0:8]   password
Feedback :
  * Use 12+ characters; length boosts entropy.
  * Avoid common words or names, even with substitutions (l33t).
  * Consider a passphrase of 4-5 random words.
```

Note the l33t normalization: the raw password contains no literal `password`, but `_normalize_leet()` maps `@→a, 0→o` before the dictionary pass, so the flag fires on the normalized form.

## Technical Reference

### Install

```bash
git clone <repo> && cd password-strength-meter
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt   # pytest
pytest -q
```

Requires Python 3.9+. No runtime dependencies.

### CLI flags

| Flag | Effect |
|------|--------|
| `password` (positional) | Password to evaluate. Optional. |
| `--json` | Emit JSON instead of the aligned text table. |
| `--show` | Echo the password back in text output (default hidden). |
| *(no args)* | Prompt via `getpass` (hidden input). |

### Entropy formula

```
charset_size = (26 if lower)
             + (26 if upper)
             + (10 if digit)
             + (32 if symbol)   # len(SYMBOLS) in meter.py
base_bits    = len(password) * log2(charset_size)
adj_bits     = max(0, base_bits - sum(pattern_penalties))
guesses      = 2 ** adj_bits
score        = bucket(adj_bits) in {0..4}
```

Score buckets: `<28 → 0`, `<36 → 1`, `<60 → 2`, `<128 → 3`, `>=128 → 4`. The 60/128 thresholds track NIST SP 800-63B's historical guidance for online vs offline attacker models.

### Pattern catalog

| Flag type | Detector | Penalty |
|-----------|----------|---------|
| `repeat` | `_find_repeated_substring` — divisor sweep, matches `chunk * k == pw` | 10.0 bits |
| `repeat-chars` | `_find_repeated_chars` — runs of length >= 3 | `(run_len - 2) * 2.0` bits |
| `sequence` | `_find_sequences` — monotonic ±1 steps in letters or digits | `(len - 2) * 1.5` bits |
| `keyboard` | `_find_keyboard_runs` — segments of QWERTY rows length >= 4, forward + reverse | `(len - 3) * 2.0` bits |
| `date` | `_find_dates` — four regexes for `YYYYMMDD`, `MMDDYYYY`, `DDMMYYYY`, `MMDDYY` with optional separators | 18.0 bits |
| `dictionary` | `_find_common_words` on raw + l33t-normalized form | 18.0 bits |

Penalties are additive and floored at zero. Each is a named constant in `_penalize()` — tune in one place.

### Breach-list source + update process

Current build ships 21 common passwords inline (`COMMON_WORDS` in `meter.py`). This covers "demo day" and the OWASP top-10 class of passwords, nothing more.

To upgrade to a real breach corpus:

1. **Pick a source.** HIBP's SHA-1 Pwned Passwords download (~40 GB uncompressed, ~1 B entries) or a rockyou-derived top-N (14 M entries, ~130 MB).
2. **Shape the artifact.** For top-N: one password per line, newline-terminated, UTF-8. Ship under `pwstrength/data/breach_top.txt.gz`.
3. **Load lazily.** Replace `COMMON_WORDS` with a module-level `_BREACH: set[str] | None = None` and a `_load_breach()` function invoked on first `estimate()`. Decompress with `gzip.open` + `set(...)` — ~400 MB RAM for 14 M entries.
4. **Memory-constrained option.** Use `pybloom-live` with FPR=0.01 — ~17 MB for 14 M entries. Add a one-line optional dep in `pyproject.toml`.
5. **Update cadence.** HIBP releases new corpora on breach disclosure. A `scripts/update_breach.sh` fetching the latest list and re-shipping the artifact is the right place for cron.

### Extending

**Add a pattern.**

1. Write `_find_<kind>(pw: str) -> list[PatternFlag]` in `pwstrength/meter.py`.
2. Append `flags.extend(_find_<kind>(password))` in `estimate()`.
3. Add a penalty branch in `_penalize()`.
4. Add feedback copy in `_feedback()`.
5. Add a test in `tests/test_meter.py` asserting the flag type appears.

**Swap the wordlist.** Replace `COMMON_WORDS` with a loader as described above. Keep the API — `_find_common_words()` only needs an iterable with `in` support, so `set` or Bloom filter both drop in.

**Change score thresholds.** `_score()` is five if-branches; adjust the bit cutoffs to match your target attacker model (online throttled, online unthrottled, offline hash, offline fast hash).

## Why This Was Built

Teaching material. Password-choice workshops hit a wall when the attendee asks "but *why* is that weak?" and the answer is "`zxcvbn` says so." This project exists so the answer can be "here is the function that penalizes it, here is the entropy before and after, here is the specific regex that matched the date in your birthday." Readable code is the pedagogical point. If it also happens to score reasonably against the common ~20 passwords, bonus.

## FAQ

**Q: How does this compare to `zxcvbn`?**
A: `zxcvbn` is more accurate and better-tuned on real breach corpora. This is more readable, trivially extensible, and has no runtime dependencies. Use `zxcvbn` in production; use this to teach or when you need to drop a password check into a script without a C-extension dependency chain.

**Q: Why not call haveibeenpwned.com directly?**
A: Shipping an offline check avoids the privacy trade of a k-anonymity API call for every password (even k-anonymous HIBP leaks the SHA-1 prefix). A bundled list is network-free and demo-safe. The HIBP range API is a reasonable upgrade — see Technical Reference → *Breach-list source*.

**Q: Is entropy really the right metric?**
A: For truly random passwords, yes. For human-chosen passwords it is an upper bound: `_penalize()` exists precisely because `len * log2(charset)` wildly overestimates realized guess-resistance when patterns are present. The score bucket is what you should quote to users, not the raw bits.

**Q: Does it support Unicode / non-English keyboards?**
A: Partially. Entropy counts any character, but `KEYBOARD_ROWS` is QWERTY-only and `COMMON_WORDS` is English. Dvorak / AZERTY / Cyrillic layouts will miss keyboard-walk detections. Adding a row set per layout is the lazy fix — one dict, one loop.

**Q: Can I use this to gate production authentication?**
A: No. Use `zxcvbn-ts`, enforce length minimums, require a password manager, and check candidates against the HIBP range API. This tool is diagnostic.

**Q: What's the fastest way to get a stronger password *right now*?**
A: Open your password manager, generate 20+ characters of mixed classes, save it, close the tab. Everything else — including this tool — is a conversation about the ones you still have to remember.

## License

MIT.
