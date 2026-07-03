# ast.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Abstract syntax tree for Arcturus.

The nodes mirror the grammar in docs/01 appendix B. Every node carries a
source line for diagnostics. The tree is deliberately close to the surface
syntax; semantic resolution (the property/attribute choice, is-as-property-test
versus is-as-equality, scope, dead-code elimination) belongs to later
milestones and is not done here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


# --------------------------------------------------------------------------
# String literals: a sequence of literal text and interpolated expressions.
# --------------------------------------------------------------------------


@dataclass
class StringText:
    text: str


@dataclass
class StringInterp:
    # The interpolated expression, already parsed. `article` is the optional
    # leading article helper (a, an, the, A, An, The); see docs/01 section 16.
    # `case` is an optional grammatical-case tag written after a colon on the
    # article (${the:acc noun}); it reaches the language layer's article block so
    # a case-inflected language (German der/den/dem) can pick the right form. Only
    # the definite/indefinite article carries it; None means nominative.
    expr: "Expr"
    article: Optional[str] = None
    case: Optional[str] = None


StringPart = Union[StringText, StringInterp]


# --------------------------------------------------------------------------
# Expressions
# --------------------------------------------------------------------------


class Expr:
    """Base class for expression nodes."""


@dataclass
class Number(Expr):
    value: int
    line: int = 0


@dataclass
class StringLit(Expr):
    parts: list[StringPart]
    line: int = 0


@dataclass
class Bool(Expr):
    value: bool
    line: int = 0


@dataclass
class Nothing(Expr):
    line: int = 0


@dataclass
class Name(Expr):
    """An identifier: an object, kind, property, global, local, or builtin
    reference (self, player, here, noun, second, turns, ...). Which one it is
    resolved in semantic analysis."""

    ident: str
    line: int = 0


@dataclass
class Dot(Expr):
    """Property read: obj.prop ."""

    obj: Expr
    prop: str
    line: int = 0


@dataclass
class DynDot(Expr):
    """Computed property read: obj.(expr), as in here.(dir)."""

    obj: Expr
    index: Expr
    line: int = 0


@dataclass
class Call(Expr):
    """A block call: name(args...)."""

    name: str
    args: list[Expr]
    line: int = 0


@dataclass
class Unary(Expr):
    op: str  # "not" or "-"
    operand: Expr
    line: int = 0


@dataclass
class Binary(Expr):
    """Arithmetic or comparison: +, -, *, /, mod, <, >, <=, >=, holds, in."""

    op: str
    left: Expr
    right: Expr
    line: int = 0


@dataclass
class Logic(Expr):
    op: str  # "and" or "or"
    left: Expr
    right: Expr
    line: int = 0


@dataclass
class IsTest(Expr):
    """left is right / left is not right. Whether this is a boolean property
    test or an equality is decided in semantic analysis (docs/01 section 9)."""

    left: Expr
    right: Expr
    negated: bool = False
    line: int = 0


# --------------------------------------------------------------------------
# Statements
# --------------------------------------------------------------------------


class Stmt:
    """Base class for statement nodes."""


@dataclass
class Let(Stmt):
    name: str
    value: Expr
    line: int = 0


@dataclass
class Change(Stmt):
    target: Expr  # a Name or a Dot (an lvalue)
    value: Expr
    line: int = 0


@dataclass
class Now(Stmt):
    """now <obj> is [not] <property>."""

    target: Expr
    prop: str
    negated: bool = False
    line: int = 0


@dataclass
class Move(Stmt):
    obj: Expr
    dest: Expr
    line: int = 0


@dataclass
class Add(Stmt):
    value: Expr
    target: Expr  # a list property place
    line: int = 0


@dataclass
class Remove(Stmt):
    value: Expr
    target: Expr
    line: int = 0


@dataclass
class Say(Stmt):
    value: Expr
    line: int = 0
    # say.yellow "...": print in that foreground colour, then restore the base
    # font colour (zcolor.font). None is a plain say. Colour names are validated
    # against prelude._ZCOLOURS at parse time.
    colour: Optional[str] = None


