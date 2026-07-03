# prelude.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The standard environment that semantic analysis resolves against.

The standard library, Cosmos, supplies the standard kinds, properties,
directions, actions, and builtin references that a game uses without declaring
them (docs/02 appendix A). Cosmos is written in Arcturus and will be compiled
from its `.prelude` source in a later milestone (B4). Until then, this module
provides the same interface as data, so semantic analysis and the world model
can be built and checked now.

This is the one place that mirrors the Cosmos vocabulary, kept isolated and
spec-derived (docs/02 appendix A). Semantic analysis takes the environment as
an argument rather than reaching for it directly, so when Cosmos source is
compiled in B4 the analyzer can run over the real prelude AST unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Property value types. A property's type is fixed program-wide by its declared
# default (docs/01 section 6).
T_BOOL = "bool"
T_NUMBER = "number"
T_TEXT = "text"
T_OBJECT = "object"
T_LIST = "list"
T_BLOCK = "block"

ALL_TYPES = frozenset({T_BOOL, T_NUMBER, T_TEXT, T_OBJECT, T_LIST, T_BLOCK})


@dataclass
class StdProp:
    name: str
    type: str


@dataclass
class StdKind:
    name: str
    parent: Optional[str]


@dataclass
class StdBuiltin:
    name: str
    type: str  # T_OBJECT for object references, T_NUMBER for counters, ...


@dataclass
class Environment:
    """The names a game may use without declaring them. Semantic analysis is
    parameterized by this so nothing about Cosmos is hardcoded in the analyzer
    itself."""

    kinds: dict[str, StdKind] = field(default_factory=dict)
    properties: dict[str, StdProp] = field(default_factory=dict)
    directions: list[str] = field(default_factory=list)
    actions: set[str] = field(default_factory=set)
    events: set[str] = field(default_factory=set)
    builtins: dict[str, StdBuiltin] = field(default_factory=dict)
    objects: dict[str, str] = field(default_factory=dict)  # name -> kind

    def is_direction(self, name: str) -> bool:
        return name in self.directions


# Standard kinds and their parent chain (docs/02 section 10, appendix A).
_STD_KINDS = [
    StdKind("thing", None),
    StdKind("room", None),
    StdKind("container", "thing"),
    StdKind("supporter", "thing"),
    StdKind("door", "thing"),
    StdKind("character", "thing"),
]

# Standard boolean properties become attribute candidates (docs/02 appendix A).
_STD_BOOL_PROPS = [
    "fixed", "scenery", "hidden", "concealed", "wearable", "worn", "lit",
    "edible", "named", "switchable", "openable", "open", "lockable", "locked",
    "visited",
    # A see-through container: you can see and reach its contents even when it is
    # closed (a glass jar). Our equivalent of Inform's `transparent`. An open or
    # `clear` container puts its contents in scope; a closed opaque one does not.
    "clear",
    # Set once the player has been shown an object (a content of an open container,
    # something taken or examined). A closed opaque container still lists the
    # contents the player has `seen`, so the player is not made to forget what they
    # put away; contents never seen stay hidden until the box is opened.
    "seen",
    # Set the first time the player takes an object; while clear, the object
    # shows its `intro` text in a room description instead of the plain listing.
    "moved",
    # An animate agent: people, animals, robots, AIs. The conversation and give
    # verbs apply only to the animate; the character kind sets it by default, and
    # animate objects refuse being taken.
    "animate",
    # Set when the indefinite article should be "an" instead of "a". The compiler
    # derives it from the object's name (a vowel-initial name -> "an") unless the
    # author sets it explicitly, so "an apple" / "a coin" come out right with no
    # author work; declare `an` (or `an false`) only for the odd exception (an
    # hour, a unicorn).
    "an",
    # Grammatical gender for languages that need it (Spanish la/una, and the basis a
    # language pack reads for its articles). Masculine is the default; the compiler
    # derives `feminine` from a name ending in -a unless the author sets it, so
    # "la lampara" / "el libro" come out right, with an override for the exceptions
    # (el mapa, la mano). English ignores it.
    "feminine",
    # The third gender, for a language with three (German der/die/das). German has
    # no reliable spelling rule, so the author declares the article on the object
    # (der / die / das) and the compiler maps it: die -> feminine, das -> neutral,
    # der -> masculine (neither bit). Masculine is still the default, so a masculine
    # noun needs nothing. English and Spanish ignore `neutral`.
    "neutral",
]

