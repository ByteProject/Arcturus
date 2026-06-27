# test_lexer.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Lexer unit tests: token kinds, indentation, strings, UUID, and the
representative lexical errors from docs/01 section 16."""

import pytest

from arcturus import tokens as T
from arcturus.errors import ArcError
from arcturus.lexer import RawInterp, tokenize
from arcturus import ast


def kinds(src):
    return [t.kind for t in tokenize(src)]


def test_keywords_versus_names():
    toks = tokenize("room hallway\n")
    assert toks[0].kind == T.KW and toks[0].value == "room"
    # `hallway` is an ordinary identifier; direction and Cosmos names are NAMEs.
    assert toks[1].kind == T.NAME and toks[1].value == "hallway"


def test_cosmos_names_are_identifiers():
    # Directions and standard boolean properties are reserved by Cosmos, not the
    # core language, so they lex as NAME (docs/01 appendix A note).
    for word in ("north", "switchable", "lit", "container", "examine"):
        toks = tokenize(word + "\n")
        assert toks[0].kind == T.NAME, word


def test_number_token():
    toks = tokenize("release 1\n")
    assert toks[1].kind == T.NUMBER and toks[1].value == 1


def test_indentation_emits_indent_dedent():
    src = "room hallway\n    name \"Hallway\"\n"
    ks = kinds(src)
    assert T.INDENT in ks and T.DEDENT in ks
    # Structure: room hallway NEWLINE INDENT name STRING NEWLINE DEDENT EOF
    assert ks == [
        T.KW, T.NAME, T.NEWLINE,
        T.INDENT, T.NAME, T.STRING, T.NEWLINE,
        T.DEDENT, T.EOF,
    ]


def test_blank_and_comment_lines_do_not_indent():
    src = "room hallway\n\n    // a comment\n    name \"H\"\n"
    ks = kinds(src)
    # Only one INDENT and one DEDENT despite the blank and comment lines.
    assert ks.count(T.INDENT) == 1
    assert ks.count(T.DEDENT) == 1


def test_nested_dedents_at_eof():
    src = "kind k of thing\n    on x\n        say \"hi\"\n"
    ks = kinds(src)
    assert ks.count(T.INDENT) == 2
    assert ks.count(T.DEDENT) == 2
    assert ks[-1] == T.EOF


def test_comment_is_skipped():
    toks = tokenize("say \"hi\" // trailing\n")
    assert [t.kind for t in toks if t.kind not in (T.NEWLINE, T.EOF)] == [
        T.KW,
        T.STRING,
    ]


def test_string_whitespace_collapses_across_lines():
    src = 'desc "A damp cellar\n      of black stone."\n'
    toks = tokenize(src)
    string_tok = next(t for t in toks if t.kind == T.STRING)
    parts = string_tok.value
    assert len(parts) == 1
    assert isinstance(parts[0], ast.StringText)
    assert parts[0].text == "A damp cellar of black stone."


def test_string_escapes():
    toks = tokenize(r'say "a \"quote\" and \\ and \$ and \n done"' + "\n")
    parts = next(t for t in toks if t.kind == T.STRING).value
    text = "".join(p.text for p in parts if isinstance(p, ast.StringText))
    assert text == 'a "quote" and \\ and $ and \n done'


def test_escaped_newline_not_collapsed():
    toks = tokenize(r'say "line one\n   line two"' + "\n")
    parts = next(t for t in toks if t.kind == T.STRING).value
    text = "".join(p.text for p in parts if isinstance(p, ast.StringText))
    assert "\n" in text  # the escaped newline survives the whitespace collapse


def test_interpolation_captured_as_rawinterp():
    toks = tokenize('say "Score: ${score} now"\n')
    parts = next(t for t in toks if t.kind == T.STRING).value
    raws = [p for p in parts if isinstance(p, RawInterp)]
    assert len(raws) == 1
    assert raws[0].source == "score"


def test_uuid_is_single_token():
    toks = tokenize("UUID 7f3a9c20-1e44-4b8a-9d51-6c2f0b9a7e10\n")
    assert toks[1].kind == T.UUID
    assert toks[1].value == "7f3a9c20-1e44-4b8a-9d51-6c2f0b9a7e10"
    # The hyphens are not minus operators.
    assert not any(t.is_op("-") for t in toks)


def test_two_char_operators():
    toks = tokenize("if a <= b\n")
    assert any(t.is_op("<=") for t in toks)


def test_error_tabs_in_indentation():
    with pytest.raises(ArcError) as exc:
        tokenize("room r\n\tname \"R\"\n")
    assert "tab" in str(exc.value).lower()


def test_error_inconsistent_dedent():
    # Dedent to a column that matches no open indentation level.
    src = "room r\n        a 1\n    b 2\n"
    with pytest.raises(ArcError) as exc:
        tokenize(src)
    assert "indentation" in str(exc.value).lower()


def test_error_unterminated_string():
    with pytest.raises(ArcError):
        tokenize('say "never ends\n')


def test_error_invalid_escape():
    with pytest.raises(ArcError):
        tokenize(r'say "bad \q escape"' + "\n")


def test_error_unexpected_character():
    with pytest.raises(ArcError):
        tokenize("say @\n")
