---
title: Password Strength Meter
---

# Password Strength Meter (CLI)

![Demo](./demo.gif)

A tiny, dependency-free CLI that estimates entropy and flags patterns
(repeats, dates, l33t, sequences, keyboard runs) with zxcvbn-style tips.

## Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