# The three German definite articles, written as bare object declarations to state
# an object's gender the way an author naturally thinks of it ("das Buch"), instead
# of an abstract attribute. The parser maps them to the gender attributes above.
# Reserved project-wide so they always mean gender; a non-German game simply never
# writes them.
_GENDER_ARTICLES = {
    "der": None,        # masculine: the default, so no bit is set
    "die": "feminine",
    "das": "neutral",
}

# Canonical verb-particle roles and their ids. A language pack declares which
# words fill each role (`particle on "an", "ein"`), and the parser's compound()
# block reads the id to remap a base verb (switch + on -> switch_on, schliess +
# auf -> unlock). on/off cover the switch family; auf/zu are the German separable
# lock words ("schliess die Tuer auf" / "... zu"). The id is what compound() tests,
# so this table is the shared contract between the dictionary and the language
# layer; keep the ids stable.
_PARTICLE_ROLES = {"on": 1, "off": 2, "auf": 3, "zu": 4}

# The Z-machine colour numbers (Standard 1.1 section 8.3.1), as the author-facing
# names of the zcolor statement and the say.<colour> form. "default" asks the
# interpreter for its own default colour.
# Canonical pronoun roles and their ids: the compiler contract the dictionary
# writes and the language layer's blocks read (the same shape as the particle
# roles). A pack maps its own words onto the slots (`pronoun her "sie"` in
# German, where grammatical gender rules) and its note_pronouns block decides
# which slot a resolved noun lands in.
_PRONOUN_ROLES = {"it": 1, "him": 2, "her": 3, "them": 4}

_ZCOLOURS = {
    "default": 1, "black": 2, "red": 3, "green": 4, "yellow": 5,
    "blue": 6, "magenta": 7, "cyan": 8, "white": 9,
}

# Standard value properties and their types.
_STD_VALUE_PROPS = {
    "name": T_TEXT,
    "desc": T_TEXT,
    # The object's initial appearance: shown in the room description while the
    # object sits untouched in place (until it has `moved`), in place of the
    # plain "You can see X here." Useful for set dressing and static objects.
    "intro": T_TEXT,
    # Article overrides, for the objects derivation cannot reach: `article` is
    # what ${the x} prints ("las" for las tijeras, "el" for el agua), and
    # `indefinite` what ${a x} prints ("unas"; English "some" for mass nouns).
    # Unset, the language layer derives as usual.
    "article": T_TEXT,
    "indefinite": T_TEXT,
    "words": T_LIST,
    "capacity": T_NUMBER,
    # The object that locks and unlocks a lockable thing (a door or chest). Named
    # `unseal_with` rather than `key` so the common vocabulary word "key" stays
    # free for a key object's own `words`.
    "unseal_with": T_OBJECT,
    # The extra rooms a fixed object is in scope in, beyond its tree location (the
    # `spans` sugar, docs/01 section 5). Emitted as an array of room object numbers
    # like `words`; scope reads it. Authors write `spans a, b` or `in a, b`.
    "spans": T_LIST,
    # Conversation topics (docs/02 section 14). Authors never write this; the
    # compiler synthesizes it from a character's `topic` declarations as the address
    # of that character's runtime topic table (objects.py emits the table, the
    # conversation granules walk it). T_LIST so it is a slot holding a pointer.
    "topics": T_LIST,
}

# Direction properties on a room, each an object defaulting to nothing.
_DIRECTIONS = [
    "north", "south", "east", "west", "northeast", "northwest", "southeast",
    "southwest", "up", "down", "in", "out",
]

# Standard action names a verb grammar line can produce (docs/02 appendix A).
_STD_ACTIONS = {
    "look", "examine", "search", "take", "drop", "put", "wear", "take_off",
    "inventory", "go", "enter", "exit", "open", "close", "lock", "unlock",
    "switch_on", "switch_off", "push", "pull", "turn", "give", "show", "talk",
    "wait", "again", "insert",
    # The rest of the standard verb set (docs/verb-set.md). These exist as verbs
    # in the language layer, but the names must be known here too, so a handler
    # (`on touch`) or a grain line (`touch "stone"`) checks out even when a
    # program is analyzed without Cosmos (--no-cosmos, the bare IR tests).
    "touch", "smell", "listen", "taste", "eat", "drink", "attack", "climb",
    "kiss", "jump", "sing",
    # The meta verbs, same reasoning.
    "quit", "restart", "save", "restore", "undo", "oops", "score", "xyzzy",
}

