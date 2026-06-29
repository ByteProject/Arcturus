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
    StdKind("person", "thing"),
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
    # A living thing: people and creatures. The conversation and give verbs apply
    # only to the animate; the person kind sets it by default.
    "animate",
    # Set when the indefinite article should be "an" instead of "a". The compiler
    # derives it from the object's name (a vowel-initial name -> "an") unless the
    # author sets it explicitly, so "an apple" / "a coin" come out right with no
    # author work; declare `an` (or `an false`) only for the odd exception (an
    # hour, a unicorn).
    "an",
]

# Standard value properties and their types.
_STD_VALUE_PROPS = {
    "name": T_TEXT,
    "desc": T_TEXT,
    # The object's initial appearance: shown in the room description while the
    # object sits untouched in place (until it has `moved`), in place of the
    # plain "You can see X here." Useful for set dressing and static objects.
    "intro": T_TEXT,
    "words": T_LIST,
    "capacity": T_NUMBER,
    "key": T_OBJECT,
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
}

# Objects Cosmos provides. `player` is the distinguished person instance.
_STD_OBJECTS = {"player": "person"}


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
