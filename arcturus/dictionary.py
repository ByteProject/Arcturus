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
from . import prelude
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
# A grain word: data bytes 1 and 2 hold the ADDRESS of the word's grain chain, a
# static table of (grain id, owner object) word pairs terminated by a zero id.
# One word can serve several grains in several rooms; the parser walks the chain
# and answers with the grain whose owner is in scope (docs/01 section 14).
_SCENERY_FLAG = 0x10
# A pronoun word: data byte 1 holds the canonical role id (prelude
# _PRONOUN_ROLES: it 1, him 2, her 3, them 4). The noun matcher resolves it to
# the role's remembered referent. Deliberately NOT a phrase boundary: "put coin
# in it" must bind "it" as the second noun, so is_separator exempts this flag.
_PRONOUN_FLAG = 0x04
# A chain word ("and", "then", the comma): it ends the current command and the
# words after it run as the next command once this one succeeds (docs/02 8b).
# The words come from the language layer's `chain` declarations.
_CHAIN_FLAG = 0x02
# An all-word ("all", "everything", from the takeall granule's `all`
# declaration): the parser hands the command to the granule's expander, which
# runs the action once per object within reach (TAKE ALL, DROP ALL).
_ALL_FLAG = 0x01
# flags bit 3 marks a grammar preposition (the "to"/"with" joining two noun
# slots), so the parser knows where the first noun phrase ends and the second
# begins. Words already flagged otherwise (on/in are a particle/direction) are
# left as they are; the parser treats any flagged word as a phrase boundary.
_PREPOSITION_FLAG = 0x08

# Verb particles for multi-word verbs (switch on, schliess auf). The WORDS are no
# longer hardcoded: a language pack declares them (`particle on "on"` in English,
# `particle on "an", "ein"` in German) and they arrive in world.particles as
# word -> role. The canonical role -> id table is prelude._PARTICLE_ROLES, shared
# with the parser's compound() block, which reads the id.


def _pronoun_words(world: wm.World) -> dict:
    """word -> pronoun role id, from the language layer's `pronoun` declarations."""
    return {w: prelude._PRONOUN_ROLES[role] for w, role in world.pronouns.items()
            if role in prelude._PRONOUN_ROLES}


def _particle_words(world: wm.World) -> dict:
    """word -> particle id, from the language layer's `particle` declarations."""
    return {w: prelude._PARTICLE_ROLES[role] for w, role in world.particles.items()
            if role in prelude._PARTICLE_ROLES}

# Direction words are no longer hardcoded here: they are declared in the language
# layer with `direction north "north", "n"` (english.prelude) and collected into
# world.directions, so a language pack localizes them. direction_props() below
# turns them into dictionary entries (the go action plus the direction property).


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
    (grain) words (from `scenery`: word -> chain address) carry the address of
    their grain chain, in their data bytes."""
    words = set(collect_vocab(world))
    if direction_props:
        words |= set(direction_props)
    particle_words = _particle_words(world)
    words |= set(particle_words)
    pronoun_words = _pronoun_words(world)
    words |= set(pronoun_words)
    chain_words = set(world.chain_words)
    words |= chain_words
    all_words = set(world.all_words)
    words |= all_words
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
    for word, pid in particle_words.items():
        enc_data[encoded[word]] = bytes([_PARTICLE_FLAG, pid, 0])
    for word, rid in pronoun_words.items():
        enc_data[encoded[word]] = bytes([_PRONOUN_FLAG, rid, 0])
    for word in chain_words:
        enc_data[encoded[word]] = bytes([_CHAIN_FLAG, 0, 0])
    for word in all_words:
        enc_data[encoded[word]] = bytes([_ALL_FLAG, 0, 0])
    if scenery:
        for word, chain_addr in scenery.items():
            enc_data[encoded[word]] = bytes(
                [_SCENERY_FLAG, (chain_addr >> 8) & 0xFF, chain_addr & 0xFF]
            )
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


def direction_props(layout, world) -> dict:
    """word -> direction property number, for the words whose direction property is
    in this program's object table. The words come from the language layer's
    `direction` declarations (world.directions), so a language pack localizes
    them; the property names are fixed."""
    out: dict = {}
    for word, canonical in world.directions.items():
        if canonical in layout.prop_number:
            out[word] = layout.prop_number[canonical]
    return out
