# Arcturus Syntax Reference

Status: stable. This is the authoritative definition of the Arcturus
language surface and its semantics, at the level an author needs to write
correct programs. The language is proven in the field: Hibernated 2, a
full-length commercial game, is ported and plays to completion, and the two
reference games in sections 18 and 19 are the conformance anchors of the
whole toolchain. Where the compiler and this document disagree, the document
wins: the code gets fixed, or the document is amended in the same commit.

Scope boundary. This document defines the language. The runtime behavior the
language drives, the standard library (named Cosmos), the parser, the action
pipeline, the banner, and the optional summonable features are defined in
02-cosmos-and-parser.md. The lowering of each construct to z5 is recorded in
03-compiler-pipeline.md and 04-codegen-mapping.md. Where this document says
"Cosmos provides X", X is specified in 02.

The worked examples in sections 18 and 19, the Brass Lantern and the iconic
Cloak of Darkness, use only constructs defined here and serve as the shared
reference programs across all documents.

## 1. Design principles

1. One way to read a thing. `change` sets any mutable state; `is` tests any
   boolean; the dot reads any property.
2. The author describes the world; the compiler handles the machine, and
   aims for the smallest possible z-code in doing so.
3. Structure from indentation. No braces and no `end`.
4. Declarative shape, imperative behavior. Objects are data; behavior hangs
   off them in `on` handlers and `block` routines.
5. Errors at compile time, not surprises at run time.

## 2. Lexical structure

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
string may span several physical lines (section 16). One exception continues a
logical line: a line ending in a comma runs on to the next, so a long
comma-separated list (a `spans` set, an `in` clause, `words`, verb synonyms)
can be broken across lines and indented freely. Blank and comment-only lines
between the comma and the continuation are ignored.

## 3. Values and types

- number: a 16-bit signed integer, -32768 to 32767, wrapping arithmetic. No
  floats.
- text: a string, ZSCII encoded at compile time, with `${ }` interpolation.
- boolean: `true` or `false`.
- object: a reference to a declared object; the literal `nothing` is null.
- list: an ordered, bounded collection, declared with a capacity.
- block: a routine value (section 11). A property may hold a block, which
  makes it a computed property.

Conditions must be boolean; `if n` for a number is a compile error, write
`if n > 0`. Object presence is tested with `is not nothing`.

## 4. Program structure

Top-level constructs, in any order: the `game` metadata block, `summon`
directives, `kind`, `room`, `thing`, `verb`, `global`, `constant`, `block`,
and free-standing `on` rules. A language pack additionally uses the
language-layer declarations `language` (its self-identifying marker),
`direction`, `particle`, `pronoun`, `chain` (the words that join several
commands on one line), and `noise` (the articles the parser knows but
ignores), which map player-typed words to the compiler's fixed properties
and roles (02, sections 8, 8a, 8b, and 14a); and a German
object declares its gender with a bare `der`, `die`, or `das` line, which the
compiler maps to the gender attributes (02, section 14a).

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
banner. `banner false` stops the automatic banner at start: the game prints it
later with `print_banner` (after a quote box, say), or never.
The banner also names the compiler (Arcturus) and the library
(Cosmos) with their versions; see 02.

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
(strings, numbers, or objects), the compiler counting so no size is ever
written:

```
catalog colonel_letter
    "Doctor,"
    ""
    "A matter from the old days requires"
    "attention."

catalog suspects
    butler
    gardener
    doctor
```

The operations, all 1-based, all total (out of range answers 0/nothing):

```
calculate(suspects)              // how many entries: 3
entry(colonel_letter, 3)         // the third entry
last(colonel_letter)             // the final entry
dice(omens)                      // one entry at random
position(suspects, butler)       // an entry's number, or 0 when absent
if butler in suspects            // membership: the `in` you already know
for each line in colonel_letter  // iterate in order; say line prints right
change entry(verdicts, 2) to "guilty"   // rewrite ONE entry in place
```

