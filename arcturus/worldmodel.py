# worldmodel.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The world-model intermediate representation.

Semantic analysis (sema.py) turns the AST into this checked, resolved model:
the objects and their kind chains, the program-wide property table with each
property's type and provisional storage, the verbs and actions, the handlers
with their dispatch specificity, and the grains. Code generation (a later
milestone) consumes the World; it does not look at the AST again.

Storage on a property is provisional here. A boolean-only property is an
attribute candidate; everything else is a slot. The final bit packing, the
48-bit budget, and dead-code elimination are the size pass (B5); this model
records the intent so it is visible early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import ast

# Provisional storage classes.
STORE_ATTRIBUTE = "attribute"  # a boolean-only property: an attribute bit
STORE_SLOT = "slot"  # a number, text, object, list, or block: a property slot

# The life-cycle events the turn loop fires (not verbs): the game's opening, a
# room being entered, and the per-turn pulse. They share the action-number space
# with verbs so the loop can fire them through the same react routines.
EVENT_NAMES = frozenset({"start", "enter", "each_turn"})


# The out-of-world actions (Inform's meta verbs, Puny's `Verb meta`): they
# report on or manage the session rather than act in the world, so no object
# or room handler ever sees them. Numbered LAST so the dispatcher's guard is
# a single compare against meta_floor() (see dispatch.prelude).
META_ACTIONS = ("score", "save", "restore", "restart", "quit",
                "transcript", "transcript_off")


def meta_actions(world: "World") -> set:
    """Every out-of-world action: the library's fixed set plus the actions of
    verbs declared `meta` (`verb "about" meta`; the debug granule's
    reach-anything tools). The dispatcher routes them straight to the free
    rules, past every object and room handler, `on other` included."""
    return set(META_ACTIONS) | world.meta_actions


def actions_with_after(world: "World") -> list:
    """Every action name that has at least one `on after` handler anywhere:
    on an object, on a kind, or free-standing. Each gets a synthetic after
    action (see action_numbers); the dispatcher's after phase fires it through
    the same chain once the real action completes unrefused (docs/02 s.9)."""
    found = set()
    pools = [obj.handlers for obj in world.objects.values()]
    pools.extend(kind.handlers for kind in world.kinds.values())
    pools.append(world.free_handlers)
    for handlers in pools:
        for h in handlers:
            if h.after:
                found.update(h.events)
    return sorted(found)


def after_key(action: str) -> str:
    """The synthetic action name an `on after <action>` handler answers to.
    The colon keeps it out of any author-writable namespace."""
    return "after:" + action


def action_numbers(world: "World") -> dict:
    """The deterministic action -> number map (0 means no action), shared by
    codegen (react routines, dictionary verb data) and lower (event firing).
    Verbs and the life-cycle events live in one numbering so a react routine can
    switch on either. The ordering carries two floors: the synthetic after
    actions sort past every real in-world action (after_floor), and the meta
    actions sort past those (meta_floor), so a single compare identifies each
    band at run time."""
    metas = meta_actions(world)
    names = sorted(set(world.actions) | {"other"} | EVENT_NAMES)
    world_names = [n for n in names if n not in metas]
    after_names = [after_key(n) for n in actions_with_after(world)]
    meta_names = [n for n in names if n in metas]
    return {name: i + 1 for i, name in enumerate(world_names + after_names + meta_names)}


def after_floor(world: "World") -> int:
    """The first synthetic after action number: react routines skip their
    `on other` catch-all at or past it (an after pass is not a player action).
    With no after handler in the program it equals meta_floor, and the guard
    never fires for anything the dispatcher lets through."""
    nums = action_numbers(world)
    afters = [nums[after_key(n)] for n in actions_with_after(world)]
    return min(afters) if afters else meta_floor(world)


