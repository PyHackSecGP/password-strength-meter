import pytest
from pwstrength.meter import estimate

def test_empty():
    r = estimate("")
    assert r.score == 0
    assert "Empty password." in r.feedback

def test_common_word_and_leet():
    r = estimate("p@ssw0rd")
    types = [f.type for f in r.flags]
    assert "dictionary" in types
    assert r.score <= 2

def test_date_detection():
    r = estimate("Summer2024-07-15!")
    assert any(f.type=="date" for f in r.flags)

def test_sequence_and_keyboard():
    r = estimate("qwerty1234")
    types = [f.type for f in r.flags]
    assert "keyboard" in types and "sequence" in types
    assert r.score in (0,1)

def test_repeat_substring():
    r = estimate("abcabcabc")
    assert any(f.type=="repeat" for f in r.flags)

def test_repeat_chars():
    r = estimate("AAAaaaa!!!!")
    assert any(f.type=="repeat-chars" for f in r.flags)
