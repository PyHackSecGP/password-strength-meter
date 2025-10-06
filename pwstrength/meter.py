from __future__ import annotations
import math
import re
from dataclasses import dataclass, field
from typing import List, Tuple

LOWER = set("abcdefghijklmnopqrstuvwxyz")
UPPER = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = set("0123456789")
SYMBOLS = set(r""" !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")

COMMON_WORDS = [
    "password","letmein","qwerty","admin","welcome","iloveyou","monkey",
    "dragon","princess","football","baseball","sunshine","login","abc123",
    "trustno1","hello","freedom","whatever","zaq","passw0rd","master"
]

KEYBOARD_ROWS = [
    "1234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm"
]

LEET_MAP = {
    "4":"a","@":"a",
    "3":"e",
    "1":"l", "!":"i", "|":"l",
    "0":"o",
    "5":"s","$":"s",
    "7":"t",
    "8":"b"
}

@dataclass
class PatternFlag:
    type: str
    span: Tuple[int,int]
    detail: str

@dataclass
class StrengthResult:
    password: str
    length: int
    categories: List[str]
    base_entropy_bits: float
    adjusted_entropy_bits: float
    guesses: float
    score: int
    flags: List[PatternFlag] = field(default_factory=list)
    feedback: List[str] = field(default_factory=list)

def _char_categories(pw: str) -> List[str]:
    cats = []
    s = set(pw)
    if any(c in LOWER for c in s): cats.append("lower")
    if any(c in UPPER for c in s): cats.append("upper")
    if any(c in DIGITS for c in s): cats.append("digit")
    if any(c in SYMBOLS for c in s): cats.append("symbol")
    return cats

def _charset_size(categories: List[str]) -> int:
    size = 0
    if "lower" in categories: size += 26
    if "upper" in categories: size += 26
    if "digit" in categories: size += 10
    if "symbol" in categories: size += len(SYMBOLS)
    if size == 0:
        size = 26
    return size

def _normalize_leet(pw: str) -> str:
    return "".join(LEET_MAP.get(c.lower(), c.lower()) for c in pw)

def _find_repeated_substring(pw: str):
    n = len(pw)
    for k in range(1, n//2 + 1):
        if n % k == 0:
            chunk = pw[:k]
            if chunk * (n//k) == pw:
                return PatternFlag("repeat", (0, n), f"{n//k}x '{chunk}'")
    return None

def _find_repeated_chars(pw: str):
    flags = []
    i = 0
    while i < len(pw):
        j = i+1
        while j < len(pw) and pw[j] == pw[i]:
            j += 1
        run_len = j - i
        if run_len >= 3:
            flags.append(PatternFlag("repeat-chars", (i, j), f"{pw[i]}x{run_len}"))
        i = j
    return flags

def _find_sequences(pw: str):
    flags = []
    def is_seq(a: str, b: str) -> int:
        if a.isalpha() and b.isalpha():
            return (ord(b.lower()) - ord(a.lower()))
        if a.isdigit() and b.isdigit():
            return (ord(b) - ord(a))
        return 999
    i = 0
    while i < len(pw)-2:
        d1 = is_seq(pw[i], pw[i+1])
        d2 = is_seq(pw[i+1], pw[i+2])
        if d1 in (1,-1) and d2 == d1:
            j = i+3
            while j < len(pw) and is_seq(pw[j-1], pw[j]) == d1:
                j += 1
            flags.append(PatternFlag("sequence", (i, j), f"step {d1:+d}"))
            i = j
        else:
            i += 1
    return flags

def _find_keyboard_runs(pw: str):
    flags = []
    low = pw.lower()
    for row in KEYBOARD_ROWS:
        for s in (row, row[::-1]):
            for L in range(4, len(s)+1):
                for i in range(0, len(s)-L+1):
                    seg = s[i:i+L]
                    idx = low.find(seg)
                    if idx != -1:
                        flags.append(PatternFlag("keyboard", (idx, idx+L), seg))
    return flags

DATE_PATTERNS = [
    r"\b(19|20)\d{2}[-/_\.]?(0[1-9]|1[0-2])[-/_\.]?(0[1-9]|[12]\d|3[01])\b",
    r"\b(0[1-9]|1[0-2])[-/_\.]?(0[1-9]|[12]\d|3[01])[-/_\.]?((19|20)\d{2})\b",
    r"\b(0[1-9]|[12]\d|3[01])[-/_\.]?(0[1-2])[-/_\.]?((19|20)\d{2})\b".replace("(0[1-2])","(0[1-9]|1[0-2])"),
    r"\b(0[1-9]|1[0-2])[-/_\.]?(0[1-9]|[12]\d|3[01])[-/_\.]?(\d{2})\b",
]

def _find_dates(pw: str):
    flags = []
    for pat in DATE_PATTERNS:
        for m in re.finditer(pat, pw):
            flags.append(PatternFlag("date", (m.start(), m.end()), pw[m.start():m.end()]))
    return flags

def _find_common_words(pw: str):
    flags = []
    low = pw.lower()
    for w in COMMON_WORDS:
        idx = low.find(w)
        if idx != -1:
            flags.append(PatternFlag("dictionary", (idx, idx+len(w)), w))
    return flags

def _find_leet_words(pw: str):
    norm = _normalize_leet(pw)
    if norm == pw.lower():
        return []
    return _find_common_words(norm)

def _penalize(bits: float, flags):
    penalty = 0.0
    for f in flags:
        if f.type == "repeat":
            penalty += 10.0
        elif f.type == "repeat-chars":
            run = f.span[1]-f.span[0]
            penalty += max(0, (run-2))*2.0
        elif f.type == "sequence":
            L = f.span[1]-f.span[0]
            penalty += (L-2)*1.5
        elif f.type == "keyboard":
            L = f.span[1]-f.span[0]
            penalty += (L-3)*2.0
        elif f.type == "date":
            penalty += 18.0
        elif f.type == "dictionary":
            penalty += 18.0
    return max(0.0, bits - penalty)

def _score(entropy_bits: float) -> int:
    if entropy_bits < 28: return 0
    if entropy_bits < 36: return 1
    if entropy_bits < 60: return 2
    if entropy_bits < 128: return 3
    return 4

def _feedback(flags, length, categories, score):
    tips = []
    if length < 12:
        tips.append("Use 12+ characters; length boosts entropy.")
    if "digit" not in categories or "symbol" not in categories or "upper" not in categories:
        tips.append("Mix upper/lowercase, digits, and symbols to expand the character space.")
    for f in flags:
        if f.type == "date":
            tips.append("Avoid using dates; they are easy to guess.")
        elif f.type == "dictionary":
            tips.append("Avoid common words or names, even with substitutions (l33t).")
        elif f.type == "repeat" or f.type == "repeat-chars":
            tips.append("Do not repeat words or characters.")
        elif f.type == "sequence":
            tips.append("Avoid sequences like abcd or 1234.")
        elif f.type == "keyboard":
            tips.append("Avoid keyboard runs like qwerty or asdf.")
    if score < 3:
        tips.append("Consider a passphrase of 4-5 random words.")
    out = []
    for t in tips:
        if t not in out:
            out.append(t)
    return out

@dataclass
class PatternFlag:
    type: str
    span: tuple
    detail: str

def estimate(password: str) -> StrengthResult:
    if not password:
        return StrengthResult("", 0, [], 0.0, 0.0, 1.0, 0, [], ["Empty password."])
    cats = _char_categories(password)
    charset = 0
    if "lower" in cats: charset += 26
    if "upper" in cats: charset += 26
    if "digit" in cats: charset += 10
    if "symbol" in cats: charset += len(SYMBOLS)
    if charset == 0: charset = 26
    base_bits = len(password) * math.log2(charset)
    flags = []
    rep_sub = _find_repeated_substring(password)
    if rep_sub: flags.append(rep_sub)
    flags.extend(_find_repeated_chars(password))
    flags.extend(_find_sequences(password))
    flags.extend(_find_keyboard_runs(password))
    flags.extend(_find_dates(password))
    flags.extend(_find_common_words(password))
    flags.extend(_find_leet_words(password))
    adj_bits = _penalize(base_bits, flags)
    score = _score(adj_bits)
    guesses = 2.0 ** adj_bits
    tips = _feedback(flags, len(password), cats, score)
    return StrengthResult(
        password=password,
        length=len(password),
        categories=cats,
        base_entropy_bits=round(base_bits,2),
        adjusted_entropy_bits=round(adj_bits,2),
        guesses=guesses,
        score=score,
        flags=flags,
        feedback=tips
    )
