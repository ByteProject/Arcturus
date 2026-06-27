# astdump.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A deterministic textual dump of the AST, for `arcc --dump-ast` and as a
stable form for golden tests."""

from __future__ import annotations

import dataclasses


def dump(node, indent: int = 0) -> str:
    lines: list[str] = []
    _dump(node, indent, lines)
    return "\n".join(lines)


def _dump(node, indent: int, out: list[str]) -> None:
    pad = "  " * indent
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        out.append(f"{pad}{type(node).__name__}")
        for f in dataclasses.fields(node):
            value = getattr(node, f.name)
            _dump_field(f.name, value, indent + 1, out)
    elif isinstance(node, list):
        if not node:
            out.append(f"{pad}[]")
        for item in node:
            _dump(item, indent, out)
    else:
        out.append(f"{pad}{node!r}")


def _dump_field(name: str, value, indent: int, out: list[str]) -> None:
    pad = "  " * indent
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        out.append(f"{pad}{name}:")
        _dump(value, indent + 1, out)
    elif isinstance(value, list):
        if not value:
            out.append(f"{pad}{name}: []")
        else:
            out.append(f"{pad}{name}:")
            for item in value:
                _dump(item, indent + 1, out)
    else:
        out.append(f"{pad}{name}: {value!r}")
