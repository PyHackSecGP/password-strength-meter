# Password Strength Meter (CLI)

A tiny, dependency-free password strength meter for the command line. It estimates entropy, flags risky patterns (repeats, dates, keyboard runs, sequences, and l33t-ified dictionary words), and offers zxcvbn-style feedback tips.

## Features
- Entropy estimate from character classes x length
- Pattern detection: repeated substrings/chars, sequences, keyboard runs, dates
- l33t normalization to catch disguised words (p@ssw0rd -> password)
- Human feedback with actionable tips
- JSON output for scripting
- Unit tests with pytest

Note: This tool is heuristic. It is intended for education and guidance, not as a definitive security auditor.

## Install (local)
```
cd password-strength-meter
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
pip install -e .
```

Or just run the CLI without installing:
```
python -m pwstrength.cli "yourPassword123!"
```

## Usage
```
pwstrength "Summer2024-07-15!"
# or prompt (hidden input)
pwstrength
```

Example:
```
Length   : 18
Classes  : lower, upper, digit, symbol
Entropy  : 69.32 bits (base 87.32)
Score    : 3 / 4
Flags    :
  - date          [6:16]  2024-07-15
Feedback :
  * Avoid using dates; they are easy to guess.
  * Mix upper/lowercase, digits, and symbols to expand the character space.
  * Consider a passphrase of 4-5 random words.
```

JSON:
```
pwstrength --json "p@ssw0rd"
```

## What is measured
1) Base entropy ~ length * log2(character_set_size) using classes present.
2) Pattern penalties reduce the estimate when risky patterns are found:
   - repeated substrings or characters
   - alphabetic or digit sequences (e.g., abcd, 4321)
   - common keyboard runs (e.g., qwerty, asdf)
   - dates in common formats (YYYYMMDD, YYYY-MM-DD, MMDDYYYY, etc.)
   - common words (and their l33t versions), e.g., p@ssw0rd

3) Score: 0-4 based on adjusted entropy:
   - <28: 0 (very weak)
   - 28-35: 1
   - 36-59: 2
   - 60-127: 3
   - 128+: 4

## Run tests
```
pip install -r requirements-dev.txt
pytest -q
```

## Demo
See demo.gif for a quick terminal-style demonstration.

## Packaging (optional)
Create a console entry point by adding this to pyproject.toml:
```
[project]
name = "pwstrength"
version = "0.1.0"
requires-python = ">=3.9"

[project.scripts]
pwstrength = "pwstrength.cli:main"
```
Then:
```
pip install -e .
```

## Caveats
- Heuristic penalties are intentionally simple. Do not use this to gate production auth.
- Unicode and locale-specific keyboards are not modeled exhaustively.
- For serious password strength estimation, combine multiple approaches and real-world breach corpora.