@dataclass
class ZColor(Stmt):
    # zcolor.font white / zcolor.background black: set a base screen colour.
    # Setting the background also repaints the screen (the erase that makes the
    # new colour cover the whole display, not just new text). Both are no-ops on
    # an interpreter that reports no colour support.
    target: str  # "font" or "background"
    colour: str
    line: int = 0


@dataclass
class Line(Stmt):
    # A conversation line in a topic body: `you "..."` (the player) or
    # `reply "..."` (the NPC), auto-quoted and auto-attributed when printed.
    who: str  # "you" or "reply"
    text: Expr
    line: int = 0


@dataclass
class TopicToggle(Stmt):
    # `reveal <id>` / `hide <id>`: show or hide another topic by its subject id.
    reveal: bool
    target: str
    line: int = 0


@dataclass
class Stop(Stmt):
    line: int = 0


@dataclass
class Continue(Stmt):
    line: int = 0


@dataclass
class Finish(Stmt):
    message: Optional[Expr] = None
    line: int = 0


@dataclass
class Return(Stmt):
    value: Optional[Expr] = None
    line: int = 0


@dataclass
class ExprStmt(Stmt):
    """A bare expression used as a statement, typically a block call."""

    expr: Expr
    line: int = 0


@dataclass
class Schedule(Stmt):
    """after <n> turns do <event> / every <n> turns do <event> (docs/02 s.13)."""

    every: bool
    count: Expr
    event: str
    line: int = 0


@dataclass
class IfClause:
    """One arm of an if/else-if chain. cond is None for the final else."""

    cond: Optional[Expr]
    body: list[Stmt]
    line: int = 0


@dataclass
class If(Stmt):
    clauses: list[IfClause]
    line: int = 0


@dataclass
class While(Stmt):
    cond: Expr
    body: list[Stmt]
    line: int = 0


@dataclass
class ForEach(Stmt):
    var: str
    relation: str  # "in" (tree children / list elements) or "of" (instances)
    source: Expr
    body: list[Stmt]
    line: int = 0


@dataclass
class Case:
    values: list[Expr]  # empty list marks the else case
    body: list[Stmt]
    line: int = 0


@dataclass
class Switch(Stmt):
    subject: Expr
    cases: list[Case]
    line: int = 0


# --------------------------------------------------------------------------
# Declarations and members
# --------------------------------------------------------------------------


@dataclass
class MetaLine:
    key: str
    value: object  # str, int, or a Name for an object reference (start)
    line: int = 0


@dataclass
class GameBlock:
    meta: list[MetaLine]
    line: int = 0


@dataclass
class Summon:
    # The three summon forms (docs/05). `target` is a feature id, a granule
    # filename, or a path, depending on `form`:
    #   "feature"  summon.statusline        - the bundled copy, always
    #   "name"     summon statusline.granule - story dir, then -L dirs, then bundled
    #   "path"     summon "x.granule"        - an explicit file, no bundled fallback
    target: str
    form: str = "feature"
    arg: Optional[str] = None  # the optional string argument of a feature
    line: int = 0


# Property declaration forms (docs/01 section 6).
PROP_VALUE = "value"  # name <value> (or a comma list, as for words)
PROP_BOOL = "bool"  # bare name, a boolean defaulting to true
PROP_LIST = "list"  # name list <n>
PROP_BLOCK = "block"  # name block + an indented computed body


@dataclass
class PropertyDecl:
    name: str
    form: str
    values: list[Expr] = field(default_factory=list)  # PROP_VALUE
    capacity: Optional[int] = None  # PROP_LIST
    body: list[Stmt] = field(default_factory=list)  # PROP_BLOCK
    line: int = 0


@dataclass
class Operand:
    """One operand position in a handler header, with `or` alternatives."""

    names: list[str]


@dataclass
class Prep:
    """A literal preposition word between operands (in, on, with, to, ...)."""

    word: str


PatternItem = Union[Operand, Prep]


@dataclass
class Handler:
    # One or more action names. A header may list several verbs separated by
    # commas (on attack, push, pull), so this is always a list with at least
    # one entry. `other` is the catch-all (docs/01 section 12).
    events: list[str]
    after: bool = False
    pattern: list[PatternItem] = field(default_factory=list)
    when: Optional[Expr] = None
    body: list[Stmt] = field(default_factory=list)
    line: int = 0


