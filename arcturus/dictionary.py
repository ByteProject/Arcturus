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
# Per-entry data bytes: [flags, action, reserved]. flags bit 7 marks a verb word
# and action is its action number, so the parser can resolve the verb.
_DATA_BYTES = 3
_ENTRY_LEN = 6 + _DATA_BYTES
_VERB_FLAG = 0x80


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


def _verb_actions(world: wm.World, action_numbers) -> dict:
    """word -> action number for single-word verbs. Multi-word verbs ("take
    off") are handled with the turn loop in B4.5e."""
    out: dict = {}
    if action_numbers is None:
        return out
    for verb in world.verbs:
        if not verb.grammar:
            continue
        action = action_numbers.get(verb.grammar[0].action)
        if action is None:
            continue
        for phrase in verb.words:
            tokens = phrase.lower().split()
            if len(tokens) == 1:
                out[tokens[0]] = action
    return out


def build(world: wm.World, action_numbers=None) -> tuple[bytes, dict]:
    """Return the dictionary bytes and a word -> offset (within the dictionary)
    map for the entry each word resolves to. Verb words carry their action in
    their data bytes when action_numbers is given."""
    words = collect_vocab(world)
    encoded = {w: zstring.encode_dict_word(w) for w in words}
    verb_action = _verb_actions(world, action_numbers)
    # Map each distinct encoded entry to a verb action, if any word for it is a verb.
    enc_action: dict[bytes, int] = {}
    for word, action in verb_action.items():
        enc_action[encoded[word]] = action
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
        out += enc
        if enc in enc_action:
            out += bytes([_VERB_FLAG, enc_action[enc] & 0xFF, 0])
        else:
            out += bytes(_DATA_BYTES)

    word_offset = {w: offset_of[encoded[w]] for w in words}
    return bytes(out), word_offset
