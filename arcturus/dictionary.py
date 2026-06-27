# dictionary.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Z-machine version 5 dictionary.

Collects every word the parser might match (verb words, object `words`, and
grain words) and lays them out as a dictionary the interpreter's built-in
tokenizer reads (standard 1.1, section 13): a header of word separators, the
entry length, and the entry count, then the entries themselves. Each entry is a
6-byte Z-encoded word (truncated to nine Z-characters) followed by data bytes
reserved for the parser (B4.5). Entries are sorted by their encoded bytes so the
tokenizer can binary-search; words that share a nine-character prefix collapse
to one entry.

build() also returns a word -> byte-offset map so a later stage can turn each
object's vocabulary into dictionary addresses.
"""

from __future__ import annotations

from . import ast
from . import worldmodel as wm
from . import zstring

# Characters that are tokens in their own right (so "lamp,box" splits).
_SEPARATORS = [ord("."), ord(",")]
_DATA_BYTES = 3  # per-entry bytes reserved for parser flags (zero for now)
_ENTRY_LEN = 6 + _DATA_BYTES


def collect_vocab(world: wm.World) -> set:
    """Every matchable word in the program, lowercased."""
    words: set = set()
    for verb in world.verbs:
        for phrase in verb.words:
            # A multi-word verb ("take off") contributes each of its tokens.
            for token in phrase.lower().split():
                words.add(token)
    for obj in world.objects.values():
        wd = obj.props.get("words")
        if wd is not None and wd.form == ast.PROP_VALUE:
            for v in wd.values:
                if isinstance(v, ast.Name):
                    words.add(v.ident.lower())
        for grain in obj.grains:
            for gw in grain.words:
                words.add(gw.lower())
    for kind in world.kinds.values():
        for grain in kind.grains:
            for gw in grain.words:
                words.add(gw.lower())
    return words


def build(world: wm.World) -> tuple[bytes, dict]:
    """Return the dictionary bytes and a word -> offset (within the dictionary)
    map for the entry each word resolves to."""
    words = collect_vocab(world)
    encoded = {w: zstring.encode_dict_word(w) for w in words}
    # Distinct entries, sorted by encoded bytes for binary search.
    distinct = sorted(set(encoded.values()))

    out = bytearray()
    out.append(len(_SEPARATORS))
    out += bytes(_SEPARATORS)
    out.append(_ENTRY_LEN)
    out += bytes([(len(distinct) >> 8) & 0xFF, len(distinct) & 0xFF])

    offset_of: dict[bytes, int] = {}
    for enc in distinct:
        offset_of[enc] = len(out)
        out += enc + bytes(_DATA_BYTES)

    word_offset = {w: offset_of[encoded[w]] for w in words}
    return bytes(out), word_offset