def meta_floor(world: "World") -> int:
    """The first meta action number: actions at or past it are out-of-world.
    With no meta action in the program (never in practice; the standard verbs
    carry them), the floor sits past every action and the guard never fires."""
    nums = action_numbers(world)
    metas = [nums[n] for n in meta_actions(world) if n in nums]
    return min(metas) if metas else len(nums) + 1


@dataclass
class Property:
    name: str
    type: str  # one of prelude.ALL_TYPES
    origin: str  # "standard" or "game"
    storage: str  # STORE_ATTRIBUTE or STORE_SLOT (provisional)
    # Every site that fixes or uses the type, for clash diagnostics.
    decl_sites: list[tuple[str, int]] = field(default_factory=list)

    @property
    def bool_only(self) -> bool:
        return self.type == "bool"


@dataclass
class Kind:
    name: str
    parent: Optional[str]
    origin: str  # "standard" or "game"
    chain: list[str] = field(default_factory=list)  # self ... root
    # A kind supplies default properties and shared handlers to its instances.
    props: dict[str, "ast.Expr"] = field(default_factory=dict)
    handlers: list["Handler"] = field(default_factory=list)
    grains: list["Grain"] = field(default_factory=list)
    topics: list["ast.TopicDecl"] = field(default_factory=list)
    decl: Optional[ast.KindDecl] = None
    line: int = 0


@dataclass
class Handler:
    events: list[str]
    after: bool
    pattern: list[ast.PatternItem]
    when: Optional[ast.Expr]
    body: list[ast.Stmt]
    owner: Optional[str]  # the object or kind name, or None for a top-level rule
    origin_kind: bool  # True if declared on a kind (vs an instance/room/rule)
    line: int = 0
    # None for the game, "granule", or "library": free rules for one action
    # run most-specific-origin first (codegen._ORIGIN_RANK).
    origin: Optional[str] = None


@dataclass
class Grain:
    verbs: list[str]
    words: list[str]
    owner: str
    # The response, exactly one of which is set (mirrors ast.Grain): a say
    # string, a do-block name, or an inline statement body.
    say: Optional["ast.Expr"] = None
    do: Optional[str] = None
    body: list["ast.Stmt"] = field(default_factory=list)
    line: int = 0


@dataclass
class Catalog:
    name: str
    etype: str  # "text", "number", or "object": one element type per catalog
    values: list = field(default_factory=list)  # ast.Expr, homogeneous
    line: int = 0


@dataclass
class Matrix:
    """A matrix: the mutable sibling of a catalog (summon.matrix). A
    capacity-bounded sequence in dynamic memory whose length changes at
    runtime. It shares a catalog's region, base global, and [count, widest,
    cells] header (widest 0, count = the LIVE length), reserving `capacity`
    cells, so every read verb (entry, calculate, last, for each, position) is
    the catalog machinery unchanged; only the mutators and the layout are new.
    Numeric only: cell is number (word), object (word), or byte (0..255)."""

    name: str
    cell: str  # "number" | "object" | "byte"
    capacity: int
    seed: list = field(default_factory=list)  # ast.Expr initial values (<= capacity)
    checked: bool = False
    line: int = 0
    # 2D grid form: rows > 0 marks it. A fixed R x C table with no mutable
    # length (no header): entry(m, r, c) reads a cell, rows/columns the dims.
    rows: int = 0
    cols: int = 0
    seed_rows: list = field(default_factory=list)  # list[list[ast.Expr]]

    @property
    def is_2d(self) -> bool:
        return self.rows > 0

    @property
    def etype(self) -> str:
        # The element type in catalog terms, so shared read code types the
        # value: object cells read as objects, direction cells as directions
        # (say speaks the word), number/byte cells as numbers.
        if self.cell == "object":
            return "object"
        if self.cell == "direction":
            return "direction"
        return "number"