@dataclass
class Grain:
    verbs: list[str]
    words: list[str]
    # Exactly one of these is set: a single say string, a do-block name, or an
    # indented statement body.
    say: Optional[Expr] = None
    do: Optional[str] = None
    body: list[Stmt] = field(default_factory=list)
    line: int = 0


@dataclass
class GrainsBlock:
    grains: list[Grain]
    line: int = 0


@dataclass
class TopicDecl:
    # A conversation topic on a person (docs/02 section 14). `subject` is the id
    # (used by reveal/hide); `label` is the menu line; `words` are the ask/tell
    # match words (empty for conversations-only). `when` guards visibility, `once`
    # retires after use, `hidden` starts it out of view. The body is the exchange.
    subject: str
    label: Expr
    words: list[str] = field(default_factory=list)
    when: Optional[Expr] = None
    once: bool = False
    hidden: bool = False
    body: list[Stmt] = field(default_factory=list)
    line: int = 0


Member = Union[PropertyDecl, Handler, GrainsBlock, TopicDecl]


@dataclass
class ObjectDecl:
    category: str  # "room" or "thing"
    name: str
    parent: Optional[str] = None  # of <kind>
    location: Optional[str] = None  # in <location>
    members: list[Member] = field(default_factory=list)
    line: int = 0
    # Extra rooms this (fixed) object is in scope in, beyond its tree location:
    # from `in A, B` / `in A and B` sugar or a `spans B, C` member. The object
    # lives in `location` in the tree and is visible in these too (docs/01 s5).
    spans: list[str] = field(default_factory=list)


@dataclass
class KindDecl:
    name: str
    parent: Optional[str] = None
    members: list[Member] = field(default_factory=list)
    line: int = 0


@dataclass
class Slot:
    kind: str  # "noun", "held", "multi", "text", "direction"


@dataclass
class Word:
    text: str  # a literal preposition word in a grammar line


GrammarItem = Union[Slot, Word]


@dataclass
class GrammarLine:
    action: str
    items: list[GrammarItem]
    line: int = 0


@dataclass
class VerbDecl:
    words: list[str]
    grammar: list[GrammarLine]
    line: int = 0


@dataclass
class LanguageDecl:
    # A self-identifying marker at the top of a language pack: `language "spanish"`.
    # The compiler uses it to require that a language granule is selected with
    # `summon.language "spanish"` (which does the swap) and to reject the generic
    # `summon spanish.granule` (which would not). Consumed by the loader, not sema.
    code: str
    line: int = 0


@dataclass
class DirectionDecl:
    # A language layer maps player-facing words to a fixed direction property:
    # `direction north "north", "n"`. The property (`prop`) is one of the standard
    # direction names; the words are the vocabulary. Localized by a language pack.
    prop: str
    words: list[str]
    line: int = 0


@dataclass
class PlayerDecl:
    # A top-level augmentation of the seeded player object: `player.words
    # Olivia, Lund` (ADDS to the words already declared, the language layer's
    # standard self-words), `player.desc "You are..."`, or a computed
    # `player.desc block`. The wrapped decl is an ordinary PropertyDecl.
    prop: "PropertyDecl"
    line: int = 0


@dataclass
class PronounDecl:
    # A language layer maps player-typed words to a canonical pronoun role:
    # `pronoun it "it"` (English), `pronoun her "sie"` (German, grammatical
    # gender). The role is one of prelude._PRONOUN_ROLES; the words resolve to
    # that role's remembered referent when typed as a noun.
    role: str
    words: list[str]
    line: int = 0


@dataclass
class ParticleDecl:
    # A language layer maps player-facing words to a canonical verb particle:
    # `particle on "on"` (English), `particle on "an", "ein"` (German). The role is
    # `on` or `off`; the words are the vocabulary the parser combines with a base
    # verb (switch + on -> switch_on). Localized by a language pack, so the compiler
    # hardcodes no particle words.
    role: str
    words: list[str]
    line: int = 0


@dataclass
class ChainDecl:
    # A language layer declares the words that chain commands on one line:
    # `chain ",", "and", "then"` (English), `chain ",", "y", "luego"` (Spanish).
    # A chain word ends the current command; the parser runs what follows as the
    # next command once the current one succeeds (docs/02 section 8b). All chain
    # words behave identically, so this is a plain word list with no role.
    words: list[str]
    line: int = 0