A catalog passes to a block as an ordinary value (`quote_catalog(letter)`,
docs/05), and entry/calculate work on the parameter inside; `for each` and
the compile-folds need the catalog named in place. Underneath: a static
table in dynamic memory, so `calculate` on a named catalog folds to a
constant at compile time, `entry` and `last` are a single memory read,
`change entry` a single write, and there is no heap and no allocator
anywhere (the Dialog trap, deliberately refused: the list features that
would need one, append/reverse/collect, are the ones left out). A game
that declares no catalog is byte-identical. The interpolation rule matches
plain property strings: a catalog string is static, so `${...}` inside one
is a compile error. `calculate`, `entry`, `last`, `dice`, and `position`
are library-owned names.

## 5. The world model

Two built-in categories introduce objects: `room` for locations, `thing` for
everything else. Both are kinds and can be extended.

```
room  <id> [of <kind>]
thing <id> [of <kind>] [in <location>]
thing <id> [of <kind>] in <room>, <room> ...
```

`of <kind>` sets the parent kind; `in <location>` sets the initial tree
position. The body is property settings, `on` handlers, an optional `grains`
block (section 14), `topic` blocks on a character (section 15), and, with
`summon.ambience`, `ambience` blocks (02, section 14; docs/05).

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
section 10).

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
lines as read well, and a line ending in a comma continues on the next (section
2):

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
    switchable
```

The object identifier (`lantern`) is the code symbol; the `name` property is
the printed text. They are different. The `words` property is a third thing
again: the vocabulary the parser matches, holding the object's nouns and
adjectives as equal entries. `name` is printed but not typed; `words` is
typed but not printed. Adjectives are simply words in `words` (02, section 8).

## 5a. The player

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
(02, section 7). A bare `move lamp to player` leaves auto-scored points
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
    switchable
    lit false

    on switch_on
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
provides is listed in 02 section 10.

## 6. Properties and the unified model

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
block, and whatever it says is what the property prints. This is text only: a
computed `desc` is the headline use, and a computed value property (a number
or object decided at run time) is reported as a compile error, because a read
cannot tell a small value apart from the block's address.

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
  (section 7).

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
| `pluribus` | Grammatical number: ONE object that is grammatically plural (the scissors, the boots; e pluribus unum, many speaking through one). The articles read it ("some scissors"; German's bare indefinite plural and die/die/den/der by case; Spanish los/las, unos/unas), `${is x}` agrees (is/are, ist/sind, está/están), and the core messages conjugate ("The scissors stay exactly where they are."). NOT the plurals granule, whose group words sweep several distinct singular objects ("take coins"). Costs nothing in a game that never sets it. |
| `switchable` | Marks a thing the `switch` verb targets, but the effect is the author's: unlike `openable` or `edible`, there is no built-in on/off behavior (the library has no way to know what turning a thing on should do), so give the object `on switch_on` and `on switch_off` handlers. Without them, switching it is refused (`msg_no_switch`). The attribute itself only advertises intent. |
| `openable` | Can be opened and closed; the `open` / `close` verbs apply. |
| `open` | Currently open (a container or door). Set by `open`, cleared by `close`. A closed container hides its contents from scope. |
| `clear` | A see-through container (a glass jar): its contents are in scope and referable even when closed. An open or `clear` container exposes its contents; a closed opaque one shields them. |
| `seen` | Set once the player has been shown an object (a content of an open container, something taken or examined). A closed opaque container still lists the contents the player has `seen`, so they are not forgotten when put away; contents never seen stay hidden until the box is opened. Cosmos manages this; you rarely set it. The full container knowledge model is in 02, section 5a. |
| `lockable` | Can be locked and unlocked with a key (`lock` / `unlock`). |
| `locked` | Currently locked; blocks `open` until unlocked with the matching key. |
| `scored` | Managed by `scoring` (section 6a): the compiler sets it on every room and takeable thing; write `scored false` to exempt one. Set it by hand only in a game without `scoring` that wants a single classic auto-payer. |
| `visited` | The room has been entered before (Cosmos sets it on entry). Use it to vary a room's description on return. |
| `moved` | Set the first time the player takes an object. While clear, the object shows its `intro` text in a room description instead of the plain listing. |
| `animate` | An animate agent (a person, animal, robot, or AI). The conversation and give verbs apply only to the animate; the `character` kind sets it by default, and animate objects refuse being taken. |
| `component` | This thing is PART OF the thing it sits `in` (a lever in a machine, a button on a panel; the equivalent of Dialog's `#partof`). The object tree carries the relation, so the part follows its whole wherever the whole moves; the attribute grants what a plain thing's insides never get: the part is in scope whenever the whole is, `take` answers that it is part of it (`msg_part_of`), and it never lists as the whole's contents. Make the part `on pull` / `on push` handlers do the machine's work. To detach one in play, clear the attribute and move it. A game with no components pays nothing (`any_components`). |