@dataclass
class Obj:
    name: str
    category: str  # "room" or "thing"
    kind: str  # the immediate kind: a declared kind, or "thing"/"room"
    chain: list[str] = field(default_factory=list)  # kind chain, nearest first
    location: Optional[str] = None  # initial tree parent (an object name)
    # Extra rooms this fixed object is in scope in, beyond its tree location
    # (the `spans` sugar; resolved room names, docs/01 section 5).
    spans: list[str] = field(default_factory=list)
    # Property name -> the initial value expression set on this object.
    props: dict[str, ast.Expr] = field(default_factory=dict)
    handlers: list[Handler] = field(default_factory=list)
    grains: list[Grain] = field(default_factory=list)
    topics: list["ast.TopicDecl"] = field(default_factory=list)
    # The object's ambience blocks (summon.ambience, docs/05), kept as their
    # AST declarations; codegen compiles the lines and guards directly.
    ambiences: list["ast.AmbienceBlock"] = field(default_factory=list)
    decl: Optional[ast.ObjectDecl] = None
    line: int = 0


@dataclass
class GrammarLine:
    action: str
    items: list[ast.GrammarItem]
    # A reversed two-noun line (give/show BOB COIN): the two noun roles swap.
    reverse: bool = False


@dataclass
class Verb:
    words: list[str]
    grammar: list[GrammarLine]
    line: int = 0


def line_shape(line: GrammarLine) -> tuple:
    """The positional signature of a grammar line: its slots and literal words,
    in order. Two lines with the same shape cannot be told apart by positional
    matching (only the particle machinery can, as with switch on/off)."""
    out = []
    for it in line.items:
        if isinstance(it, ast.Slot):
            out.append(("slot", it.kind))
        else:
            out.append(("word", it.text.lower()))
    return tuple(out)


def needs_table(verb: Verb) -> bool:
    """Does this verb need the positional grammar table (docs/02 section 8c)?

    The flag model (a noun arity plus any-separator splitting) represents most
    verbs exactly, and those stay on it, byte for byte. That includes a leading
    preposition on a ONE-noun verb (look AT noun): the phrase matcher skips a
    leading boundary word and its scoring ignores stray ones. The model is
    lossy, and the table takes over, when:
      - the verb takes two nouns on some line AND a line puts a literal word
        before its first slot (dig IN noun with held): the splitter would take
        the leading word for the boundary between the two nouns; or
      - two lines with different shapes name different actions (the line's
        wording selects the action, which a single per-verb action byte
        cannot express: look_under under noun vs look_behind behind noun).
    Lines that differ in action but not in shape (switch_on noun / switch_off
    noun) do NOT table the verb: no positional match could tell them apart;
    the particle machinery already does.

    A `direction` slot (swim direction, push noun direction) always tables
    its verb: the flag model's arity byte has no room for "and a direction
    word may stand here"; only `go` gets that tolerance in the classic path."""
    for line in verb.grammar:
        for it in line.items:
            if isinstance(it, ast.Slot) and it.kind == "direction":
                return True
    max_slots = max(
        (sum(1 for it in line.items if isinstance(it, ast.Slot)) for line in verb.grammar),
        default=0,
    )
    if max_slots >= 2:
        for line in verb.grammar:
            for it in line.items:
                if isinstance(it, ast.Slot):
                    break
                return True  # a literal before any slot
    # A text slot exists only in the table: the flag model resolves nouns and
    # has no way to absorb a subject range (consult noun about text).
    for line in verb.grammar:
        for it in line.items:
            if isinstance(it, ast.Slot) and it.kind == "text":
                return True
    actions = {line.action for line in verb.grammar}
    shapes = {line_shape(line) for line in verb.grammar}
    return len(actions) > 1 and len(shapes) > 1


def tabled_verbs(world: "World") -> list:
    """The verbs whose grammar is emitted as a positional table, in declaration
    order (deterministic layout)."""
    return [v for v in world.verbs if needs_table(v)]


