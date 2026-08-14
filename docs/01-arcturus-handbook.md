# The Arcturus Handbook

This is the manual for Arcturus: the language, the standard library
(Cosmos), and the summonable granules, in one book. Each chapter takes
one topic and covers it whole, the syntax first, then what the library
does with it. The deeper technical matter (the parser's machinery,
hacking the library, the compiler and its flags) sits toward the back;
you can write a game long before you need any of it.

This book aims to be a truthful reference. If you find something in your
code not working as described here, be sure to report it in the [Arcturus
Discord channel](https://discord.gg/JF6YNUTPfT) and I will have a look.

Arcturus ships with its own reference interpreter, Actaea
([docs/06](06-actaea.md)): a GUI that runs on any modern computer and
supports arc_image, a console mode for any terminal, a debugger, and a
headless mode in the manner of dumb frotz. arc_image, the picture system
that reaches from modern machines down to the 8-bits, has its author
guide in [docs/07](07-arc-image.md); interpreter authors refer to
[docs/08](08-arcimage-interpreters.md). If you are interested in the
compiler internals, check out [the compiler
pipeline](03-compiler-pipeline.md) and [the codegen
mapping](04-codegen-mapping.md).

- [Chapter 1: Reading Arcturus](#chapter-1-reading-arcturus)
- [Chapter 2: A game and its program](#chapter-2-a-game-and-its-program)
- [Chapter 3: Rooms, things, and kinds](#chapter-3-rooms-things-and-kinds)
- [Chapter 4: The player](#chapter-4-the-player)
- [Chapter 5: Properties](#chapter-5-properties)
- [Chapter 6: Containers, supporters, and the object tree](#chapter-6-containers-supporters-and-the-object-tree)
- [Chapter 7: Scope, light, and darkness](#chapter-7-scope-light-and-darkness)
- [Chapter 8: Movement and directions](#chapter-8-movement-and-directions)
- [Chapter 9: Statements, control flow, and expressions](#chapter-9-statements-control-flow-and-expressions)
- [Chapter 10: Blocks](#chapter-10-blocks)
- [Chapter 11: Handlers and events](#chapter-11-handlers-and-events)
- [Chapter 12: Verbs, grammar, and the standard actions](#chapter-12-verbs-grammar-and-the-standard-actions)
- [Chapter 13: The turn loop and the action pipeline](#chapter-13-the-turn-loop-and-the-action-pipeline)
- [Chapter 14: The parser](#chapter-14-the-parser)
- [Chapter 15: Output and text](#chapter-15-output-and-text)
- [Chapter 16: Daemons, timers, and background performers](#chapter-16-daemons-timers-and-background-performers)
- [Chapter 17: Topics and conversation](#chapter-17-topics-and-conversation)
- [Chapter 18: Grains](#chapter-18-grains)
- [Chapter 19: Scoring](#chapter-19-scoring)
- [Chapter 20: Pictures: arc_image](#chapter-20-pictures-arc_image)
- [Chapter 21: Writing in another language](#chapter-21-writing-in-another-language)
- [Chapter 22: Summon: the granules](#chapter-22-summon-the-granules)
- [Chapter 23: Hacking Cosmos](#chapter-23-hacking-cosmos)
- [Chapter 24: The compiler, diagnostics, and the abbreviation set](#chapter-24-the-compiler-diagnostics-and-the-abbreviation-set)
- [Chapter 25: Worked example: The Brass Lantern](#chapter-25-worked-example-the-brass-lantern)
- [Chapter 26: Worked example: Cloak of Darkness](#chapter-26-worked-example-cloak-of-darkness)
- [Appendix A: Reserved words](#appendix-a-reserved-words)
- [Appendix B: Grammar summary](#appendix-b-grammar-summary)
- [Appendix C: Cosmos-reserved names](#appendix-c-cosmos-reserved-names)
- [Appendix D: The author's toolkit](#appendix-d-the-authors-toolkit)

## Chapter 1: Reading Arcturus

1. One way to read a thing. `change` sets any mutable state; `is` tests any
   boolean; the dot reads any property.
2. The author describes the world; the compiler handles the machine, and
   aims for the smallest possible z-code in doing so.
3. Structure from indentation. No braces and no `end`.
4. Declarative shape, imperative behavior. Objects are data; behavior hangs
   off them in `on` handlers and `block` routines.
5. Errors at compile time, not surprises at run time.

### Lexical structure

Arcturus source uses three file extensions, named after the star: `.storyarc`
for a story (an author's game), `.prelude` for a core Cosmos library file (the
prelude loaded before the story), and `.granule` for a summoned module (a
granule on the star's surface). A granule is anything brought in with `summon`,
whether a third-party extension or an optional Cosmos feature or language pack;
it loads only when summoned. The core Cosmos library is `.prelude`; everything
opt-in is a `.granule`. All three are the same language and lex identically; the
extension only signals the file's role.

Source is UTF-8; the compiler maps text to ZSCII at build time.

Comments start with `//` and run to end of line. There are no block comments.

Identifiers begin with a letter and contain letters, digits, and
underscores, and are case sensitive. Convention is lower_snake_case.
Reserved words (appendix A) cannot be identifiers.

Indentation defines block structure: an indent opens a body, a dedent closes
it. Use a consistent unit, four spaces recommended, and never mix tabs and
spaces. An inconsistent indent is a compile error.

Newlines are significant: one statement or declaration per line. A quoted
string may span several physical lines (chapter 15). One exception continues a
logical line: a line ending in a comma runs on to the next, so a long
comma-separated list (a `spans` set, an `in` clause, `words`, verb synonyms)
can be broken across lines and indented freely. Blank and comment-only lines
between the comma and the continuation are ignored.

### Values and types

- number: a 16-bit signed integer, -32768 to 32767, wrapping arithmetic. No
  floats.
- text: a string, ZSCII encoded at compile time, with `${ }` interpolation.
- boolean: `true` or `false`.
- object: a reference to a declared object; the literal `nothing` is null.
- list: an ordered, bounded collection, declared with a capacity.
- block: a routine value (chapter 10). A property may hold a block, which
  makes it a computed property.

Conditions must be boolean; `if n` for a number is a compile error, write
`if n > 0`. Object presence is tested with `is not nothing`.

## Chapter 2: A game and its program

Top-level constructs, in any order: the `game` metadata block, `summon`
directives, `kind`, `room`, `thing`, `verb`, `global`, `constant`, `block`,
and free-standing `on` rules. A language pack additionally uses the
language-layer declarations `language` (its self-identifying marker),
`direction`, `particle`, `pronoun`, `chain` (the words that join several
commands on one line), and `noise` (the articles the parser knows but
ignores), which map player-typed words to the compiler's fixed properties
and roles (chapters 14 and 21); and a German
object declares its gender with a bare `der`, `die`, or `das` line, which the
compiler maps to the gender attributes (chapter 21).

The metadata block sets everything the banner and story header carry:

```
game
    title    "The Brass Lantern"
    headline "An Interactive Fiction"
    author   "Stefan"
    release  1
    serial   "260626"
    UUID     c35b1143-7d7e-47f8-beb3-2637c4c094ab
    start    hallway
```

`release` is the release number (default 1). `serial` is the six-digit
YYMMDD serial; if omitted the compiler uses the build date. `UUID` is written
into the story file as an IFID array so IFDB and similar can identify the
game; it is optional but recommended. `headline` is the subtitle line of the
banner. `copyright` is an optional line printed in the banner under the
headline ("(c) 2026 Moonmist Entertainment"), the way Infocom credited a
publisher; absent, nothing prints. `banner false` stops the automatic banner at start: the game prints it
later with `print_banner` (after a quote box, say), or never.
The banner also names the compiler (Arcturus) and the library
(Cosmos) with their versions; the banner section later in this chapter has the details.

Story state comes in three declarations, and the head tells the reader what
they are holding:

```
flag grill_open                 // boolean state; starts false
flag emergency_power = true     // the rare pre-set one
counter grill_pushes            // a number that counts; starts 0
counter lives = 3
global motto = "Per aspera ad astra."   // the general drawer
global favorite = lantern
constant max_carry = 7
```

A FLAG holds only `true` or `false`, forever: `change grill_open to 3` is a
compile error, and no `= false` is ever written, since a flag starts false
by itself. A COUNTER is a number with the counting mechanics attached:

```
grill_pushes++
lives--
```

`++` and `--` belong to counters alone; everything else, and any other
assignment, keeps the one way to write state, `change x to <value>` (the
`=` appears only at the declaration). A GLOBAL is everything else: numbers
that are values rather than counts, object references, and strings (a text
global holds its string and prints as text in `${...}` interpolation).

All three are Z-machine globals underneath; the split is for the reader and
the compiler, which checks the promise each head makes, and is free to pack
flags into bits later without any source change. The Z-machine offers 240;
the compiler allocates them and errors only if a program exceeds that.

A CONSTANT costs no global at all: it inlines to its value at every use. A
STRING constant stands for its text anywhere text stands, so one wording is
written once and shared:

```
constant MOTTO = "Measure twice, ship once."

thing plaque in office
    desc MOTTO          // the property reads as the literal

on rub
    say MOTTO           // and say / show print it
```

The string is stored once (identical strings always are) and the name is
purely compile-time. One care: a plain property string is a static Z-string,
so `${...}` interpolation inside one is dropped at runtime (the compiler
notes it and names the cure, a computed `desc block`); in `say` and `show`
the same constant interpolates as usual.

A CATALOG is a fixed, ordered collection declared once, like a star
catalog: one value per indented line, one TYPE of value per catalog
(strings, numbers, objects, or directions), the compiler counting so no
size is ever written:

```
catalog last_letter
    "To be read when I am gone:"
    ""
    "The garden knows. Dig nowhere."
    "E. Mereweather"

catalog suspects
    butler
    gardener
    doctor
```

The operations, all 1-based, all total (out of range answers 0/nothing):

```
calculate(suspects)              // how many entries: 3
entry(last_letter, 3)            // the third entry
last(last_letter)                // the final entry
dice(omens)                      // one entry at random
position(suspects, butler)       // an entry's number, or 0 when absent
if butler in suspects            // membership: the `in` you already know
for each line in last_letter     // iterate in order; say line prints right
change entry(verdicts, 2) to "guilty"   // rewrite ONE entry in place
```

A catalog of DIRECTIONS holds a fixed route the way a matrix holds a
mutable one: each entry is the direction's property number, an ordinary
cell, so `for each d in route` with `switch d / case north` walks a maze
solution or a patrol path, and `exit_dest(here, entry(route, 1))` asks
where the first leg leads. Saying such an entry speaks the direction's
canonical word, the same voice as `say way`: `say "${entry(route, 1)}"`
prints north (objects print their names, directions their words). An
object name always wins over a direction name, as everywhere. A local
carries the type with the value: after `let d = north`, or a
`change d to entry(route, 2)` into a local declared earlier, `say "${d}"`
speaks the word; assign the local a plain number and it prints digits
again. The same flow carries text and object entries read into a local.
That knowledge ends at a block parameter (a parameter is just a value, the
same boundary `for each` has): inside a shared helper, ask for the word
explicitly with `dir_name`, which speaks any direction value at runtime:
`say "${dir_name(entry(m, i))}"`. It prints in place and is not a value.

```
catalog escape_route
    north
    east
    up
```

A catalog passes to a block as an ordinary value (`quote_catalog(letter)`,
chapter 22), and entry/calculate work on the parameter inside; `for each` and
the compile-folds need the catalog named in place. A property can hold a
catalog the same way: `writing plaque_text` on an object (or as a kind
default) stores the catalog, and `entry(self.writing, 1)` in a kind
handler reads each object's own; the property types as a number, since a
catalog value is one. Underneath: a static
table in dynamic memory, so `calculate` on a named catalog folds to a
constant at compile time, `entry` and `last` are a single memory read,
`change entry` a single write, and there is no heap and no allocator
anywhere (the Dialog trap, deliberately refused: a catalog never grows or
shrinks). A game that declares no catalog is byte-identical. The
interpolation rule matches plain property strings: a catalog string is
static, so `${...}` inside one is a compile error. `calculate`, `entry`,
`last`, `dice`, and `position` are library-owned names. When you genuinely
need a collection whose length changes as the game plays, that is a
`matrix` (next), not a catalog.

### 4a. matrix: a catalog you can grow (summon.matrix)

Before reaching for a matrix, be sure you need one. A **catalog** is what
you want almost always: fixed data you read, index (`entry`), iterate (`for
each`), test (`in`, `position`), even rewrite in place (`change entry`). It
is near-free on 8-bit hardware because it is static tables and single
opcodes. Reach for a matrix only when a catalog cannot give you one of two
things: a collection whose **length changes at runtime** (you grow or
shrink it), or a two-dimensional **table** (Phase 2). Hibernated 2,
Rabenstein, and Ghosts never needed one; many whole games port with lists
alone. A matrix is a specialized tool, and it carries a real cost, dynamic
memory that rides in every save frame, that a catalog largely avoids. If
you are not doing one of those two things, stop, and use a catalog.

A matrix is the mutable sibling of a catalog, and a strictly summoned
feature: without `summon.matrix` the syntax is inert and it contributes
zero bytes. Declare one with a capacity (its reserved maximum), optionally a
cell kind and a bounds mode, and optional seed values:

```
summon.matrix

matrix clues capacity 12               // up to 12 cells, starts empty
matrix suspects capacity 8 of object   // cells hold object references
matrix counters capacity 20 of byte    // 0..255 cells
matrix primes capacity 6               // seeded, length starts at 3
    2
    3
    5
```

Cells are numeric only: `number` (a word, the default), `object` (a word
holding an object reference; `for each` types the item as an object), or
`byte` (0..255). DIRECTIONS are numbers too (a direction is its property),
so a route or a patrol stores them directly: `append north to route`, and a
read compares (`if d is north`) or switches (`switch d / case north`)
without any packing. A matrix never holds text; for words, keep a catalog
and store an index into it. The reads are exactly a catalog's, but the
count is the LIVE length: `calculate(m)` is the current length, `entry(m,
i)` the i-th (1-based), `last(m)`, `dice(m)`, `position(m, v)`, `v in m`,
and `for each x in m`. `change entry(m, i) to v` rewrites a cell in place.

A matrix `of direction` is the mutable route: seeds and appends are
direction names, each cell the direction's property number, and saying
a cell speaks the word, exactly as a direction catalog does.

Mind the count: entries LIVE only up to the count.
`change entry` rewrites a cell but never grows the matrix, so on a fresh
matrix the write lands in a cell the count does not yet cover, and
`calculate`, `for each`, and friends still see an empty matrix. Create
entries first: `append`, or a seed on the declaration line, or `load m
from zeros` (a catalog of zeros) to prefill; then `change entry`
mutates them.

Like a catalog, a matrix passes to a block as an ordinary value, and
`calculate`, `entry`, `last`, and `dice` all work on the parameter inside.
`for each` is the one read that needs the matrix NAMED IN PLACE: over a
block parameter the compiler cannot tell a matrix from an object, and the
loop would walk the object tree instead (on an interpreter that checks,
that surfaces as a warning about object 0). Inside a block, walk a matrix
parameter by index; every shared helper wants this shape anyway:

```
block read_route(m)
    let n = calculate(m)
    let i = 1
    while i <= n
        let d = entry(m, i)
        ...                       // switch d / case north / ...
        change i to i + 1
```

The mutators are what a catalog lacks. `append v to m` grows the length by
one, returning 1 or 0 when the matrix is full, so the policy is yours:

```
if append clue to clues is false
    say "Your notebook is full."
```

`remove entry(m, i)` removes by index and `remove v from m` by value, both
order-preserving (the tail shifts down); add `swapping` for an O(1)
remove that moves the last entry into the hole instead, unordered. `insert
v into m at i` shifts the tail up and inserts. `clear m` empties it.
`append`, `insert`, and `remove` are also expressions returning the same
success value, so any of them reads in an `if`.

`load m from cat` copies a catalog's values into the matrix as its new
contents (the compiler checks the catalog fits the capacity). This is the
bridge between the two: keep canonical data as a cheap catalog, and snapshot
it into a matrix only where you actually mutate it.

A computed index that is a literal is bounds-checked at compile time
(against the capacity); a computed index that is a variable is trusted at
runtime and fast, the same contract catalogs keep. Underneath, a matrix
shares the catalog region and reads through the same base; its header holds
the live count and the capacity, and every mutator is a short routine in the
editable `cosmos/matrix.granule`, so there is still no heap and no
allocator. `arcc -s` reports matrices and the dynamic bytes they reserve.

**Two dimensions: a table.** A matrix declared with dimensions instead of a
capacity is a fixed R by C grid, a table you index by (row, column):

```
matrix costs 3 by 3            // 9 word cells, all live
    row 2, 4, 6               // optional seed rows, each C wide
    row 1, 3, 5
    row 0, 0, 9

matrix terrain 16 by 16 of byte   // 256 cells packed one per byte
```

`entry(m, r, c)` reads a cell and `change entry(m, r, c) to v` writes one,
both indices 1-based; `rows(m)` and `columns(m)` are the dimensions
(constants). A 2D matrix has a fixed shape, so it has no length and no
mutators, only cell access. `of byte` packs a 2D grid one cell per byte,
half the memory of word cells, which is what makes a large lookup table (a
tile map, a distance table) affordable on 8-bit hardware; `of object` is not
a 2D cell kind. There is no header at all: the grid is `R*C` cells laid
row-major, and `entry(m, r, c)` is a single `loadw` (or `loadb` for a byte
grid) at `off + (r-1)*C + (c-1)`, so the whole table is exactly its cells and
nothing more. (For 1D matrices, `of byte` currently constrains values to
0..255 but is word-backed; the packing that halves memory applies to 2D
grids, where a large table actually needs it.)

### Runtime globals and story metadata

Built-in references usable in any handler or block:

- `player`: the player object, an instance of `character`.
- `here`: the room the player is in, maintained as the player moves.
- `turns`: a number, the elapsed turn count, starting at 0.
- `score`, `max_score`: numbers for games that keep score.
- `nothing`: the null object.
- `refused`: set to 1 by a handler that refuses a command, so a chained line
  stops at the failure (chapter 14). The library's own refusals set it; it
  resets before every command.

Cosmos owns `here` and `turns`; assigning to them is a compile error. The
author may change `score` and set `refused`.

Story metadata from the `game` block (this chapter) is carried into the
story file: `title`, `headline`, `author`, `copyright`, `release`,
`serial`, and `UUID`.
If `serial` is omitted Cosmos uses the build date in YYMMDD form. The `UUID`
is written as an IFID array in static memory, in the form Inform uses
(`UUID://<uuid>//`), so IFDB and similar tools can identify the game; the
compiler emits it without a warning.

### The banner

Cosmos prints the banner at game start, before `on start` output. It carries
everything Inform's banner does, and names both the compiler and the library:

```
The Brass Lantern
An Interactive Fiction by Stefan
Release 1 / Serial number 260626 / Arcturus 1.3 (Cosmos 1.3)
```

Line one is `title`. Line two is `headline` plus "by" and `author`, with
sensible defaults if either is absent; a declared `copyright` prints on its
own line beneath. The last line carries the release number, the serial, and
then the toolchain as a single final field: the compiler name and version
(Arcturus) with the library version in parentheses (Cosmos), since the
library ships inside the compiler.
The compiler and library versions are build constants, not author-set. A game
that wants its own opening first (a quote box, a pregame prelude) sets
`banner false` in the game block, which stops the automatic banner, and calls
`print_banner` whenever the banner should appear; never calling it leaves
the banner out entirely, and dead-code elimination drops it. The banner
manages its own vertical space: it flushes a pending paragraph break before
printing (so it splices cleanly after mid-game prose) and marks one after,
and at game start under a status bar the title sits DIRECTLY below the bar
(where Inform leaves a stray blank line). No story ever pads a banner.

The words in line two are language, not structure, so they come from the
language layer: `line_by` prints the connector (" by "; " de " in Spanish,
" von " in German) and `banner_headline` the default headline when a game sets
none ("An Interactive Fiction"; "Una aventura conversacional"; "Ein
Textadventure"). A pack localizes both, and a story may override either block
for a custom banner voice.

## Chapter 3: Rooms, things, and kinds

Two built-in categories introduce objects: `room` for locations, `thing` for
everything else. Both are kinds and can be extended.

```
room  <id> [of <kind>]
thing <id> [of <kind>] [in <location>]
thing <id> [of <kind>] in <room>, <room> ...
```

`of <kind>` sets the parent kind; `in <location>` sets the initial tree
position. The body is property settings, `on` handlers, an optional `grains`
block (chapter 18), `topic` blocks on a character (chapter 17), and, with
`summon.ambience`, `ambience` blocks (chapter 22).

An object can also live BACKSTAGE: `thing vlad of character in scope` places
it in an invisible room whose contents the parser always has in scope, in
every room, light or dark. That is the home of a companion who follows the
player everywhere, of their examinable parts, of anything the game should
always answer for; `move x to scope` and back stages things at run time (the
seen-but-unreachable chip in a droid's chest). A backstage object is never
listed (its room is never entered), so it defends itself in its own handlers:
make it `scenery`, or answer `on take` yourself. The whole mechanism folds
away in a game that stages nothing. The name `scope` is reserved as a
location only in games that use it.

A fixed object can be in scope in more than one room. The object tree gives each
object a single home, so a second (and third) room is a *span*: `in hall, vault`
puts the object in `hall` and spans it into `vault`, and a `spans a, b, c` line
in the body does the same for a scenery object with no single home (a moon seen
from three clearings). The object lives in one room and is referable from every
room it spans. Spanning is for non-movable objects (`fixed` or `scenery`); on a
movable object it is ignored, since a carried object's scope follows it. Its
headline uses are a two-sided door (one door object in both rooms it joins) and
wide scenery. A room's exit may name such a door, gating movement on it (02
chapter 12).

A span target may be a room KIND, not just a named room: `spans outside_room`
puts the object in scope in *every* room of that kind. The sun and the sky hang
over every outdoor room, the walls stand in every indoor one, and you name the
kind once instead of listing rooms:

```
kind outside_room of room     // a marker kind: no body needed

room meadow of outside_room
    name "Meadow"
    ...

thing the_sun
    scenery
    spans outside_room        // in scope in meadow and every other outside_room
    desc "It blazes overhead."
```

Every room is known at compile time, so the kind expands to its rooms as you
build; there is no runtime cost beyond the ordinary span. A room of a subkind
counts too (a `beach_room of outside_room` is an outside room). A kind used only
to tag its instances like this can be declared with no body at all.

Roomness itself flows through the kind chain: an instance of a kind OF ROOM
is a room in every respect (exits, spans, the start room), whether it was
declared with the `room` keyword or with `thing`. The keyword is a reading
aid; the chain is the truth.

A long span is not confined to one line. Every `spans` line on an object adds
to its set, so a wide scenery object can list its rooms (or kinds) across as many
lines as read well, and a line ending in a comma continues on the next (chapter 1):

```
thing river
    scenery
    spans north_bank, south_bank, ford,
          mill_race, weir, millpond
    spans estuary
```

```
room hallway
    name "Hallway"
    desc "A bare stone hallway. Worn steps lead down, north."
    north cellar

thing lantern in hallway
    name  "brass lantern"
    words brass, lantern, lamp
    desc  "A battered brass lantern."
    binary
```

The object identifier (`lantern`) is the code symbol; the `name` property is
the printed text. They are different. The `words` property is a third thing
again: the vocabulary the parser matches, holding the object's nouns and
adjectives as equal entries. `name` is printed but not typed; `words` is
typed but not printed. Adjectives are simply words in `words` (chapter 14).

A vocabulary word is normally a bare identifier. When the word itself is not
one, quote it: `words shuttle, obsidian, "obsidian-black"` admits the
hyphenated compound the player may type, since a hyphen does not split words
at the prompt. A quoted entry is one word; spaces are not allowed in it.

### Standard kinds

`thing` (base): `name`, `words`, `desc`; booleans `fixed`, `scenery`,
`hidden`, `concealed`, `wearable`, `worn`, `lit`, `edible`, `named`. Default
handlers for examine, take, drop, push, pull, turn, and the like (chapter 15).

`room`: `name`, `desc`, `lit` (true by default; a dark room declares `lit
false`), `visited`, and the direction properties (`north`, `south`, `east`,
`west`, `northeast`, `northwest`, `southeast`, `southwest`, `up`, `down`, `in`,
`out`, and the nautical `fore`, `aft`, `port`, `starboard`, whose player words
are the nautical granule), each an object defaulting `nothing`. A direction may name a room or a
door. Default `go <direction>` reads the matching property and moves the player,
or, when there is no exit, prints "You can't go that way." A room overrides one
direction with its own `on go <direction>`. The full movement model, including
computed exits and the blocked-direction fallback, is chapter 8.

Only attributes true for essentially every instance of a kind are kind defaults;
the rest are declared per instance. So `openable` is deliberately not a container
default (a bowl is a container that never opens), while a door is `openable` and
`fixed` because every door is.

`container of thing`: an optional `capacity`. Contents are children, in scope
when the player can see in: the container is `open`, is `clear` (see-through), or
has no lid at all (not `openable`), like a bowl or a basket. Declare `openable`
(and `open false`) to make a box with a lid that must be opened. Default open,
close, and put in.

`supporter of thing`: an optional `capacity`. Contents are children, always in
scope on top. Default put on.

`door of thing`: `openable` and `fixed` by default; declare `lockable`, `locked`,
and `unseal_with <key>` to make it lock. A door joins two rooms with the `in A, B` sugar: it
lives in one room in the object tree and spans the other (chapter 7), so it is
referable and operable from both sides. When a room's exit names the door (`east
oak_door`), crossing it is gated on the door being open and unlocked and lands
the player on its far side, with no author code. Default open, close, lock,
unlock, and the movement gate.

`character of thing`: `animate`; holds and wears objects; refuses being taken
(an animate object answers TAKE with its own line, not the scenery `fixed` one)
and routes the talk verb (chapter 12). `player` is the distinguished instance.

## Chapter 4: The player

The player is a seeded object every game already has. The language layer gives
it the standard self-words, so `x me`, `x myself`, `x yourself` (and each
language's own: `untersuche dich`, `examinate`) work in every game with no
author code; taking yourself answers its own line, and examining yourself
without a `player.desc` gets a proper default ("Are we going to admire
ourselves for a while or do we play an adventure game?") rather than an
object's message.

A game augments the player with top-level `player.` declarations:

```
player.words olivia, lund
player.desc "You are Olivia Lund, exobiologist."
```

`player.words` ADDS to the words already declared (the standard self-words
stay), so the heroine answers to her name and to "me" alike. `player.desc`
sets the description `x me` prints, and it takes the computed form like any
text property:

```
player.desc block
    say "You catch a glimpse of yourself: Olivia Lund. Once just an
         exobiologist, now a ghost haunting the graveyards of the stars."
```

Any player property can be set this way (`player.name`, or a custom flag);
`words` accumulates, everything else is set with the last declaration winning.

The `intro` property is an object's initial appearance in a room description.
While the object sits untouched in place, the room lists it with its `intro`
text, as its own paragraph, instead of the plain "You can see X here." The
moment the player first takes it, Cosmos sets the `moved` attribute and the
object reverts to the plain listing. `intro` replaces the whole generated line:
for a container, that includes the `(contains ...)` contents listing, on the
principle that an author who writes the prose owns the description (mention the
contents in the `intro` itself if they should show). A fixed or static object is
never taken, so its `intro` shows for as long as it is in view, which makes
`intro` the way to write set dressing that reads as prose rather than a list:

```
thing statue in hall
    name  "marble statue"
    fixed
    intro "A marble statue of a forgotten king dominates the room."
```

Containment is the Z-machine object tree: one parent per object, set with
`in`, changed with `move`, read with `holds`, `in`, and `for each`. The tree
is a separate axis from properties and is never reached with the dot.

CAREFUL, INFORM HANDS: Arcturus's `move` is the SILENT tree operation; it
does no bookkeeping of any kind. The Inform idiom "move lamp to player" (an
acquisition the player should be credited for) is the Cosmos block
`gain(lamp)`: it pays a scored thing's points exactly once and marks it
`moved` and `seen` before moving it, the bookkeeping TAKE would have done
(chapter 13). A bare `move lamp to player` leaves auto-scored points
unreachable and the object's `intro` un-retired. Rule of thumb: `gain` when
the player RECEIVES something, `teleport` when the player ARRIVES somewhere,
`move` for silent stage management behind the scenes.

Directions are object-valued properties on a room whose value is another
room. `north cellar` sets `north` to `cellar`; it can be changed at run time
(`change hallway.north to nothing`). Cosmos defines the direction names and
the GO verb that reads them.

Kinds are templates supplying default properties and shared handlers:

```
kind lamp_kind of thing
    binary
    lit false

    on switch_on
        now self is active
        now self is lit
        say "Light floods out."
```

An instance is declared with `thing` or `room` plus `of`:

```
thing brass_lantern of lamp_kind in hallway
    name "brass lantern"
    lit  false              // overrides the inherited default
```

A kind roots at `thing` or `room`. Inheritance is single parent in v1: a kind
names one parent with `of`, forming a chain (`small_box of container of
thing`).

Resolution order. An instance inherits every property and handler of its kind
chain. Re-declaring a property overrides the inherited default. For handlers,
the most specific runs first: the instance's own, then its kind's, then each
parent, then the Cosmos default. Each handler either ends, which consumes the
action so no more general handler or default runs, or ends with `continue` to
pass control to the next handler up the chain.

Multiple-parent composition (a thing that is both a container and a
supporter) is a deliberate non-goal for v1; model it as a kind chain, or say
so if a real game needs true mixins.

The standard kinds root the tree: `thing` and `room`, and of `thing` the kinds
`container`, `supporter`, `door`, and `character`. Each is an attribute (`obj is
container`), and each supplies the defaults universal to it: a `room` is `lit`, a
`door` is `openable` and `fixed`, a `character` is `animate` and refuses being
taken. `character` is the animate kind for anyone the player addresses, gives to,
or talks to, people and animals and robots alike. What each standard kind
provides is listed in chapter 3.

## Chapter 5: Properties

The author works with one concept, the property, and the compiler decides its
physical storage.

```
<name> <default>     // a property with that default; type from the literal
<name>               // shorthand: a boolean property defaulting to true
<name> list <n>      // a list property with capacity n, initially empty
<name> block         // a computed property; the indented block follows
```

The declared default's type fixes the property's type program-wide. Using one
property as two types is a compile error naming both sites.

Representation is chosen by the compiler in the same whole-program pass that
performs dead-code elimination:

1. A property whose values are only ever boolean across the whole program
   becomes an attribute bit. `if chest is locked` compiles to a bit test;
   `now chest is open` to a bit set. Zero marginal object bytes.
2. A property holding a number, text, object, list, or block becomes a
   property slot.

You write the same `change ... to ...` and `is` either way; the bit-or-slot
choice is invisible.

Computed properties. A property whose value is a `block` is evaluated by
running the block when the property is read. The block `say`s its own text;
reading the property (for example when Cosmos prints a room `desc`) runs the
block, and whatever it says is what the property prints. This is text only,
with one exception: a computed `desc` is the headline use, and a general
computed value property (a number decided at run time) is reported as a
compile error, because a read cannot tell a small value apart from the
block's address. The exception is a computed EXIT (a direction property that
is a block; chapter 8), where the value is a room and so is always
small enough to distinguish; there the block returns a room to allow the move
or `nothing` to refuse it.

```
room cellar
    name "Cellar"
    desc block
        if here is lit
            say "A damp cellar of black stone."
        else
            say "Pitch black. You feel cold stone underfoot."
```

Boundaries the compiler enforces:

- The 48-bit budget. More boolean-only properties than there are attribute
  bits spills the least-used to one-word slots holding 0 or 1; correct,
  slightly larger, never visible.
- Declare before you change. Object layout is frozen at build time, so a
  property cannot be created at run time. `change ruby.foo to false` when
  `ruby` never declared `foo` is a compile error. `add` is for lists only
  (chapter 9).

Unused declared properties are removed by dead-code elimination.

### Standard attributes

Cosmos predefines these boolean attributes. Set one by naming it (`fixed`),
clear it with `false` (`fixed false`), test it with `is`.

| Attribute | Meaning and usage |
|---|---|
| `fixed` | The object cannot be taken; it stays where it is. `take` refuses it. |
| `scenery` | Background detail: still referable for `examine`, but left out of the room's contents listing and not takeable (gives the scenery line). A game that wants what sits ON or IN scenery holders told anyway opts in once with `constant scenery_contents = 1`: each such holder then gets its own paragraph ("On the counter you can see a bell and a candle."), the knowledge model deciding per item (PunyInform's OPTIONAL_PRINT_SCENERY_CONTENTS, as a fold: off by default, zero bytes unused). Worked example: [examples/features/scenery-contents.storyarc](../examples/features/scenery-contents.storyarc). |
| `hidden` | Out of scope entirely until cleared: an undiscovered object, neither listed nor referable. Clear it when the object is revealed. |
| `concealed` | In scope and actable, but omitted from the room's contents listing (present but not spelled out in the description). |
| `wearable` | Can be worn; the `wear` verb accepts it. |
| `worn` | Currently worn. Set by `wear`, cleared by `drop` / `take_off`. Inventory tags it "(worn)". |
| `lit` | Gives light. On a `room`, the room is independently lit; on a thing, the thing glows and lights its location. Light is otherwise computed. |
| `edible` | Can be eaten; the `eat` verb consumes it rather than refusing. |
| `named` | A proper-named thing (Linda, Excalibur). Takes no article: `${the noun}` and `${a noun}` print just the name. |
| `an` | The indefinite article is "an", not "a". Derived from the name's first letter (a vowel -> `an`); set `an` or `an false` only for an exception (an hour, a unicorn). |
| `feminine` | Grammatical gender. Drives the Spanish articles and agreement (la lampara, Cogida), the German article (declared there with `die`, which sets this), and the English "her" pronoun on a character. Spanish derives it from a head noun ending in -a or a reliably feminine suffix; declare it where spelling cannot reveal it (la llave; an English Ruth). Masculine is the unmarked default. |
| `neutral` | The third German gender, declared there with `das` (das Buch, "es"). English and Spanish never read it. |
| `beyond` | Visible but not touchable: in scope and examinable (a chandelier overhead, a jar one shelf too high), while every touching action refuses ("${The noun} is beyond your reach.", msg_beyond, overridable). Conversation crosses the gap (an animate beyond person still answers ASK), and throwing AT a beyond thing stays legal: the arm reaches where the hand cannot. It is STATE: `now jar is not beyond` when the stool is gained. The refusal can carry the WHY (a field request): `beyond "Without the ladder, the top shelf might as well be the moon."` speaks your line instead of the generic one, and `beyond block` opens a computed body (the desc-block shape) for wording by state; a bare `beyond` keeps the pack's message. The property points BOTH ways: `now player is beyond` puts the PLAYER out of everything's reach instead, the mounted-on-a-horse case. While the player is beyond, only the arm's bubble stays touchable: themself, what they hold, and the thing they are on or in with everything it carries (the mare, her saddlebag, the apple inside); un-nested it collapses to self and held alone (hands bound, tied to a chair). Sight and speech cross the gap exactly as above, and EXIT is never blocked, so dismounting always works. Set it in the after phase, once the boarding has really happened: `on after enter mare / now player is beyond`, and `on after exit mare / now player is not beyond`. The player's refusal can carry its own why, settable at RUNTIME: `change player.beyond_why to "You can't reach that from up here."` speaks your line, `change player.beyond_why to nothing` reverts to the pack default (the slot is allocated automatically for any game that writes it). Static faraway decoration needs no object at all, that is a grain's job (chapter 18); beyond is for distance that matters to the model. Costs nothing unused. Worked example: [examples/features/beyond.storyarc](../examples/features/beyond.storyarc). |
| `shiftable` | The thing can be pushed through an exit, the player following (PUSH CRATE NORTH). Section 10. |
| `restless` | A background performer: its `on each_turn` fires EVERY turn, wherever the object is, not only in scope. Work follows the performer's nature; prose follows scope: what a restless object prints while out of scope is discarded by the system, so the handler writes its `say` unconditionally and the player hears it exactly when the performer shares their scene: present, arriving, or leaving before their eyes (in scope at either end of its turn); a turn taken wholly offstage is silence. It never fires twice. It is STATE: declare `restless` to be born performing, or arm and disarm at runtime (`now guard is restless`, `now guard is not restless`), with no declaration needed anywhere; a `when` guard on the handler still decides whether an armed performer acts this turn. A game with no restless object pays nothing (the walk, the mute buffer, everything folds away). Section 12; worked example: [examples/features/daemons-and-timers.storyarc](../examples/features/daemons-and-timers.storyarc). |
| `pluribus` | Grammatical number: ONE object that is grammatically plural (the scissors, the boots; e pluribus unum, many speaking through one). The articles read it ("some scissors"; German's bare indefinite plural and die/die/den/der by case; Spanish los/las, unos/unas), `${is x}` agrees (is/are, ist/sind, está/están), and the core messages conjugate ("The scissors stay exactly where they are."). NOT the plurals granule, whose group words sweep several distinct singular objects ("take coins"). Costs nothing in a game that never sets it. |
| `binary` | A two-state device: a lamp, a lever, a valve, a machine. The library owns the state the way it owns open/shut: switching it on sets `active` and reports; switching it off clears it; asking for the state it already holds is refused honestly ("is already on/off") in the verb contract, before any handler. A binary that also declares `lit` is a GLOW thing: the default flip carries the light with it, so a working lamp is these two lines and no code. An author's own `on switch_on` / `on switch_off` handler overrides the default for flavor and then owns the flip (`now self is active`, plus `now self is lit` on a glow thing): validation stays with the library, the response is yours, the same split as everywhere in the pipeline. `switchable` is accepted as a compatibility spelling of `binary`. |
| `active` | The binary state, tested like any attribute (`if noun is active`) and flipped by the library's switch defaults, or by your flavor handlers. |
| `openable` | Can be opened and closed; the `open` / `close` verbs apply. |
| `open` | Currently open (a container or door). Set by `open`, cleared by `close`. A closed container hides its contents from scope. |
| `clear` | A see-through container (a glass jar): its contents are in scope and referable even when closed. An open or `clear` container exposes its contents; a closed opaque one shields them. |
| `seen` | Set once the player has been shown an object (a content of an open container, something taken or examined). A closed opaque container still lists the contents the player has `seen`, so they are not forgotten when put away; contents never seen stay hidden until the box is opened. Cosmos manages this; you rarely set it. The full container knowledge model is in chapter 6. |
| `lockable` | Can be locked and unlocked. LOCK / UNLOCK read the object's state: with the object's `unseal_with` opener held, they succeed; without it (or with no opener defined) they refuse ("you don't have whatever it wants"); UNLOCK on a thing that is not `locked`, or not `lockable` at all, simply opens it. |
| `locked` | Currently locked; blocks `open` until unlocked. A `lockable` + `locked` thing with NO `unseal_with` is a keyless lock the player cannot open by the verb (no opener to hold): the story springs it itself with `now x is not locked` (a chest you pry open with a crowbar). |
| `scored` | Managed by `scoring` (chapter 19): the compiler sets it on every room and takeable thing; write `scored false` to exempt one. Set it by hand only in a game without `scoring` that wants a single classic auto-payer. |
| `visited` | The room has been entered before (Cosmos sets it on entry). Use it to vary a room's description on return. |
| `moved` | Set the first time the player takes an object. While clear, the object shows its `intro` text in a room description instead of the plain listing. |
| `animate` | An animate agent (a person, animal, robot, or AI). The conversation and give verbs apply only to the animate; the `character` kind sets it by default, and animate objects refuse being taken. |
| `component` | This thing is PART OF the thing it sits `in` (a lever in a machine, a button on a panel; the equivalent of Dialog's `#partof`). The object tree carries the relation, so the part follows its whole wherever the whole moves; the attribute grants what a plain thing's insides never get: the part is in scope whenever the whole is, `take` answers that it is part of it (`msg_part_of`), and it never lists as the whole's contents. Make the part `on pull` / `on push` handlers do the machine's work. To detach one in play, clear the attribute and move it. A game with no components pays nothing (`any_components`). |

The standard kinds are set by `of <kind>` and tested with `is <kind>`: `thing`,
`room`, `container`, `supporter`, `door`, `character`.

**Kinds are effectively unlimited, and cost you nothing until you test one.**
A kind is Arcturus sugar, not a Z-machine concept: the Z-machine has no classes,
only objects, and Arcturus keeps it that way. The Z-machine gives each object 48
attributes (single-bit true/false slots), and a kind earns one of those slots
only where your program actually writes `obj is <kind>` and needs to ask at run
time. A kind used purely to organize, to share handlers or properties, or to
span scenery is resolved entirely at compile time and consumes no attribute at
all, so declare as many of those as your world wants.

When you do test a kind, it takes a fast one-byte membership test from the
attribute slots your genuine object attributes leave free, the busiest-tested
kinds first. If you test more kinds than those slots can hold, the rest fall
back automatically to a catalog membership scan: a little slower, but only on
the least-tested kinds and only on a real machine's cold path (the scan reads
resident memory, so even an 8-bit target never pages a disk for it). Either way
the result is identical and you never meet a "too many kinds" wall.

The one real ceiling, then, is the Z-machine's own: 48 genuine object attributes
(the mutable per-object true/false state you set with `now`). Kinds never count
against it, so `arcc -s` reports the two separately, for example `attributes
26/48, kinds 63 (41 spilled to catalogs)`. Read that as: 26 of your 48 real
attributes are in use (22 free), and all 63 kinds work, 41 of them via the
catalog scan. If you ever do run out, it is genuinely attributes you are short
of, not kinds, and the compiler says so. (This is distinct from the `flag`
feature, which declares a global boolean, not an object attribute.)

### Standard value properties

| Property | Type | Meaning and usage |
|---|---|---|
| `name` | text | The printed short name ("brass lantern"). Distinct from the object's id and from `words`. |
| `desc` | text | The description shown by `examine` (and on first look at a room). |
| `words` | list | The vocabulary the parser matches: the object's nouns and adjectives, as equal entries. Typed but not printed. |
| `tag` | text | A short state qualifier appended to the object in listings and the inventory: "a fluid canister (full)". Usually computed (`tag block`); print with `show`, not `say`, so it stays inline. The parentheses come from the listing. |
| `plural` | list | The words that name this object AS PART OF A GROUP (`plural coins` on each coin): "take coins" acts on every match in scope. Only with `summon.plurals` (chapter 22); ignored otherwise. |
| `intro` | text | An object's initial appearance in a room, shown as its own paragraph while the object is untouched (`moved` clear). |
| `appearance` | text | The paragraph the object ALWAYS owns in a room description, replacing its listing line and never expiring ("The keeper is trimming the wick."): Inform's describe, Dialog's `(appearance $)`. A computed block (`appearance block`) words it by state; checked before `intro`; `hidden`/`concealed` still suppress. Costs nothing in a game that never sets one. |
| `capacity` | number | How many objects a container or supporter holds. |
| `article` | text | The definite article, verbatim, when derivation cannot reach it: `article "las"` (las tijeras), `article "el"` (el agua). |
| `indefinite` | text | The indefinite article, verbatim: `indefinite "unas"`, or an English mass noun with `indefinite "some"` ("You can see some water here."). |
| `unseal_with` | object | The opener that locks and unlocks this one (for `lockable` things): a key, a keycard, a code object, whatever fits the fiction. It must be HELD to work. Omit it for a keyless lock only the story can spring. |
| `arc_image` | number | Optional. A room's picture, named by its resource id (`arc_image 8`, or a constant that folds to one). Shown on an aware interpreter, ignored on a standard one. Section 6b. |

`score`, `max_score`, and `turns` are runtime globals, not object properties (02
chapter 1).

## Chapter 6: Containers, supporters, and the object tree

Containment is the Z-machine object tree: one parent per object, reached with
`in`, `move`, `holds`, and `for each`. The tree stores only parent and child.
To TEST where something is, use the predicate: `if lamp is in chest`. To READ
where something is (print it, compare it, walk upward to the room), use
`parent_of(obj)`, which returns the holder itself, or `nothing` when the
object is nowhere (appendix D, the author's toolkit).

The in-versus-on distinction is carried by the parent's kind: a child of a
`container` is in it, a child of a `supporter` is on it, a child of a
`character` or the player is carried, or worn if its `worn` property is set.
Cosmos uses the parent's kind to choose the preposition when listing or
describing contents and to decide scope.

Two small services for a story describing the player's outfit (a custom
`player.desc block`, say): `worn_count` is the number of things the player
wears, and `list_worn` prints them as a punctuated list ("a hat, a cloak
and a ring"; German declines the articles, Spanish joins with "y") with no
framing and no newline, returning the count, so the story writes its own
prose around it. Both cost nothing unless called (dead-code elimination),
and each language layer words its own.

### The container knowledge model

Cosmos tracks what the player has learned, not only what is in view this instant,
and lists a container's contents by that knowledge. This is what makes room
descriptions read the way memory actually works, and it is a feature few other
systems have.

The switch is the `seen` attribute, which Cosmos sets on an object the moment the
player has been shown it: listed inside an open (or `clear`) container, resting on
a supporter, taken, or examined. From then on the object is known to the player.

Whether a container spells out its contents follows that knowledge, not just its
lid:

- An **open** container lists everything inside, and marks each content `seen`.
- A **`clear`** container (a glass jar) lists everything, open or shut, since its
  contents are always in view.
- A **closed, opaque** container lists only the contents the player has already
  `seen`. A content the player has never seen is not listed at all, and is not
  referable: there is no x-raying a shut box.

So a box the player has never looked into is described bare, and the ring inside
stays unknown:

```
> look
You can see an iron box here.

> examine ring
You see nothing of the sort here.
```

Open the box and Cosmos reveals what is inside, describing it and marking it seen:

```
> open box
Open. Inside you find a gold ring.
```

Close the box again, and the ring is now remembered. Because the player knows it is
there, the room keeps listing it, even with the lid shut:

```
> close box
> look
You can see an iron box (contains a gold ring) here.
```

Knowledge sharpens the parser's answers too. Once the player has seen the ring,
naming it while the box is shut earns a reminder to open the box, not a flat
denial, because the object is known but out of reach:

```
> examine ring
You'll have to open the iron box first.
```

A content the player has never seen still gives the ordinary "you see nothing of
the sort here", since the player has no reason to believe it exists. Cosmos manages
`seen` throughout; an author touches it only to pre-seed knowledge (something the
character already knows about) or to clear it and make the character forget. The
related attributes are `open` (the lid), `clear` (see-through, always shown),
`concealed` (present but left out of a listing), and `hidden` (out of scope
entirely until revealed).

## Chapter 7: Scope, light, and darkness

Scope is the set of objects the parser considers when resolving a noun, and
that an action may touch. Cosmos computes it each time it parses a noun.

In scope, when the location is lit: the room `here` and its direct contents
(minus `hidden` and concealed objects); everything the player holds or wears,
recursively; the contents of any in-scope `container` that is `open` or `clear`
(see-through); the contents of any in-scope `supporter`; and objects reached
through these recursively. The noun matcher follows exactly this rule, recursing
into open and `clear` containers and onto supporters, so a coin in an open box is
referable while a coin in a closed opaque box is not: the closed lid shields its
contents from scope until the box is opened. A `clear` container (a glass jar) is
the exception, exposing its contents while still shut.

A `component` (chapter 5, the standard attributes) rides its own scope rule: the part
is in scope whenever its whole is, whatever the whole's kind, so a lever
declared `component` and placed in a plain machine is referable while an
ordinary thing dropped "inside" a plain thing stays out of scope (a plain
thing has no insides to see into). The rule, like the take answer and the
listing exclusion, folds away in a game with no components
(`any_components`).

One place stands outside the room-and-carry rule: the BACKSTAGE scope room
(chapter 3). An object placed `in scope` (or moved there at run time,
`move x to scope`) is in scope in every room, light or dark: the home of a
companion who follows the player, of their examinable parts, of anything the
parser should always answer for. Backstage contents are never listed, since
their room is never entered, so they defend themselves in their own
handlers. The whole mechanism folds away in a game that stages nothing.

Two predicates Cosmos provides for conditions: `<obj> is visible` (in scope
and the location lit; examining needs this) and `<obj> is reachable` (visible
and not behind a closed container; taking and most physical actions need
this). The open-air case of the same doctrine is the `beyond` attribute
(chapter 5): visible and examinable while every touching action refuses,
toggled with `now` as the geometry changes. `hidden` removes an object from scope entirely until cleared.
`scenery` keeps it referable for examining but omits it from contents
listings and refuses taking.

The room description paragraphs an object can own, in the order checked:
`appearance` (always, never expiring, computed by state if a block),
`intro` (until the object is first taken), and the plain listing
("You can see a broom here."). `hidden` and `concealed` suppress all
three. The appearance check folds away in a game that sets none
(`any_appearance`).

Every plain-listed object shares one combined sentence, the classic
idiom: "You can see a MRE, a lantern and a backpack here.", never a
line per item. Objects with their own `appearance` or unexpired `intro`
keep their own paragraphs above it. The closed-openable qualifier and
a holder's contents ride along inline per item ("a pine box (closed)").
The sentence is the language layer's `list_room`, which speaks each
item through `name_room_item`; a single object goes through `list_item`
unchanged, so a game that overrides `list_item` to reword its listing
keeps that wording for the single case, and overrides `list_room` to
reshape the sentence itself. Which objects are plain is the loop's
`room_plain` predicate, shared between the count and the printing.

Scenery holders can join the room description too: with
`constant scenery_contents = 1` declared once, every scenery container or
supporter in the room gets its own paragraph after the listing pass
("On the counter you can see a bell and a candle."), worded by
`scenery_holder_line` in the language layer, the knowledge model deciding
per item exactly as in chapter 6: a closed opaque holder keeps its
secret until first opened, then is remembered. Empty holders print
nothing. Off by default and folded away entirely when the constant is
absent (examples/features/scenery-contents.storyarc).

### Light and darkness

Cosmos computes light automatically. The location is lit when the room's own
`lit` is true, or an in-scope object has `lit` true and gives light. A room's
`lit` means the room is independently lit; a thing's `lit` means it is
glowing.

When the location is dark, scope collapses to what the player carries, room
contents are not visible, and visibility-dependent actions report "It is
pitch dark, and you can see nothing." Movement is still allowed unless a room
blocks it. Because light is computed, authors rarely set it by hand; a game
that needs special behavior overrides at the room, as the Cloak bar does.

If you are coming from systems like Inform 6, PunyInform or Dialog, read
this section carefully because Arcturus behaves differently to what you
are used to.

Arcturus adapts to the so-called IF "Cave Rule", which is a more modern
approach to how the player can interact with darkness. The rule itself:
While the parser allows the player to list the items they are carrying,
they generally cannot examine or interact with those items if the action
requires visibility. The interactive fiction logic here is that a person
in pitch blackness can still feel the shape and weight of the items in
their hands well enough to count them, but they cannot see visual details
like text or color.

Arcturus is analog to Inform 7 in that context. What this means: by
default the player is allowed to list the inventory (the cave rule), but
they generally cannot EXAMINE or interact with those items if the action
requires visibility (e.g. READ). For those that want to be more
restrictive: in Inform 7 you can create a simple rule if you want to
prevent the player from listing the inventory in darkness. This
translates almost 1:1 to the Arcturus handler syntax:

```
on inventory when is_lit is false
    say "It is far too dark to rummage through your belongings."
    stop
```

## Chapter 8: Movement and directions

The player moves by typing a direction, bare (NORTH, N) or with GO, and a
room's exits are properties naming where each direction leads. A
`direction` declaration maps player-facing words to a direction property:

```
direction north     "north", "n"
direction northeast "northeast", "ne"
```

The property name (`north`, `northeast`, `up`, `in`, ...) is one of the standard
directions and never changes; the quoted words are the player's vocabulary. The
standard set also holds the four nautical directions (`fore`, `aft`, `port`,
`starboard`) for a vessel or a deep space craft; their player words, with
ALOFT and BELOW riding `up` and `down` and the `dirs_nautical` gate for
going ashore, are the opt-in nautical granule (chapter 22), while the
properties are always legal in exits and handlers and, like every
direction, cost nothing unused. Like
verbs and messages, direction words are part of the language layer, so a language
pack redeclares them (`direction north "norte", "n"`) and Cosmos ships the English
set. A game rarely writes these; it summons a language, or uses the default
English. Selecting a language is one summon: `summon.language "spanish"` compiles
that language layer in place of English (chapter 14).

CUSTOM DIRECTIONS. When a game needs directions of its own (the compass
fails on a ringworld as surely as on a ship), it declares them, right in
the story, and the declaration CREATES the direction:

```
direction widdershins "widdershins", "wid"
direction turnwise    "turnwise", "turn"
```

The player types WIDDERSHINS (or WID), rooms write the exit with the new
property (`widdershins rim`), and everything the compass has comes along:
the bare typed word, `on go widdershins` handlers, `if way is
widdershins`, computed exits, teleports, catalogs of directions, and the
exit list speaking the declared word. Custom and standard directions
coexist freely, nautical included.

The cost is the author's call, and it is flagged plainly: each custom
direction used by a room consumes one Z-machine property slot from the
same stock everything else draws on, a hard ceiling of the machine
(`arcc -s` shows the running count, "properties 32/62"). Declared but
never walked, it costs only its dictionary words; declared not at all,
nothing. A `direction` declaration naming an EXISTING direction property
adds vocabulary to it instead (that is how the nautical granule words
fore and aft, and how ALOFT rides `up`), and the canonical word the
output speaks follows the most specific declaration: the game's own
beats a granule's beats the language layer's.

A room's exit is written with this property name, not the word: `north cellar`,
`east door` (chapter 3). So an exit stays in the fixed English name even in a
translated game (`east puerta`), while the player types the localized word
(`este`). A named exit target is checked at compile time: it must be a
declared room, a door-kind thing, or a computed block (`nothing` is the
explicit no-exit), so a typo'd room name is a compile error rather than a
silent runtime "There's no exit in that direction.", and an exit can never
point at a plain thing (which would walk the player inside it). The same split runs through the language: the fixed identifiers a game's
code uses (`thing`, `room`, `openable`, the direction properties, the grain
actions in chapter 18) are English; only what the player reads and types is
localized.

### Movement and blocked directions

The `go` verb reads the room's direction property for the chosen direction and
moves the player to the room it names. The model has four tiers, from most
specific to least, with no per-room boilerplate required:

1. A static exit: `north cellar` names the destination room directly.
2. A computed exit: a direction property may be a `block` (chapter 5), so
   an exit can depend on world state. The block returns a room to allow the
   move or `nothing` to refuse it:

   ```
   room cave_mouth
       name "Cave Mouth"

       north block
           if portcullis is open
               return inner_hall
           return nothing
   ```

   Because Cosmos reads every live direction to list exits (see
   `verbose_exits` in chapter 22), direction blocks must be free of side
   effects: reading an exit may happen more than once per turn.

   A story reads an exit the same total way Cosmos does, with
   `exit_dest(room, direction)`: it returns the destination, running a
   computed exit's block when one stands there, and folds to a plain
   property read (`here.(way)`, chapter 9) in a game with none.
3. A per-direction override: `on go <direction>` runs custom logic or a custom
   message for one direction, as the Cloak of Darkness foyer does for north.
   Ending the handler consumes the action; `continue` falls through to the
   normal move.
4. A per-room fallback: `on go other` fires for any direction that has no exit
   and no specific `on go <direction>` handler. It is the room-wide
   "you cannot go that way here" hook, replacing Inform's `cant_go` without a
   new property:

   ```
   room ledge
       name "Narrow Ledge"
       east cliff_path

       on go other
           say "You can only go east from here."
           stop
   ```

   `other` is not a direction; it is the reserved fallback operand of `go`,
   matched only after a real exit and a specific direction handler have both
   been ruled out, so genuine exits and specific overrides always win.

When a direction has no exit and the room defines no `on go other`, the global
behavior applies: by default "You can't go that way.", or, with
`summon.verbose_exits` (chapter 22), an automatically listed set of the room's
available exits.

### The way family: querying the room graph

The map the exits weave is queryable from any handler, no summon needed;
each block folds away unless called. A direction is named by its INDEX (the
same currency as `exit_prop(i)`), and absence is always the constant
`no_way`, which is -1: never 0, because 0 is a real direction index and a
real direction property is a real value. Comparing against `no_way` is
always unambiguous.

- `way_between(a, b)`: the direction index leading from room `a` straight
  to room `b`, or `no_way` when they are not adjacent. This is the MAP:
  a door between them is read through to its far side whatever its state,
  because adjacency is topology, not passability.
- `way_toward(a, b)`: the first step of a shortest path from `a` to `b`
  as a direction index, or `no_way` when no path exists (or when `a` is
  already `b`; that case belongs to the caller). This is the WALK: a
  breadth-first search over the room graph. A door passes only where
  `door_bars` allows; a room joins the path only where `path_admits`
  allows. Called each turn, it walks an actor one step per turn toward
  any goal.
- `door_bars(d)`: the per-door seam the walk consults. The default bars
  any door that is not open; override it and a bead curtain never bars,
  or a haunted arch bars even when open.
- `path_admits(r)`: the per-room seam the walk consults; everything is
  admitted by default. The pathfinding granule (chapter 22) narrows it to
  the player's knowledge while a GO TO or FIND is resolving; an author's
  own calls, an NPC walking toward a goal, are not bound by what the
  player has seen.

Computed exits are read during the search exactly as the go handler and
verbose_exits read them, which is why direction blocks must be free of side
effects (the rule above). A program that never calls `way_toward` carries
none of the search's scratch memory.

## Chapter 9: Statements, control flow, and expressions

Statements appear inside `on` handlers, `block` bodies, and computed
properties.

A block may have an EMPTY body: it is a seam, a named point another layer
overrides (the statusline granule claims `screen_ready` to raise its bar
before `on start` prints). A statement-call to a block whose final body
is empty emits no code at all, so an unclaimed seam costs zero bytes.

`let` introduces a local: `let n = 0`. A local lives to the end of the
BLOCK that declared it: a `let` inside an if branch or a loop body ends
with that branch. To set a value differently per branch, declare it
before the if (`let z = 0`) and `change z to ...` inside the branches
(the compile error teaches this shape when it sees the pattern).

`change ... to ...` is the universal setter, for a local, a global, or a
property:

```
change n to n + 1
change score to score + 10
change ruby.desc to "The ruby sits exposed."
```

`now ... is / is not ...` is boolean-set sugar: `now ruby is lit`,
`now door is not locked`.

`move ... to ...` is the only tree operation; `nothing` detaches:

```
move knife to player
move note to nothing
```

Three calls elevate `move` for the set pieces a silent tree operation
would get wrong, each doing the bookkeeping its verb would have done
(all three in chapter 13). `teleport(dest)` moves the player without
walking (a crash landing, a transit pod) and describes the arrival.
`gain(obj)` hands the player an object without TAKE (a panel pried open,
a mechanism yielding its prize); chapter 3 has the move-versus-gain
warning, and with `scoring` on both pay exactly like their verbs
(chapter 19). `convey(vehicle, dest)` moves a VEHICLE the player rides
(a boat, a lift, a mine cart): the player sits inside the vehicle in the
object tree, so moving the vehicle carries them, but what a plain `move`
cannot do is refresh `here`, the player's cached room, and scope then
still answers for the room left behind (the vehicle trap). `convey`
moves the vehicle, updates `here` when the player is aboard, and
describes the arrival, so a self-driving boat is one line in
`on each_turn`: `convey(boat, here.south)`. See
[examples/features/vehicles.storyarc](../examples/features/vehicles.storyarc).

The general form is `perform`: run any action as part of the current turn,
exactly as the player's own command would dispatch it, refusals, handlers,
and messages included (Inform's `<<take book>>`, Dialog's `(try ...)`):

```
perform("take", book)         // the full TAKE, report line and all
perform("go", west)           // a real move; a direction rides the way slot
perform("give", coin, bob)    // two nouns
if perform("open", chest) is false
    say "The chest defies you."   // 0 means the action refused
```

The action name is checked at compile time; the enclosing command's own
operands are restored afterwards (a later AGAIN still repeats what the
player typed), and no extra turn passes: it is one turn's work. Where
`teleport` and `gain` exist they stay the better word (they are silent
about the how); `perform` is for when you want the verb's whole voice.
Costs nothing in a game that never calls it.

One trap, named plainly: perform re-enters the WHOLE chain, the calling
handler included. An `on burn` that calls `perform("burn", ...)` unguarded
dispatches straight back into itself, forever (the interpreter dies at the
prompt). To run your checks and then let the default happen, the chain's
own word is `continue`, not perform:

```
on burn
    if second is nothing
        say "You need something to light it with."
        change refused to 1
        stop
    continue                  // the default burn takes it from here
```

perform inside a handler is for OTHER actions (a redirect, like climb
boarding via enter), or for re-dispatching the same action past a `when`
guard or operand pattern the re-entry will fail. The compiler notes the
unguarded self-perform shape at compile time.

`add ... to ...` and `remove ... from ...` operate on list properties only:

```
add "ruby" to ruby.synonyms
remove "old" from chest.synonyms
```

`say` prints text or a value followed by a line break; printing a number prints
digits, an object prints its `name`: `say "Score: ${score}."`. `show` prints the
same way but without the trailing line break, for building one line from pieces:
`show("You can only go ")` then more `show`/`say` calls finish the line, the last
one ending it. Both honor the library's paragraph spacing (a pending blank line
is flushed before either prints). Use `say` to finish a line, `show` to build
one.

`stop` ends the current handler or block immediately; in an action handler
that also consumes the action (chapter 11). `continue` ends the current
handler and passes the action to the next, more general handler (chapter 11).

`alter` REGISTERS an action's report in your own words, keeping the
default MECHANICS: give your line (or compose one under `alter block`,
the same shape a computed property takes; a bare `alter` on its own line
opens the same body), then `continue`. The line prints at REPORT TIME,
instead of the library's success line, and only if the action actually
succeeds: a refused take, a walk with no exit, never fires it, so the
custom narration cannot narrate a success that did not happen (a field
report). On a successful GO it prints just before the new room's
description. A plain `say` before `continue` keeps its classic meaning,
flavor printed immediately and regardless of outcome, so the two cover
the attempt and the success between them. The registered body runs after
the handler has returned: it reads globals, `noun`, and `self`, but not
the handler's own `let` locals.

The `continue` is REQUIRED, not decoration: a handler that alters but
never continues dies at the handler level (the general handler design,
chapter 11), so it consumes the action, the library's success site never
runs, and your report can never fire, nor does the action itself happen.
The compiler notes this at build time. Put `continue` in the handler
body, one indent out from the alter; it does not belong inside an `alter
block`, which is the report's text, not handler flow.

```
on take
    alter "The idol comes free with a reluctance you can feel."
    continue

on drop
    alter block
        show("You set the idol down")
        if here is shrine
            show(", and the shrine seems to sigh")
        say "."
    continue
```

Costs nothing in a game that never alters (any_alter). Worked example:
[examples/features/alter.storyarc](../examples/features/alter.storyarc).

`finish` ends the game, printing its final message; Cosmos then reports the
final score (the same line SCORE prints) and offers the classic RESTART,
RESTORE, QUIT prompt, answered in the pack's own words (chapter 13).
`death` is the same statement for an ending the player may take back: its
prompt adds UNDO, which rewinds the fatal command itself, while a `finish`
(a victory, a completed story) stays final; a won game must stay won.
Write `finish "*** You have won ***"`, `death "*** You have died ***"`.

### Control flow

`if`, `else if`, `else`, by indentation:

```
if ruby is lit
    say "It glows."
else if ruby is hidden
    say "You see nothing of note."
else
    say "A dull red stone."
```

`while`:

```
while count > 0
    say "."
    change count to count - 1
```

`for each ... in / of ...`:

```
for each item in player        // tree children of an object
for each word in ruby.synonyms // list elements
for each door of room          // every instance of a kind
```

The tree walk is MOVE-SAFE for its own loop object: the next child is noted
before the body runs, so emptying a container the obvious way just works,
with no drain idiom to learn:

```
for each x in bucket
    move x to here
```

Moving OTHER objects out of the same parent inside the body remains the
author's own risk, as it has been on every Z-machine library.

`switch`, on any value, with no fall-through; a `case` may list several
values, and `else` is the default. A case is a compile-time value: a
number, a string, a direction, an object, or a declared constant, so a
stored direction switches as naturally as it compares (`switch d / case
north`, the maze-route shape):

```
switch reply
    case "yes", "y"
        say "Good."
    case "no", "n"
        say "As you wish."
    else
        say "I did not understand."

switch count
    case 0
        say "None."
    case 1
        say "Just one."
    else
        say "Several."
```

A number switch compiles to a compact comparison chain. A string switch
compiles to equality tests, cheapest when the values are dictionary words
(parser tokens), which is the common case for topics and replies.

### Expressions and operators

Arithmetic on numbers: `+`, `-`, `*`, `/` (integer), `mod`.
Comparison: `<`, `>`, `<=`, `>=`.
Equality and identity: `is`, `is not`, for numbers, booleans, objects.
Boolean property test: `<obj> is <property>` and `<obj> is not <property>`
when the right side names a declared boolean property of the object:

```
if lantern is lit
if door is not locked
```

Kind-membership test: `<obj> is <kind>` and `<obj> is not <kind>` when the right
side names a kind, testing whether the object is of that kind (any kind in its
chain):

```
if hook is supporter
if noun is not container
```

The direction `in` doubles as a keyword (the containment operator, and the
copula form `x is in y`). Where only a value can stand, it is the direction:
`perform("go", in)` and `if way is in` both read naturally, while
`x is in y` with an operand after the `in` stays the tree test.

Predicate test: `<value> is <block>` and `<value> is not <block>` when the right
side names a block with exactly one parameter: the block is called with the left
side and the test is its truth (nonzero). So the library's predicates read the
way the attributes do:

```
if lamp is visible
if coin is not reachable
```

The block should return 0 or 1; `visible(lamp)` remains equivalent. Blocks of
any other arity are ordinary values here and keep the call-them-with-parens
error.

Disambiguation: when the right operand is a bare identifier, `is` is a property
test if it names a declared boolean property, a kind-membership test if it names
a kind, a predicate test if it names a one-parameter block, and otherwise an
equality. A name that is both a boolean property and an object (or a kind and an
object) used with `is` is a compile-time clash to rename.

Logic: `and`, `or`, `not`, short-circuiting.
Property read with the dot, chainable: `ruby.value`, `hallway.north.name`.
The name after the dot is fixed at compile time; to read a property CHOSEN
AT RUN TIME, parenthesize an expression that yields it: `here.(way)` reads
the exit in the direction the player chose. (A bare `here.way` does not
work, and the reason teaches the form: it would look up a property
literally named "way", and no such property exists. `way` is the global
holding the chosen direction, a direction IS its property, and the
parentheses say "evaluate this, then read the property it names".) The form
takes any property-valued expression, so a block can receive a direction as
a parameter and probe it: `if here.(dir) is nothing`. For the common
question behind all this, WHICH ROOM LIES THAT WAY, there is also the total
form `exit_dest(here, way)`: it reads the exit and, when a computed exit
block stands there (chapter 8), runs it and returns the room it
allows, folding to the plain read in a game with no computed exit. Prefer
it when your game computes exits; otherwise the two are the same read.
An `is` comparison distributes over `or` when the extra operands are bare
values: `if way is aft or north` means `way is aft or way is north`, and
chains extend it (`aft or north or up`). The negated form means NEITHER:
`if way is not aft or north` is `way is not aft and way is not north`, the
sentence's own reading. Only compile-time values distribute (directions,
objects, numbers, constants); a flag or global after `or` stays the
condition it always was (`if lamp is lit or emergency_power`), so nothing
existing changes meaning. A bare value the sugar cannot claim still earns
a compile note naming the cure.

Tree tests: `player holds lantern`, `lantern in player`, and the transitive
`coin within player`, true anywhere in the tree however nested (the coin in
a purse in a bucket the player holds; Inform's IndirectlyContains). All
three are total (`nothing` answers false); negate `within` with
`if not (coin within player)`. It costs nothing in a game that never asks.

The right side of `within` can be anything, a ROOM included: containment IS
the tree, and a room is the tree's top. `coin within treasure_chamber` is
true with the coin nested in a chest there, and `coin within here` asks
whether something is physically in the current room, however buried (a
carried coin is within whatever room the player stands in). Two edges:
`within` answers physical containment only, so a spanning scenery object is
within its home room alone (scope is `visible`'s business, not the tree's),
and a two-sided door seats in one place, so probing doors with `within` may
surprise.

Built-in references in handler and block bodies: `self` (the enclosing
object), `player`, `here` (the current room), `noun` and `second` (the
matched objects), `nothing`. Cosmos also provides `<obj> is visible` and
`<obj> is reachable` (scope rules in chapter 7).

Swapping one object for another. When an action replaces a thing with a
different one, moving the old thing away and a new one in (Bob knocked out
becomes an Unconscious Bob object), do it with `swap(old, new)`:

```
on attack
    say "You punch him and he falls, unconscious."
    swap(self, unconscious_bob)
```

`swap` moves `new` into `old`'s exact place in the tree, removes `old`, and
hands off every live reference the current turn is holding: `noun`, `second`,
and the pronouns IT / HIM / HER / THEM. That matters because Cosmos remembers
a command by its resolved objects, not its text: without the hand-off, the
old thing has left, so AGAIN would replay a noun that is no longer there
("You see nothing of the sort here.") and a following "hit him" would dangle.
With `swap`, AGAIN repeats the blow on the unconscious Bob and "examine him"
finds him, because the turn's bindings moved with the swap. Doing the two
`move`s by hand works too, but then you must also `change noun to new` (and
the pronouns) yourself; `swap` is the one call that never forgets. It costs
nothing in a game that never swaps.

## Chapter 10: Blocks

A block is a named routine. It takes arguments, may `return` a value, and is
called from your code:

```
block points_for(item)
    return item.value * 2

block describe_exit(dir)
    if here.(dir) is nothing
        say "no exit"
    else
        say "a way ${dir}"
```

Calling: `points_for(ruby)`, `describe_exit(north)`. Parameters are values
and need no type annotation. A block takes at most SEVEN parameters, and a
call passes at most seven values: the Z-machine's own call ceiling, which
the compiler enforces with a clear error either way; a bigger payload
travels as a catalog or a matrix, passed as one value. Recursion is
allowed, bounded by the Z-machine stack. A Z-machine routine holds at most
15 locals, parameters and `let`s together; the compiler refuses an
over-full block with a clear error and the cure (move part of the work
into a helper block). Automatic stack spill, lifting that ceiling
invisibly, is on the feature roadmap (WHATSNEW.md).

PARENTHESES ONLY WHERE THEY EARN THEIR KEEP: a block (or intrinsic) that
takes no values is called by its bare name, in statement position
(`print_banner`, `describe_room`) and in value position alike
(`let k = read_key`, `if any_scored is 1`). The bare name resolves as a call
only after every data name (locals, globals, objects, constants,
directions), so story names always win, and naming a block that does take
values is a compile error pointing at the parenthesized form. Parens appear
exactly where arguments do: `teleport(wreckage_site)`, `random(6)`,
`quote(5, 29)`. The same doctrine prefers the English tests over call
shapes: `if shard is not moved` (never `if not (shard is moved)`; the
grouped form is for genuinely compound conditions), and `if chip is in
scope` or the short `chip in box` for the tree test, with `is not in` the
negation.

Blocks also serve as computed property values (chapter 5) and as grain
responses (chapter 18). A block attached to a property or grain may be named
and referenced, or written inline as an indented body.

The split is deliberate: `block` routines are called by you; `on` handlers
are entry points the engine fires.

## Chapter 11: Handlers and events

Handlers are the heart of Arcturus behavior. Everything a game DOES beyond
the library defaults - a door that argues, a character that accepts one gift
and refuses another, a room that guards its own exit - is a handler, and it
is ONE mechanism, not a collection of special cases: the same `on` syntax,
the same resolution, wherever it lives.

A handler lives in four places, and together they form the dispatch chain.
When an action fires, Cosmos walks the chain most specific first, and the
first handler that consumes the action ends the walk:

1. The NOUN's handlers: the acted-on object's own `on take`, then its
   kind's, up the kind chain.
2. The SECOND object's handlers, for a two-noun action: the recipient of a
   give, the container of a put, answers for itself right after the noun
   (see "The second object answers too", below).
3. The ROOM's handlers: the room the player is in, then its room kind's.
4. The free-standing rules, at file level, and last of all the library's
   own default for the verb.

Ending a handler consumes the action; `continue` declines it and the walk
resumes where it left off, so a handler can add its lines and still let the
normal thing happen. `on after <verb>` is the same chain again, run once
the action has really completed. That is the whole model; the rest of this
section is its vocabulary. A complete worked game exercising every form is
[examples/features/handlers.storyarc](../examples/features/handlers.storyarc),
and the precise ordering is chapter 13.

Action handlers match a verb and its objects:

```
on switch_on lantern
on take ruby
on put ruby in chest
```

To handle a whole kind, match the kind in any slot and refer to the matched
objects with `noun` and `second`. Both slots of a two-object verb may be a
specific object, a kind, or a mix:

```
on take container
    say "${The noun} is too heavy to lift."

on put thing in chest          // any thing put into the chest
    if noun is not ruby
        say "Only the ruby fits the slot."
        stop
    say "The ruby drops in with a click."
```

Here `noun` is the object put and `second` is the chest. The matched object
is always `noun` (and `second` for the second slot); test it against a
specific object with `is` and `is not`, as in `if noun is not ruby`.

A handler header may also list alternatives with `or`, so one handler covers
several specific objects:

```
on put ruby or ring in chest
    say "${The noun} settles into the velvet."
```

The handler fires when `noun` is the ruby or the ring and `second` is the
chest, with `noun` bound to whichever matched.

Inside an object or kind body, `self` stands as an operand for the enclosing
object itself, which reads naturally where the object appears in its own
pattern:

```
thing haystack of container in farm
    ...
    on put noun in self       // anything put into THIS haystack
        move noun to nothing
        say "${The noun} vanishes into the hay."
```

In a kind body `self` means each instance, so every barrel of a kind guards
its own number. A free-standing rule has no enclosure and names its object
instead; writing `self` there is a compile error that says so.

The second object answers too. For a two-noun action, the SECOND object's
handlers run right after the noun's: the recipient of a give or show, the
container of a put, decides for itself what it accepts. So a character's
acceptance logic lives on the character, written once, with the given thing
as `noun`:

```
thing clockmaker of character in shop
    ...
    on give coin            // GIVE COIN TO CLOCKMAKER lands here
        move coin to self
        now self is paid
        say "He makes the coin disappear."
```

The handler sits on the clockmaker, not on the coin and not free-floating:
whoever is offered something answers for it. An unpatterned `on give` on a
character catches every gift; the pattern narrows it to the coin, and a
`when` guard narrows it by state. What the recipient does not consume falls
through to the noun's own handlers' verdicts and the library default (a
character politely declines by default).

One handler may answer several verbs at once, by listing the verbs separated
by commas, so a shared response is written once:

```
on attack, push, pull
    say "It is too far away for this."
    stop
```

Comma joins verbs; `or` joins operand alternatives. The two combine, and any
operands apply to every listed verb:

```
on push, pull lever
    say "The lever does not budge."
```

A `when` guard restricts a handler to a condition: it applies only while the
condition holds, and otherwise defers to the next handler up the chain.

```
on push slab when player holds crowbar
    say "You lever the slab aside."
```

Default versus override. A matching handler replaces the verb's default
behavior, with the most specific winning (the chapter 3 resolution order).
Writing the handler switches the built-in behavior off: when the action
fires, your lines run instead of it, and the built-in part only happens if
you ask for it back. How the handler ENDS decides how much happens:

1. End it (reach the last line, or `stop` early): your lines are ALL that
   happens. An `on go west` that only says "LEAVING" prints the word and
   the player stays in the room.

2. End with `continue`: your lines happen, THEN the normal action does.
   The same handler with `continue` as its last line prints "LEAVING" and
   then the player really walks west. (`continue` hands the action to the
   next, more general handler: the kind's, the room's, and finally the
   Cosmos default, which does the real work.)

3. `on after <verb>` is a separate handler for the third timing: your
   lines happen AFTER the action has really taken place. The player walks
   west first, then "The door clicks shut behind you." If the walk never
   happened (refused, or replaced by a handler that did not continue),
   the after handler stays silent. And because the action has taken
   place, the after pass runs in the world the action MADE: for movement,
   `here` is already the destination, so a room's `on after go` belongs
   to the room the walk ARRIVES in, never the one it leaves (the example
   below is two rooms' worth of code for exactly that reason).

`stop` on a handler's last line changes nothing: reaching the end blocks
the built-in behavior anyway. `stop` exists to end the handler from the
MIDDLE of the body, almost always inside an `if`, when a refusal means the
remaining lines should not run:

```
room hallway
    name "Hallway"
    west study

    on go west
        if door is locked
            say "The door won't budge."
            stop            // end here: no movement
        say "You slip through."
        continue            // unlocked: and now the go really happens

room study
    name "Study"

    on after go west
        // The walk has landed and here is the study now, which is why
        // this handler lives here and not in the hallway it left.
        say "The door clicks shut behind you."
```

The full ordering is in chapter 13.

The after handler, fully. `on after <verb>` takes everything an ordinary
handler header takes: comma-separated verb lists, operand patterns, `or`
alternatives, and `when` guards, and it lives anywhere a handler lives (an
object, a kind, a room, or free-standing at file level):

```
on after take when here is vault
    say "An alarm begins to wail somewhere above."

on after drop, put
    if here is cloakroom
        now bar is lit
```

Two rules govern when it fires. First, the action must have COMPLETED: it
ran, and nothing refused it. Every library refusal (can't see it, it's
fixed, the door is locked) marks the turn refused, and a story handler that
refuses something should do the same by setting the `refused` global before
it stops. Second, replacing counts as completing: an `on take` that ends
after printing its own version of the take still completed the action, so
its after handlers run. Only a REFUSED turn silences them.

WHERE a movement's after handler lives follows from the first rule: the
walk has completed, `here` is the destination, and the handler resolves
there. A room's `on after go <direction>` therefore answers walks that
arrive in that room; the departure side of the same walk belongs to the
origin's plain `on go` (with `continue`). A handler that must hear every
walk wherever it lands is written free-standing at file level, and it
fires after the arrival's room description, the after pass's fixed
timing; the hook that speaks BEFORE the description is the destination's
`on enter`.

Within the after pass, handlers resolve exactly like the main ones: most
specific first, and `continue` passes to the next (the kind's after, the
room's, a free-standing one). The two catch-alls keep to their own bands:
`on other` never answers the after pass (it is for the player's verbs, not
for bookkeeping), and `on after other` is the after pass's OWN catch-all,
firing after any completed action that has no specific `on after` here, and
shadowed by one that does, exactly as `on other` is shadowed in the main
pass. Refusals and the out-of-world verbs (SCORE, SAVE) never reach it. In
a game with no `on after` anywhere the whole machinery folds away at
compile time and costs nothing.

`on other` is the catch-all handler: it fires for any action on the object
that no specific `on <verb>` handler caught. It is the object's own default,
the least specific of its handlers, running before the action climbs to the
kind, the room, or the Cosmos default; `stop` consumes the action and
`continue` passes it on. This is the equivalent of an Inform `default:` branch:

```
thing statue
    name "marble statue"

    on examine
        say "A nobleman, nose long since chipped away."

    on other
        say "The statue suffers your attentions in silence."
```

Here examine has its own reply and every other verb falls to `on other`.

Because `on other` answers many verbs at once, it often wants to know which
one arrived. `action` reads the action the turn is running, and compares
against a bare action name:

```
    on other
        if action is push
            say "The statue rocks on its plinth, then settles."
        else
            say "The statue suffers your attentions in silence."
```

That is the same sugar `way` has for directions, and it resolves last, so a
name of your own always wins over the action vocabulary. `action` is
available wherever a turn is being dispatched, including grain bodies
(chapter 18).

The
name `other` always means "anything not otherwise matched": as a verb here, and
as the fallback direction in `on go other` (chapter 8). A specific handler that runs
and ends with `continue` climbs to the kind, the room, and the defaults; it
does not fall into the same object's `on other`, so `on look / continue`
reads as "pass look through untouched". Inside a `go` handler, `way` holds
the chosen direction and a bare direction name is comparable against it
(`if way is not north`), for rules that treat one direction differently;
`here.(way)` reads the exit that direction names, the room the move would
reach (chapter 9, the run-time property read). The full dispatch chain is
defined in chapter 13.

Free-standing rules. A handler at file level belongs to no object: it joins
the chain after the rooms and before the library defaults, so it is the
game-wide layer, the place for behavior that is about the STORY rather than
any one thing. `on sing / say "Every clock loses a beat."` answers SING
anywhere; add a `when` guard and it becomes a scene rule, awake only while
its condition holds. A free rule consumes and continues like any other, and
a free `on <verb>` is also how a story overrides a library default wholesale
(the library's own defaults are just the last free rules in the chain).

Life-cycle events. Besides the action events named by verbs, Cosmos fires three
events as the game runs, handled with the same `on` syntax:

- `on start` runs once at the very beginning, BEFORE the banner: this is where
  everything that must happen before the game proper belongs. Set up the world,
  arm timers from the outset, choose the screen colours (`zcolor.background` and
  friends, so the banner prints on the colours you chose instead of being erased
  by them), and show an opening the way the Infocom games did, a scene or an
  epigraph before the title. The banner, then the first room description, follow.
- `on enter` runs when the player arrives in a room, as that room's handler, so a
  room can react to being entered. The name is shared with the ENTER verb, and
  the owner decides which is meant: on a room it is this arrival event (every
  hook fires; walking continues), while on a thing it is the ordinary verb
  handler, consuming like any other, which is what lets a scenery facade
  redirect ENTER into a `teleport` without the default refusal following.
- `on each_turn` runs once per turn, the per-turn daemon. A `when` guard decides
  when it is awake, and its reach follows scope: a room's runs while the player is
  there, an object's while it is in scope, a free-standing one every turn.

```
on each_turn when ruby is hidden
    say "Water ticks against stone."
```

An object marked `restless` breaks the scope tether: its `on each_turn`
fires every turn wherever it is, and what it prints while out of scope is
discarded by the system, so a wandering character keeps moving, taking,
and scheming offstage while the player only ever reads the prose of what
happens in front of them. See the attribute's row in chapter 19.

Recurring and delayed behavior beyond every turn uses the `after` and `every`
scheduling statements (one-shot and repeating timers), and each timer stops
by the exact statement that armed it, or all at once at a scene break:

```
every 5 turns do water_dripping
stop every 5 turns do water_dripping
stop all timers
```

Daemons and timers together are covered in full in chapter 16.

## Chapter 12: Verbs, grammar, and the standard actions

A `verb` declaration lists the player's words, then grammar lines:

```
verb "take", "get"
    take noun

verb "put"
    put noun in noun
    put noun on noun
```

A grammar line is an action name, then slots and literal words.
Particle words chain with `or` on one line: `put noun in or into
noun` accepts both wordings (the parser expands the alternatives
into sibling lines, so it costs what writing them out costs). Slots:
`noun` (one in-scope object), `held` (a held object), `multi` (several,
including "all"), `text` (free text), and `direction` (one direction word,
below). Bare words such as `in`, `on`, `with` are literal prepositions.
Two-object lines bind `noun` and `second`.

A two-noun line may end in `reverse`, for a verb whose two objects can be typed
in the other order without a preposition, the classic dative: GIVE and SHOW take
both `give noun to noun` ("give the coin to Bob") and `give noun noun reverse`
("give Bob the coin"). On a reversed line the first object is the recipient
(`second`) and the last is the thing (`noun`), so both orders reach the same
handler with the same roles. The parser splits the two adjacent nouns for you;
`reverse` needs exactly two `noun` slots and no preposition between them.
`reverse` is part of the grammar, not English, so a language pack declares the
reversed lines its language wants: the German pack does, since recipient-first
(`gib Bob die Muenze`) is the natural dative there.

POSITIONAL GRAMMAR. A line's first name is its action, and the action need not
be the same on every line, so a verb's wording can say more than "one noun" or
"two nouns around a preposition":

```
verb "dig", "excavate"
    dig
    dig noun
    dig noun with held
    dig in noun with held

verb "look", "l"
    look
    look noun
    look at noun
    look_under under noun
    look_behind behind noun
```

A literal may open a line (`dig in noun with held`), and a leading word may
select the line's own action, so LOOK UNDER BED and LOOK BEHIND BED reach
`look_under` and `look_behind`, two ordinary actions with ordinary handlers.
The compiler notices such a verb and matches it positionally: lines are tried
most specific first (most literal words, then, among literal-free lines,
fewest slots), and the first line that fits the typed words wins. Everything
else about the turn is unchanged: slots resolve through the same scoring
matcher, ambiguity still asks, pronouns still bind, and a command no line
accounts for is refused honestly. A quoted literal (`dig "in" noun`) is the
same as the bare word.

This costs bytes only where it is used: a verb whose lines are the plain
shapes stays on the compact model, and a game with no positional verb compiles
byte-identical to one built before the feature existed. A positional verb
follows the checked rules: at most two noun slots per line, a literal word
between two noun slots (adjacent bare nouns belong to `reverse`, which is a
plain-model feature), and single-word verb synonyms.

THE DIRECTION SLOT. A line ending in `direction` accepts a direction word
there, which is how SWIM SOUTH and PUSH CRATE WEST parse:

```
verb "swim", "paddle"
    swim
    swim direction

verb "push", "shove"
    push noun
    push noun direction
```

`say way` (or `${way}` in any text) speaks the direction's canonical word, north or aft, so a custom message can name the way taken. The direction is not a noun: it rides `way`, the same slot GO uses, so the
handler asks `if way is nothing` (declare the bare line too, so a plain SWIM
can ask "which way?"), compares `if way is south`, or hands the move to the
walking machinery whole with `perform("go", way)`. A noun slot before it
ends its phrase at the direction word, so in PUSH CRATE WEST the noun is the
crate. One `direction` slot per line, always last; a verb with such a line
compiles to the positional table. The worked showcase is
[examples/features/direction-grammar.storyarc](../examples/features/direction-grammar.storyarc).

A verb whose actions are OUT-OF-WORLD takes a trailing `meta`:

```
verb "about", "credits" meta
    about
```

Its actions dispatch straight to the free rules, past every object and room
handler (`on other` included), beside score/save/quit: the right shape for
ABOUT and HELP verbs, and what keeps the debug granule's GONEAR from firing
story code on the way past. A meta handler that should not cost a turn sets
`meta_turn`, as the standard session verbs do (chapter 13).

THE BARE-COMMAND ASK. A verb typed without a noun its grammar wants is an
incomplete command, and the library answers it centrally, before any
handler runs and without costing a move:

```
> THROW
The verb throw requires you to be more specific.
```

The line echoes the verb AS TYPED, full length and in the player's own
word (bare ROLL says "roll", even when roll is a push synonym), and it
never guesses the missing role: "Throw what?" guesses wrong when the
grammar wanted AT WHOM. This holds for every verb alike,
the standard set, your own (`verb "wibble" / wib noun` asks the moment
WIBBLE is typed bare), and partial commands too: PUT LAMP, with nowhere
to put it, gets the same honest ask. Your grammar decides what counts as
complete: DANCE never asks, because the standard grammar declares its
bare line (a dance needs no object), while a verb whose every line wants
a noun asks the moment it stands alone. A verb with a declared slotless
line owns its bare form, and the handler then sees `noun` as `nothing`:

```
verb "whittle"
    whittle
    whittle noun
```

Bare WHITTLE reaches `on whittle` (branch on `if noun is nothing`); bare WIBBLE,
whose only line wants a noun, asks. The message is msg_noun_missing, one
overridable block, worded natively by every language pack.

VERB_TRIGGER. The word that resolved the verb is readable in any handler
as `verb_trigger`, compared against a quoted verb word, so one action
family can answer each of its synonyms in its own voice:

```
on push
    if verb_trigger is "roll"
        say "The trunk rolls a half turn and settles."
        stop
    say "The trunk grinds a few inches across the boards."
```

The compare works at any word length (both sides meet in the dictionary),
and a word no verb or direction declares is a compile error, not a test
that can never be true. During AGAIN the remembered command's word is
restored; inside a `perform` there is no typed word and verb_trigger reads
0, so a phrasing branch falls to its default. A game that never reads
verb_trigger pays nothing for any of this. The worked showcase for both
seams is
[examples/features/enhance-redefine.storyarc](../examples/features/enhance-redefine.storyarc).

EXTENDING THE STANDARD GRAMMAR. The grammar is not a fixed table you write
additions into; it is the sum of every `verb` declaration in the compile,
Cosmos's and yours alike, and your game is expected to add its own. Three
patterns cover what a game wants:

A new verb is just a declaration plus handlers. The action name is yours to
invent; naming it in a grammar line is what creates it:

```
verb "dig", "excavate"
    dig
    dig noun
    dig noun with held
    dig in noun with held

on dig
    ...noun and second are bound as usual...
```

A new way to say an old thing reuses the standard action, so every handler
and default response already in place answers the new wording too. The line
names the standard action, and nothing else is needed:

```
verb "peruse"
    examine noun
```

A richer shape for a standard verb redeclares it. List the verb's words and
every line you want, the standard ones you keep plus your own; for the words
it declares, the later declaration wins, so your version replaces the Cosmos
one wholesale:

```
verb "attack", "hit", "break", "kill", "fight", "smash"
    attack noun
    attack noun with held
```

The showcase for all of this, including the LOOK extension with its two
wording-selected actions, is `examples/features/grammar.storyarc`; compile it
and type along. The same patterns hold in any language, because a language
pack's verbs are ordinary declarations too: a German game redeclares `grabe`
with `dig in noun mit noun` and the same matcher serves it (chapter 14).
When several of your lines could fit the same typed command, remember the
matcher's order: the line with more literal words is tried first, declaration
order breaks ties, so you rarely need to think about it; when in doubt, put
the more specific wording first anyway, which reads better in the source.

Standard verbs, including talk-to, come from Cosmos; the full list of
standard grammar lines is the verb table in chapter 12, and how input is tokenized and
resolved is defined in chapter 14 (the positional matcher). This
section defines only how you declare a verb and how its grammar names the
action your handlers receive.

### Score notification (notify), and VERSION

Score changes are silent by default. A game that wants the classic
bracket line enables it, usually at the start:

```
on start
    change notify to true
```

From then on a score change announces itself at the end of the turn,
"[Your score has just gone up by 5.]", and the player verb NOTIFY toggles
it. The two are coupled on purpose: enabling the feature anywhere brings
the verb along automatically, and a game that never writes `notify` has
no bracket lines, no verb, and pays nothing, the word is not even in its
dictionary. VERSION, by contrast, is always in: it prints the banner
mid-game, which is how a player tells you which build their bug lives in.

### Pushing things between rooms (shiftable)

A thing marked `shiftable` can be pushed through an exit, and the player
goes with it:

```
thing barrel in dock
    name "tar barrel"
    words barrel, tar
    shiftable
```

```
> push barrel north
You put your shoulder to the tar barrel and shove it along.

Warehouse
...
You can see a tar barrel here.
```

Doors are respected exactly as walking respects them, an exit that is not
there refuses the same way, anything unmarked answers that it will not
shift, and a bare PUSH keeps its flat default. PICK UP arrived in the same
pass: PICK UP THE LAMP and PICK THE LAMP UP are the everyday take, in all
three languages (aufheben, recoger).

### Typed answers, and lighting things

YES and NO are ordinary in-world actions: a game that asks the player
something reads the reply with `on yes` / `on no` (a `when` guard scopes
the question to its moment), and untended they get a flat flavor line.
They are never meta: answering is speech, and it happens in the story.
LIGHT is a switch_on synonym (LIGHT THE TORCH, LIGHT THE CANDLE), so
lamp-game phrasing works everywhere the switch does; the packs carry
their own words for all of these (ja/nein, sí/no, zünde an, prender).

### Noun lists

A two-noun command takes a list in its first slot: the second is bound
once, and each item runs as its own full turn, reported by name and
stopped at the first refusal, exactly as a chained line stops:

```
> put coin and nail in box
gold coin: Done.
rusty nail: Done.
```

The "and" chains instead, as it always did, when a verb follows it ("take
gem and put coin in box") or when the verb takes one noun ("take gem and
coin", the verb borrow). The verb contract guards every item: "give coin
and gem to bob" stops at the gem you are not carrying.

### Growing and replacing verbs (enhance, redefine)

An existing verb, standard or your own, is grown or replaced with intent
stated out loud:

```
enhance verb "look"              // the family keeps everything it had
    look_under under noun        // ...and these lines join it

enhance verb "push", "roll"      // roll joins as a synonym
    push noun direction          // and pushing gains a direction line

redefine verb "read"             // the family is replaced WHOLE:
    read_it noun                 // new grammar, and only the words
                                 // restated here survive
```

`enhance` appends: new grammar lines, new synonym words, or both (a body is
optional when only synonyms join). `redefine` replaces the family whole,
so a synonym the redefinition does not restate is gone from the dictionary;
the action's contract (`requires`, 10a) is wording-independent and stands.
Both anchor on the first quoted word, which must already be a verb; there
is nothing to enhance or redefine otherwise, and the compiler says so.

A plain redeclaration of an existing verb word still compiles, shadowing
word by word as it always did, but the compiler now notes what that means
(the family's other synonyms keep their old grammar) and names these two
forms, which say what they do.

### The verb contract (requires)

A verb can state what it requires of its operands, and the library enforces
it before any handler runs:

```
verb "sacrifice"
    sacrifice noun
    requires noun carried
```

Two requirement words exist: `carried` (the object is on your person, worn
included) and `animate`. Each applies to `noun` or `second`. The standard
GIVE and SHOW declare a carried noun and an animate second, which is why an
object's `on give` override answers real offers and never gibberish, unheld
gifts, or donations to furniture: a turn that fails the contract is refused
by the library, with its own message, and no handler sees it. A slot the
grammar requires but the player left empty is refused earlier still, by
the library's bare-command ask ("The verb give requires you to be more
specific.", see the verbs section above); a grammar-optional empty slot
passes through for the action to interpret. `perform` bypasses the
contract, since an author performing an action means it.

The in-body form above binds to the verb's own actions. The free-standing
form names the action, which is how requirements stay language-neutral
(actions.prelude declares the standard ones this way; a language pack
redeclares a verb's words and grammar, never its contract):

```
requires sacrifice noun carried
```

Requirements compile onto the action into one table; a verb that declares
none costs nothing, and requirement kinds no verb in the game uses are not
even compiled. The summonable foresight granule (chapter 22) builds on this
same declaration: a repairable failure, the carried gift you merely have
not picked up yet, becomes "(taking the pebble first)" instead of a
refusal, and only when the take is certain to succeed; closed doors and
containers join the repairs the same way (chapter 22).

### Verbless actions: `action`

A bare declaration names an action with no verb attached:

```
action ritual
action take_all, drop_all
```

The name joins the ordinary action numbering, so everything that works
on a verb's action works on it: `on ritual` handlers at every level of
the chain, `when` clauses, `action_id("ritual")` in low-level code, and
`dispatch`. What it does not get is a word: nothing reaches the action
from the keyboard until some code sends the player there, by
dispatching it or by remapping a typed verb to it. Two uses carry it:
a granule can route a piece of machinery through the standard pipeline
so stories can hook it (the takeall granule's sweep events, chapter 22),
and a language layer or story can redirect a verb to a private action
of its own.

### The standard verbs, action by action

A handler names the ACTION, never the typed phrase: `on take_off` is how
you catch REMOVE. The identifiers cannot be guessed from the phrases (TAKE
OFF raises `take_off`, but TALK TO raises `talk`, and READ raises
`examine`), so this table is the registry. The first column is what you
write after `on`; the second is what the player types; the third is the
grammar and the default behavior. The wiring itself is readable in
english.prelude (`arcc --extract`).

The world verbs:

| Action | The player types | Grammar and default |
|---|---|---|
| `look` | LOOK, L | `look`; describes `here`. LOOK AT X is `examine`; LOOK AROUND is a look. |
| `examine` | EXAMINE, X, READ, LOOK THROUGH | `examine noun`; prints `desc`. Needs visibility. |
| `look_under` | LOOK UNDER/UNDERNEATH/BENEATH | `look_under noun` (the under particle riding LOOK); "You find nothing of interest under..." unless handled. |
| `take` | TAKE, GET, CARRY, PICK (UP), GRAB | `take noun`; "You take X with you", or "out" from a carried container; refused if fixed. A game with `constant item_cap = N` refuses past N carried things ("Your hands are full, and so are your pockets."); no constant, no check, no cost. |
| `drop` | DROP | `drop noun`; move to `here`; a worn thing is refused until removed. |
| `put` | PUT, PLACE | `put noun on noun`, `put noun in noun`. |
| `insert` | INSERT | `insert noun in noun`. |
| `wear` | WEAR, DON | `wear noun`. |
| `take_off` | REMOVE, DOFF, DISROBE, SHED, TAKE OFF | `take_off noun`; TAKE plus the off particle raises the same action. |
| `inventory` | INVENTORY, I, INV | `inventory`. |
| `go` | GO, WALK, RUN, or a bare direction word | `go`, `go noun`; the noun slot is the direction and rides `way` (chapter 8). |
| `enter` | ENTER, BOARD, MOUNT, SIT (ON/IN), REST | `enter noun`; sitting is boarding. |
| `exit` | EXIT, LEAVE, OUT, STAND (UP) | `exit`, `exit noun`; STAND ON X boards instead. |
| `open` | OPEN, UNCOVER, UNWRAP | `open noun`, `open noun with noun`. |
| `close` | CLOSE, SHUT, COVER | `close noun`. |
| `lock` | LOCK | `lock noun with noun`, `lock noun`. |
| `unlock` | UNLOCK | `unlock noun with noun`, `unlock noun`. |
| `switch_on` | SWITCH/TURN ... ON, LIGHT | `switch_on noun`; the particle works in either order (SWITCH ON THE LAMP, TURN THE LAMP OFF). |
| `switch_off` | SWITCH/TURN ... OFF | `switch_off noun`. |
| `push` | PUSH, PRESS, SHOVE, NUDGE | `push noun`; "You give X a bit of a push." unless handled; PUSH X NORTH moves a `shiftable` thing. |
| `pull` | PULL, DRAG, YANK | `pull noun`; "You yank at X but nothing noteworthy happens." |
| `turn` | TURN, ROTATE, TWIST, SCREW, UNSCREW | `turn noun`; same default. |
| `climb` | CLIMB, SCALE | `climb noun`. |
| `give` | GIVE, OFFER, FEED, PAY | `give noun to noun` (also GIVE X Y reversed). |
| `show` | SHOW, DISPLAY, PRESENT | `show noun to noun` (also reversed). |
| `talk` | TALK TO, TALK, GREET | `talk noun`; the conversation action (below). Talking to yourself: "Nothing you hear surprises you." |
| `ask` | ASK | `ask noun`, `ask noun about text`. |
| `ask_for` | ASK ... FOR | `ask_for noun for text`; a request, distinct from asking about. |
| `tell` | TELL, INFORM | `tell noun`, `tell noun about`. |
| `answer` | ANSWER, RESPOND | `answer noun`. |
| `touch` | TOUCH, FEEL, PAT | `touch noun`. |
| `smell` | SMELL, SNIFF | `smell`, `smell noun`; the air, yourself, and the thing each answer differently. |
| `taste` | TASTE, LICK | `taste noun`. |
| `listen` | LISTEN, HEAR | `listen`, `listen noun`; yourself, a creature, and a thing each answer differently. |
| `eat` | EAT | `eat noun`; needs `edible`. |
| `drink` | DRINK, SIP, SWALLOW | `drink`, `drink noun`. |
| `attack` | ATTACK, HIT, BREAK, KILL, FIGHT, SMASH, KICK | `attack noun`. |
| `kiss` | KISS, HUG, EMBRACE | `kiss noun`; yourself, a creature, and a thing each answer differently. |
| `jump` | JUMP, HOP | `jump`. |
| `sing` | SING, HUM | `sing`, `sing with noun`; "You hum a few notes." |
| `yes` / `no` | YES, AFFIRMATIVE / NO, NEGATIVE | typed answers, caught with `on yes` / `on no` and a `when` guard; never meta, answering is speech. |
| `wait` | WAIT, Z | `wait`. |
| `xyzzy` | XYZZY | the magic word; a normal (if fruitless) action that costs a turn. |

The session verbs, each setting meta_turn so a cancelled quit costs no
turn (UNDO and AGAIN are intercepted by the turn loop before dispatch):

| Action | The player types | What it does |
|---|---|---|
| `save` / `restore` | SAVE / RESTORE, LOAD | the Z-machine save facilities. |
| `undo` | UNDO | take back the previous turn (the interpreter's save_undo/restore_undo pair does the snapshot). |
| `again` | AGAIN, G, CONTINUE | replay the previous non-meta command. |
| `oops` | OOPS | correct the last unknown word. |
| `quit` / `restart` | QUIT, Q / RESTART | both confirm first. |
| `score` | SCORE | the one score verb, Infocom-shaped: score, maximum, turn count, and the rank when a ladder is declared. |
| `version` | VERSION | prints the banner, so a bug report can say which build. |
| `notify` | NOTIFY | the score-notification toggle; exists only when the author enables scoring. |
| `transcript` / `transcript_off` | TRANSCRIPT, SCRIPT / TRANSCRIPT OFF, UNSCRIPT | see the transcript note below. |

SEARCH is not in the core set: it ships in the extendedverbs granule
(chapter 22), which adds the classic long-tail verbs (search, throw, dig,
rub, pray, and their kin).

The talk action. `talk to <person>` dispatches the `talk` action on the
person. Without the conversations feature, the Cosmos default routes to the
person's own `on talk` handler, or prints "There is no reply." With
`summon.conversations` (chapter 22), `talk to <person>` opens that person's
topic menu instead. ask, tell, and answer are likewise standard;
with no conversation granule they hand over to the same talk brush-off, so
asking IS talking until a granule redefines it.

The transcript. TRANSCRIPT (or SCRIPT) opens output stream 2, the transcript the interpreter
records to a file of the player's choosing; TRANSCRIPT OFF (or UNSCRIPT, the
Infocom word) closes it. The library reads the truth back from Flags 2 bit 0,
so a player who cancels the interpreter's file prompt gets an honest "No
transcript was started" rather than a false confirmation, and the closing
"Transcript off" is printed before the stream shuts so it lands in the file.
German words it MITSCHRIFT/PROTOKOLL AN and AUS; Spanish TRANSCRIPCION and
TRANSCRIPCION NO.

The English meta words work in every language pack: QUIT, SCORE, RESTART,
SAVE, RESTORE (and LOAD), UNDO, AGAIN, OOPS, TRANSCRIPT/SCRIPT ON/OFF, and
UNSCRIPT are declared as extra synonyms in the German and Spanish packs. A
player used to English adventures guesses the localized session verb wrong
at first; the session must never be hostage to vocabulary, so the original
always answers. In-world verbs stay purely native: the fallback is a meta
courtesy, not a second grammar.

Every default message is a Cosmos string, overridable globally by replacing
the Cosmos default or locally by handling the verb on an object or kind.

## Chapter 13: The turn loop and the action pipeline

Each turn Cosmos runs:

1. If the player entered a new room this turn, describe it: print the room
   `name`, the `desc` if unseen or on look, then the listed contents, and
   fire the room's `on enter`.
2. Print the prompt (default ">").
3. Read a line and tokenize it (chapter 14).
4. Parse: identify the verb, fill slots, resolve nouns in scope,
   disambiguate. On failure, print the refusal and skip to step 7.
5. Dispatch the action through the pipeline (this chapter).
6. Run `on after` handlers if the action completed.
7. Fire active `on each_turn` handlers (the room's, and in-scope objects'),
   subject to their `when` guards, then fire any scheduled events (chapter 16).
8. Increment `turns`. If a `finish` or `death` ended the game, print the
   final message, then the post-mortem: the final score (msg_score, rank
   included) and the classic prompt, answered with the pack's own
   restart/restore/undo/quit verb words (matched by action, so every
   language works untranslated). After a `death` the prompt adds UNDO
   (msg_game_over_died), which takes back the fatal command itself through
   the checkpoint every turn already takes, resuming play as if it were
   never typed; after a `finish` the prompt is the classic three
   (msg_game_over) and an UNDO answer is refused: a won game stays won. A
   failed restore or undo reports and re-asks, anything else re-prompts.
9. If the line chained further commands (chapter 14) and this one succeeded,
   continue with the next from step 4.
10. Loop.

The room is described once on entry. The status line (the room name, plus
the score and move count in a scored game, the move count alone otherwise)
is repainted before every prompt. At game start, with the
statusline summoned, the opening description skips its title line: the bar
already names the room, and the opening prose scrolls straight under it;
every later look prints the title as usual.

When the player stands on a supporter or inside a container, the room
title and the status bar both say where: "Crypt (on the altar)", "Cellar
(in the crate)". The wording is the language layer's `line_nested(obj)`
block (English on/in; German auf/in with the dative article through
art_the; Spanish sobre/en), so a language pack or a story overrides the
phrasing like any other line_* block. The whole feature rides the
compile-time `any_enterable` flag (1 when any object is a supporter or a
container by kind): a game with nothing to climb into folds it away and
its story file is byte-identical. The same flag guards the rule that the
player never appears in a holder's contents listing ("an altar (contains
yourself)" never prints).

A story moves the player without walking through `teleport(dest)`, the
cutscene arrival (a crash landing, a transit pod, a trapdoor): it relocates
the player, pays a scored room's points exactly once (the same `arrive`
the go handler funnels through), marks the room visited, and describes it.
It does not fire the room's `on enter` (that event belongs to walking; a
teleport's own prose sets the scene). Its sibling `gain(obj)` is the
acquisition without TAKE (a cutscene handover): it pays a scored thing's
points exactly once and marks it `moved` and `seen` before moving it to the
player; the take handler itself funnels through gain, so there is exactly
one acquisition path. Neither is Arcturus's `move`, the silent tree
operation with no bookkeeping (chapter 3 carries the warning for
Inform hands). Unused by stories, both fold to nothing extra.

### The action pipeline

An action carries its verb, `noun`, and optional `second`. Before the chain
runs at all, the VERB CONTRACT is enforced: what the action `requires` of
its operands (a carried noun, an animate recipient; chapter 12). A turn
whose operands fail the contract is refused by the library, message spoken,
and no handler of any kind sees it, which is the point: an object's
override owns the response to a valid turn, never the validation. A slot
the grammar requires but the player left empty is refused earlier still,
by the loop's central bare-command ask (chapter 14); a grammar-optional
empty slot (unlock noun beside unlock noun with noun) passes through for
the action to interpret. `perform` bypasses the contract entirely, since
an author performing an action means it. Then Cosmos dispatches the action as one chain of
handlers, most specific first:

0. (between 1 and 2) for a two-noun action, the `second` object's handlers:
   the RECIPIENT of a give or show, the container of a put, answers for
   itself ("give chip to vlad" runs Vlad's own `on give`), the way Inform
   consults the second's life-routine.
1. the `noun` object's own `on <verb>` handler,
2. the `noun` object's own `on other` handler,
3. its kind chain, nearest kind first, each kind's `on <verb>` before its
   `on other`,
4. the room's `on <verb>` handler, then the room's `on other`,
5. any free-standing top-level `on <verb>` rule,
6. the Cosmos default `on <verb>` handler.

When the whole chain declines, the dispatcher itself answers: the refusal
(`msg_cant_do`, "You can't do that to the lever.", nounless "You can't do
that.") ends the turn, so a story-declared verb that no handler claims can
never end a turn in silence. Cosmos rules every standard action, so this
tail exists only in a game that declares a verb and gives its action no
free rule; every other game folds it away, byte-identical (the compile-time
`any_unruled` flag). The after pass is exempt: an after number that nothing
answers is normal and stays quiet.

`on other` is the catch-all (chapter 11): at each level a specific
`on <verb>` is tried before that level's `on other`, so an object's own
`on other` is its private default, sitting below its specific handlers but
above the kind chain. It fires only for actions the object does not
otherwise ADDRESS: a specific handler that ran and continued climbs to the
kind, the room, and the defaults, it never falls into the same object's
catch-all (so `on look / continue` reads as "pass look through untouched").
A direction-guarded `on go north` addresses only norths: a southward go on
an object with no other go handler still reaches its `on other`. A handler
that lists several verbs (`on attack, push, pull`) is a specific handler
for each of those verbs.

Out-of-world actions never enter the chain at all: score, save, restore,
restart, quit, and the transcript pair report on or manage the session
rather than act in the world, so no object, recipient, or room handler ever
sees them (Inform and PunyInform mark the same verbs meta). The compiler
numbers them past `meta_floor` and the dispatcher routes them straight to
the free rules, where a story-level `on score` can still override the
default. The band is open to declaration: `verb "about" meta` puts a
verb's actions there too, for ABOUT and HELP verbs and the debug granule's
reach-anything tools, whose GONEAR must never fire an object's `on other`
on the way past.

Each handler runs until it ends or calls `continue`. Ending consumes the
action and stops the chain; `continue` passes to the next handler. If the
chain reaches the Cosmos default and it ends, the action took its standard
effect.

After phase. If the action completed, Cosmos runs `on after <verb>` handlers
in the same specificity order. A `when` guard that does not hold makes a
handler skipped, and the chain continues as if it were absent.

"Completed" means the turn ended with `refused` still 0: every library
refusal (can't see it, it's fixed, the door is locked) sets `refused`, and a
story handler that refuses something should set it the same way. An action a
handler consumed as its own effect (the instead case) still completed; a
scenery grain's quip is flavor, not a world action, so a grain turn takes no
after pass. An after handler may `continue` like any other, passing to the
next in specificity order; an object's `on other` never answers the after
pass, and `on after other` is the after pass's own catch-all: it fires
after any completed world action with no specific `on after` here, is
shadowed by one that exists, and never answers a refusal or an out-of-world
verb. In a game with no `on after` anywhere the entire phase folds away at
compile time and costs nothing.

This is leaner than Inform's rulebooks: one ordered chain, an explicit
`continue`, and an `after` pass, expressing instead, before-with-continue,
and after without further machinery.

## Chapter 14: The parser

The parser turns input into an action with bound objects.

Tokenizing. Input is lowercased and split on spaces and punctuation. Noise
words ("the", "a", "an", "my"; each pack declares its own with `noise`) are
known to the dictionary and ignored: being known is what lets a noun-list
segment carry them while a truly unknown word refuses the borrowed verb
(this chapter). Remaining tokens are matched
against the dictionary, which holds every verb word, every object's `words`,
and all grain words (chapter 22). An object's printed `name` is not matched;
matchable vocabulary comes only from `words`, which keeps the dictionary
small and under the author's control. Dictionary entries are truncated to the
Z-machine word resolution, so long words collide on their prefix; this is a
property of the format.

Verb resolution. The first verb word selects a `verb` declaration. Most
verbs compile to the flag model: the word's dictionary entry carries the
action and the noun arity, a two-noun command splits at its preposition, and
a one-noun phrase reaches past a leading one (LOOK AT CLOAK). A verb whose
grammar says more than that (a leading word on a two-noun verb, or wording
that selects the action) is matched positionally against its grammar lines
instead: this chapter.

Noun resolution and adjectives. Arcturus has no separate adjective type;
adjectives are ordinary entries in an object's `words`, ranked the same as
nouns. A noun phrase runs from the verb (or a grammar preposition) to the
next grammar preposition, and the scoring matcher (`match_phrase`, in the
agnostic skeleton) scores every in-scope object by how many of the phrase's
typed words its `words` contain, then takes the single best:

- No object matches: the grain check, then "You see nothing of the sort
  here." if a known object word was typed, or "This story doesn't know
  the word \"...\"" (the word spelled back from the input) if a typed
  word is in no dictionary entry at all. Either way the action is NOT
  dispatched: a handler that sees `noun is nothing` can trust it means
  the player typed the bare verb, never an unresolved phrase.
- One object scores best: it fills the slot.
- Several tie at the best score: first the HELD TIEBREAK. A tie where
  exactly one candidate is in the player's hands is not an ambiguity
  worth a question: EXAMINE MIRROR with your own in hand and the guard's
  on the guard means yours, silently. TAKE runs the tiebreak the other
  way (exactly one candidate NOT held wins, since taking wants the
  takeable one), so a held thing never shadows the one on the table. A
  tie with nobody on the wanted side, or two candidates there, stands.
- The tie survives: a genuine ambiguity. The parser asks
  "Which do you mean, the gold coin or the silver coin?", printing each
  candidate with its article (in German, declined to the accusative), and
  reads the answer. An answer that starts with a verb or a direction is a
  change of mind and replaces the command outright; anything else is taken
  as narrowing words, woven into the command right after the ambiguous
  phrase, and the whole line re-parses, so answering "gold" resolves
  exactly like typing "take gold coin" whole. An empty answer, or one that
  cannot narrow, falls back to "You'll have to be more specific."

So typing more adjectives narrows the result: with a gold coin and a silver
coin in scope, "coin" is ambiguous and asks, "gold coin" resolves directly,
and after the question a bare "gold" selects. Membership in the object's own
`words` is the whole scoring test, so a word that also serves as a verb
elsewhere still matches (a person named Pat survives "pat" the verb). The
most recent match feeds the pronouns (this chapter). The word that scored is
never printed: the `name`-versus-`words` split is the only lever needed. A
word in `name` is printed but not matched, a word in `words` is matched but
not printed, and a word you want both printed and typed appears in each.
There is no "the brass one" anaphora in v1; that is deferred.

Multi and all. Deliberately NOT core: both ship as granules, so a game that
wants them summons them and one that does not pays nothing. `summon.takeall`
gives TAKE ALL, DROP ALL, and TAKE ALL FROM (chapter 22).
`summon.plurals` gives group words (`plural coins` on each coin, so "take
coins" sweeps them) and THEM for the last group; noun lists ("take lamp and
box") are core (this chapter). Every swept item is a full turn, the chaining
rule. Unsummoned, "all" and group words are ordinary unknown words.

Unknown words. A word in no dictionary entry is ignored where it cannot
matter; where it sat in a noun slot the turn answers "This story doesn't
know the word \"...\"", naming the word (msg_unknown_word, parse_fault 4,
the word spelled back from the text buffer), so a typo is told apart from
a real thing that is not here, and OOPS corrects it on the next line. An
empty line gets an answer of its own, "Silence is not a command."
(msg_no_input), never a silent reprompt. The messages are Cosmos blocks
and overridable.

The refusals stay distinct, three situations, three answers: an INCOMPLETE
COMMAND (a bare verb whose grammar wants a noun, a PUT with nowhere to put)
gets the one honest ask, "The verb take requires you to be more specific."
(msg_noun_missing), echoing the verb AS TYPED from the text buffer, full
length and in the player's own word, so a synonym stays itself; the line
never guesses the missing role the way "Take what?" did, because the grammar
may want WITH WHOM or ON WHAT. The ask is central: the resolvers mark the
command (`incomplete`) and the loop refuses it before any handler runs, no
move consumed, custom verbs and standard verbs alike. A verb whose grammar
DECLARES a bare line (look, listen, a custom `whittle` beside `whittle noun`) is
never marked: its handler owns the bare command and sees noun = nothing. A
named thing that is simply NOT HERE keeps the classic refusal (msg_cant_see,
parse_fault 1); and a PRONOUN WITH NOTHING TO REFER TO (IT before anything
was named, THEM with no group, an unbound Spanish clitic) asks the player to
say what they mean (msg_no_it, parse_fault 5).

Grains. When a `noun` slot finds no real object but the typed word is a grain
word on `here` or an in-scope object, and the action's verb is one the grain
answers, Cosmos runs the grain's response (a `say`, a `do` block, or its
inline body) and treats the action as handled. Grains are checked after real
objects, so a real object always wins. See chapter 22.

Language seam. The parser is written in Arcturus, split into a language
agnostic skeleton (reading the line, computing scope, dispatching the action,
the turn loop) and language-specific routines (tokenizing and normalizing
words, resolving the verb, matching a noun phrase, and applying word order).
The English routines are the default; a language pack (chapter 22) overrides
the language-specific routines through ordinary resolution to handle a
language's morphology and grammar, without forking the skeleton. The skeleton
makes no English-specific assumption about word order, articles, or inflection.

### Reaching beyond scope (the reach_unscoped seam)

Ordinary matching resolves against scope, and for almost every verb that is
right: what the player cannot see, they cannot act on. A few verbs are
exceptions by nature, FOLLOW the classic among them: the one moment the
command makes sense is the moment its object has just left. The escape
hatch is the `reach_unscoped` seam, a block the parser calls only after
ordinary matching has failed, answering with an object to bind or `nothing`
to let the honest refusal stand:

```
verb "follow"
    follow noun

block reach_unscoped()
    // Only FOLLOW reaches beyond the room, and only for the drover.
    if verb_trigger is "follow"
        return drover
    return nothing
```

The contract has two sides. The parser's side: whatever the seam returns is
bound as the noun exactly as if it had been in scope, and AGAIN replays a
reach-bound noun without the usual left-scope refusal. The author's side: a
verb that reaches beyond scope owns its own validity, in its handler,
because only the verb knows what reachable means for it (the next room,
anywhere at all, only while the tracks are fresh); answer the impossible
case yourself, and remember the object may have moved between the command
and an AGAIN. `verb_trigger` (chapter 12) is the natural way to scope the
seam to the verbs that need it, so every other verb keeps refusing
normally. The seam is consulted on the single-noun path only; a two-noun
command resolves both of its slots against ordinary scope.

A game that never overrides the seam pays nothing: the plumbing folds away.
The debug granule's fetch and warp verbs are the library's own use of the
same seam (chapter 23).

### Pronouns

The parser remembers what the pronouns mean. Four canonical referent slots,
`it`, `him`, `her`, and `them`, hold the objects the player last dealt with;
typing a pronoun as a noun resolves to its slot's referent, and a referent
that has left scope answers with the ordinary "you see nothing of the sort",
the honest failure. A pronoun binds in either noun position, so "put coin in
it" works. The referents survive between turns and reset only on restart.

The words and the rules are language, so both live in the language layer. A
pack declares its words with `pronoun <role> "word", ...`:

```
pronoun it  "it"        // English
pronoun him "ihn"       // German: the accusative, the object of a command
pronoun her "sie"
```

and defines a `note_pronouns(obj)` block deciding which slot a just-resolved
noun fills. English splits by animacy (a character becomes him or her,
everything else it) and, within characters, by the `feminine` attribute:
declare `feminine` on a female character so "her" finds her (the -a name
heuristic that serves Spanish also runs, so a Marta derives it, but a Ruth
does not); a male character needs nothing, masculine being the default. The
slots are separate: "him" never returns a character noted as "her", and an
empty slot answers the ordinary "you see nothing of the sort". German follows
grammatical gender, so die Lampe becomes "sie" and das Buch "es".

Spanish takes its pronouns as CLITICS, the natural form: "cogela" is coge with
la attached, so an unknown first word ending in -lo, -la, -le (the leísmo
form, taken as masculine), -los, -las, or -les splits its clitic off in the
typed text, the verb re-resolves, and the pronoun's referent becomes the
command's noun; -te is the reflexive and points at the player ("examinate").
Accents fold first, PunyInformES-style, so "cógela" typed with its tilde works
too. This chains with the infinitive retry: "cogerlo" sheds the clitic, then
the -r, and lands on coge. The clitics are deliberately NOT dictionary words:
bare la and los are the articles, and "coge la lámpara" must keep resolving
the lámpara. A referent that has left scope falls into the ordinary honest
failure, and the plurals (-los, -las, -les) wait, like `them`, for a plural
model.

The roles are the compiler contract (like the particle roles); the slot ids
ride the pronoun words' dictionary entries where a pack declares words.

### Command chaining

Several commands fit on one line, joined by the language layer's chain words:

```
> take the lamp and open the door then go north
> drop cloak, hang cloak on hook
```

A pack declares the words with a `chain` declaration; all chain words behave
identically, and the comma tokenizes as its own word, so it chains with or
without spaces around it:

```
chain ",", "and", "then"      // English
chain ",", "y", "luego"       // Spanish
chain ",", "und", "dann"      // German
```

Each chained command is a full turn of its own, exactly as if typed on its own
line: it dispatches through the ordinary pipeline, fires the per-turn events,
and counts a turn. The responses are separated by the usual paragraph break. A
run of chain words ("take lamp, then go north") chains once, and a trailing
chain word is harmless.

THE CHAIN STOPS AT A FAILURE, and what was already done stays done. Two things
count as failure: a command that does not parse (an unknown word, something
out of scope), and a turn a refusal path could not carry out. The library's
refusals distinguish honestly between the two ways a command can come to
nothing:

- A GENUINE REFUSAL (can't, won't, wrong key, no exit that way) stops the
  line. "take statue and go north" with a fixed statue prints the refusal and
  goes nowhere.
- An outcome that ALREADY HOLDS ("you already have it", "it's already open")
  does not stop the line: the command's goal is met, so the rest still makes
  sense. "open door and go north" walks through a door that was already open.

The signal is the `refused` global: every library refusal sets it to 1 before
its message, and the turn loop reads it after each chained command. A story
handler that refuses something should set it the same way, so a chain stops at
its refusal too:

```
on take
    if noun is idol
        change refused to 1
        say "The idol is welded to its pedestal."
        stop
```

A handler that omits it simply never stops a chain, which is the right default
for handlers that succeed. `again` after a chained line repeats only the LAST
command of the line (the loop replays the resolved command it already
remembers, so replaying the whole line would re-fire every side effect).
Rewinding play cancels the queue: undo, and a mid-turn line read (the quit and
restart confirmations, and the disambiguation ask, claim the same typed-text
buffer), and a restore, all drop whatever was still queued.

The mechanics reuse the typed line itself as the queue: the parser truncates
the buffer's length byte at the first chain word (the tail stays where it was
typed), runs the command, then blanks the consumed part, restores the length,
and re-tokenizes. Nothing is copied and no second buffer exists.

NOUN LISTS ride the same machinery: a chained segment with no verb of its
own borrows the previous command's verb, so "take lamp and box" runs as take
lamp, take box, one full turn each, and "drop the sword and the shield" works
the way a player expects. Only a segment that starts with something noun-like
borrows; anything else keeps the honest "those words don't add up to
anything", and a bare noun typed on its own line is still no command. Since
the list words are the chain words, a language pack localizes noun lists
automatically. Lists distribute over ONE-noun verbs; "give x and y to z"
stays out (v1).

### Positional grammar

Two grammar models serve one `verb` declaration syntax, and the compiler
picks per verb. The FLAG MODEL is the compact default: the verb's dictionary
entry carries its action and its noun arity, a two-noun command splits at the
first preposition-flagged word, and the phrase matcher's scoring tolerates a
leading or stray literal in a one-noun phrase. It represents every standard
verb exactly and costs nothing beyond the dictionary entry. The POSITIONAL
MODEL takes over for a verb whose grammar the flags cannot express:

- a literal word before the first slot of a verb that takes two nouns
  somewhere (`dig in noun with held`: the splitter would take the leading IN
  for the boundary between the nouns); or
- lines with different shapes naming different actions (`look_under under
  noun` next to `look_behind behind noun`: one verb word, and the wording
  picks the action, where the flag model has a single action byte).

ONE STANDARD VERB rides the table: English ASK. `ask noun about text` and
`ask_for noun for text` are different acts chosen by wording, and both name
a SUBJECT rather than an object, which is the `text` slot below. So an
English game carries the matcher; German and Spanish phrase a request with
a verb of their own (BITTE, PIDE) and table nothing.

Lines that differ in action but not in shape (`switch_on noun` next to
`switch_off noun`) stay on the flag model: no positional match could tell
them apart, and the particle machinery already does.

Such a verb compiles to a GRAMMAR TABLE in static memory. Its dictionary
entry is flagged as a tabled verb and its data bytes hold the table's address
instead of an action and an arity. The table is the verb's lines in matcher
order: per line an action byte, one byte per token (noun, held, multi, text,
direction; a literal word carries its dictionary address), and a closing
zero; a zero in action position ends the table. Matcher order is most literal words first, so
`dig in noun with held` is probed before `dig noun`, whose bare slot would
absorb the literals; among literal-free lines, fewest tokens first, so a bare
`dig` catches DIG before `dig noun` matches it with an empty slot. The sort
is stable; lines it does not separate keep their declared order.

The matcher (`grammar_match` / `try_line`, in the agnostic skeleton) walks
the typed words against each line and the first line that fits wins. A
literal token must BE the typed word at its position; a slot absorbs the
words up to the line's next literal, or to the end; the whole command must be
consumed.

A `text` slot is the exception to resolution: it absorbs its words the same
way, but they are never matched against objects. The range is handed on
(`topic_lo`, `topic_hi`) for the conversation layer to match against topics,
because what it names is a SUBJECT: you ask ABOUT the old mine, which is no
object at all, and you ask FOR a drink the barkeeper has and you do not, so
neither could be resolved against scope. A pack still on the flag model
finds the subject itself, at the first separator, so both models work. On a fit the line's action is taken and the slots resolve through
the same scoring matcher as everything else, with the same faults: a tie asks
"which do you mean", a named-but-unresolved noun on a two-slot line is
rejected, a one-slot miss falls through to grains and the honest can't-see,
and an EMPTY slot marks the command incomplete, so the loop's central ask
answers before any handler runs ("The verb dig requires you to be more
specific."); a verb with a declared slotless line never lands there bare,
that line sorts first and matches. When no line fits at all, the verb was
understood but the rest was not: "You lost me after that." Disambiguation answers, pronouns, chaining,
AGAIN, and OOPS all work on tabled verbs unchanged.

The `direction` slot (SWIM SOUTH, PUSH CRATE WEST) lives on this model: a
line ending in `direction` demands a direction word at that position and
consumes it, and a noun slot before it stops its phrase at the first typed
direction word, so in PUSH CRATE WEST the noun is the crate. The word needs
no binding of its own: the parser sets `way` from the whole line before any
grammar runs, exactly as it does for GO, so the handler asks `if way is
south` or hands the move to the walking machinery with `perform("go", way)`.
A verb with a direction line always compiles to a table: the flag model's
arity byte has no room for "and a direction word may stand here", and only
`go` gets that tolerance on the classic path. The worked showcase is
`examples/features/direction-grammar.storyarc`.

The rules a positional verb must follow are checked at compile time: two
noun slots per line at most, a literal word between two noun slots (the
adjacent-noun `reverse` form stays a flag-model feature), single-word verb
synonyms, and at most one `direction` slot, closing its line.

Pay for use: the matcher and the packs' tabled-verb branches sit behind the
`any_tables` compile-time flag, so a game whose verbs all fit the flag model
folds the whole path away and its story file does not grow by a byte. A game
that declares one positional verb pays once for the matcher and then a few
bytes per line. The matcher is language-agnostic; each pack's grammar lines
feed it through the same table format, so a German `grabe in noun mit noun`
works the moment it is declared.

The worked showcase is `examples/features/grammar.storyarc`: the dig verb
with its leading IN, and a LOOK extended with `look_under`/`look_behind`,
two wording-selected actions. The authoring patterns (adding verbs, feeding
standard actions from new words, redeclaring a standard verb with richer
lines) are chapter 12.

## Chapter 15: Output and text

### vary: prose that varies by itself

The second time a player reads an identical idle line, the game feels dead,
and the classic fix, a counter global and an if-chain per site, is so
tedious nobody does it consistently. `vary` is the fix done right: speak
one of several variants, the site keeping its own INVISIBLE state, one word
the compiler allocates, correct across save, undo, and restart, never named
by the author. The policy word says how the site moves on:

```
vary sequence        // advance once, then stick on the last: room descs
    "A raven lands on the gibbet."
    "The raven picks at something."
    "The raven is still there."

vary loop            // round-robin, A B C A B C: background machinery

vary mutate          // random, never the same twice running: the default
                     // for flavor (footsteps, weather)

vary dice            // the honest roll, repeats allowed (the catalogs'
                     // dice, same word): coin flips, static noise
```

Each bare string line is its own variant, an implicit say: the text IS the
content (the form catalogs taught). A variant that needs to DO something
opens with an `or` line at the vary's level and holds ordinary statements;
the forms mix freely:

```
vary loop
    "A tap drips."
    "A fly circles the sink."
or
    say "The fridge shudders once, alarmingly."
    now fridge is suspect
```

vary is a statement, and in Arcturus all dynamic prose flows through
statement contexts, so it plugs in anywhere text is made, tied to nothing:
computed descriptions, handlers, grains, and conversation `topic` bodies
alike (a character whose replies vary is the topic section's own worked
case, chapter 17):

```
room cellar
    desc block                       // computed properties: desc,
        vary sequence                // appearance, intro, beyond block
            "Stairs descend into a dark that feels inhabited."
            "The cellar again. The dark has not warmed to you."

thing bell in chapel
    on push                          // any handler: on X, on after X, on other
        vary loop
            "The bell tolls, deep and bronze."
            "The toll again, felt in the teeth this time."

    on take
        alter                        // an alter report body is statements too
            vary mutate
                "You lift the bell free."
                "The bell comes away with a last sulky clank."
        continue

on each_turn when here is marsh      // daemons, free rules
    vary mutate
        "Something plops into unseen water."
        "A dragonfly stitches past."

block msg_cant_go()                  // library message overrides
    vary loop
        "No road that way."
        "Still no road that way."
```

Conversation reply bodies and grain inline bodies are statement contexts
too. The two places it cannot go, both by nature: inside a quoted string
(mid-sentence variation is not supported), and static data (a one-line
`desc "..."`, a catalog entry); the block form of any property is the
upgrade path, as in the cellar above.

Underneath: one word of dynamic memory per stateful site (dice keeps
none), a single load and store, and the same jump chain a `switch`
compiles to; a handful of instructions per site, native Z-machine
operations, no library involved. A game that never varies is
byte-identical. Each site is independent, and the state rides ordinary
dynamic memory, so narrative continuity survives saves and undo for free.

A string is written in double quotes and may span physical lines; runs of
whitespace, including line breaks, collapse to a single space, so
continuation lines may be indented:

```
desc "A damp cellar of black stone. A squat pedestal stands at its
      centre, a rusted lever set into the base."
```

Because a real line break collapses to a space, a forced line break is written
`\n` (Arcturus's spelling of Inform's `^`); `\n\n` leaves a blank line, a
paragraph break. A `say` already ends its line, so `\n` is only for breaks
within a line of text:

```
say "Hey\n\nThis is two lines below.\n\n\nAnd this three."
```

To follow a say with a paragraph break, say it with the `par` modifier:
`say.par "..."` prints the text and marks the library's pending break, which
the next output flushes as a single blank line (repeats collapse, chapter 15).
Consecutive prose paragraphs are each a `say.par` line, no bookkeeping
between them. The mirrored `par.say "..."` puts the break FIRST: the reveal
paragraph appended under existing prose (a first-visit aside, a description
that grows a second paragraph when the state changes). Both compose with a
colour in any order (`say.yellow.par`, `par.say.yellow`), and `par.say.par`
is a free-standing paragraph. The banner manages its own spacing the same
way (a trailing pending break; under a status bar the title sits directly
below the bar), so a story never calls the bare `par` for routine prose. If
story code reads like Inform new_lines, something is being done wrong.

Interpolation embeds an expression with `${ }`; printing an object prints its
`name`. Article helpers: `${the ruby}`, `${a ruby}`, and the capitalized
`${The ruby}`, `${A ruby}`; an object with `named` set takes no article.
Their full behavior is later in this chapter. Escapes: `\"`, `\\`, `\$`, and `\n`.

An object may override its articles outright with the `article` (definite) and
`indefinite` properties, for the cases derivation cannot reach: `article
"las"` and `indefinite "unas"` for las tijeras, `article "el"` for el agua,
`indefinite "some"` for an English mass noun. The stored text prints verbatim,
so keep it lowercase and prefer messages that keep such objects mid-sentence:
a hand-set article does not capitalize itself at a sentence start.

An article may carry a grammatical-case tag after a colon, `${the:acc noun}` or
`${a:dat noun}`, for a language whose article inflects for case (German
der/den/dem). The cases are `nom`, `acc` (or `akk`), `dat`, and `gen`; with no
tag the case is nominative. English and Spanish ignore the tag, so it costs
nothing there; a language pack's article block reads it (chapter 21). Only
the definite and indefinite article take a tag.

The copula agrees the same way: `${is ruby}` (capitalized `${Is ruby}`) prints
"is", or "are" when the object is `pluribus` (the scissors), worded by the
language pack (ist/sind; está/están, the estar of states and places). One
sentence template serves every number in every language: "${The coins}
${is coins} under the steamshovel." It takes no case tag.

Screen colours have their own section, 16a, below.

### Screen colours (zcolor)

The Z-machine draws in nine standard colours, and Arcturus exposes them by
name. The palette, as the Standard defines it (chapter 9.3.1):

| Name | Number | Colour |
|------|--------|--------|
| `default` | 1 | the interpreter's own default |
| `black`   | 2 | black |
| `red`     | 3 | red |
| `green`   | 4 | green |
| `yellow`  | 5 | yellow |
| `blue`    | 6 | blue |
| `magenta` | 7 | magenta (purple) |
| `cyan`    | 8 | cyan (light blue) |
| `white`   | 9 | white |

(Later revisions of the Standard add interpreter-specific greys; Arcturus
supports the portable nine, which every colour interpreter carries, down to
the 8-bit machines.)

The `zcolor` statement sets the base colours, one target per line, usually in
`on start`:

- `zcolor.font <colour>`: the base text colour. Remembered, so every one-shot
  colour below restores to it.
- `zcolor.background <colour>`: the background. Setting it also repaints the
  screen, so the new colour covers the whole display rather than only the text
  printed from then on.
- `zcolor.statusline <colour>`: the status bar's text colour (with the
  statusline granule). The bar draws in it and the base font colour returns
  after every draw.
- `zcolor.input <colour>`: the colour of the text the player types. The
  command echoes in it, and the base font colour returns the moment the line
  is entered.

`say.<colour> "..."` prints one text in that colour and then restores the base
font colour by itself, so an emphasized passage is a single line with no state
to manage and no restore to forget. It composes with interpolation
(`say.yellow "${The noun} glows."`) and with the `par` modifier in either
order (`say.yellow.par`, this chapter). Together, the classic Infocom-era look is
four lines and stays out of the prose:

```
on start
    zcolor.font white
    zcolor.background black
    zcolor.statusline cyan
    zcolor.input cyan

    say.yellow "For my part I know nothing with any certainty, but the
        sight of the stars makes me dream."
    say "-- Vincent van Gogh"
```

`show.<colour> "..."` is the inline sibling: the same one-shot colour, but no
trailing newline, so a single word or phrase can sit highlighted inside a
sentence the surrounding `show(...)` calls build. A help text that names its
verbs in colour reads like this, and the whole thing lands on one line:

```
on help
    show("Conversations are handled via ")
    show.yellow "[talk to NPC]"
    say "."
```

A colour is required after the dot (`show.yellow`, never a bare `show.par`):
show is inline by definition, so the paragraph modifiers do not apply. The
plain `show("...")` intrinsic is unchanged.

Colour support is handled for you, at both ends. The compiler marks the story
as colour-using in the header (Flags 2 bit 6, which interpreters require
before they enable colour at all), and every colour operation checks at run
time whether the interpreter reports colour support (Flags 1 bit 0): on an
interpreter without it, `zcolor` does nothing and `say.<colour>` is exactly a
plain `say`. No author-side guard is ever needed, and a game that never uses
colours pays nothing for the feature. An unknown colour name is a compile
error that lists the palette.

### Standard responses

Representative defaults, all overridable: take a fixed object, "${The noun}
is fixed in place."; take something held, "You already have ${the noun}.";
take success, "Taken."; drop, "Dropped."; examine with no desc, "You see
nothing special about ${the noun}."; no exit, "You can't go that way."; a
closed container, "${The noun} is closed."; darkness, "It is pitch dark, and
you can see nothing."; an unhandled push, pull, or turn, "Nothing obvious
happens."

The pacing gate belongs here too: `press_any_key` (core) prints
`msg_press_any_key`, waits for exactly one key (no echo, no Enter), and
returns its ZSCII code for whoever cares which key fell. The prompt
defaults to "[...]" in every language layer: convenient, understood
everywhere, translation-free, and overridable like any message block. A
device that speaks in its own voice calls `read_key` directly instead;
the worked example (examples/features/press-any-key.storyarc) shows the
gate, the custom prompt, and the specific-key catch side by side.

### Naming, articles, daemons, and timers

Naming. `name` is the printed short name; the object identifier is never
printed. Article helpers: `${a noun}` chooses a or an by sound, `${the
noun}`, and capitalized `${A noun}` and `${The noun}` for sentence starts. An
object with `named` set takes no article. When Cosmos lists several objects
it joins them with commas and a final "and", each with its indefinite
article.

## Chapter 16: Daemons, timers, and background performers

Daemons and timers. Arcturus gives you background behavior, code that runs on its
own as turns pass, without the timer objects, integer IDs, and start/stop calls
that this needs in other systems. There are two pieces: a per-turn daemon
(`on each_turn`) and scheduled events (`after` and `every`).

A daemon is an `on each_turn` handler. It fires once per turn, at the end of the
turn, and a `when` guard is its on/off switch:

```
room bar
    on each_turn when not lit
        say "Something rustles in the dark."
```

While the condition holds, the daemon runs; when it stops holding, the daemon
falls silent, with no explicit start or stop. Scope decides reach: a room's
each_turn is active while the player is in that room, an object's while the object
is in scope, and a free-standing each_turn (written at the top level, not inside
an object) runs every turn.

The exception is a BACKGROUND PERFORMER, an object marked `restless` (chapter 19): its each_turn fires every turn wherever the object is. The
principle is one sentence: work follows the performer's nature, prose
follows scope. Every restless firing is buffered (a scratch table,
Z-machine output stream 3, conformant on every interpreter), and the
buffer is spoken afterward when the performer is in scope at EITHER end
of its turn: standing before you, arriving as you watch, or leaving
before your eyes are all heard, while a turn taken wholly offstage is
discarded unread. So the author writes `say` unconditionally, arrival
lines included, and the system decides audibility. Nothing ever fires
twice (the scope walk skips restless objects; the performer walk owns
them). `restless` is runtime state: `now thief is restless` arms a
performer with no declaration anywhere, `now thief is not restless`
returns it to the ordinary in-scope pulse, and the `when` guard still
gates each firing. A game with no restless object folds the walk, the
mute buffer, and the skip away entirely: byte-identical.

Voicing an offstage event. When something happening far away should be
HEARD, the announcement belongs to the narrator, not to the far-away
object: an object cannot narrate itself from a place the player is not
standing, because the right words depend on where the player is (in the
belfry the bell is deafening; a village away it is faint; indoors it is
muffled). So the performer does the work, restless and silent, and a
free-standing rule (or the room's own each_turn) reads the state that
work leaves behind and speaks from the player's side:

```
thing bell in belfry
    restless
    on each_turn
        change tolls to tolls + 1

on each_turn when tolls > tolls_heard
    change tolls_heard to tolls
    if here is village
        say "Far off, a bell tolls faintly."
```

That completes the daemon vocabulary with nothing further to learn:
offstage work is `restless`, scheduled events are `after` and `every`,
and offstage narration is a free rule voicing the state the work left
behind.

While developing, the muting hides the very say lines an author sprinkles
through a handler to watch it work. The debug granule's UNMUTE verb
(chapter 22) lets every offstage voice through, each tagged with its
performer's name; UNMUTE again restores the rule.

Several each_turn handlers may be live at once; they
fire the room's first, then the in-scope objects', then the restless
performers', then the free-standing rules. Every live daemon fires:
each_turn is a pulse, not a player action, so `stop` (or a handler simply
running to its end) does not silence the sibling daemons the way it consumes a
verb. This is what lets a game's own `on each_turn` and a granule's pulse (the
ambience sweep, for instance) run side by side; the same holds for `on start`
and `on enter`.

Scheduled events fire a block after a set number of turns. `after` fires it once;
`every` fires it again and again:

```
after 3 turns do collapse_tunnel     // once, three turns from now
every 5 turns do tide_shifts         // every five turns, indefinitely
```

`do` names a `block` (chapter 10), which runs with no arguments when the timer
comes due. The count is any expression, evaluated when the statement runs, so a
timer can be armed for a computed number of turns. Scheduling is a statement, so
you arm a timer wherever it belongs, commonly in `on start` or in the very handler
that sets an event in motion:

```
on take idol
    move idol to player
    say "The pedestal sinks. Somewhere, stone grinds on stone."
    after 4 turns do temple_collapses
```

The timers count down from the turn loop, right after the each_turn pulse, so a
scheduled block sees the world as it stands at the end of the turn. Re-running an
`after` or `every` for the same block re-arms it: the countdown restarts from now
with the new period, never a duplicate, which is how you extend, shorten, or
restart a running timer. A scheduled block may even schedule itself, arming its
next fire with a fresh count, for a timer whose period changes over its life.

A timer STOPS by the exact statement that armed it, `stop` in front of the
arming line:

```
stop after 4 turns do temple_collapses
stop every 5 turns do water_dripping
```

The full triple, kind, interval, and block, is the timer's identity, and it
must MATCH what is armed: an `every 3` cannot stop an `every 5`, nor an
`after 5`, and stopping a timer that is not running is a clean no-op (that
timer is not running, which is what you asked for). The schedule keeps the
armed interval for exactly this, so a half-burnt fuse still answers to the
number it was lit with. A `stop ... do` naming a block no arming statement
ever schedules is flagged with a compile note. And a scene break clears
everything at once, one-shots and recurring alike:

```
stop all timers
```

Between them, `on each_turn` (with `restless` for the background
performers), `after`/`every`, and their stops cover the whole range: a
condition-gated daemon, an offstage agenda, a one-shot fuse, a
fixed-period timer, and the silence after, all written in ordinary
Arcturus with no timer objects and no hand-kept turn counters.

## Chapter 17: Topics and conversation

A character (a thing that is `animate`, which the `character` kind sets) can hold
conversation `topic`s. A topic is one subject the player can raise, together with
the exchange that follows. Topics are inert on their own: a summoned feature
presents them, either through the Infocom-style ask/tell verbs
(`summon.infocom_talking`) or as a numbered menu (`summon.conversations`).
The two are mutually exclusive by the compiler: a game summons exactly one,
and switching presentations later is a one-line change. How they are
presented is defined in chapter 22; this chapter defines the construct.

### The five ways to address a character

Arcturus separates them, because they are different acts:

| | reaches |
|---|---|
| `ask <person> about <subject>` | the person's topics |
| `tell <person> about <subject>` | the same topics (`action is tell` to differ) |
| `ask <person> for <subject>` | the same topics (`action is ask_for`) |
| `give <thing> to <person>` | the person's `on give` |
| `show <thing> to <person>` | the person's `on show` |

The first three name a SUBJECT, which is words rather than an object (you
ask about the old mine, and you ask for a drink the barkeeper has and you
do not), so they run through topics. The last two name a real object you
are holding, so they are ordinary two-noun actions. Commanding a character
outright is a separate matter and belongs to the NPC engine.

### Shared subjects

When several characters can be asked about the same thing, declare the
SUBJECT once at file level and let each of them supply only their answer.
The subject owns the match words and the menu label, so adding a synonym
later is one edit rather than one per character, and the vocabulary is
stored once in the story file however large the cast:

```
subject cowboy "the evil cowboy" words cowboy, buckaroo, mean
    reply "Nobody around here likes to talk about him."

thing pope of character in rome
    topic cowboy
        reply "I think he's swell."

thing sheriff of character in town
    topic cowboy once
        reply "I'll see him hang."

thing bard of character in inn
    topic cowboy "that dreadful man"
        reply "I wrote a song about him."

thing drunk of character in tavern
    topic cowboy
```

The subject's own indented body, if it has one, is the DEFAULT exchange: the
drunk above writes no body and answers with it. A character may override the
label (the bard) and keeps its own modifiers (`once`, `when`, `hidden`,
`idle`) and its own `reveal`/`hide` state, because the subject supplies
vocabulary and wording, never behaviour. A topic that names a subject must
not declare `words` of its own; edit the subject instead. A topic that names
no subject carries its own label, as always.

A topic is declared in the person's body:

```
topic <subject> "<label>" [words a, b, ...] [when <cond>] [once] [hidden]
topic <subject> "<label>" idle [when <cond>] [once]
    <body>
```

The header parts, with the modifiers in any order:

- `<subject>` is a barename id, local to this person; `reveal` and `hide` address
  topics by it.
- `"<label>"` is the line shown in the conversations menu (any expression).
- `words a, b, ...` are the words ask/tell match against (`ask <person> about
  <word>`). They are optional: a menu-only topic needs none, since the player
  picks it by number.
- `when <cond>` guards visibility; the topic is offered only while the condition
  holds, evaluated with `self` bound to the person.
- `once` makes the topic one-shot: after it runs, the player cannot raise it
  again. Code can still bring it back with `reveal` (below).
- `hidden` starts the topic out of view, until a `reveal` brings it in.
- `idle` makes the topic the ask/tell fallback: it answers when the player asks
  or tells about something no other topic matched, the person's default reply
  instead of the flat library line. It takes no `words` (it matches on "nothing
  else did"), and it is otherwise an ordinary topic: it carries a full exchange,
  and `once` (a one-time "that is all I know") and `when` (a scene-dependent
  brush-off) work on it. A person may have several; the first in view answers.
  Idle topics belong to the ask/tell presentation only; the conversations menu
  ignores them (a menu has no unmatched-subject case), so one declared in a
  menu game is silently unused.

By default a topic is repeatable and never leaves on its own: the player can
raise it as often as they like. Nothing is needed to keep a topic around; every
control below only ever takes one OUT of view. (How often a topic can be raised
also depends on the presentation, and the two differ: see the note below.)

Three ways out of view, and when to use which. They differ in who is in control
and whether the topic can come back:

- A `when` guard is LIVE STATE: the topic appears and disappears as the
  condition moves, with no bookkeeping. A topic whose own body changes the
  state it is guarded on ("ask Vlad to cut the grill" sets the grill open,
  and the guard was `... and not grill_open`) therefore vanishes the moment
  it has run, with no `once` needed, and would return by itself if the state
  ever reverted. When the story state already encodes what the topic is
  about, the guard alone is usually the whole answer.
- `hidden` / `reveal` / `hide` is a MANUAL SWITCH: the author decides the
  exact moment a topic enters or leaves, from another topic's body or any
  handler. Revealing is repeatable; use it when no world state naturally
  expresses "this is now worth raising".
- `once` is a ONE-SHOT: after one telling the player cannot raise it again,
  regardless of guards. Unlike a `when` guard it does not return on its own,
  and the player can never bring it back, which is the point (a confession the
  suspect will not repeat, a joke that dies on the second telling). Only the
  author can stage a return, with a `reveal` in code, for a line that fires
  again under new circumstances; `once` then retires it once more. Do not use
  it for topics a `when` guard already retires, or the guard becomes irrelevant.

They combine: `hidden once` is a one-shot that starts out of view, and a `when`
guard on a `once` topic gates the single telling.

The body is an ordinary statement block, so any statement is allowed. It adds
four conversation forms:

- `you "..."` prints the player's line, auto-quoted and attributed: `You: "..."`.
- `reply "..."` prints the person's line, auto-quoted and attributed by name:
  `<Name>: "..."` (the person is `self`).
- `say "..."` is plain narration, a stage direction with no speaker or quotes.
- `reveal <subject>` brings another of the person's topics into view; `hide
  <subject>` takes one out of view.

The speaker labels and the quotation marks live in overridable library blocks
(`line_you`, `line_reply`, `line_end`), so a story or a language pack can restyle
or translate the framing without touching the topics.

Because the body is a statement block, `vary` (chapter 15) works here like
anywhere else, and a person whose answer changes on each asking is exactly
that: reply-framed variants in `or` groups. Bare-string lines between them
stay stage directions, per the forms above:

```
    topic cowboy
        you "What about the cowboy?"
        vary loop
            reply "Nobody around here likes to talk about him."
        or
            reply "Still asking? Some questions cost more than others."
        or
            reply "I have said all I will say."
```

A worked fragment:

```
thing esme of character in tent
    name "Madame Esme"
    named

    topic fortune "your fortune"
        you "What do you see for me?"
        reply "A long road, and a choice you will not want to make."
        reveal road

    topic road "the long road" hidden once
        you "This road. Where does it lead?"
        reply "North, into the dark."

    topic charm "the silver charm" words charm, relic when player holds charm
        you "What is this charm worth to you?"
        reply "More than you have. Keep it close."
```

Raising `fortune`, by asking or by picking it, runs the exchange and reveals
`road`, which then appears (it began `hidden`); `road` is `once`, so it retires
after one telling. The `charm` topic is offered only while the player holds the
charm, and answers to `ask esme about charm` or `about relic`.

## Chapter 18: Grains

Grains are prose texture: one line each for the words a room description
mentions in passing (the gravel, the ceiling, the distant hills) that
deserve an answer but no existence. A grain is deliberately ONE grammar
line, and the line is the whole feature: it may answer several verbs and
several words, shade its response with `if action is`, and that is all it
will ever do. The cap is the point. A grain has no state, no place in the
tree, no handlers, no kind, no listing: nothing but words and an answer.

Grains are NOT a cheap-object device, and they are deliberately less than
PunyInform's cheap_scenery. That pattern serves the Z-machine version 3
world, where the object ceiling is real and an author is pushed to make
one non-object do as much as possible. Arcturus targets version 5 and 8,
where objects are not scarce, so a grain never needs to imitate one. The
rule of thumb: the moment a patch of scenery wants different answers per
verb beyond a one-line `if action is`, or state, or to be seen in more
than prose, stop growing the grain and declare a `scenery` thing. That is
not a workaround; it is the intended escalation, and it costs you nothing
the version 3 author had to fear.

A `grains` block lists grain lines. Each line names the actions it answers, the
scenery words it matches (one or more, joined by `or`), and a response, which
is a one-line `say`, a `do` of a named block, or an indented body. The actions
are named the way an `on` handler names them, by action (`examine`, `touch`,
`smell`), not by the player's word: they are fixed identifiers, while the scenery
words are the vocabulary the player types and a language pack localizes. In
English the two coincide, so `examine` reads as both; a Spanish grain still writes
`examine "mar"`, the action in the fixed name and `mar` in Spanish.

```
room foyer
    name "Foyer of the Opera House"
    desc "Red and gold, with glittering chandeliers overhead."

    grains
        touch, examine "chandeliers" or "hall" say "Pretty nice."
        examine "gold" say "Holy crap, that is worth a fortune."
        examine "carpet"
            say "Threadbare in the corners."
            change foyer.noticed to true
        examine "ceiling" do describe_ceiling
```

Grains may also be attached from outside the object's body, which lets
extensions or language packs add them:

```
foyer.grains
    examine "molding" or "cornice" say "Ornate plasterwork."
```

A grain matches when the player's verb resolves to one of the grain's actions
and names one of its words, and no real object in scope matches that word. The parser handling of grains
is defined in chapter 14. Grains cost only dictionary words and a small table, never
an object entry.

A grain word may be reused freely across rooms: "steps" can be set dressing in
the hallway and again in the cellar, each with its own response. The word gets
one dictionary entry, which points at a chain of (grain, owner) pairs, and the
parser answers with the grain whose owner is in scope. When several grains of
the same word are in scope at once (rare: a room and something the player
carries), the first declared wins.

Within one owner, though, a word belongs to a single grain line. All the
verbs that word answers go on that one line, and they share its response:

```
    grains
        examine, touch "junk" say "Sticky, and useless."
```

Splitting them across two lines does not give you two answers. The first
grain for the word answers whatever verb is typed, so the second line never
runs, and the compiler says so rather than leaving you to find out in play.

When the answers should differ per verb, keep the one line and branch on
`action`, which reads the action the turn is running:

```
    grains
        examine, touch, smell "junk"
            if action is touch
                say "Sticky, and you regret it."
            else
                say "A heap of laboratory junk."
```

`action` works anywhere a turn is being dispatched, and it earns its keep
most in the two places that answer many verbs at once: a grain like this
one, and an object's `on other` catch-all, which can finally tell what was
tried. Compare it against a bare action name (`action is touch`), the same
sugar `way` has for directions; a name of your own always wins, so an object
called `touch` still means the object. For an answer that differs in more
than wording, a `scenery` thing with its own `on examine` and `on touch` is
still the clearer tool. For one piece of scenery genuinely visible
from several rooms, a `scenery` thing with `spans` (chapter 3) is still the
better tool: one object, one description, one identity.

### Dual-role words

A grain word may also be a command word: LIGHT is one of the most used
scenery words in the genre, and LIGHT is a verb. Both live. The command
owns the word's dictionary entry, so typed FIRST it is always the verb
(LIGHT LAMP switches; SMELL DUST smells); named as a NOUN it reaches the
grain (X LIGHT answers the scenery). The compiler notices the collision
itself and emits a small side table only then; a game whose grain words
never collide with a verb is byte-identical to one built before the
mechanism existed.

## Chapter 19: Scoring

Score just works. One line in the game block turns it on:

```
game
    title "Hibernated 2"
    scoring
```

With `scoring` on, every room pays five points on the first visit and every
takeable thing five points on the first take, automatically: no attributes,
no bookkeeping, no table. The start room and whatever the player starts
holding never pay (nothing is earned by beginning). A room or thing that
should not score opts out with one line:

```
room broom_closet
    scored false
```

Things a plain take refuses anyway (scenery, fixed, animate, doors) never
pay and never count.

For everything the compiler cannot know, the events, there is `award`, a
statement legal anywhere a statement is (handlers, topic bodies, grains):

```
on push
    award 15
    say "The mechanism yields."
```

Every award site pays EXACTLY ONCE, by construction; a second push is a
silent no-op, and no `moved`/`visited`/flag guard is ever written. When one
problem has alternative solutions worth different points, name the pool:

```
if hacked_it
    award 10 for door_solved "outsmarting the blast door"
else
    award 5 for door_solved "outsmarting the blast door"
```

A pool pays once, whichever branch fires first. Its label is author
documentation: it names the pool in the source and in the compile ledger,
and costs the story file nothing.

MAX_SCORE COMPUTES ITSELF: the sum of every automatic room and thing, every
anonymous award site, and every pool counted once at its maximum. It is
never typed, so it can never drift from the game (no more 355/350). The
compile ledger prints the plan (`scoring 6 award sites, 1 pool, 12
auto-scored; max_score 95`), which is your scoring table: generated, not
written. The one honest limit: an award that is UNREACHABLE still counts,
because reachability is yours, not the compiler's; the ledger makes such a
site easy to spot.

RANKS, the Infocom ladder, need no numbers either:

```
ranks
    "Cosmic Explorer"
    "Interstellar Apprentice"
    "Space Archaeologist"
    "Savior of the Universe"
```

The titles spread evenly across the summed max (the last always means full
score) and the score verb announces them: "You have scored 55 of a possible
95, which earns you the rank of Interstellar Apprentice." An entry may pin
its own threshold, overriding the spread, in either unit:

```
ranks
    "Cosmic Explorer"
    "Interstellar Apprentice" at 17 percent
    "Slayer of the Prime Unit" at 320 points
    "Savior of the Universe" at 100 percent
```

A PERCENT pin scales with the summed max, so the ladder keeps its shape as
the game grows during development; a POINTS pin is the definite value,
verbatim, for when a rank must sit exactly at a known threshold. Mix them
freely; unpinned titles keep the even spread.

SCORE is the one score verb, Infocom-shaped:

```
You have scored 55 of a possible 95, in 21 turns, which earns you the rank
of Space Archaeologist.
```

One care the automatic points ask for: they pay through the verbs, so a
cutscene must pay the same way. Moving the player without walking (a crash
landing, a transit pod) is `teleport(dest)`; handing the player an object
without TAKE (a panel pried open, a mechanism yielding its prize) is
`gain(obj)`. Each pays exactly like the verb would, so no auto-scored
point ever becomes unreachable; a bare `move obj to player` pays nothing.
Section 5 has the rule of thumb (the move-versus-gain warning), chapter 9
the statements themselves.

The escape hatch: `change score` stays legal (penalties, score-as-resource),
but it is off the paved road: hand-changed points play no part in the
computed max. `award` is the road.

## Chapter 20: Pictures: arc_image

Optional graphics. A room can carry a picture, shown on an interpreter that can
display one (Actaea's window) and silently absent everywhere else. The story
stays a conformant z5 file that runs unchanged, text-only, on any standard
interpreter: an interpreter only decodes bytes its control flow reaches, and the
draw sits behind a capability guard a text interpreter never passes. A game that
declares no picture is byte-identical to one that never could.

A picture is named by its `arc_image` id, a resource slot. The id is one number
shared by every target: on a modern system the interpreter loads `<id>.png`; a
retro build (B12) loads slot `<id>` in the machine's own format. So there is no
name table to translate down. Write the id as a plain number, or, for
readability, as a constant that folds to one:

```
constant scene_path = 8
constant scene_church = 1

room opening
    name "Forsaken Path"
    desc "A path deep in the Black Forest, extending north."
    arc_image scene_path
    north church

room church
    name "Churchyard"
    desc "A small stone church, its door ajar. The path leads back south."
    arc_image scene_church
    south opening
```

Ids start at 1; 0 is reserved to mean "no picture" (it clears the band). Cosmos
reads the property on room entry, behind the guard, and draws the picture; a
room with no `arc_image` clears the band, so the picture always matches the
room. Re-looking in the same room does not redraw (it would make a retro target
re-decompress its art for nothing). What a cleared band looks like depends on
the interpreter: a windowed one may give the rows back to the prose, a retro
screen keeps a blank strip. If you dislike that strip across a long pictureless
stretch, give those rooms a placeholder picture; Arthur and the DAAD games did
the same.

THE PICTURE FOLLOWS THE SCENE. `arc_image` is an ordinary value property,
so a handler can move it, and the band repaints at the end of that same
turn, no LOOK needed:

```
constant door_shut = 3
constant door_open = 4

room gatehouse
    name "Gatehouse"
    desc "A studded door bars the way north."
    arc_image door_shut

thing studded_door in gatehouse
    name "studded door"
    words door, studded
    fixed
    on open
        change gatehouse.arc_image to door_open
        say "The door grinds open."
```

The room must declare an initial `arc_image` for the slot to exist; after
that, what you set is what the band shows. (Behind the scenes the library
checks one property per turn and only draws on a change, so a quiet turn
costs a comparison and a noisy one costs one draw.)

DARKNESS IS A SCENE TOO. In a game where darkness can happen (a room with
`lit false`, or a handler that clears `lit`), an images game must declare
the picture the band shows in the dark, and the compiler refuses to build
without it:

```
constant arc_image_dark = 7    // the band in the dark: id 7
```

The band then never shows a stale picture over a dark room: walk into the
dark and the darkness picture appears, restore the light and the room's
own picture returns. What the darkness picture depicts is yours; black
with two red eyes has been suggested. A game with no darkness anywhere
never declares it and pays nothing.

Art is authored once as PNGs in one of two shapes, each a whole number of
8-pixel text rows tall so the status bar sits flush under the band:

| Mode | Pixels | Rows | `arc_mode` | Look |
|---|---|---|---|---|
| Infocom | 320x72 | 9 | `9` | The upper third, the classic Arthur style. |
| DAAD | 320x96 | 12 | `12` | The upper half, the Rabenstein style. |

You declare the mode once, game-wide, with a constant named `arc_mode`, whose
value is the band height in text rows:

```
constant arc_mode = 12    // DAAD mode (320x96); 9 for Infocom mode (320x72)
```

This is deliberate, and it matters for the retro targets: the interpreter learns
the band size from the story, not by measuring a picture. It reserves the band
and lays out the screen (and, on an 8-bit machine, its memory) before any
picture is loaded, so nothing depends on a picture's pixel dimensions. The mode
travels in the draw opcode itself. `arc_mode` must be `9` or `12`; omitted, it
defaults to `9` (Infocom mode). All of a game's pictures share the one mode, so
author your art to match it.

A modern interpreter integer-scales the picture to the window width, which keeps
pixel art crisp at any font size; pixel art is the medium that looks best.

During development, point the interpreter at a directory of numbered PNGs
(`actaea game.z5 --images art/`). For distribution, the `arcimg` tool packs
them into a Blorb, the IF world's standard resource container: a sibling
`game.blorb` the interpreter reads automatically next to the story, or,
with the story embedded, a single `game.zblorb` that carries the whole
game. The same finished files feed the `proteus` web builder (docs/09).

`arcimg` is the third standalone tool, shipped like `arcc` and `actaea`
(`build/arcimg`, a single self-contained file). The two commands of the
modern path:

```
arcimg prep opening.jpg --id 8 --mode daad -o art/    # art/8.png at 320x96
arcimg pack art/ -o game.blorb                        # the distributable pack
arcimg pack art/ --zblorb game.z5 -o game.zblorb      # the whole game, one file
```

The full picture workflow, the retro conversions, and which interpreters
play the pictures today and next, is its own author guide: docs/07.

Mode-sized PNGs need nothing but the standard library; `prep` reaches for Pillow
only to resize or convert, and offers a guided install the first time. A worked
example, with its `.blorb` and heavily commented source, is in
[examples/arc_image](../examples/arc_image).

## Chapter 21: Writing in another language

Arcturus is meant to be authored and played in languages other than English.
Spanish and German are official, first-class Arcturus languages, maintained
alongside Cosmos: Spanish (`cosmos/spanish.granule`, informal tuteo) and German
(`cosmos/german.granule`, informal du) both ship, each a first pass pending
native review. Others are the same shape of work. This section gathers what a foreign-language author needs; the mechanics
each live in their own place, cross-referenced here.

Selecting a language. `summon.language "spanish"` compiles the Spanish layer in
place of English. English is the default, exactly one language is built into a
story, and a plain English game pays nothing for the others. That directive is the
only way to select a language, because only it does the swap (drops
`english.prelude`).

What is and is not translated. The language layer is one granule, a full fork of
`english.prelude` in three parts: the parser hooks that read the language, the
verb, `direction`, and `particle` vocabulary, and every message (including the
framing the status-line and conversation-menu granules print). Everything else,
the agnostic parser skeleton, scope, dispatch, and the action handlers, is shared
and untouched.

Three refinements that came out of the Spanish native review (Pablo Martinez)
and serve every language: a closed openable announces itself in listings
("Ves un cofre de roble (que está cerrado).", "(closed)", "(geschlossen)"),
declared per pack in `list_item` with whatever agreement the language needs;
the `article`/`indefinite` properties override a derived article verbatim
(chapter 15); and the Spanish pack retries an unknown first word that
ends in -r with the -r stripped, so a regular infinitive finds its imperative
("comer" reaches "come"), a trick a pack implements in its own `resolve_verb`.

The player's standard self-words are the language layer's too: each pack
declares them with `player.words` (me/myself/self/yourself/you;
mich/dich/selbst; yo/mismo) plus a printable `player.name` its own messages
read well with, and a game's own `player.words` ADD on top (chapter 4).

So are the chain words (chapter 14): `chain ",", "and", "then"` in English,
`chain ",", "y", "luego"` in Spanish, `chain ",", "und", "dann"` in German.
The splitting itself is the agnostic skeleton's; the pack only names the
words. And so are the noise words (`noise "the", "a", ...`; el/la/los...;
der/die/den...), the articles the parser knows but ignores, which noun lists
depend on (chapter 14).

Verb particles, so separable verbs read naturally. A multi-word verb combines a
base verb with a particle (English "switch on", "take off"; German "schalt ... an",
"schliess ... auf"). The particle words are declared in the language layer, not the
compiler, with `particle <role> "word", ...`. The roles are `on`, `off`, `auf`, and
`zu` (prelude `_PARTICLE_ROLES`), and the parser's `compound` block maps a base
verb plus a role to the real action, so the same word can mean different things
after different verbs. German uses all four:

- `particle on "an", "ein"` / `particle off "aus", "ab"` with base `verb "schalt",
  "schalte"` give "schalt die Lampe an", "... ein", "... aus", and the loose
  "schalt an Lampe".
- `particle auf "auf"` / `particle zu "zu"` with a base `verb "schliess", ...`
  (whose first grammar line is `close`) give the everyday "schliess die Tuer mit
  dem Schluessel auf" (unlock), "... ab" and "... zu" (lock), while bare "schliess
  die Kiste" still closes. "ab" doubles as the switch-off particle; `compound`
  keys on the base verb, so "ab" means off after schalt and lock after schliess.

The parser finds the particle wherever it falls (both orders work for a one-noun
verb), and a word may be both a particle and a preposition (English "on" in "put X
on Y", German "an" in "gib X an Y", "auf" in "leg X auf Y"): the parser treats any
tagged word as a phrase boundary, so the double duty just works. The line to hold onto: the identifiers a game's *code* uses stay
English, only what the player *reads and types* is translated. So kinds (`thing`,
`room`), attributes (`openable`), the direction properties in a room exit (`east
puerta`), and the actions a `grains` line answers (`examine "mar"`) are fixed
English names, while the player types `este` and `examinar`. A translator forks
one file and touches nothing else.

Accents, and typing on 8-bit systems. Display text is fully accented: the encoder
writes each accented character with its Z-machine ZSCII code (chapter 23), so the
acute vowels, u-diaeresis, n-tilde, and the inverted marks render on any
conformant interpreter, the 8-bit and 16-bit ones included. But an 8-bit
interpreter renders an accent it cannot type, so every word the player must *type*
also carries a tilde-free form: the language's verbs list both (`oir`/`oír`,
`ensena`/`enseña`), and an object with an accented name lists both spellings in
its `words` (`words lampara, lámpara`). The rule: accent the display, and give
every typeable word a plain-ASCII spelling too.

Gender and articles, automatically. In a gendered language the article (un/una,
el/la) and adjective agreement are automatic, with no per-object work. The
compiler derives a `feminine` attribute from the object's head noun, the first
word of its name: a head ending in -a, or in a reliably feminine suffix such as
-ción, -sión, -dad, -tad, -tud, or -umbre, is feminine, everything else masculine.
The pack's article blocks (`art_the`, `art_a`) and its messages read that
attribute and agree on their own (`una lámpara`, `la caja está cerrada`). The
author declares `feminine` only for the residue no spelling can reveal (la llave,
el mapa), the same one-time act as the English `an` exception. `${the noun}` and
`${a noun}` lower to a call to the article blocks precisely so a pack owns the
article words (chapter 16).

Gender where spelling cannot reveal it (German). German has three genders and no
rule to guess them from, so the author states the gender the natural way, by
declaring the object's article: `der`, `die`, or `das` on its own line in the
object, like any attribute. The compiler maps that to the gender the pack reads
(`die` sets `feminine`, `das` sets `neutral`, `der` is the masculine default), so
the source reads as an author thinks (`das Buch`, `die Kiste`), not as an abstract
flag. Because the gender is explicit, the Spanish -a spelling guess is turned off
for German, so a masculine noun ending in -a is left masculine. The German article
also inflects for case, and a message asks for the case it needs with the tag from
chapter 15, `${the:acc noun}` or `${the:dat noun}`; the pack's `art_the`
turns gender and case into the right word (der/den/dem). German predicate
adjectives do not inflect ("die Kiste ist offen", "der Schrank ist offen"), so the
messages carry no per-gender variants: only the article changes, in the one place
it is printed. The worked example is `examples/beispiel-deutsch.storyarc`.

Number joins gender: the `pluribus` attribute (chapter 5, the standard attributes)
marks the one object that is grammatically plural (the scissors), and the same
machinery agrees. The article blocks grow a plural column (English "some";
German's bare indefinite plural and die/die/den/der by case; Spanish los/las,
unos/unas, by gender), the pack's `art_is` block words the `${is x}` copula
(is/are, ist/sind, está/están), and the core messages carry number branches
beside the gender ones, every one under the `any_pluribus` fold, so a game
with no pluribus object compiles byte-identical. The German and Spanish plural
wordings await their native passes.

Abbreviations. The baked-in abbreviation set is tuned to the English library, so a
non-English game is built with no default set rather than English abbreviations
that would not fit and would only cost the table (docs/04 chapter 3). Cosmos
deliberately ships no standard set per language. Abbreviations barely matter for a
small game; for a larger foreign game the recommendation is to run `arcc
--make-abbreviations`, which sees the selected language's translated text and
writes a set tuned to it (on the Spanish example, several hundred bytes below the
no-abbreviation size).

Forking a language, or adding one. A language pack is a granule, `<code>.granule`,
that self-identifies with a marker at its top, `language "<code>"`. To fork one,
`arcc --eject-granule spanish` writes it out; translate or adjust it, keep (or
rename) it as `mylang.granule`, and select it with `summon.language "mylang"`, the
filename being the selection key. To start a language from scratch, `arcc
--eject-language` writes `english.prelude` to translate into a new
`<code>.granule` (add the marker). Because a language pack must be selected with
`summon.language` (which does the swap), a plain `summon spanish.granule` is a
compile error that points you to `summon.language`, and `summon.language` on a
granule that is not a language pack is likewise an error; neither can silently
leave English baked in beside the new language. The worked example is
`examples/ejemplo-espanol.storyarc`.

## Chapter 22: Summon: the granules

`summon` brings an optional Cosmos feature, or your own granule, into the build.
A granule is ordinary Arcturus source (kinds, verbs, blocks, grains) in a
`.granule` file, loaded only when summoned. There are three forms, which differ
in where the granule is found; the resolution rules and the fork workflow are in
05.

```
summon.statusline                        // the bundled feature, always
summon statusline.granule                // your copy if present, else bundled
summon "extensions/lockpicking.granule"  // an explicit file
summon.extendedverbs squeeze, burn       // a granule that declares verbs,
                                         // sliced to these families (chapter 22)
```

- The dotted form (`summon.statusline`) always uses the copy that ships inside
  the compiler. It also carries the non-granule feature `summon.language
  "<name>"`, which selects a language pack (a granule that overrides not only the
  messages and vocabulary but the parser's grammar logic where a language needs
  it, 02).
- The bare filename form (`summon statusline.granule`) prefers a copy in the
  story's directory or a `-L` directory, and otherwise falls back to the bundled
  one with a notice. This is how you summon a forked granule by name, and also how
  you summon a tuned `abbreviations.granule` (below).
- The quoted form is an explicit path, with no bundled fallback.

A MULTI-FILE GAME summons its own chapters the same way: `summon
rooms.storyarc`, `summon messages.storyarc`, and so on from the main file.
A summoned `.storyarc` is a CHAPTER of the game, not a module: EVERY
declaration in it ranks as GAME in the override chain (this chapter), so a
message override in messages.storyarc, or a `verb` redefined in
grammar.storyarc, beats the library's and a summoned granule's exactly as
if it were written in the main file, in any summon order. The main file
(the one you hand to `arcc`) is the most specific of all, so it overrides
its own chapters where they both declare the same thing. Only `.granule`
files ride at granule rank, below the game.

Text compression is not a summonable feature. The compiler always applies a
standard abbreviation set, so nothing is required to get it. A story can tune the
set to its own text with `arcc --make-abbreviations`, which writes an
`abbreviations.granule` beside it; summon that by name (`summon
abbreviations.granule`) to use it in place of the default (chapter 24).

The granules that ship with Cosmos - extended verbs, the status line, verbose
exits, the conversation menu, and debug verbs - are catalogued in chapter 22. Debug is
opt-in by the summon alone; there is no separate release build to strip it.

### Summonable features

These ship with Cosmos but are off until summoned (this chapter). Each is a
granule, an official one distributed with Cosmos: a separate `.granule` module
that enters the build only when summoned, so dead-code elimination keeps an
unsummoned feature out of the story file entirely. Only the core Cosmos library
is `.prelude`; everything opt-in here is a granule.

`summon.conversations`. The menu presentation of the `topic` model. `talk to
<person>` lists the topics in view as a numbered menu; the player presses the
number to ask one, the exchange prints, and the menu redraws (topics reveal,
retire, or unlock by `when` exactly as on the ask/tell path) until 0 or ENTER
ends it. The menu prints inline in the main window and selects with a single
keypress (the `read_key` intrinsic, backed by the `read_char` opcode), so there
is no upper-window juggling; every line of wording is an overridable block
(`draw_menu`, `msg_no_topics`, `msg_talk_over`). A sketch:

```
summon.conversations

thing barman of character in bar
    name "barman"

    topic cloak "the cloak" words cloak when player holds cloak
        you "About this cloak of yours."
        reply "Best hang that up, sir. It unsettles the regulars."

    topic message "the message" words message once
        reply "Folk scrawl all sorts in the dark. I pay it no mind."
```

This is the same `topic` construct the Infocom-style ask/tell path uses
(summon.infocom_talking, chapter 22): `words` are the ask/tell subject words,
`when` gates visibility, `hidden` plus `reveal`/`hide` unlock by name, `once`
retires after use, and `you`/`reply`/`say` form the exchange.

The one place the two presentations differ is REPETITION, and it follows each
one's shape. In the MENU, every topic the player picks leaves the list, so the
menu shrinks as the person is drawn out: a plain topic is spent when picked, and
`once` adds nothing there. On the ASK/TELL path there is no list to shrink, so a
plain topic is REPEATABLE, the player may raise it again and again, and `once` is
what marks the one that should answer only the first time (the confession, not
the weather). Either way `once` stops only the PLAYER: a `reveal` in the author's
code brings a spent or `once` topic back for another turn, after which it is
spent again.

The two granules are two presentations of one model and are mutually exclusive
BY THE COMPILER:
summoning both is an error, an author settles on one. ASK, TELL, and ANSWER
are standard verbs either way (as in PunyInform): with no conversation granule
they hand over to the talk brush-off (elevated conversation belongs to the
granules alone); conversations makes ASK open the person's menu (asking IS
talking) and TELL answer with the use-TALK hint; infocom_talking makes both
dispatch the person's topics, with its own flat defaults as the no-match
fallback (they cost other games nothing). The seams are overridable blocks
(ask_to, tell_to, answer_to), so the words and wording stay in the language
layer.

`summon.language "<name>"`. Localization: compile a language pack (`spanish`) in
place of English so the game plays in another language. Selecting, writing,
forking, accents, gender, and abbreviations for a non-English game are gathered in
chapter 21.

`summon.debug`. Developer verbs for testing, catalogued in chapter 22: `tree` (the
whole object tree), `scope` (what is reachable here), `fetch`/`purloin` (pull any
object to you), `warp`/`gonear` (teleport to an object's room), `inspect`/`showobj`
(an object's location and attributes), and `unmute` (hear the muted offstage
prose of the background performers, name-tagged). They reach objects out of scope, which the
parser normally refuses, through the `reach_unscoped` parser seam the granule
overrides. There is no separate release build to strip them: not summoning the
granule leaves them out entirely, which is the exclusion.

`summon.takeall`. TAKE ALL, DROP ALL, and TAKE ALL FROM <container>,
catalogued in chapter 22. Every swept item is a full turn (daemons and the clock move
per item, the same rule as a chained line; a deliberate departure from
Inform's one-turn ALL), undo takes the whole sweep back, and an empty sweep
refuses so a chain stops. The core deliberately omits ALL; the granule's
`all` declaration names the words and its hand-off folds away unsummoned.

`summon.plurals`. The group model, catalogued in chapter 22: group words (each coin
declares `plural coins`, and "take coins" runs the take on every coin in
scope) and THEM for the last group. A group word matching a single object
binds it singularly; a tie between group members sweeps instead of asking.
Every item is a full turn. Noun lists ("take lamp and box") are NOT part of
this granule: they are core (chapter 14). English-worded; a translation forks
the granule (a Spanish fork should keep THEM out: the clitic plurals in the
core pack already cover it, and bare los/las are the articles).

`summon.ambience`. Rooms and things murmur over time, catalogued in chapter 22: an
`ambience` block of lines with a cadence (`about` breathes, `every` ticks,
`in order` recites), topic-style `when` guards on the block and on single
lines, `do <block>` computed lines, and the `ambience_rate` dial (0 mutes).
One line at most per turn. A single recurring line is better served by a
plain daemon; the granule is for shuffled texture (NPC behavior, layered
room mood).

`summon.verbose_exits`. Helpful blocked-direction messages, game-wide. When a
player tries a direction with no exit, instead of the default "You can't go
that way." Cosmos lists the room's available exits, for example "You can only
go north or east from here." The list is computed from the room's live
direction properties each time, so it stays correct as exits open and close;
computed direction blocks (chapter 8) are read to build it, which is why they
must be side-effect free. The phrasing is an ordinary overridable Cosmos
string, and a room's own `on go other` (chapter 8) takes precedence over the
listed message. This replaces hand-writing a blocked message in every room.

### Granules and preludes

Cosmos comes in two kinds of file, both ordinary Arcturus that lex identically;
the extension marks the role (chapter 1):

- A `.prelude` is part of the core library, loaded before every story.
- A `.granule` is a **summoned module**, loaded only when a story summons it,
  and left out entirely otherwise.

Overriding is one rule, the chain complete: **most specific wins**. A game
block overrides a granule block overrides a library block of the same name.
That is how the statusline granule replaces the core `prompt` (a granule
overriding the prelude), how a translation's blocks replace the English
wording (a language pack is a granule), and how a story reskins one line of
a summoned feature: redefine `msg_throw` and yours speaks, extendedverbs
summoned or not.

> **Most specific wins: game over granule over library, block by block.**

A summoned `.storyarc` (the chapters of a multi-file game, this chapter)
counts as GAME here for EVERY declaration it holds, blocks, handlers, and
verbs alike, whatever order it loads in; only `.granule` files ride at
granule rank. So a `verb` a chapter redefines wins over a granule's verb of
the same word, exactly as a chapter's message override wins over a granule's
message.

One courtesy at the granule seam: a granule's messages (`msg_*`, `line_*`)
are its public skin and reskin silently, but a game block that replaces any
OTHER granule block gets a compile note, because colliding with a granule's
internal helper by accident (a block name you never saw, in a file you never
opened) breaks the granule mysteriously. The note names the block; if the
override is deliberate, it is working as declared, and if not, rename yours.

Forking (chapter 23) remains the way to reshape a granule wholesale: take the
file, edit anything, summon your copy.

### Summoning a granule

There are three forms (this chapter), and they differ in where the granule is
found:

```
summon.statusline             // the bundled copy, always
summon statusline.granule     // your copy if present, else the bundled copy
summon "/path/to/fork.granule"  // exactly this file
```

- **`summon.statusline`** (dotted) always uses the copy baked into `arcc`. It
  never looks at your directories. This is the form to use for the official
  feature, and the one the shipped examples use. Mind the fork trap: editing
  an extracted granule beside the story does nothing while the summon stays
  dotted (a deleted default message keeps printing, because the bundled copy
  still supplies it); the compiler notices a same-named `.granule` beside the
  story and prints a note naming the fix, which is the bare-filename form
  below. The dotted form also covers the
  non-granule feature `summon.language "<name>"`, a compiler feature rather than a
  runtime module (this chapter). The tuned abbreviation set is not a dotted feature;
  it is summoned by name (chapter 24).
- **`summon statusline.granule`** (a bare filename) searches the story's own
  directory, then each `-L` directory, and only then falls back to the bundled
  copy - printing a note when it does, so you know your fork was not picked up.
  A custom name found nowhere and not bundled is an error. This is the
  fork-friendly form.
- **`summon "..."`** (a quoted string) is an explicit file: an absolute path as
  written, or for a bare quoted name the story directory and then the working
  directory. There is no bundled fallback; a missing file is an error.

`-L` directories must be absolute paths, so the library a story compiles against
is deliberate and unambiguous.

### when language: granules that speak

A `when language` group holds ordinary declarations that exist only when
the named language is the game's language; the other groups vanish at
combine time and cost nothing:

```
when language "german"
    verb "finde", "suche"
        find_where text
```

Two homes serve a speaking granule, by one rule. A LIBRARY granule's
messages live in the language packs beside everything else the library
says (the statusline's "Punkte" and "Züge" sit in german.granule), so
`arcc --eject-language` hands a translator ONE file that carries the
whole library, granule wording included; the blocks fold away in a game
that never summons the granule. What cannot live in a pack is GRAMMAR,
because verbs and dictionary words do not fold: a granule that brings
new verbs declares them inside itself under `when language` groups, one
per language, stacked and visible (the pathfinding granule is the
model). A THIRD-PARTY granule has no pack to lean on and self-hosts
everything, wording and grammar alike, in its own `when language`
groups; [examples/granules/whistle.granule](../examples/granules/whistle.granule)
is the worked pattern. Groups do not nest, and a language without a
group simply contributes nothing.

### The shipped granules

Which granule speaks which language, at a glance. SPEAKS ALL means the
granule works in every shipped language out of the box: its words sit in
`when language` groups (or it declares none) and its messages live in the
language packs. NEUTRAL means the granule has no words and no voice of
its own, so language never touches it. ENGLISH means the granule is
English-worded by design, and a game in another language forks it and
translates the fork (chapter 23), summoning the fork in the granule's
place; the more intricate the wording, the more the translation deserves
an author's own voice, which is why these stay untranslated.

| granule         | languages | notes                                    |
|-----------------|-----------|------------------------------------------|
| conversations   | speaks all | menu framing from the packs             |
| infocom_talking | speaks all | ask/tell wording from the packs         |
| statusline      | speaks all | score/moves labels from the packs       |
| pathfinding     | speaks all | grammar in `when language` groups       |
| takeall         | speaks all | all-words per language, wording in packs |
| plurals         | speaks all* | group words are the author's own vocabulary, so the sweep works anywhere; only THEM is English, and a fork drops or renames it (see its section) |
| foresight       | speaks all | wording from the packs                  |
| verbose_exits   | english    | the exit frames are English-worded; fork to translate |
| quotes          | neutral    | draws boxes, says nothing               |
| ambience        | neutral    | timing machinery; your lines are yours  |
| matrix          | neutral    | machinery only                          |
| nautical        | english    | the terms ARE the flavor; fork to translate |
| use             | english    | one verb and two lines; fork to translate |
| extendedverbs   | english    | the big verb set; fork and translate the slice you summon |
| debug           | english    | a developer tool, deliberately          |

### extendedverbs

```
summon.extendedverbs                         // every verb in the set
summon.extendedverbs squeeze, burn, search   // exactly these families
summon extendedverbs.granule squeeze, burn   // the same slice of your fork
```

The verbs beyond the always-in standard set, taken whole or by the slice.
A SELECTION names verb families, where a family is one verb declaration
and its synonyms, named by its action: `search` brings "frisk" along,
because they are one action with two wordings, and it never brings `dig`
as a neighbour. You pay only for what you take: an unselected verb's words
never enter the dictionary, its grammar never compiles, its handlers are
dropped at load, and its messages sweep out with them. A name the granule
does not offer is a compile error that lists what it does. The bare form
keeps meaning all of it, so no existing game changes, and the same
selection works on a fork, which is the intended shape: one canonical verb
library that forks carry whole and stories slice. The full verb-to-action table
with every synonym, and each default line, is the granule source itself
(cosmos/extendedverbs.granule, the editable template); the roster:

- RUMMAGING: `search`/`frisk` works on ANY object, and the rule is: search
  tells you what is there, and makes findable what wasn't. A LIVING thing
  gets a social rebuff (frisking a person is not a discovery), a SHUT
  container keeps its secrets, and everything else searches for real: the
  contents are listed ("You find a wallet and a knife."), marked seen, and,
  for a plain thing that cannot be looked into (a knocked-out guard, a
  haystack), spilled to the room so they are truly takeable; an open
  container or supporter only lists, its contents being reachable already.
  So the whole authoring recipe for a lootable body is: clear `animate` on
  the knockout and put the loot inside; nothing else. `alter` on the object
  rewords the report while the mechanics run regardless. Things you marked
  `hidden` stay yours to reveal. And the engine is public: `search_loot(self)`
  from an instance `on search` runs the success path where the default
  declines, the compliant frisk of a still-animate character being the
  canonical case. One thing to know about the rebuff: it wins over your
  wording. A living character refuses before any report is reached, so an
  `alter` followed by `continue` never speaks on someone who is still
  `animate`. That is deliberate, since a conscious person should almost
  always refuse to be frisked. When you do want the exception, call
  `search_loot(self)` instead of continuing: it runs the success path and
  speaks your alter with it.
- ACTING ON THINGS, futile by default until an object overrides:
  `throw ... at`, `rub` (polish, clean, wipe...), `squeeze`, `tie ... to`,
  `cut`, `fill`, `burn`, `blow`, `set ... to`, `empty`, `buy`.
- CONSULT ... ABOUT, the reference-book verb, and no longer futile: the
  subject rides a `text` slot (the ASK machinery), and the object's own
  inline `topic` declarations answer it. Topics parse on any object, so a
  gazetteer, a logbook, or a terminal answers CONSULT THE TOME ABOUT THE
  MINE with its matching topic, with either conversation granule summoned
  or neither. No match: "has nothing to say on the matter"; no subject:
  "Consult it about what?"; both granule-owned messages, reskinnable.
- BODY AND IDLE: `dig`, `wave`, `sleep`, `swim`, `swing`, `think`,
  `pray`, `shout`. And `swear`, the oldest Easter egg in the medium: a
  player who curses gets a dry line back instead of "unknown word"
  (reskin msg_swear for your own tone; select it or leave it out like
  any family). (`sit`/`rest` and `stand` are STANDARD verbs riding
  enter and exit: SIT ON THE CHAIR boards it, STAND or STAND UP leaves
  it, STAND ON THE STOOL boards too, in every game, no summon needed.)

(Conversation is not this granule's business: ask/tell/answer are STANDARD
verbs, and the two topic presentations are their own granules, conversations
and infocom_talking, below. There is no fullscore verb anywhere: SCORE is
the one score verb and reports score, turns, and rank itself.)

Every default is an ordinary free handler, so the override story is the
usual one: an object's own `on rub` wins ("on rub / say ..."), a top-level
`on rub` rule reskins the verb game-wide, and `continue` defers back to the
granule's default. The granule's own message blocks (msg_throw, msg_dig,
...) are granule-owned wording: override any of them from the story
(most-specific-wins), or fork the granule to reshape the set wholesale (chapter 23) rather than overriding from the story.

### infocom_talking

```
summon.infocom_talking
```

The Infocom-style conversation surface, the menu-less presentation of the
`topic` model: `ask innkeeper about lighthouse` scans the person's inline
`topic` declarations (chapter 17; they live in the person's body) for one
whose `words` match a typed subject word and is in view, runs it, and falls
back to its own flat "stays mum" default when nothing matches (those richer
defaults live here alone; every other game answers ask/tell with the one
talk brush-off). `tell`
shares the same path. Only the SUBJECT phrase is matched, the words after
the about/for; the person's own name (the listener) is not, so a topic whose
words happen to include the character's name does not fire for every ask.
There is no topic list anywhere: discovery is play,
the Infocom way, and TALK TO stays the flat brush-off a person can override
to nudge the player toward the two verbs that matter.

Several characters who answer about the same thing share one `subject`
declaration (chapter 17): it owns the match words and the label, each
character writes only its reply, and the vocabulary is stored once no matter
how large the cast.

ASK <person> FOR <thing> reaches the same topics: a request names a subject
just as a question does, and the topic tells them apart with `action is
ask_for` (so one topic can answer "what about the beer?" and "may I have a
beer?" differently). Nothing matching falls to the flat request default.

One topic serves both ASK and TELL, because a topic is one SUBJECT and the
two verbs raise the same subject. When the exchange should differ, branch on
`action` inside the body (chapter 11), which is also how a topic tells a
question from a statement:

```
    topic vase "the vase" words vase
        if action is tell
            reply "I know all about that vase, thank you."
        else
            reply "The vase was my mother's."
```

AGAIN repeats the last exchange, as retyping it would.

For a per-person default answer, give the person an `idle` topic (chapter 17): it answers when the player asks or tells about a subject no other topic
matched, in place of the flat library line. It is an ordinary topic with a
full exchange, `once` and `when` and all, that matches on "nothing else did"
rather than on words; several are allowed, and the first in view answers.
This is the ask/tell counterpart of the flat default; the conversations menu
has no unmatched case and ignores idle topics entirely.

With no list to exhaust, a plain topic here is REPEATABLE: the player may raise
it again and again (asking about the weather twice answers twice), and `once` is
what marks the topic that should answer only the first time (a confession the
suspect will not repeat). `once` stops only the PLAYER; a `reveal` in the
author's code brings a spent one back for another turn, after which it is spent
again. This is the opposite default from the conversations menu, where picking a
topic removes it from the list, so `once` adds nothing there (below).

The granule holds ONLY logic, and is as translatable as the menu: the
ask/tell/answer verb words, their grammar, and every message live in the
language layer (the packs carry them), and the granule overrides the
standard `ask_to`/`tell_to` seams with the dispatch. It is mutually
exclusive with the conversations menu BY THE COMPILER: summoning both is an
error, an author settles on one presentation. The topics themselves are
identical either way, so switching later is a one-line change.

### statusline

```
summon.statusline
```

A one-line status bar across the top of the screen, painted before every prompt:
the room on the left, the score and move count on the right, in reverse video.
The right side adapts to the screen width the way PunyInform does - the full
`Score: n   Moves: n` on a wide screen, the compact `Score: s/t` on a narrow
retro one - and to the game: one that scores nothing shows only the move
count (`Moves: n`), never a permanent "Score: 0". The fold decides at
compile time, so neither game pays for the other's bar. It coexists with the conversations menu: when both are summoned the
bar sits pinned above the topic list.

In the dark the bar does not name the room, because naming an unseen room
is a spoiler: it shows the language layer's darkness line instead ("In the
dark"; the German and Spanish packs carry their own wording). The whole
branch folds away in a game where darkness cannot happen, which the
compiler knows exactly (a room with `lit false`, or a handler clearing
`lit`, is what makes it possible).

### foresight

```
summon.foresight
```

The game does the obvious preparatory step for you. GIVE APPLE TO STACY
with the apple at your feet becomes:

```
(taking the apple first)
You give the apple to Stacy.
```

Built on the verb contract (chapter 12): a failed `requires noun
carried` is repaired with an implicit take instead of refused. The
parenthetical is a PROMISE, and it prints only when the promise is certain:
the repair asks the default take's own factored guard chain (take_probe)
first, so an unreachable or fixed thing refuses plainly, with the take's
own line and no promise before it. "(taking the sun first) The sun is
beyond your reach." does not happen here. The one residue is an object or
room with its own take handler, whose outcome no probe can know without
running it: those get promise-then-run, author prose landing between the
promise and the outcome, where it belongs. A free-standing `on take` rule
is not consulted by the certain path; a game that gates all taking through
free rules should not summon this.

Doors and containers get the same courtesy. A closed, UNLOCKED door on
the walk opens itself, "(opening the oak door first)", and the walk goes
on; naming a thing you KNOW is inside a closed, unlocked container opens
the container and the command continues, and the two chain: GIVE PEARL TO
BOB with the pearl visible in a sealed clear jar runs "(opening the clear
jar first)", "(taking the pearl first)", and then the give, and the plain
TAKE PEARL through the same glass opens the jar just as readily (the
sealed-take seam; the direct take and the give-chain share one manners
model). The same
probe rule governs every step (open_probe is the default open's own guard
chain), locked things stay honest refusals, since unlocking is a decision
where opening is mechanics, and the knowledge model draws the other line:
contents you have never seen cannot even be named, so nothing is ever
conjured. A container or door with its own `on open` handler gets
promise-then-run, the same residue as the take.

Off unless summoned, deliberately: implicit actions are a matter of taste.
The repaired take is silent (the bookkeeping runs, the points pay, no "Got
it."), one UNDO takes back the whole exchange, and the parentheticals'
wording is the language layer's (`line_foresight_take`,
`line_foresight_open`), so each pack speaks its own idiom.

### quotes

```
summon.quotes
```

The one-call form draws the whole box from a text catalog (chapter 2,
catalogs): `quote_catalog(last_letter)` sizes the frame from the
catalog's compile-time header (line count and widest line, no author
arithmetic, nothing measured at run time) and prints every entry. The
line-by-line form below remains for hand-built boxes.

A centered, reverse-video quote box in the upper window, in the tradition of
Infocom's Trinity: the classic way to open a game with an epigraph. The box is
centered from the interpreter-reported screen width, so it sits right on a
40-column 8-bit machine and a wide terminal alike, and it sits in the upper
third of the screen, where the eye expects it.

Three blocks, called in order:

- `quote(lines, width)` opens the box: `lines` is the number of text lines,
  `width` the length of the LONGEST line, counted by hand the way one counts a
  fixed-width layout. The box adds one space of padding on each side and a
  blank reverse row above and below. Opening the box clears the screen.
- `quote_line` advances to the next line and leaves the cursor inside it;
  the author's own `show("...")` then prints that line's text. One
  `quote_line` / `show(...)` pair per line, top to bottom. Lines print
  left-aligned inside the box; pad with leading spaces by hand for a
  right-aligned attribution, exactly as on paper. An empty line is
  `quote_line` followed by `show("")`.
- `quote_done` draws the bottom row, waits for a single keypress, and clears
  the screen for whatever follows. The status line, if summoned, redraws at
  the next prompt.

```
on start
    quote(3, 37)
    quote_line
    show("In order to make an apple pie from")
    quote_line
    show("scratch, you must first create the")
    quote_line
    show("universe.        -- Carl Sagan")
    quote_done
```

The text goes through `show(...)` directly because a string cannot travel
through a block parameter (chapter 1); the box manages the geometry, the
author supplies the words. Keep `width` under the narrowest screen you target
minus four (36 is safe on a 40-column Commodore 64); on a screen too narrow to
center, the box clamps to the left edge rather than wrapping.

An opening quote usually comes BEFORE the banner. Pair the granule with
`banner false` in the game block and a `print_banner` call after
`quote_done` (chapter 2; chapter 2), and the game opens in the
classic order: quote, keypress, banner, story. The box prints no words of its
own, so it works identically in every language, and it draws with the same
colours the game set with `zcolor` (chapter 15).

### verbose_exits

```
summon.verbose_exits
```

Replaces the blunt "there's no exit in that direction" with a list of the room's
actual exits ("You can only go north or east from here."), read from the
compiler's own direction data, so it always matches the map.

### nautical

```
summon.nautical
```

The nautical directions, FORE, AFT, PORT, and STARBOARD (with F and SB as
the ship's shorthand), plus ALOFT and BELOW riding the existing up and
down, because a vessel is a volume, not a deck plan (a submarine, a
crow's nest): for a game set aboard a ship or a deep space craft, where
the compass fails (cardinal directions are measured around the pole of a
planet, and in deep space there is no pole; the Hibernated problem). The
four horizontal properties are part of the compiler's standard set, so
exits, handlers, and `way` tests read like any other (`fore engine_room`,
`on go fore`, `if way is aft`); the granule adds the player-facing words.
Nautical and compass directions coexist in one game.

WHERE THE WORDS APPLY: `dirs_nautical`, the granule's flag, true by
default, so a pure ship game never touches it. Set it false as the player
steps ashore (`change dirs_nautical to false`, back to true at the
gangplank) and the four nautical-only words refuse honestly, "Nautical
directions mean nothing here." (msg_no_nautical, overridable), instead of
a misleading "no exit". ALOFT and BELOW stay live either way: they are
synonyms of up and down, which exist everywhere, and gating them would
gate every cellar staircase ashore.

If your game BEGINS ashore, set the flag false at the very start, not just
when stepping off the boat: the default is true (aboard), so the opening
room would otherwise treat nautical directions as live and answer "no
exit" there. An `on start` rule does it: `on start` / `change dirs_nautical
to false`. The compiler emits a note when the nautical granule is summoned
and the start room has no nautical exit, since the opening room is the one
place a step-off handler can never reach.

### pathfinding

```
summon.pathfinding
```

The player-facing half of the way family (chapter 8): GO TO a visited room
by name, FIND a thing you know of, LOOK <direction> to ask what lies that
way. The engine itself, `way_between` and `way_toward`, is core library and
needs no summon; the granule adds the verbs and the knowledge. Knowledge is
the visited set: GO TO resolves only rooms the player has stood in, the
walk routes only through rooms they have seen, and LOOK names only visited
destinations. An unvisited place answers "You don't know that place.",
exactly as unknown as a place that does not exist.

Summoning the granule turns every room's `name` words into that room's
vocabulary, so GO TO CHURCHYARD works with no declarations; `words` on a
room overrides, exactly as on a thing.

THE WALK. A GO TO or FIND performs each step as an ordinary go action,
doors, refusals, `on enter`, and alter lines all behaving, and every
intermediate step is a full world beat: daemons and timers run and the
clock ticks, exactly as if the step had been typed. Passage through an
intermediate room prints one breadcrumb, "(through the Arcade)", in place
of the full description; arrival describes normally. The whole walk is one
command, so a single UNDO takes it all back, and the walk stops the moment
the world pushes back: a refused step, a step that lands somewhere
unexpected, or the path dissolving mid-walk. Whatever intervened has
already spoken, and the walk adds nothing over it. A route through a
closed door is no route; open the door and it is.

FIND speaks for what is present ("The silver locket is right here."),
walks to what is elsewhere and known ("(setting off for the Dusty
Attic)"), and refuses what is not ("You don't know of any such thing.",
or, for a thing whose room the player has never seen, "You don't know the
way there."). LOOK FOR is the same verb.

LOOK <direction> leads with the direction word as typed, so it composes
with nautical: "North lies the Churchyard.", "Aft lies your cabin.", "The
way east is open, but you haven't been that way yet.", "Nothing lies that
way.", and for a shut door, "North lies the oak door, closed."

The granule speaks every shipped language. Its grammar lives inside it
under `when language` groups (English GO TO and FIND; German GEH
ZU/ZUR/ZUM, FINDE, SUCHE, SCHAU [NACH]; Spanish VE A/AL/HACIA, BUSCA,
ENCUENTRA, MIRA [HACIA EL/AL]), and its messages live in the language
packs beside the rest of the library's voice, so an ejected language
file carries them to a translator with everything else. Reskin any line
by redefining its msg_ block. A game that never summons the granule pays
nothing anywhere, and its own calls into the way family stay free of the
granule's knowledge gate.

### conversations

```
summon.conversations
```

The menu presentation of the `topic` model: TALK TO <person> opens a numbered
list of what there is to talk about, pinned in the upper window while the
conversation scrolls beneath it.

WHERE TOPICS LIVE. Topics are not declared in the granule or in any separate
registry: they live INLINE in the person's body, like properties and
handlers, and the same declarations serve both conversation systems (this
menu, and infocom_talking's ask/tell). The full header grammar is chapter 17; the shape:

```
thing wirtin of character in inn
    name "innkeeper"
    named

    topic lighthouse "the lighthouse" words lighthouse, tower
        you "What about that lighthouse out there?"
        reply "Dark since that night. Nobody has gone back up."
        reveal key_talk

    topic key_talk "the key" hidden
        you "Is there a key somewhere?"
        reply "In the chest, by the hearth."

    topic debt "the old debt" when player holds ledger once
        reply "So you found it. Then you know what I owe."
```

- The MENU LABEL is the quoted string after the subject id ("the
  lighthouse"): that is the line the player sees, numbered, in the list.
- `words` are only for ask/tell (`ask innkeeper about tower`); the menu does
  not need them, players pick by number.
- `idle` topics are only for ask/tell (the per-person default answer); the
  menu has no unmatched-subject case, so it never lists or runs one. An idle
  topic declared in a menu game is simply inert.
- VISIBILITY is live, three ways (chapter 17 explains when to use which):
  a `when` guard follows the story state by itself; `hidden` topics enter
  view when another topic's body (or any handler) runs `reveal <subject>`;
  `once` retires a topic after one telling. In the menu, picking a topic
  removes it from the list regardless, so `once` is redundant here; it earns
  its keep on the ask/tell path (above), where plain topics repeat. Either
  way a `reveal` in code brings a retired topic back for another turn.
- The BODY is an ordinary statement block: `you`/`reply` print attributed,
  auto-quoted dialogue (framing overridable via line_you/line_reply/
  line_end), `say` is narration, and any statement works: set flags, move
  objects, change the score. The person is `self`.

THE MENU FLOW. TALK TO paints the list (the statusline, if summoned, stays
pinned above it); a digit runs that topic's exchange in the lower window and
the list repaints, reflecting anything the topic revealed, hid, or retired;
0, or running out of topics, closes it ("You let the conversation rest
there."). A person with nothing to raise answers msg_no_topics ("You can't
think of anything worth raising right now."). Every framing line is in the
language layer, so packs translate it.

ASK AND TELL. The standard ask lands in the menu (asking IS talking:
`ask vlad`, and even `ask vlad about the vines`, opens Vlad's menu, the
subject words riding along), and the standard tell answers with the
use-TALK hint (msg_use_talk, a language-layer line): the granule overrides
the `ask_to`/`tell_to` seams and holds no words and no strings itself.
The infocom_talking granule is the other presentation of the same topic
declarations, and the two are mutually exclusive BY THE COMPILER: summoning
both is an error. The topics are identical either way, so switching
presentations is a one-line change. A person can still override `on talk`
for a one-off custom exchange that bypasses the menu.

### ambience

```
summon.ambience
```

Rooms and things murmur over time. An `ambience` block is a list of lines; on
a room it plays while the player is there, on a thing while the thing is in
scope, which is what makes a companion or a muttering radio work. At most one
ambient line plays per turn, so a busy room never floods the transcript.

```
room monorail
    ambience
        "Vlad steps over the skeletal remains without adjusting his gait."
        "Vlad runs a rapid scan of the chamber, then dismisses it as redundant."
        "Somewhere far down the tunnel, metal settles."

    ambience about 12 turns when door_open
        "A draught moves through the open blast door."
```

The header, modifiers in any order (`when` reads to the end of the line, so
it comes last):

- bare `ambience`: ABOUT the `ambience_rate` dial (default 8), random order,
  never the same line twice running.
- `about N turns`: living odds. Each silent turn shortens them, a fired line
  resets them, so the room breathes instead of ticking. The firing time
  spreads evenly around the rate, so "about 7" truly averages one line
  every 7 turns.
- `every N turns`: the strict metronome.
- `in order`: the lines play as written, then cycle; `in order once` falls
  silent after the last, for scene-setting that quietly exhausts itself.
- bare `once`: the shuffled deal. Each line fires once, in random order,
  then the block falls quiet; when the block drops out of play (the player
  leaves the room, the thing leaves scope) the deck re-deals, so a
  revisited room starts fresh. The way an NPC companion comments on a
  location: every remark lands exactly once per visit, and none repeats
  while you stand there. A `once` deck holds at most 15 lines (the
  compiler checks, and says so).
- `when <cond>`: gates the whole block live, like a topic guard.

A line is a string, or `do <block>` for a computed one, and each line may
carry its own trailing `when`. The dial: `ambience_rate` is the default
cadence, and `change ambience_rate to 0` mutes every block (bring it back
after the tense scene); blocks with their own cadence keep it otherwise.

KNOW WHEN NOT TO USE IT. One line that fires until a condition flips is a
plain daemon, two lines of code and no granule (`every 3 turns do drip`);
the ruby-gem style room pulse in the daemons example is exactly that.
Ambience earns its summon for shuffled, breathing texture: NPC behavior and
layered room mood.

### takeall

```
summon.takeall
```

TAKE ALL, DROP ALL, and TAKE ALL FROM <container>. The core deliberately
omits ALL (it flattens scenes into transactional loot runs), so it is a
granule: a game that wants the convenience summons it, and a game that does
not pays nothing (the parser's hand-off folds away without the summon).

The sweep tries what a plain take would not refuse on sight: nothing fixed,
scenery, animate, hidden, or already carried, including what sits on
supporters and in open containers; DROP ALL keeps what is worn; a shut
source refuses honestly ("The chest is shut."). Each attempt still runs the
object's own handlers, so a custom `on take` refusal simply prints after the
item's name:

```
>take all
brass lamp: You take the brass lamp with you.
wooden box: You take the wooden box with you.
idol: The idol is welded to its pedestal.
```

THE SWEEP IS HOOKABLE: the granule declares two verbless actions,
`take_all` and `drop_all` (chapter 12), and dispatches them through the
ordinary pipeline before sweeping. A story intercepts the sweep the same
way it intercepts anything:

```
on drop_all when here is shrine
    say "Nothing may be set down here."
```

The chain runs as always: for TAKE ALL FROM the source is the bound
`noun`, so the container's own `on take_all` answers first; then the
room, then the free rules; the granule's default handlers at the end of
the chain perform the sweep. `continue` defers to them, so a handler can
comment and still let the sweep run. An intercepted sweep costs its turn
and ends a chained line: the interception was the outcome. Per-item
control needs no hook at all, because each swept item runs its own full
`on take` or `on drop`.

Every swept item is a FULL TURN: daemons fire and the clock moves per item,
exactly as if the takes had been typed one by one. This is a deliberate
departure from Inform, where ALL costs one turn; in Arcturus doing three
things costs three turns, the same rule a chained line follows (chapter 14). UNDO takes back the whole sweep, because the sweep is one typed command
and undo peels typed commands. An empty sweep, and ALL with any other verb
("eat all"), refuse, so a chained line stops there honestly.

The granule speaks every shipped language. Its words live inside it under
`when language` groups (English ALL and EVERYTHING with the filler FROM;
German ALLES and ALLE, "nimm alles aus der Kiste" with no extra filler,
since AUS is already the off-particle and phrase matching compares
dictionary entries, not flags; Spanish TODO, "coge todo de la caja"), and
its messages live in the language packs beside the rest of the library's
voice. Reskin any line by redefining its msg_ block; a new language
declares its own group in a fork (chapter 23).

### plurals

```
summon.plurals
```

The group model, two parts that arrive together (noun lists, "take lamp
and box", are a CORE chaining feature, not part of this granule; chapter 14):

- GROUP WORDS. Each member of a group declares the words that name it as a
  group: `plural coins` on the gold coin and the silver coin. "take coins"
  then runs the take on every coin in scope, one line and one full turn per
  coin, exactly like TAKE ALL's sweep; with only one coin left, the same word
  binds it singularly with no ceremony. The ordinary singular vocabulary
  still disambiguates: "take coin" (a `words` entry on both) asks which.
- THEM. The pronoun for the last group: "take coins" then "drop them". THEM
  re-runs the group word, so it honestly covers whatever of the group is
  still in scope.

English-worded like every granule; a translation forks it. A Spanish fork
should keep the THEM declaration out: the clitic plurals (-los, -las) in the
core Spanish pack already fill that role, and bare "los"/"las" are the
articles. The granule's `pronoun them "them"` declaration doubles as its
compile-time marker: every hook in the core parser folds away without it.

### debug

```
summon.debug
```

Developer verbs, opt-in by the summon alone (there is no separate release build
to strip them from; not summoning them leaves them out). Arcturus-named with the
familiar Inform synonyms:

- `tree` / `objects` - the whole object tree.
- `scope` - what is reachable from here.
- `fetch` / `purloin` - pull any object into your hands.
- `warp` / `gonear` - teleport to an object's room.
- `inspect` / `showobj` - an object's location and the attributes it has set.
- `unmute` - hear the background performers: offstage restless prose, muted
  for the player by design (chapter 16), is spoken anyway, each
  pulse tagged with the performer's name in brackets so you can tell who
  speaks from where; a performer whose turn printed nothing stays silent.
  `unmute` again restores the rule.

`fetch`, `warp`, and `inspect` reach objects that are out of scope, which the
parser would normally refuse; the granule teaches the parser to reach them
through the `reach_unscoped` seam (chapter 23).

Looking for Inform's RECORDING / REPLAY to step through a walkthrough? That is
not a game verb in Arcturus; it lives in the interpreter, where it costs the
story nothing. Actaea records a session, replays it, and checks whether a
changed game still plays the same, with `actaea --record`, `--replay`, and
`--check` (docs/06 this chapter, "Record, replay, and check").

### use

```
summon.use
```

The accessibility hub, from Hibernated 2: USE X guesses the obvious
action from what X is (edible eats, wearable wears, binary switches
on, a closed openable opens), and coaches toward a real verb otherwise;
USE X WITH Y unlocks a lockable Y with X and coaches otherwise. ACTIVATE,
OPERATE, ENGAGE, and START come along as synonyms. An object's own `on use`
handler beats the guessing, so puzzles keep their answers; a bare USE
asks the standard way.

### matrix

```
summon.matrix
```

The mutable sibling of a catalog: a capacity-bounded, numeric sequence whose
LENGTH changes at runtime. A catalog is fixed data; a matrix you `append` to,
`remove` from, and `insert` into. Reach for one only when a collection truly
grows or shrinks as the game plays; for everything else a catalog is smaller
and faster (chapter 2 has the full "do you need this?" guidance and
the syntax). The declaration and reads are compiler sugar, but the mutators
themselves live here, in editable Arcturus, so you can override any of them by
declaring a block of the same name:

- `matrix_append(m, v)`, `matrix_insert(m, i, v)` - grow, with a full check.
- `matrix_remove_at(m, i, swap)`, `matrix_remove_val(m, v, swap)` - shrink,
  order-preserving or O(1) swap-with-last.
- `matrix_load(m, src)` - copy a catalog's values in as the new contents.

A matrix shares the catalog region and base, so its cells are peek_word /
poke_word against `catalogs_base` at word `m + 1 + i`, the count at `m` and the
capacity at `m + 1`. There is no heap and no allocator; a game that does not
summon matrix contributes zero bytes.

### Not a granule: the language pack

`summon.language "<name>"` is a compiler feature rather than a runtime granule: it
selects a localization (milestone B7). A language pack is a translation of
english.prelude, saved as a granule whose blocks override the English ones (a
granule overriding the prelude, this chapter). Start from `arcc --eject-language`,
translate, and ship the result. The pack may replace the parser's grammar logic
too, not only its wording, since an inflected language parses differently (chapter 14). An ejected language file carries the same fork stamp as any other
library file, so a pack that predates a change to the English layer is told so
rather than quietly missing a message.

## Chapter 23: Hacking Cosmos

Cosmos is not a compiled black box. It is ordinary Arcturus source, shipped as
a default and compiled together with the author's program. It defines the
standard kinds, the standard verbs and their grammar, the default action
behavior, the messages, the banner, and the turn loop.

Three layers, from fixed to free:

1. Core and runtime: the compiler and the primitives it relies on (the object
   tree, attribute and property access, the parse and print intrinsics).
   Fixed.
2. Cosmos: everything in this document, written in Arcturus. Shipped as a
   default the author can read, override piecemeal, or fork wholesale.
3. The game: the author's program, only what differs from Cosmos.

Overriding uses the ordinary resolution order from 01 (chapters 7 and 15):
the author's handlers are more specific than Cosmos's, so they win, falling
back with `continue`. A default is just the least specific handler. The
standard take, for example, is defined in Cosmos in plain Arcturus:

```
verb "take", "get", "pick"
    take noun

on take noun
    if noun is fixed
        say "${The noun} is fixed in place."
        stop
    if player holds noun
        say "You already have ${the noun}."
        stop
    move noun to player
    say "Taken."
```

Cosmos ships as a set of library files, each with the `.prelude` extension. The
split follows one line: what is specific to the English language, versus what is
not.

- `english.prelude` is **the language layer**: everything English lives in this
  one file, in three documented parts (the parser hooks that read English, the
  standard verb words and grammar, and every message shown to the player). A
  translation is a fork of this file alone; `arcc --eject-language` writes it out
  (chapters 14 and 21).

  **Your game's voice.** The default messages carry one deliberate voice:
  quick, dry, a little amused. That is a feature, not an accident, and it is
  meant to be REPLACED as much as enjoyed: for a real game with its own
  register (a horror piece, a period drama), the intended first move is
  `arcc --eject-language`, which writes the whole voice as one file beside
  your story; fork it and every line is yours. Overriding a single `msg_`
  block is the other tool, for when the stock tone suits you and a few lines
  need adjusting. Both are ordinary Arcturus source; neither touches the
  parser.
- `actions.prelude` holds the **standard action handlers**, the behaviour behind
  each verb. It is language-agnostic: no words, no wording, only logic that works
  on the normalized slots the parser fills (`noun`, `second`, `way`, the action),
  so it is identical in every language and a translator never touches it.
- `parser.prelude` is the **agnostic parser skeleton** that drives the language
  hooks; `scope.prelude`, `dispatch.prelude`, `loop.prelude`, and `core.prelude`
  are the scope rules, the action pipeline, the turn loop, and the base
  environment, all agnostic.

The build includes them unless the author supplies their own copies, which is how
a wholesale fork works. Dead-code elimination ensures unused Cosmos verbs and
properties never reach the story file.

### Overriding Cosmos in practice

Four patterns, in increasing scope: change one message by handling the verb
on the object; change a verb everywhere with a top-level `on <verb>` rule;
add a verb with a `verb` declaration plus its `on <verb>` default (as the
Brass Lantern's pull and the Cloak's hang); or fork a Cosmos file by copying
it into the project and editing it, so the build uses the local copy. Most
games use only the first three; the fourth exists so Cosmos is never a
ceiling.

The GRAMMAR is overridable the same way, and no fork is ever needed for it:
a game's `verb` declaration extends the standard set, feeds an existing
action from a new word (`verb "peruse"` with `examine noun`), or redeclares a
standard verb with a richer line set, positional lines included, and the
later declaration wins for its words. The authoring patterns are chapter 12; the worked showcase is `examples/features/grammar.storyarc`.

### How the examples use Cosmos

The Brass Lantern:

- The cellar uses automatic light: with no `lit` of its own it is dark until
  the player brings the switched-on lantern, whose `lit` lights the room. The
  example's `on enter` additionally bounces the player back, a stricter
  custom behavior than standard darkness; both are valid.
- `switch_on` and `switch_off` are Cosmos verbs; the lantern's handlers
  replace the default messages, consuming the action.
- `pull` is an added verb; the lever's handler consumes it, so the default
  "Nothing obvious happens." never runs.
- `${turns}` reads the Cosmos turn counter, and the foyer's grain shows
  prose texture answering examine without an object (grains, chapter 18).

Cloak of Darkness (a 1:1 port of Firth's reference cloak.inf, which is also
the PunyInform size benchmark):

- The foyer blocks north with `on go north`, a room-level override at pipeline
  step 3. The 1:1 port carries no grains: the original answers for nothing
  beyond its three objects.
- The cloak is `wearable` and starts `worn`; Cosmos's wear and take-off verbs
  manage `worn`, and putting it on the hook clears `worn` as part of put-on.
  Its light logic is event-driven, as in the original: `on after take` darkens
  the bar, `on after drop, put` in the cloakroom relights it, and the first
  hang on the hook runs an `award 1` (paid once by award's own semantics,
  where the original needed a flag).
- The hook is a `supporter`; its child the cloak is on it and in scope, so
  `hook holds cloak` is the test the hook's examine uses.
- The bar's dark rules are the original's two tiers: `on go` charges two
  disturbances for a wrong-way grope (`if way is not north`, the direction
  name as a value), `on other` charges one for any other in-world action,
  `on look, inventory` pass through (a matched handler that continues climbs
  the chain, it never falls into the object's own catch-all), and the meta
  verbs never reach the room at all (out-of-world dispatch, chapter 13).
- The `disturbed` counter, the two `award 1` sites self-summing max_score 2,
  and the two `finish` endings need nothing from Cosmos beyond the loop.

### Forking a granule

To change a granule, take a copy and edit it.

- One granule next to a story:

  ```
  arcc --eject-granule statusline      // writes statusline.granule here
  // edit statusline.granule, then in the story:
  summon statusline.granule            // your copy wins over the bundled one
  ```

- The whole library, to fork several files or a prelude:

  ```
  arcc --extract-library /abs/cosmos   // every prelude and granule
  // edit files in /abs/cosmos, then:
  arcc game.storyarc -L /abs/cosmos    // -L must be absolute
  ```

  With `-L /abs/cosmos`, a `summon statusline.granule` in the story finds your
  edited `/abs/cosmos/statusline.granule` before the bundled one. A prelude can
  only be forked this way: there is no single-prelude eject (except
  `--eject-language` for translation, chapter 22) - to hack a prelude you extract
  the whole library and point `-L` at it.

### Keeping a fork current

A fork wins over the bundled copy for as long as it sits beside your story.
That is the point of it, and it has one consequence worth knowing before you
take your first one: the file you copied keeps improving in later releases, and
your copy does not. A fork left alone long enough is a version of Cosmos from
whenever you took it, and nothing about compiling makes that visible.

So every file arcc writes out starts with a stamp:

```
// cosmos 1.2.14 base a06f30acb367
```

Leave it in place. The version is for you to read; the fingerprint identifies
the source your fork came from, and the compiler compares it against its own
copy of that file. If the file has not changed since, nothing is said, however
old the stamp reads and however heavily you have edited your copy. If it has
changed, one note tells you, on every compile until you deal with it:

```
arcc: note: extendedverbs.granule was forked from Cosmos 0.36.5 and the
bundled extendedverbs.granule has changed since (now 1.2.14). Diff it against
a fresh `arcc --eject-granule extendedverbs` to see what your fork is missing.
```

That is the whole recipe for catching up: eject a fresh copy somewhere else,
diff it against yours, and move over what you want. Then re-stamp by taking the
new copy and re-applying your edits to it, so the next release can tell you the
same thing again.

```
arcc --library-status            // every fork here: current, AGED, unstamped
arcc --library-status /abs/cosmos
```

Two notes on the edges. A fork you took before stamps existed carries none, so
it gets a milder note saying its age cannot be told; re-eject to establish one.
And a granule of your own, with no bundled file of the same name, is not a fork
of anything and is never mentioned. Deleting the stamp line opts out entirely,
which is fair once a fork has diverged past caring, but you lose the warning
with it.

### Writing your own granule

A granule is plain Arcturus in a `.granule` file. It may declare verbs, kinds,
objects, and blocks, and it may **override prelude blocks** by defining a block
of the same name. Summon it by filename (`summon mygranule.granule`) or path.

A few patterns the shipped granules use:

- **Override a message or behavior.** Define a block named like a prelude block
  (a `msg_*`, or `prompt`, `describe_room`, the parser blocks) and yours replaces
  it. This is how statusline overrides `prompt` and verbose_exits overrides
  `msg_cant_go`.
- **Add a verb with an overridable default.** Declare the `verb`, write a free
  `on <verb>` handler that speaks a default, and let an object override it with
  its own `on <verb>` (most-specific-wins).
- **Integrate optionally with another feature through a seam.** When two granules
  may or may not both be present, neither can override the other's blocks. Put a
  default block in the *prelude* and have each granule override or call it. The
  statusline/conversations coexistence works this way (`status_bar`, a prelude
  no-op the statusline overrides and the menu calls), and so does the debug
  granule reaching out of scope (`reach_unscoped`, a prelude hook the parser
  calls and debug overrides). A seam is the only way to compose two optional
  granules, and it is what lets a language pack and the debug granule both extend
  the parser at once.
- **Depend on another granule.** A granule may itself `summon` another; the
  loader resolves summons transitively, each granule loaded once.

Keep a granule self-contained and summon-gated: anything it ships is left out of
a story that does not summon it.

## Chapter 24: The compiler, diagnostics, and the abbreviation set

Representative compile-time errors:

- Mutating an undeclared property.
- Property type clash across sites.
- A non-boolean condition (`if n`).
- Unknown verb or action in a handler header.
- Inconsistent indentation or mixed tabs and spaces.
- A `switch` mixing number and string cases.
- A name clash between a boolean property and an object used with `is`.
- A `summon` of a missing file or unknown built-in feature.

### The tuned abbreviation set

Most of a story file is text, so the compiler compresses it against the
Z-machine's abbreviation table (docs/00 chapter 23). This asks nothing of you:
every build already applies a standard abbreviation set, computed once from the
Cosmos library text and baked into `arcc`.

A particular story can do better than the standard set by curating one over its
own text. Run:

```
arcc --make-abbreviations mystory.storyarc
```

which pools the strings of the story and every granule it summons, computes an
optimized set up to the Z-machine's ceiling of 96 entries, and writes an
`abbreviations.granule` beside the story. Summon it by name to use it in place of
the default:

```
summon abbreviations.granule
```

It is neither a dotted feature nor runtime code. The file is compile-time data the
text encoder reads, so it holds only string literals (and therefore lexes and
highlights like any Arcturus source). A story that never summons it simply keeps
the standard set, and summoning it costs nothing at run time; it only changes how
the text is packed. Regenerate it after large text edits. The optimizer is the
same one that computes the built-in default (tools/arcabbr.py), so a
`--make-abbreviations` run is slower than a plain build, but it runs only when you
ask, which is why the two-pass split exists: the fast default on every build, the
slow tuned set on request.

## Chapter 25: Worked example: The Brass Lantern

A complete, winnable game using only constructs defined above. Cosmos
supplies the parser, the turn loop, the player, and the everyday verbs, so
this file is the world and the few behaviors that differ from the defaults.

```
game
    title  "The Brass Lantern"
    author "Stefan"
    UUID   7f3a9c20-1e44-4b8a-9d51-6c2f0b9a7e10
    start  hallway

on start
    say "A cold draught curls up from somewhere below."
    say "You came for the ruby. You should find some light first."


room hallway
    name "Hallway"
    desc "A bare stone hallway. Worn steps lead down into the dark, north."
    north cellar

thing lantern in hallway
    name  "brass lantern"
    words brass, lantern, lamp
    desc  "A battered brass lantern, and it still works."
    binary
    lit   false

    on switch_on
        now self is active
        now self is lit
        say "The lantern catches with a soft hiss."

    on switch_off
        now self is not active
        now self is not lit
        say "The flame gutters out, and the dark leans in."


room cellar
    name "Cellar"
    desc "A damp cellar of black stone. A squat pedestal stands at its
          centre, a rusted lever set into the base."
    south hallway

    on enter
        if not (player holds lantern and lantern is lit)
            say "You grope down the steps, but sense wins over greed,
                 and you back up into the hallway."
            move player to hallway
            stop

    on each_turn when ruby is hidden
        say "Somewhere water ticks against stone, patient and unhurried."


thing pedestal in cellar
    name "stone pedestal"
    desc "Waist high and cold, a rusted lever set into its base."
    fixed

thing lever in cellar
    name "rusted lever"
    desc "A stubby iron lever, begging to be pulled."
    fixed
    pulled false

    on pull
        if lever is pulled
            say "It will not give a second time."
            stop
        now lever is pulled
        now ruby is not hidden
        change ruby.desc to "The ruby sits exposed, drinking the lantern."
        say "The lever grinds down. A panel slides back, and a red gleam
             answers the light."


thing ruby in cellar
    name  "blood ruby"
    words red, blood, ruby, gem, jewel
    desc  "A ruby the size of a plum, drinking the light, giving back fire."
    hidden

    on take
        move ruby to player
        say "It is warm in your hand, almost a pulse."
        finish "*** You carry the blood ruby home in ${turns} turns ***"


verb "pull", "yank"
    pull noun
```

## Chapter 26: Worked example: Cloak of Darkness

The benchmark game implemented in nearly every IF system, the natural second
conformance target, and a 1:1 port of Roger Firth's reference implementation
(the PunyInform cloak.inf, which is also the size benchmark, so the content
matches byte for byte in spirit). It exercises darkness, a wearable item that
changes a room's light, a supporter (the hook), a state counter with the
original's two-tier disturbance rules, two `award` sites self-summing the
classic MAX_SCORE of 2, and a win-or-lose ending.

```
game
    title  "Cloak of Darkness"
    headline "A basic IF demonstration."
    author "Roger Firth"
    release 3
    serial "221116"
    UUID   2a1f8e63-9b07-4c2d-8f3a-5e1d6042b7c9
    start  foyer

// The classic Cloak of Darkness, a 1:1 port of Roger Firth's reference
// implementation (the PunyInform cloak.inf, release 3): three rooms, three
// objects, two points. The original shows the score on its status line, so
// this port summons one; the two `award 1` sites self-sum the max of 2.
// One knowing divergence, truer to Firth's spec than to his code: an action
// aimed at something unseen in the dark ("x message") disturbs the sawdust
// here, where the Inform parser rejected it before any rule could run.
summon.statusline

counter disturbed

on start
    say "Hurrying through the rainswept November night, you're glad to see
         the bright lights of the Opera House. It's surprising that there
         aren't more people about but, hey, what do you expect in a cheap
         demo game...?"

room foyer
    name "Foyer of the Opera House"
    desc "You are standing in a spacious hall, splendidly decorated in red
          and gold, with glittering chandeliers overhead. The entrance from
          the street is to the north, and there are doorways south and west."
    south bar
    west  cloakroom

    on go north
        say "You've only just arrived, and besides, the weather outside
             seems to be getting worse."
        stop

room cloakroom
    name "Cloakroom"
    desc "The walls of this small room were clearly once lined with hooks,
          though now only one remains. The exit is a door to the east."
    east foyer

thing hook of supporter in cloakroom
    name  "small brass hook"
    words small, brass, hook, peg
    scenery

    on examine
        if hook holds cloak
            say "It's just a small brass hook, with a cloak hanging on it."
        else
            say "It's just a small brass hook, screwed to the wall."
        stop

thing cloak in player
    name  "velvet cloak"
    words handsome, dark, black, velvet, satin, cloak
    desc  "A handsome cloak, of velvet trimmed with satin, and slightly
           spattered with raindrops. Its blackness is so deep that it
           almost seems to suck light from the room."
    wearable
    worn

    // The cloak is the light switch: while it is anywhere on the player the
    // bar stays dark, and it may only be put down in the cloakroom. The
    // first hang on the hook is worth a point (award pays once by itself).
    on drop, put
        if here is not cloakroom
            say "This isn't the best place to leave a smart cloak lying
                 around."
            stop
        continue

    on after take
        now bar is not lit

    on after drop, put
        if here is cloakroom
            now bar is lit
            if second is hook
                award 1

room bar
    name "Foyer bar"
    desc "The bar, much rougher than you'd have guessed after the opulence
          of the foyer to the north, is completely empty. There seems to be
          some sort of message scrawled in the sawdust on the floor."
    north foyer
    lit  false

    // In the dark, going anywhere but north gropes badly (two disturbances,
    // instant ruin) and any other action risks one; look and inventory pass
    // through untouched, and the meta verbs never reach the room at all
    // (out-of-world, as in the original).
    on go
        if here is not lit
            if way is not north
                change disturbed to disturbed + 2
                say "Blundering around in the dark isn't a good idea!"
                stop
        continue

    on look, inventory
        continue

    on other
        if here is not lit
            disturbed++
            say "In the dark? You could easily disturb something!"
            stop
        continue

thing message in bar
    name  "scrawled message"
    words message, sawdust, floor
    scenery

    on examine
        if disturbed < 2
            award 1
            say "The message, neatly marked in the sawdust, reads..."
            finish "*** You have won ***"
        else
            say "The message has been carelessly trampled, making it
                 difficult to read. You can just distinguish the words..."
            death "*** You have lost ***"
        stop

verb "read"
    examine noun

verb "hang"
    put noun on noun
```

Both examples lean on Cosmos for the parser, the turn loop, scope, light, and
the everyday verbs; the per-game logic above is all defined in this document.
Chapter 23 reconciles each example with the Cosmos model in detail.

## Appendix A: Reserved words

`game`, `room`, `thing`, `kind`, `verb`, `of`, `in`, `on`, `after`, `block`,
`return`, `global`, `flag`, `counter`, `constant`, `let`, `change`, `to`,
`now`, `is`, `not`,
`add`, `remove`, `from`, `move`, `say`, `stop`, `continue`, `finish`, `death`, `alter`, `if`,
`catalog` and `matrix` (as declaration heads), `vary` (as a statement head,
before a policy word: sequence, loop, mutate, dice),
`else`, `while`, `for`, `each`, `switch`, `case`, `and`, `or`, `holds`,
`when`, `self`, `player`, `here`, `noun`, `second`, `nothing`, `true`,
`false`, `list`, `summon`, `grains`, `do`, `title`, `headline`, `author`,
`release`, `serial`, `UUID`, `start`, `mod`, `every`, `topic`, `you`, `reply`,
`reveal`, `hide`.

Grammar slot words (`held`, `multi`, `text`) and the standard direction and
verb names are reserved by Cosmos rather than the core language; see appendix C.

## Appendix B: Grammar summary

Informal sketch; INDENT and DEDENT are indentation tokens.

```
program        := { toplevel }
toplevel       := game_block | summon | kind_decl | object_decl | verb_decl
                | global_decl | constant_decl | block_decl | rule

game_block     := "game" INDENT { meta_line } DEDENT
summon         := "summon" ( string | id )
                | "summon" "." id [ string ]
object_decl    := ("room" | "thing") id [ "of" id ] [ "in" id ]
                  INDENT { member } DEDENT
kind_decl      := "kind" id [ "of" id ] INDENT { member } DEDENT
member         := property_decl | handler | grains_block
property_decl  := id [ value ] | id "list" number | id "block"
                  INDENT { statement } DEDENT
handler        := "on" [ "after" ] event { "," event } [ pattern ]
                  [ "when" expr ] INDENT { statement } DEDENT
event          := id            (* a verb or action name, or "other" *)
pattern        := { operand | word }
operand        := id { "or" id }
grains_block   := "grains" INDENT { grain } DEDENT
grain          := verbs words ( "say" string | "do" id
                              | INDENT { statement } DEDENT )

verb_decl      := "verb" string { "," string } INDENT { grammar } DEDENT
grammar        := id { slot | word }
slot           := "noun" | "held" | "multi" | "text"

block_decl     := "block" id "(" [ params ] ")" INDENT { statement } DEDENT
global_decl    := "global" id "=" expr
flag_decl      := "flag" id [ "=" ( "true" | "false" ) ]
counter_decl   := "counter" id [ "=" number ]
constant_decl  := "constant" id "=" expr
rule           := handler

statement      := let | change | now | move | add | remove | say
                | stop | continue | finish | death | alter | if | while | for | switch
                | return | call | schedule | stop_timer
schedule       := ( "after" | "every" ) expr "turns" "do" id
stop_timer     := "stop" ( "after" | "every" ) expr "turns" "do" id
                | "stop" "all" "timers"
switch         := "switch" expr INDENT { case } [ else_case ] DEDENT
case           := "case" value { "," value } INDENT { statement } DEDENT
for            := "for" "each" id ( "in" | "of" ) expr
                  INDENT { statement } DEDENT

place          := id | expr "." id
expr           := (* numbers, strings, booleans, object refs, nothing,
                     dot access, calls, is / is not, holds, in,
                     and / or / not, arithmetic and comparison *)
```

## Appendix C: Cosmos-reserved names

Direction names: `north`, `south`, `east`, `west`, `northeast`, `northwest`,
`southeast`, `southwest`, `up`, `down`, `in`, `out`, `fore`, `aft`, `port`,
`starboard` (the nautical four; their words are the nautical granule). The
`go` verb also
reserves `other` as the blocked-direction fallback operand (`on go other`,
chapter 8); it is not itself a direction.

Standard kinds: `thing`, `room`, `container`, `supporter`, `door`, `character`.

Standard boolean properties: `fixed`, `scenery`, `hidden`, `concealed`,
`wearable`, `worn`, `lit`, `edible`, `named`, `an`, `clear`, `seen`, `binary`, `active`,
`openable`, `open`, `lockable`, `locked`, `visited`, `moved`, `animate`. The full
table with each one's usage is in chapter 5.

Standard value properties: `name`, `words`, `desc`, `capacity`, `unseal_with`,
`score`, `max_score`, `turns`.

Standard action names: `look`, `examine`, `search`, `take`, `drop`, `put`,
`wear`, `take_off`, `inventory`, `go`, `enter`, `exit`, `open`, `close`,
`lock`, `unlock`, `switch_on`, `switch_off`, `push`, `pull`, `turn`, `give`,
`show`, `talk`, `wait`, `again`.

Summonable features: `extendedverbs`, `infocom_talking`, `statusline`,
`verbose_exits`, `conversations`, `takeall`, `plurals`, `ambience`, `debug`,
and `language`. Text compression is not a summonable
feature: the standard abbreviation set is always applied, and a story tunes it
with its own `abbreviations.granule` (`arcc --make-abbreviations`, then summoned by
name), which the text encoder reads as data rather than loading as runtime blocks
(chapter 24).

## Appendix D: The author's toolkit

The callable names a game reaches for beyond its own declarations: the
intrinsic functions the compiler provides and the Cosmos blocks an author
may call (or override; every block here obeys the ordinary most-specific-
wins chain). An author never needs to know which of the two layers a name
lives in, so this list does not sort by that.

The world model:

- `parent_of(obj)`: where an object sits, the holder itself (`nothing` when
  it is nowhere). The idiomatic TEST is the predicate you already know,
  `if lamp is in chest`; `parent_of` is for READING the place, to print it,
  compare it, or walk upward to the room.
- `object_count`: how many objects the story has; with `parent_of` it makes
  the classic full sweep (`let i = 1` ... `while i <= object_count`).
- `in_scope(obj)`: whether the player can perceive the object this turn.
- `see_into(obj)`: whether a holder shows its contents (a supporter, or an
  open, clear, or lidless container).
- `set_here(room)`: retarget the narration to another room (a teleport;
  pair with `move player to room` and `describe_room`).
- `describe_room`: the full room description, the body of LOOK.

Naming and listing (the wording lives in the language layer, so every
language pack speaks its own):

- `print_name(obj)`: the bare short name, no article. The article family
  is interpolation: `${a obj}`, `${the obj}`, capitalized `${A obj}` and
  `${The obj}`.
- `name_contents(holder)`: the composable bare list, "a sabre, a dagger
  and an iron axe": the holder's listable contents with their articles,
  commas, and a final "and", each marked seen, one level deep. Returns
  how many it named, and zero prints nothing at all, so your sentence
  decides what emptiness deserves:

  ```
  show("Rusting on the rack you find ")
  if name_contents(rack) is 0
      show("nothing at all")
  say "."
  ```

- `listable_count(holder)`: how many the listing would name, without
  printing, for guarding a prefix.
- `list_contents(holder)`: the " (contains ...)" suffix used by the room
  and inventory listings.
- `reveal_contents(holder)`: "Inside you find ...", the line an open
  prints.
- `content_listable(holder, x)`: the per-item filter behind all of them,
  the knowledge model in one place: not hidden or concealed, and either
  the holder shows its contents or the player has already seen the item.
- `list_worn()` and `worn_count()`: the same composable contract for what
  the player wears: the bare punctuated list (returning the count), and
  the count alone.

The screen and the session:

- `clear_screen()`: erase the play area.
- `screen_width()` and `screen_height()`: the interpreter-reported size,
  for anything that spans the screen.
- `press_any_key`: hold for a keypress (the staged-opening idiom, with
  `banner false` and `print_banner`).
- `print_banner`: the release banner on demand.
- `status_bar`: the one seam the status line hangs on; override it and
  the statusline granule's bar steps aside.
- `confirm_quit` and `do_quit`, `do_restart`, `do_save`, `do_restore`:
  the primitives the meta verbs stand on, reusable in a custom ending
  ("RESTART, RESTORE or QUIT?").
- `action_id("word")`: an action's number, for comparisons in low-level
  seams (the debug granule's `reach_unscoped` is the worked example).

Beneath all of this sits the library's substrate: the parse-buffer
readers (`read_line`, `word_count`, `word_dict`, `word_len`, `word_pos`,
`retokenize`), raw memory (`peek_byte`, `peek_word`, `poke_byte`,
`poke_word`), dispatch (`call_handler`, `handler_of`, the `ev_*` event
ids, `run_free`, `run_grain`, `run_alter`, `tick_timers`), the property
accessors (`desc_addr` and its `*_addr` kin), the mute buffer
(`mute_begin`, `mute_end`, `mute_buf`), the conversation machinery
(`topic_*`), the screen opcodes (`set_window`, `split_window`,
`set_cursor`, `set_colour`, `set_style`, `show_char`), and the arc_image
plumbing (`draw_image`, `image_of`, `pictures_available`). These are the
primitives Cosmos itself is written on. They are not secret (`arcc
--extract` hands you every use of them, commented), but they are the
library's vocabulary rather than the author's, and the design records
(03 and 04) are their reference.