The standard kinds are also attributes, set by `of <kind>` and tested with `is
<kind>`: `thing`, `room`, `container`, `supporter`, `door`, `character`. An object
carries the attribute of every kind in its chain.

### Standard value properties

| Property | Type | Meaning and usage |
|---|---|---|
| `name` | text | The printed short name ("brass lantern"). Distinct from the object's id and from `words`. |
| `desc` | text | The description shown by `examine` (and on first look at a room). |
| `words` | list | The vocabulary the parser matches: the object's nouns and adjectives, as equal entries. Typed but not printed. |
| `tag` | text | A short state qualifier appended to the object in listings and the inventory: "a fluid canister (full)". Usually computed (`tag block`); print with `show`, not `say`, so it stays inline. The parentheses come from the listing. |
| `plural` | list | The words that name this object AS PART OF A GROUP (`plural coins` on each coin): "take coins" acts on every match in scope. Only with `summon.plurals` (02 section 8; docs/05); ignored otherwise. |
| `intro` | text | An object's initial appearance in a room, shown as its own paragraph while the object is untouched (`moved` clear). |
| `appearance` | text | The paragraph the object ALWAYS owns in a room description, replacing its listing line and never expiring ("The keeper is trimming the wick."): Inform's describe, Dialog's `(appearance $)`. A computed block (`appearance block`) words it by state; checked before `intro`; `hidden`/`concealed` still suppress. Costs nothing in a game that never sets one. |
| `capacity` | number | How many objects a container or supporter holds. |
| `article` | text | The definite article, verbatim, when derivation cannot reach it: `article "las"` (las tijeras), `article "el"` (el agua). |
| `indefinite` | text | The indefinite article, verbatim: `indefinite "unas"`, or an English mass noun with `indefinite "some"` ("You can see some water here."). |
| `unseal_with` | object | The object (a key) that locks and unlocks this one (for `lockable` things). |
| `arc_image` | number | Optional. A room's picture, named by its resource id (`arc_image 8`, or a constant that folds to one). Shown on an aware interpreter, ignored on a standard one. Section 6b. |

`score`, `max_score`, and `turns` are runtime globals, not object properties (02
section 2).

## 6a. Scoring

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
Section 5 has the rule of thumb (the move-versus-gain warning), section 7
the statements themselves.

The escape hatch: `change score` stays legal (penalties, score-as-resource),
but it is off the paved road: hand-changed points play no part in the
computed max. `award` is the road.

## 6b. Room pictures (arc_image)

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
re-decompress its art for nothing).

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

The pictures live beside the story, not inside it. During development, point the
interpreter at a directory of numbered PNGs (`actaea game.z5 --images art/`).
For distribution, the `arcimg` tool packs them into a single `.arcres` file (a
zip of the numbered PNGs), which the interpreter reads automatically when it
sits next to the story; the z5 stays a separate file.

`arcimg` is the third standalone tool, shipped like `arcc` and `actaea`
(`build/arcimg`, a single self-contained file). The two commands of the
modern path:

```
arcimg prep opening.jpg --id 8 --mode daad -o art/    # art/8.png at 320x96
arcimg pack art/ -o game.arcres                        # the distributable pack
```

The full picture workflow, the retro conversions, and which interpreters
play the pictures today and next, is its own author guide: docs/07.

Mode-sized PNGs need nothing but the standard library; `prep` reaches for Pillow
only to resize or convert, and offers a guided install the first time. A worked
example, with its `.arcres` and heavily commented source, is in
[examples/arc_image](../examples/arc_image).

## 7. Statements

