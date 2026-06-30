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
# Per-entry data bytes: [flags, b1, b2]. flags bit 7 marks a verb word (b1 = its
# action number, b2 = its noun arity: 0 intransitive, 1 one noun, 2 two nouns);
# flags bit 6 marks a direction word (b1 = the go action, b2 = the direction's
# property number); flags bit 5 marks a verb particle (b1 = its id), so the parser
# can resolve all three.
_DATA_BYTES = 3
_ENTRY_LEN = 6 + _DATA_BYTES
_VERB_FLAG = 0x80
_DIR_FLAG = 0x40
_PARTICLE_FLAG = 0x20
_SCENERY_FLAG = 0x10  # a grain word: data byte 1 = grain id (index+1), byte 2 = owner object
# flags bit 3 marks a grammar preposition (the "to"/"with" joining two noun
# slots), so the parser knows where the first noun phrase ends and the second
# begins. Words already flagged otherwise (on/in are a particle/direction) are
# left as they are; the parser treats any flagged word as a phrase boundary.
_PREPOSITION_FLAG = 0x08

# Verb particles for multi-word verbs (switch on, take off). English; moves into
# the language pack when localized. up/down/in/out are omitted (they are
# direction words); the examples only need on/off.
_PARTICLE_WORDS = {"on": 1, "off": 2}

# English direction words (with abbreviations) mapped to their canonical
# direction property. This vocabulary is English; it moves into the language
# pack (spanish.granule) when localized. The parser turns a direction word into
# the go action plus the direction's property number (see english.prelude).
_DIRECTION_WORDS = {
    "north": "north", "n": "north", "south": "south", "s": "south",
    "east": "east", "e": "east", "west": "west", "w": "west",
    "northeast": "northeast", "ne": "northeast",
    "northwest": "northwest", "nw": "northwest",
    "southeast": "southeast", "se": "southeast",
    "southwest": "southwest", "sw": "southwest",
    "up": "up", "u": "up", "down": "down", "d": "down",
    "in": "in", "out": "out",
}


def collect_vocab(world: wm.World) -> set:
    """Every matchable word in the program, lowercased."""
    from . import objects  # local import avoids a module cycle

    words: set = set()
    for verb in world.verbs:
        for phrase in verb.words:
            # A multi-word verb ("take off") contributes each of its tokens.
            for token in phrase.lower().split():
                words.add(token)
        # Literal prepositions in the grammar (the "on" of put noun on noun).
        for line in verb.grammar:
            for it in line.items:
                if isinstance(it, ast.Word):
                    words.add(it.text.lower())
    for obj in world.objects.values():
        # An object's matchable vocabulary (explicit words plus its name words),
        # computed the same way the object table emits it.
        words.update(objects.object_words(objects._effective_props(world, obj), obj.category == "room"))
        for grain in obj.grains:
            for gw in grain.words:
                words.add(gw.lower())
        # A person's topic match-words (the ask/tell words) must be in the
        # dictionary so the topic table's word entries can be backpatched.
        for topic in obj.topics:
            for tw in topic.words:
                words.add(tw.lower())
    for kind in world.kinds.values():
        for grain in kind.grains:
            for gw in grain.words:
                words.add(gw.lower())
    return words


def _preposition_words(world: wm.World) -> set:
    """Literal preposition words in verb grammar (the "to" of give noun to noun),
    lowercased, so the parser can mark the boundary between two noun phrases."""
    out: set = set()
    for verb in world.verbs:
        for line in verb.grammar:
            for it in line.items:
                if isinstance(it, ast.Word):
                    out.add(it.text.lower())
    return out


def _verb_arity(world: wm.World) -> dict:
    """Single-word verb word -> how many noun slots its richest grammar line takes
    (capped at 2). 0 marks an intransitive verb (jump, look, wait): the parser
    uses this to reject a command that piles words onto a verb with no slot for
    them, instead of silently dropping them. 2 marks a two-noun verb (put noun on
    noun), so the parser resolves a second noun."""
    out: dict = {}
    for verb in world.verbs:
        slots = max(
            (sum(1 for it in line.items if isinstance(it, ast.Slot)) for line in verb.grammar),
            default=0,
        )
        if slots > 2:
            slots = 2
        for phrase in verb.words:
            tokens = phrase.lower().split()
            if len(tokens) == 1:
                out[tokens[0]] = max(out.get(tokens[0], 0), slots)
    return out


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


def build(world: wm.World, action_numbers=None, direction_props=None, scenery=None) -> tuple[bytes, dict]:
    """Return the dictionary bytes and a word -> offset (within the dictionary)
    map for the entry each word resolves to. Verb words carry their action,
    direction words carry the go action and the direction property, and scenery
    (grain) words (from `scenery`: word -> (grain id, owner object)) carry their
    grain, in their data bytes."""
    words = set(collect_vocab(world))
    if direction_props:
        words |= set(direction_props)
    words |= set(_PARTICLE_WORDS)
    encoded = {w: zstring.encode_dict_word(w) for w in words}
    # Map each distinct encoded entry to its three data bytes.
    enc_data: dict[bytes, bytes] = {}
    arity = _verb_arity(world)
    for word, action in _verb_actions(world, action_numbers).items():
        b2 = arity.get(word, 0)  # data byte 2: noun arity (0 intransitive, 1, or 2)
        enc_data[encoded[word]] = bytes([_VERB_FLAG, action & 0xFF, b2])
    if direction_props and action_numbers and "go" in action_numbers:
        go = action_numbers["go"]
        for word, prop in direction_props.items():
            enc_data[encoded[word]] = bytes([_DIR_FLAG, go & 0xFF, prop & 0xFF])
    for word, pid in _PARTICLE_WORDS.items():
        enc_data[encoded[word]] = bytes([_PARTICLE_FLAG, pid, 0])
    if scenery:
        for word, (gid, owner) in scenery.items():
            enc_data[encoded[word]] = bytes([_SCENERY_FLAG, gid & 0xFF, owner & 0xFF])
    # Prepositions last, and only where nothing else claimed the word: on/in are
    # already a particle/direction, and the parser treats those as boundaries too.
    for word in _preposition_words(world):
        enc = encoded[word]
        if enc not in enc_data:
            enc_data[enc] = bytes([_PREPOSITION_FLAG, 0, 0])
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
        out += enc_data.get(enc, bytes(_DATA_BYTES))

    word_offset = {w: offset_of[encoded[w]] for w in words}
    return bytes(out), word_offset


def direction_props(layout) -> dict:
    """word -> direction property number, for the words whose canonical
    direction is a property in this program's object table."""
    out: dict = {}
    for word, canonical in _DIRECTION_WORDS.items():
        if canonical in layout.prop_number:
            out[word] = layout.prop_number[canonical]
    return out