def table_line_order(grammar: list) -> list:
    """The order the runtime tries a tabled verb's lines in: most literal words
    first (so `dig in noun with held` is probed before `dig noun`, whose bare
    slot would swallow the literals), and among the literal-free lines fewest
    tokens first (so a bare `dig` catches DIG before `dig noun` matches it with
    an empty slot). The sort is stable, so lines the rule does not separate keep
    their declared order."""
    def lits(line):
        return sum(1 for it in line.items if isinstance(it, ast.Word))

    return sorted(
        grammar, key=lambda l: (-lits(l), len(l.items) if lits(l) == 0 else 0)
    )


@dataclass
class Global:
    # See ast.GlobalDecl: "global", "flag", or "counter".
    name: str
    type: str
    value: ast.Expr
    line: int = 0
    role: str = "global"


@dataclass
class Constant:
    name: str
    type: str
    value: ast.Expr
    line: int = 0


@dataclass
class Block:
    name: str
    params: list[str]
    body: list[ast.Stmt]
    line: int = 0
    origin: str = "game"  # library / granule / game; see ast.BlockDecl


# How an `is` test resolved (docs/01 section 9).
IS_PROPERTY = "property"  # right side is a boolean property: an attribute test
IS_KIND = "kind"  # right side is a kind name: a kind-membership test
IS_PREDICATE = "predicate"  # right side names a one-parameter block: a call test
IS_EQUALITY = "equality"  # otherwise: an equality / identity comparison


