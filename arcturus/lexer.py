# lexer.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

r"""The Arcturus lexer.

Turns UTF-8 source into a flat token stream with explicit NEWLINE, INDENT, and
DEDENT tokens, in the spirit of Python's tokenizer. The lexer owns:

- indentation: an indent stack drives INDENT and DEDENT; mixing tabs and spaces
  or an inconsistent dedent is a compile error (docs/01 section 2);
- significant newlines: one statement or declaration per logical line;
- strings: double-quoted, may span physical lines, runs of literal whitespace
  collapse to a single space, with \" \\ \$ \n escapes and ${ } interpolation
  whose raw source is captured for the parser (docs/01 section 16);
- UUID literals: the 8-4-4-4-12 hex form, lexed whole so its hyphens are never
  read as minus operators;
- numbers, identifiers and keywords, and operators.

Blank lines and comment-only lines do not affect indentation. Physical
newlines inside a string do not produce NEWLINE or indentation tokens.
"""

from __future__ import annotations

import re

from .errors import ArcError
from . import tokens as T
from .tokens import Token

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_NUMBER_RE = re.compile(r"[0-9]+")

# Escape character -> the literal character it produces.
_ESCAPES = {'"': '"', "\\": "\\", "$": "$", "n": "\n"}


# A captured interpolation: the raw source between ${ and }, with its position,
# parsed later by the parser into an expression.
class RawInterp:
    __slots__ = ("source", "line", "column")

    def __init__(self, source: str, line: int, column: int) -> None:
        self.source = source
        self.line = line
        self.column = column