Statements appear inside `on` handlers, `block` bodies, and computed
properties.

`let` introduces a local: `let n = 0`.

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
(all three in 02, section 7). `teleport(dest)` moves the player without
walking (a crash landing, a transit pod) and describes the arrival.
`gain(obj)` hands the player an object without TAKE (a panel pried open,
a mechanism yielding its prize); section 5 has the move-versus-gain
warning, and with `scoring` on both pay exactly like their verbs
(section 6a). `convey(vehicle, dest)` moves a VEHICLE the player rides
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
perform("take", book)         // the full TAKE, "Got it." and all
perform("go", west)           // a real move; a direction rides the way slot
perform("give", coin, bob)    // two nouns
if perform("open", chest) is 0
    say "The chest defies you."   // 0 means the action refused
```

The action name is checked at compile time; the enclosing command's own
operands are restored afterwards (a later AGAIN still repeats what the
player typed), and no extra turn passes: it is one turn's work. Where
`teleport` and `gain` exist they stay the better word (they are silent
about the how); `perform` is for when you want the verb's whole voice.
Costs nothing in a game that never calls it.

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
that also consumes the action (section 12). `continue` ends the current
handler and passes the action to the next, more general handler (section 12).

`finish` ends the game, printing its final message; Cosmos then reports the
final score (the same line SCORE prints) and offers the classic RESTART,
RESTORE, QUIT prompt, answered in the pack's own words (02, section 7).
`death` is the same statement for an ending the player may take back: its
prompt adds UNDO, which rewinds the fatal command itself, while a `finish`
(a victory, a completed story) stays final; a won game must stay won.
Write `finish "*** You have won ***"`, `death "*** You have died ***"`.

## 8. Control flow

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

`switch`, on a number or a string, with no fall-through; a `case` may list
several values, and `else` is the default:

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

## 9. Expressions and operators

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
`<obj> is reachable` (scope rules in 02).

## 10. Verbs and grammar

A `verb` declaration lists the player's words, then grammar lines:

```
verb "take", "get"
    take noun

verb "put"
    put noun in noun
    put noun on noun
```

A grammar line is an action name, then slots and literal words. Slots:
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

The direction is not a noun: it rides `way`, the same slot GO uses, so the
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
`meta_turn`, as the standard session verbs do (02, section 9).

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
with `dig in noun mit noun` and the same matcher serves it (02 section 8c).
When several of your lines could fit the same typed command, remember the
matcher's order: the line with more literal words is tried first, declaration
order breaks ties, so you rarely need to think about it; when in doubt, put
the more specific wording first anyway, which reads better in the source.

Standard verbs, including talk-to, come from Cosmos; the full list of
standard grammar lines is 02 appendix B, and how input is tokenized and
resolved is defined in 02 (the positional matcher in 02 section 8c). This
section defines only how you declare a verb and how its grammar names the
action your handlers receive.

Direction words are declared the same spirit, mapping vocabulary to a fixed
direction property:

```
direction north     "north", "n"
direction northeast "northeast", "ne"
```

The property name (`north`, `northeast`, `up`, `in`, ...) is one of the standard
directions and never changes; the quoted words are the player's vocabulary. The
standard set also holds the four nautical directions (`fore`, `aft`, `port`,
`starboard`) for a vessel or a deep space craft; their player words are the
opt-in nautical granule (docs/05), while the properties are always legal in
exits and handlers and, like every direction, cost nothing unused. Like
verbs and messages, direction words are part of the language layer, so a language
pack redeclares them (`direction north "norte", "n"`) and Cosmos ships the English
set. A game rarely writes these; it summons a language, or uses the default
English. Selecting a language is one summon: `summon.language "spanish"` compiles
that language layer in place of English (02, section 8).

A room's exit is written with this property name, not the word: `north cellar`,
`east door` (section 5). So an exit stays in the fixed English name even in a
translated game (`east puerta`), while the player types the localized word
(`este`). The same split runs through the language: the fixed identifiers a game's
code uses (`thing`, `room`, `openable`, the direction properties, the grain
actions in section 14) are English; only what the player reads and types is
localized.

## 11. Blocks

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
and need no type annotation. Recursion is allowed, bounded by the Z-machine
stack. The 15-locals limit per Z-machine routine is managed by the compiler,
which spills to the stack as needed.

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

Blocks also serve as computed property values (section 6) and as grain
responses (section 14). A block attached to a property or grain may be named
and referenced, or written inline as an indented body.

The split is deliberate: `block` routines are called by you; `on` handlers
are entry points the engine fires.

## 12. Handlers and events

A handler runs when its event fires. Handlers live inside an object or kind
body, where `self` is that object, or as free-standing top-level rules naming
their object.

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
behavior, with the most specific winning (the section 5 resolution order).
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
   the after handler stays silent.

`stop` on a handler's last line changes nothing: reaching the end blocks
the built-in behavior anyway. `stop` exists to end the handler from the
MIDDLE of the body, almost always inside an `if`, when a refusal means the
remaining lines should not run:

```
on go west
    if door is locked
        say "The door won't budge."
        stop            // end here: no movement
    say "You slip through."
    continue            // unlocked: and now the go really happens

