# tokens.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Token kinds and the reserved-word set for the Arcturus lexer.

A token has a kind, a value, and a 1-based source position. Most kinds carry
their text in value; for KW the value is the keyword, for OP the operator
symbol, for NAME the identifier, for NUMBER an int, for STRING a list of string
parts (see ast.StringText / ast.StringInterp), and for UUID the uuid text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Token kinds.
NEWLINE = "NEWLINE"
INDENT = "INDENT"
DEDENT = "DEDENT"
EOF = "EOF"
NUMBER = "NUMBER"
STRING = "STRING"
UUID = "UUID"
NAME = "NAME"
KW = "KW"
OP = "OP"

# Reserved words of the core language (docs/01 appendix A). These lex as KW
# tokens. Direction names, the standard verb and kind names, and the grammar
# slot words `held`, `multi`, and `text` are reserved by Cosmos rather than the
# core language, so they lex as ordinary NAME identifiers and are recognized by
# context in the parser.
KEYWORDS = frozenset(
    {
        "game", "room", "thing", "kind", "verb", "of", "in", "on", "after",
        "block", "return", "global", "constant", "let", "change", "to", "now",
        "is", "not", "add", "remove", "from", "move", "say", "stop",
        "continue", "finish", "death", "if", "else", "while", "for", "each", "switch",
        "case", "and", "or", "holds", "when", "self", "player", "here", "noun",
        "second", "nothing", "true", "false", "list", "summon", "grains", "do",
        "title", "headline", "author", "release", "serial", "UUID", "start",
        # `mod` is the modulo operator (docs/01 section 9). `every` introduces a
        # recurring scheduled event (docs/02 section 13); both read as keyword
        # operators / statement heads.
        "mod", "every",
        # Conversation topics (docs/02 section 14): `topic` declares one on a
        # person; in a topic body `you` and `reply` are the player's and the
        # NPC's lines (auto-quoted, auto-attributed) and `reveal` / `hide` toggle
        # another topic's visibility by name.
        "topic", "you", "reply", "reveal", "hide",
    }
)

# Multi-character operators, tried before single characters.
TWO_CHAR_OPS = ("++", "--", "<=", ">=")
ONE_CHAR_OPS = frozenset("()+-*/=<>.,")


@dataclass
class Token:
    kind: str
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.column})"

    def is_kw(self, word: str) -> bool:
        return self.kind == KW and self.value == word

    def is_op(self, sym: str) -> bool:
        return self.kind == OP and self.value == sym
