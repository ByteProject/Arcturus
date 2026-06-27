# test_zstring.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Z-string encoder tests: known encodings, the end bit, and round-trips
through the decoder for lowercase, uppercase, punctuation, newline, and a
ZSCII-escape character."""

import pytest

from arcturus import zstring


@pytest.mark.parametrize(
    "text",
    [
        "hello",
        "Hello, World!",
        "The Brass Lantern",
        "abc\ndef",
        "UPPER lower 12345 .,!?()",
        "tab\there",  # tab needs the ZSCII escape
        "x",
        "",
    ],
)
def test_round_trip(text):
    assert zstring.decode(zstring.encode(text)) == text


def test_known_encoding_of_a():
    # 'a' is Z-char 6, padded with two shift-5s: (6<<10)|(5<<5)|5 = 0x18A5,
    # with the end bit set on the high byte -> 0x98A5.
    assert zstring.encode("a") == bytes([0x98, 0xA5])


def test_end_bit_set_on_last_word():
    enc = zstring.encode("a longer string of text")
    assert len(enc) % 2 == 0
    assert enc[-2] & 0x80  # end bit on the final word's high byte
    # and on no earlier word
    for i in range(0, len(enc) - 2, 2):
        assert not (enc[i] & 0x80)


def test_string_length_is_word_aligned():
    for s in ("", "a", "ab", "abc", "abcd"):
        assert len(zstring.encode(s)) % 2 == 0