on after go west
    say "The door clicks shut behind you."
```

The full ordering is in 02.

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

Within the after pass, handlers resolve exactly like the main ones: most
specific first, and `continue` passes to the next (the kind's after, the
room's, a free-standing one). An `on other` catch-all never answers the
after pass; it is for the player's verbs, not for bookkeeping. In a game
with no `on after` anywhere the whole machinery folds away at compile time
and costs nothing.

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

Here examine has its own reply and every other verb falls to `on other`. The
name `other` always means "anything not otherwise matched": as a verb here, and
as the fallback direction in `on go other` (02). A specific handler that runs
and ends with `continue` climbs to the kind, the room, and the defaults; it
does not fall into the same object's `on other`, so `on look / continue`
reads as "pass look through untouched". Inside a `go` handler, `way` holds
the chosen direction and a bare direction name is comparable against it
(`if way is not north`), for rules that treat one direction differently.
The full dispatch chain is defined in 02, section 9.

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

Recurring and delayed behavior beyond every turn uses the `after` and `every`
scheduling statements (one-shot and repeating timers); daemons and timers together
are covered in full in 02, section 13.

## 13. Summon

`summon` brings an optional Cosmos feature, or your own granule, into the build.
A granule is ordinary Arcturus source (kinds, verbs, blocks, grains) in a
`.granule` file, loaded only when summoned. There are three forms, which differ
in where the granule is found; the resolution rules and the fork workflow are in
05.

```
summon.statusline                        // the bundled feature, always
summon statusline.granule                // your copy if present, else bundled
summon "extensions/lockpicking.granule"  // an explicit file
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

Text compression is not a summonable feature. The compiler always applies a
standard abbreviation set, so nothing is required to get it. A story can tune the
set to its own text with `arcc --make-abbreviations`, which writes an
`abbreviations.granule` beside it; summon that by name (`summon
abbreviations.granule`) to use it in place of the default (02, and 05 section 7).

The granules that ship with Cosmos - extended verbs, the status line, verbose
exits, the conversation menu, and debug verbs - are catalogued in 05. Debug is
opt-in by the summon alone; there is no separate release build to strip it.

## 14. Grains

Grains are built-in cheap scenery: words that respond to a few verbs without
the cost of a full object. They replace the cheap_scenery pattern and are
part of the language, not an import.

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
is defined in 02. Grains cost only dictionary words and a small table, never
an object entry.

A grain word may be reused freely across rooms: "steps" can be set dressing in
the hallway and again in the cellar, each with its own response. The word gets
one dictionary entry, which points at a chain of (grain, owner) pairs, and the
parser answers with the grain whose owner is in scope. When several grains of
the same word are in scope at once (rare: a room and something the player
carries), the first declared wins. For one piece of scenery genuinely visible
from several rooms, a `scenery` thing with `spans` (section 5) is still the
better tool: one object, one description, one identity.

## 15. Topics and conversation