# Engine-fired events, plus the catch-all (docs/01 section 12, docs/02).
_CORE_EVENTS = {"start", "enter", "each_turn", "other"}

# Builtin references usable in any handler or block (docs/02 section 2).
_BUILTINS = {
    "player": T_OBJECT,
    "here": T_OBJECT,
    "self": T_OBJECT,
    "noun": T_OBJECT,
    "second": T_OBJECT,
    "turns": T_NUMBER,
    "score": T_NUMBER,
    "max_score": T_NUMBER,
    "way": T_NUMBER,  # the chosen direction's property number, set by the parser
    # The pending-paragraph flag the print layer flushes as one blank line before
    # the next text. Library-internal: upper-window drawing holds it across a
    # draw (a bar or menu print must not consume the transcript's break).
    "par_pending": T_NUMBER,
    # The pronoun referents, one per canonical role (docs/02 section 8a): what
    # "it", "him", "her", and "them" currently mean. The language layer's
    # note_pronouns fills them as nouns resolve; scope_match reads them back.
    "pron_it": T_OBJECT,
    "pron_him": T_OBJECT,
    "pron_her": T_OBJECT,
    "pron_them": T_OBJECT,
    "grain": T_NUMBER,  # the matched scenery grain (id+1), set by the parser
    "parse_fault": T_NUMBER,  # set by the parser when a named object is out of scope
    "meta_turn": T_NUMBER,  # set by a meta verb so the loop skips the turn pulse
    # The previous non-meta command, remembered so "again" can replay it.
    "last_act": T_NUMBER,
    "last_noun": T_OBJECT,
    "last_second": T_OBJECT,
    "last_way": T_NUMBER,
    "last_grain": T_NUMBER,
    # oops correction: a flag and the offending word's parse-buffer index.
    "oops_ready": T_NUMBER,
    "oops_word": T_NUMBER,
    # The closed container a named-but-shut-away object sits in (open-first hint).
    "shut_in": T_OBJECT,
    # Set to 1 by a refusal path when a command could not be carried out, so a
    # chained line ("take lamp and go north") stops at the failed command. The
    # library's default refusals set it; a story handler can too (docs/02 8b).
    "refused": T_NUMBER,
    # Command chaining (docs/02 section 8b), library-internal: the text-buffer
    # offset where the queued rest of a chained line starts (0 when none), and
    # the full typed length chain_next restores before re-tokenizing.
    "chain_pos": T_NUMBER,
    "chain_max": T_NUMBER,
    # The disambiguation ask (docs/02 section 8), library-internal: the tied
    # phrase's word range and winning score (so the question can list the
    # candidates), and the text offset where an answer's narrowing words are
    # woven back into the saved command.
    "ask_lo": T_NUMBER,
    "ask_hi": T_NUMBER,
    "ask_score": T_NUMBER,
    "ask_at": T_NUMBER,
    # Set by the parser when a typed all-word hands the command to the takeall
    # granule's expander (TAKE ALL); consumed by the turn loop.
    "all_go": T_NUMBER,
}

# Objects Cosmos provides. `player` is the distinguished character instance.
_STD_OBJECTS = {"player": "character"}


def standard_environment() -> Environment:
    """Build the provisional Cosmos environment for semantic analysis."""
    env = Environment()
    for k in _STD_KINDS:
        env.kinds[k.name] = k
    for name in _STD_BOOL_PROPS:
        env.properties[name] = StdProp(name, T_BOOL)
    for name, ty in _STD_VALUE_PROPS.items():
        env.properties[name] = StdProp(name, ty)
    for name in _DIRECTIONS:
        env.properties[name] = StdProp(name, T_OBJECT)
    env.directions = list(_DIRECTIONS)
    env.actions = set(_STD_ACTIONS)
    env.events = set(_STD_ACTIONS) | set(_CORE_EVENTS)
    for name, ty in _BUILTINS.items():
        env.builtins[name] = StdBuiltin(name, ty)
    env.objects = dict(_STD_OBJECTS)
    return env