@dataclass
class World:
    game: Optional[ast.GameBlock] = None
    # Actions of verbs declared `meta` (see meta_actions above).
    meta_actions: set = field(default_factory=set)
    # catalog declarations, in declaration order (the layout is deterministic).
    # Conversation subjects declared at file level (docs/01 section 15): id ->
    # SubjectDecl. A character's `topic <id>` naming one inherits its words and
    # label, and the word array is emitted once for the whole cast.
    subjects: dict = field(default_factory=dict)
    catalogs: dict = field(default_factory=dict)
    # matrix declarations (summon.matrix), in declaration order. Empty unless
    # the granule is summoned; everything gated on it folds to nothing.
    matrices: dict = field(default_factory=dict)
    start_room: Optional[str] = None
    kinds: dict[str, Kind] = field(default_factory=dict)
    objects: dict[str, Obj] = field(default_factory=dict)
    properties: dict[str, Property] = field(default_factory=dict)
    verbs: list[Verb] = field(default_factory=list)
    actions: set[str] = field(default_factory=set)
    # Player-facing direction word -> standard direction property name, from the
    # language layer's `direction` declarations (docs/01). Localized by a pack.
    directions: dict[str, str] = field(default_factory=dict)
    # Every direction PROPERTY name (the standard set plus any declared), set
    # at the end of analysis. Codegen allows a computed exit (a direction
    # property that is a block) using this; a general computed value property
    # stays unsupported.
    direction_props: set = field(default_factory=set)
    # True when a `now ... is beyond` statement exists anywhere: the any_beyond
    # fold must survive for a game that only sets beyond at runtime (the
    # player-beyond mount) and never declares it on an object.
    sets_beyond: bool = False
    # How many vary sites need a state word (sequence/loop/mutate; dice keeps
    # none). Slots are stamped on the Vary nodes in sema, in source order, and
    # the words live at the end of the catalog region (objects.build_layout).
    vary_slots: int = 0
    # Player-facing verb-particle word -> canonical particle name ("on"/"off"),
    # from the language layer's `particle` declarations. English "on"/"off", German
    # "an"/"ein"/"aus"/"ab"; the parser combines a base verb with the particle
    # (switch + on -> switch_on). Localized by a pack, so no particle word is
    # hardcoded in the compiler.
    particles: dict[str, str] = field(default_factory=dict)
    # Player-typed pronoun word -> canonical role name (it/him/her/them), from
    # the language layer's `pronoun` declarations. The dictionary flags these
    # words and the noun matcher resolves them to the remembered referents.
    pronouns: dict[str, str] = field(default_factory=dict)
    # The words that chain commands on one line ("and", "then", the comma), from
    # the language layer's `chain` declarations. The dictionary flags them; the
    # parser splits the line at the first one and queues the rest (docs/02 8b).
    chain_words: list[str] = field(default_factory=list)
    # The takeall granule's all-words ("all", "everything"): flagged in the
    # dictionary so the parser hands the command to the granule's expander.
    # Empty unless the granule is summoned, and everything gated on it folds.
    all_words: list[str] = field(default_factory=list)
    # The language layer's noise words (articles, fillers): in the dictionary
    # so the parser KNOWS them, flagged so it ignores them.
    noise_words: list[str] = field(default_factory=list)
    # The scoring plan, gathered at lowering time (docs/01, Scoring): each
    # anonymous `award` site's points, and each named pool's running
    # (byte index, max points, label). max_score sums itself from these plus
    # the scored rooms and things; build_story seeds the global.
    award_anon: list = field(default_factory=list)
    award_pools: dict = field(default_factory=dict)
    ranks: list = field(default_factory=list)
    # True once lowering meets a colour construct (zcolor, say.<colour>). The
    # story header then announces colour use (Flags 2 bit 6), which interpreters
    # like Frotz require before they enable their colour machinery.
    uses_colours: bool = False
    globals: dict[str, Global] = field(default_factory=dict)
    constants: dict[str, Constant] = field(default_factory=dict)
    blocks: dict[str, Block] = field(default_factory=dict)
    free_handlers: list[Handler] = field(default_factory=list)
    summons: list[ast.Summon] = field(default_factory=list)
    # A tuned abbreviation set from a summoned abbreviations.granule (B6), carried
    # to codegen as the text encoder's set in place of the built-in default.
    abbreviations: Optional[list] = None
    # event block name -> timer slot, for `after`/`every` scheduling (docs/02 s.13);
    # codegen assigns the slots and lower reads them to arm a timer.
    schedule_index: dict = field(default_factory=dict)
    # Names of text properties computed on some object (`<name> block`), so a read
    # of one lowers to "print or run" rather than a plain string print (docs/01 s6).
    computed_text_props: set = field(default_factory=set)
    # Resolution of every `is` test, keyed by the node's identity.
    is_resolutions: dict[int, str] = field(default_factory=dict)
    # How many `obj is <kind>` test SITES name each kind (static count, not a
    # runtime count). A kind absent here is never membership-tested, so it
    # needs no runtime identity at all and costs zero attributes; a kind
    # present here is attribute-backed while the 48-attribute budget has room,
    # and catalog-backed (a membership scan) beyond it, the busiest kinds
    # keeping the one-byte test_attr. So a class never steals an attribute
    # from a real flag, and kinds are effectively unlimited (docs/01 s5).
    kind_tests: dict[str, int] = field(default_factory=dict)
    # arc_image (B11): True once any room declares an `arc_image` picture. The id
    # in the slot is the author's own number (the resource slot the interpreter
    # loads as <id>.png), so there is no name manifest; this flag is only the
    # pay-for-use gate, letting any_images fold the whole picture path away in a
    # game with no pictures.
    uses_images: bool = False
    # True when darkness is reachable: a room resolving `lit` false at compile
    # time, or a `now ... is not lit` anywhere. Feeds the any_dark fold, and
    # with uses_images the rule that an images game declares arc_image_dark.
    uses_darkness: bool = False
    # The declarative verb contract (the verbs overhaul, phase 2): action name
    # -> packed requirement bits (1 noun carried, 2 noun animate, 4 second
    # carried, 8 second animate). Emitted as requires_map; enforced by the
    # loop BEFORE dispatch, so a handler override owns only the response.
    requirements: dict = field(default_factory=dict)
    sets_shiftable: bool = False
    uses_notify: bool = False

    def all_handlers(self):
        for obj in self.objects.values():
            yield from obj.handlers
        for kind in self.kinds.values():
            yield from kind.handlers
        yield from self.free_handlers