@dataclass
class Award:
    # `award 5` / `award 10 for door_solved "outsmarting the door"`: grant
    # points, once per site (or once per named POOL: alternative branches
    # sharing a name pay whichever fires first, and max_score counts the
    # pool once at its maximum). The compiler sums every site and pool into
    # max_score, so it is never typed by hand (docs/01, Scoring).
    points: int
    pool: Optional[str] = None
    label: Optional["StringLit"] = None
    line: int = 0


@dataclass
class RanksDecl:
    # The Infocom-style rank ladder: a bare list of titles spread evenly
    # across the compiler-summed max_score; an entry may pin itself with
    # `at N` (percent of max). entries: (title, percent or None).
    entries: list
    line: int = 0


@dataclass
class NoiseDecl:
    # A language layer's noise words: the articles and fillers the parser
    # knows but ignores (`noise "the", "a", "an"`). Being KNOWN is the point:
    # a noun-list segment ("take lamp and the box") may contain them, while a
    # genuinely unknown word (a mistyped verb) honestly refuses the borrow.
    words: list[str]
    line: int = 0


@dataclass
class AllDecl:
    # The takeall granule's all-words: `all "all", "everything"` names the words
    # that mean "everything within reach" (TAKE ALL, DROP ALL, TAKE ALL FROM X).
    # Declared in the granule, so a game pays nothing unless it summons it; a
    # translation forks the granule and redeclares them (docs/05).
    words: list[str]
    line: int = 0


@dataclass
class Bump:
    # `grill_pushes++` / `grill_pushes--`: the counter mechanics (docs/01
    # section 4). Only a `counter` global takes them; everything else keeps
    # `change ... to`.
    name: str
    delta: int
    line: int = 0


@dataclass
class GlobalDecl:
    # role: "global" (the general drawer: numbers, object references,
    # strings), "flag" (boolean state, starts false, only ever true/false),
    # or "counter" (a number with ++/--, starts 0). The declaration head
    # says what you are holding (docs/01 section 4).
    name: str
    value: Expr
    role: str = "global"
    line: int = 0


@dataclass
class ConstantDecl:
    name: str
    value: Expr
    line: int = 0


@dataclass
class BlockDecl:
    name: str
    params: list[str]
    body: list[Stmt]
    line: int = 0
    # Where the block came from: "library" (a Cosmos .prelude), "granule" (a
    # summoned module), or "game" (the author's story). A game or granule block
    # overrides a library block of the same name (most-specific-wins).
    origin: str = "game"


@dataclass
class AmbienceLine:
    # One line of an ambience block: a string to say, or `do <block>` for a
    # computed line, each with an optional per-line `when` guard.
    text: Optional["StringLit"]
    do: Optional[str]
    when: Optional[Expr] = None
    line: int = 0


@dataclass
class AmbienceBlock:
    # An `ambience` block on a room or thing (summon.ambience, docs/05): a
    # list of lines the place or thing murmurs over time. mode is "about"
    # (living odds), "every" (strict clock), or "order" (written order);
    # rate is the declared cadence (None: the ambience_rate dial); once
    # makes an ordered block fall silent after its last line; when guards
    # the whole block.
    mode: str
    rate: Optional[int]
    once: bool
    when: Optional[Expr]
    lines: list[AmbienceLine]
    line: int = 0


@dataclass
class GrainsAttach:
    """Grains attached to an existing object from outside its body:
    <object>.grains (docs/01 section 14)."""

    target: str
    grains: list[Grain]
    line: int = 0


Decl = Union[
    GameBlock,
    Summon,
    KindDecl,
    ObjectDecl,
    VerbDecl,
    GlobalDecl,
    ConstantDecl,
    BlockDecl,
    Handler,
    GrainsAttach,
]


@dataclass
class Program:
    decls: list[Decl] = field(default_factory=list)
    # A tuned abbreviation set from a summoned abbreviations.granule (B6): compile-
    # time data for the text encoder, not runtime declarations. None when absent.
    abbreviations: Optional[list] = None