class Lexer:
    def __init__(self, src: str, filename: str = "<source>") -> None:
        self.src = src
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.indents = [0]
        self.at_line_start = True

    # -- low-level cursor helpers ------------------------------------------

    def _error(self, message: str, line: int | None = None, col: int | None = None):
        return ArcError(
            message,
            self.line if line is None else line,
            self.col if col is None else col,
            self.filename,
        )

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def _advance(self) -> str:
        c = self.src[self.pos]
        self.pos += 1
        if c == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def _emit(self, kind: str, value, line: int, col: int) -> None:
        self.tokens.append(Token(kind, value, line, col))

    # -- main loop ---------------------------------------------------------

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.src):
            if self.at_line_start:
                self._handle_line_start()
                continue
            self._scan_token()
        self._finish()
        return self.tokens

    def _finish(self) -> None:
        # A trailing line without a newline still ends a logical line.
        if self.tokens and self.tokens[-1].kind not in (T.NEWLINE, T.INDENT, T.DEDENT):
            self._emit(T.NEWLINE, "\n", self.line, self.col)
        while len(self.indents) > 1:
            self.indents.pop()
            self._emit(T.DEDENT, None, self.line, self.col)
        self._emit(T.EOF, None, self.line, self.col)

    # -- indentation -------------------------------------------------------

    def _handle_line_start(self) -> None:
        indent = 0
        saw_space = False
        saw_tab = False
        start_col = self.col
        while self._peek() in (" ", "\t"):
            if self._peek() == " ":
                saw_space = True
            else:
                saw_tab = True
            indent += 1
            self._advance()

        c = self._peek()
        # Blank or comment-only lines do not affect indentation.
        if c == "" or c == "\n":
            if c == "\n":
                self._advance()
            return
        if c == "/" and self._peek(1) == "/":
            while self._peek() not in ("", "\n"):
                self._advance()
            return

        if saw_tab:
            raise self._error(
                "tabs are not allowed in indentation; use spaces "
                "(docs/01 section 2)",
                self.line,
                start_col,
            )
        _ = saw_space  # spaces are the only permitted indentation unit

        top = self.indents[-1]
        if indent > top:
            self.indents.append(indent)
            self._emit(T.INDENT, None, self.line, self.col)
        elif indent < top:
            while self.indents[-1] > indent:
                self.indents.pop()
                self._emit(T.DEDENT, None, self.line, self.col)
            if self.indents[-1] != indent:
                raise self._error(
                    "inconsistent indentation: this line does not match any "
                    "outer indentation level",
                    self.line,
                    start_col,
                )
        self.at_line_start = False

    # -- token scanning ----------------------------------------------------

    def _scan_token(self) -> None:
        c = self._peek()

        if c == "\n":
            line, col = self.line, self.col
            self._advance()
            self._emit(T.NEWLINE, "\n", line, col)
            self.at_line_start = True
            return

        if c in (" ", "\t"):
            self._advance()
            return

        if c == "/" and self._peek(1) == "/":
            while self._peek() not in ("", "\n"):
                self._advance()
            return

        if c == '"':
            self._read_string()
            return

        # UUID before number and name, since it may start with a digit or a
        # letter and must win over both.
        m = _UUID_RE.match(self.src, self.pos)
        if m and not self._is_name_char(self.src[m.end():m.end() + 1]):
            line, col = self.line, self.col
            self._consume(m.end() - self.pos)
            self._emit(T.UUID, m.group(0), line, col)
            return

        if c.isdigit():
            self._read_number()
            return

        if c.isalpha():
            self._read_name()
            return

        self._read_operator()

    @staticmethod
    def _is_name_char(c: str) -> bool:
        return bool(c) and (c.isalnum() or c == "_")

    def _consume(self, n: int) -> None:
        for _ in range(n):
            self._advance()

    def _read_number(self) -> None:
        line, col = self.line, self.col
        m = _NUMBER_RE.match(self.src, self.pos)
        text = m.group(0)
        self._consume(len(text))
        self._emit(T.NUMBER, int(text), line, col)

    def _read_name(self) -> None:
        line, col = self.line, self.col
        m = _NAME_RE.match(self.src, self.pos)
        text = m.group(0)
        self._consume(len(text))
        if text in T.KEYWORDS:
            self._emit(T.KW, text, line, col)
        else:
            self._emit(T.NAME, text, line, col)

    def _read_operator(self) -> None:
        line, col = self.line, self.col
        two = self.src[self.pos:self.pos + 2]
        if two in T.TWO_CHAR_OPS:
            self._consume(2)
            self._emit(T.OP, two, line, col)
            return
        c = self._peek()
        if c in T.ONE_CHAR_OPS:
            self._advance()
            self._emit(T.OP, c, line, col)
            return
        raise self._error(f"unexpected character {c!r}", line, col)

    # -- strings -----------------------------------------------------------

    def _read_string(self) -> None:
        line, col = self.line, self.col
        self._advance()  # opening quote
        # items: ('raw', ch) collapsible literal source, ('lit', ch) escaped
        # literal, ('interp', RawInterp).
        items: list[tuple] = []
        while True:
            c = self._peek()
            if c == "":
                raise self._error("unterminated string literal", line, col)
            if c == '"':
                self._advance()
                break
            if c == "\\":
                esc = self._peek(1)
                if esc not in _ESCAPES:
                    raise self._error(
                        f"invalid escape \\{esc} in string", self.line, self.col
                    )
                items.append(("lit", _ESCAPES[esc]))
                self._advance()
                self._advance()
                continue
            if c == "$" and self._peek(1) == "{":
                items.append(("interp", self._read_interp()))
                continue
            items.append(("raw", c))
            self._advance()

        parts = _finalize_parts(items)
        self._emit(T.STRING, parts, line, col)

    def _read_interp(self) -> RawInterp:
        iline, icol = self.line, self.col
        self._advance()  # $
        self._advance()  # {
        buf: list[str] = []
        depth = 1
        while True:
            c = self._peek()
            if c == "":
                raise self._error(
                    "unterminated interpolation ${...} in string", iline, icol
                )
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    self._advance()
                    break
            buf.append(c)
            self._advance()
        return RawInterp("".join(buf).strip(), iline, icol)


def _finalize_parts(items: list[tuple]):
    """Convert raw string items into StringText / StringInterp parts, collapsing
    runs of unescaped whitespace (including line breaks) to a single space.
    Escaped characters, including an escaped newline, are preserved as written.
    """
    from . import ast

    parts: list = []
    textbuf: list[str] = []
    pending_ws = False

    def flush_text():
        if textbuf:
            parts.append(ast.StringText("".join(textbuf)))
            textbuf.clear()

    for it in items:
        if it[0] == "interp":
            if pending_ws:
                textbuf.append(" ")
                pending_ws = False
            flush_text()
            parts.append(it[1])  # RawInterp; resolved by the parser
        else:
            kind, ch = it
            if kind == "raw" and ch in " \t\r\n":
                pending_ws = True
            else:
                if pending_ws:
                    textbuf.append(" ")
                    pending_ws = False
                textbuf.append(ch)
    if pending_ws:
        textbuf.append(" ")
    flush_text()
    return parts


def tokenize(src: str, filename: str = "<source>") -> list[Token]:
    return Lexer(src, filename).tokenize()
