# errors.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Compile-time diagnostics.

Every error raised by the lexer, parser, and later semantic analysis is an
ArcError carrying a source position, so the compiler can report a precise
location (docs/01 section 17). Errors are surfaced at compile time, never as a
surprise at run time.
"""

from __future__ import annotations


class ArcError(Exception):
    """A compile-time error with an optional source position.

    line and column are 1-based; column is the character offset within the
    line. filename defaults to the unit being compiled.
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        filename: str = "<source>",
    ) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(self.format())

    def format(self) -> str:
        if self.line is None:
            return f"{self.filename}: error: {self.message}"
        if self.column is None:
            return f"{self.filename}:{self.line}: error: {self.message}"
        return f"{self.filename}:{self.line}:{self.column}: error: {self.message}"