A character (a thing that is `animate`, which the `character` kind sets) can hold
conversation `topic`s. A topic is one subject the player can raise, together with
the exchange that follows. Topics are inert on their own: a summoned feature
presents them, either through the Infocom-style ask/tell verbs
(`summon.infocom_talking`) or as a numbered menu (`summon.conversations`).
The two are mutually exclusive by the compiler: a game summons exactly one,
and switching presentations later is a one-line change. How they are
presented is defined in 02; this section defines the construct.

A topic is declared in the person's body:

```
topic <subject> "<label>" [words a, b, ...] [when <cond>] [once] [hidden]
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

## 16. Output and text

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
the next output flushes as a single blank line (repeats collapse, docs/02).
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
Their full behavior is in 02. Escapes: `\"`, `\\`, `\$`, and `\n`.

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
nothing there; a language pack's article block reads it (02, section 14a). Only
the definite and indefinite article take a tag.

The copula agrees the same way: `${is ruby}` (capitalized `${Is ruby}`) prints
"is", or "are" when the object is `pluribus` (the scissors), worded by the
language pack (ist/sind; está/están, the estar of states and places). One
sentence template serves every number in every language: "${The coins}
${is coins} under the steamshovel." It takes no case tag.

Screen colours have their own section, 16a, below.

## 16a. Screen colours (zcolor)

The Z-machine draws in nine standard colours, and Arcturus exposes them by
name. The palette, as the Standard defines it (section 8.3.1):

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
order (`say.yellow.par`, section 16). Together, the classic Infocom-era look is
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

Colour support is handled for you, at both ends. The compiler marks the story
as colour-using in the header (Flags 2 bit 6, which interpreters require
before they enable colour at all), and every colour operation checks at run
time whether the interpreter reports colour support (Flags 1 bit 0): on an
interpreter without it, `zcolor` does nothing and `say.<colour>` is exactly a
plain `say`. No author-side guard is ever needed, and a game that never uses
colours pays nothing for the feature. An unknown colour name is a compile
error that lists the palette.

## 17. Diagnostics

Representative compile-time errors:

- Mutating an undeclared property.
- Property type clash across sites.
- A non-boolean condition (`if n`).
- Unknown verb or action in a handler header.
- Inconsistent indentation or mixed tabs and spaces.
- A `switch` mixing number and string cases.
- A name clash between a boolean property and an object used with `is`.
- A `summon` of a missing file or unknown built-in feature.

## 18. Worked example: The Brass Lantern

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
    desc  "A battered brass lantern, switchable if you care to."
    switchable
    lit   false

    on switch_on
        now self is lit
        say "The lantern catches with a soft hiss."

    on switch_off
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

## 19. Worked example: Cloak of Darkness

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
Section 15 of 02 reconciles each example with the Cosmos model in detail.


## Appendix A: reserved words

`game`, `room`, `thing`, `kind`, `verb`, `of`, `in`, `on`, `after`, `block`,
`return`, `global`, `flag`, `counter`, `constant`, `let`, `change`, `to`,
`now`, `is`, `not`,
`add`, `remove`, `from`, `move`, `say`, `stop`, `continue`, `finish`, `death`, `if`,
`catalog` (as a declaration head),
`else`, `while`, `for`, `each`, `switch`, `case`, `and`, `or`, `holds`,
`when`, `self`, `player`, `here`, `noun`, `second`, `nothing`, `true`,
`false`, `list`, `summon`, `grains`, `do`, `title`, `headline`, `author`,
`release`, `serial`, `UUID`, `start`, `mod`, `every`, `topic`, `you`, `reply`,
`reveal`, `hide`.

Grammar slot words (`held`, `multi`, `text`) and the standard direction and
verb names are reserved by Cosmos rather than the core language; see 02.

## Appendix B: grammar summary

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
                | stop | continue | finish | death | if | while | for | switch
                | return | call
switch         := "switch" expr INDENT { case } [ else_case ] DEDENT
case           := "case" value { "," value } INDENT { statement } DEDENT
for            := "for" "each" id ( "in" | "of" ) expr
                  INDENT { statement } DEDENT

place          := id | expr "." id
expr           := (* numbers, strings, booleans, object refs, nothing,
                     dot access, calls, is / is not, holds, in,
                     and / or / not, arithmetic and comparison *)
```
