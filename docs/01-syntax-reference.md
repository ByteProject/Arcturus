# Arcturus Syntax Reference

Status: draft v2. This is the authoritative definition of the Arcturus
language surface and its semantics, at the level an author needs to write
correct programs.

Scope boundary. This document defines the language. The runtime behavior the
language drives, the standard library (named Cosmos), the parser, the action
pipeline, the banner, and the optional summonable features are defined in
02-cosmos-and-parser.md. The lowering of each construct to z5 is owned in the
implementation phase (03 and 04). Where this document says "Cosmos provides X",
X is specified in 02.

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
string may span several physical lines (section 16).

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
and free-standing `on` rules.

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
later with `print_banner()` (after a quote box, say), or never.
The banner also names the compiler (Arcturus) and the library
(Cosmos) with their versions; see 02.

Globals and constants:

```
global score = 0
constant max_score = 100
```

The Z-machine offers 240 globals; the compiler allocates them and errors only
if a program exceeds that.

## 5. The world model

Two built-in categories introduce objects: `room` for locations, `thing` for
everything else. Both are kinds and can be extended.

```
room  <id> [of <kind>]
thing <id> [of <kind>] [in <location>]
thing <id> [of <kind>] in <room>, <room> ...
```

`of <kind>` sets the parent kind; `in <location>` sets the initial tree
position. The body is property settings, `on` handlers, and an optional
`grains` block (section 14).

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
| `scenery` | Background detail: still referable for `examine`, but left out of the room's contents listing and not takeable (gives the scenery line). |
| `hidden` | Out of scope entirely until cleared: an undiscovered object, neither listed nor referable. Clear it when the object is revealed. |
| `concealed` | In scope and actable, but omitted from the room's contents listing (present but not spelled out in the description). |
| `wearable` | Can be worn; the `wear` verb accepts it. |
| `worn` | Currently worn. Set by `wear`, cleared by `drop` / `take_off`. Inventory tags it "(worn)". |
| `lit` | Gives light. On a `room`, the room is independently lit; on a thing, the thing glows and lights its location. Light is otherwise computed. |
| `edible` | Can be eaten; the `eat` verb consumes it rather than refusing. |
| `named` | A proper-named thing (Linda, Excalibur). Takes no article: `${the noun}` and `${a noun}` print just the name. |
| `an` | The indefinite article is "an", not "a". Derived from the name's first letter (a vowel -> `an`); set `an` or `an false` only for an exception (an hour, a unicorn). |
| `switchable` | Marks a thing the `switch` verb targets, but the effect is the author's: unlike `openable` or `edible`, there is no built-in on/off behavior (the library has no way to know what turning a thing on should do), so give the object `on switch_on` and `on switch_off` handlers. Without them, switching it is refused (`msg_no_switch`). The attribute itself only advertises intent. |
| `openable` | Can be opened and closed; the `open` / `close` verbs apply. |
| `open` | Currently open (a container or door). Set by `open`, cleared by `close`. A closed container hides its contents from scope. |
| `clear` | A see-through container (a glass jar): its contents are in scope and referable even when closed. An open or `clear` container exposes its contents; a closed opaque one shields them. |
| `seen` | Set once the player has been shown an object (a content of an open container, something taken or examined). A closed opaque container still lists the contents the player has `seen`, so they are not forgotten when put away; contents never seen stay hidden until the box is opened. Cosmos manages this; you rarely set it. The full container knowledge model is in 02, section 5a. |
| `lockable` | Can be locked and unlocked with a key (`lock` / `unlock`). |
| `locked` | Currently locked; blocks `open` until unlocked with the matching key. |
| `visited` | The room has been entered before (Cosmos sets it on entry). Use it to vary a room's description on return. |
| `moved` | Set the first time the player takes an object. While clear, the object shows its `intro` text in a room description instead of the plain listing. |
| `animate` | An animate agent (a person, animal, robot, or AI). The conversation and give verbs apply only to the animate; the `character` kind sets it by default, and animate objects refuse being taken. |

The standard kinds are also attributes, set by `of <kind>` and tested with `is
<kind>`: `thing`, `room`, `container`, `supporter`, `door`, `character`. An object
carries the attribute of every kind in its chain.

### Standard value properties

| Property | Type | Meaning and usage |
|---|---|---|
| `name` | text | The printed short name ("brass lantern"). Distinct from the object's id and from `words`. |
| `desc` | text | The description shown by `examine` (and on first look at a room). |
| `words` | list | The vocabulary the parser matches: the object's nouns and adjectives, as equal entries. Typed but not printed. |
| `intro` | text | An object's initial appearance in a room, shown as its own paragraph while the object is untouched (`moved` clear). |
| `capacity` | number | How many objects a container or supporter holds. |
| `unseal_with` | object | The object (a key) that locks and unlocks this one (for `lockable` things). |

`score`, `max_score`, and `turns` are runtime globals, not object properties (02
section 2).

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

`finish` ends the game, printing its final message.

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

Disambiguation: when the right operand is a bare identifier, `is` is a property
test if it names a declared boolean property, a kind-membership test if it names
a kind, and otherwise an equality. A name that is both a boolean property and an
object (or a kind and an object) used with `is` is a compile-time clash to
rename.

Logic: `and`, `or`, `not`, short-circuiting.
Property read with the dot, chainable: `ruby.value`, `hallway.north.name`.
Tree tests: `player holds lantern`, `lantern in player`.

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
including "all"), `text` (free text). Bare words such as `in`, `on`, `with`
are literal prepositions. Two-object lines bind `noun` and `second`.

Standard verbs, including talk-to, come from Cosmos; how input is tokenized
and resolved is defined in 02. This section defines only how you declare a
verb and how its grammar names the action your handlers receive.

Direction words are declared the same spirit, mapping vocabulary to a fixed
direction property:

```
direction north     "north", "n"
direction northeast "northeast", "ne"
```

The property name (`north`, `northeast`, `up`, `in`, ...) is one of the standard
directions and never changes; the quoted words are the player's vocabulary. Like
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
Ending the handler, by its end or `stop`, consumes the action, so the default
does not run; this is the common "instead" case. To run your code and then
also let the next, more general handler or the Cosmos default run, end with
`continue`. To react after the action completes, use `on after <verb> ...`.
The full ordering is in 02.

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
as the fallback direction in `on go other` (02). Its place in the dispatch
chain is defined in 02, section 9.

Life-cycle events. Besides the action events named by verbs, Cosmos fires three
events as the game runs, handled with the same `on` syntax:

- `on start` runs once, before the first prompt: opening text, initial setup, and
  any timers you want armed from the outset.
- `on enter` runs when the player arrives in a room, as that room's handler, so a
  room can react to being entered.
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
presents them, either as the Infocom-style ask/tell verbs (`summon.extendedverbs`)
or as a numbered menu (`summon.conversations`). The two are mutually exclusive,
and the menu wins when both are present. How they are presented is defined in 02;
this section defines the construct.

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
- `once` retires the topic after it runs.
- `hidden` starts the topic out of view, until a `reveal` brings it in.

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

Interpolation embeds an expression with `${ }`; printing an object prints its
`name`. Article helpers: `${the ruby}`, `${a ruby}`, and the capitalized
`${The ruby}`, `${A ruby}`; an object with `named` set takes no article.
Their full behavior is in 02. Escapes: `\"`, `\\`, `\$`, and `\n`.

An article may carry a grammatical-case tag after a colon, `${the:acc noun}` or
`${a:dat noun}`, for a language whose article inflects for case (German
der/den/dem). The cases are `nom`, `acc` (or `akk`), `dat`, and `gen`; with no
tag the case is nominative. English and Spanish ignore the tag, so it costs
nothing there; a language pack's article block reads it (02, section 14a). Only
the definite and indefinite article take a tag.

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
(`say.yellow "${The noun} glows."`). Together, the classic Infocom-era look is
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
conformance target. It exercises darkness, a wearable item that changes a
room's light, a supporter (the hook), a state counter, and a win-or-lose
ending.

```
game
    title  "Cloak of Darkness"
    author "Roger Firth, ported to Arcturus"
    UUID   2a1f8e63-9b07-4c2d-8f3a-5e1d6042b7c9
    start  foyer

// The classic Cloak of Darkness shows a status line, so this port summons one.
summon.statusline

global disturbed = 0

on start
    say "Hurrying through the rain-swept November night, you are glad to
         see the bright lights of the Opera House. It is surprising that
         there are no others around, but you make your way to the
         cloakroom to hang up your things."


room foyer
    name "Foyer of the Opera House"
    desc "You are standing in a spacious hall, splendidly decorated in red
          and gold, with glittering chandeliers overhead. The entrance from
          the street is to the north, and there are doorways south and west."
    south bar
    west  cloakroom

    on go north
        say "You have only just arrived, and besides, the weather outside
             seems to be getting worse."
        stop

    grains
        examine "chandeliers" or "decoration" say "Glittering, and far out
            of reach."


room cloakroom
    name "Cloakroom"
    desc "The walls of this small room were clearly once lined with hooks,
          though now only one remains. The exit is a door to the east."
    east foyer


thing hook of supporter in cloakroom
    name  "small brass hook"
    words small, brass, hook, peg
    fixed

    on examine
        if hook holds cloak
            say "A small brass hook, with a cloak hanging on it."
        else
            say "A small brass hook, screwed to the wall."
        stop


thing cloak in player
    name  "velvet cloak"
    words black, velvet, satin, dark, cloak
    desc  "A handsome cloak, of velvet trimmed with satin, and slightly
           spattered with raindrops. Its blackness is so deep that it
           almost seems to suck light from the room."
    wearable
    worn

    on drop
        say "This is no place to leave a smart cloak lying around."
        stop


room bar
    name "Foyer Bar"
    desc "The bar, much rougher than you would have guessed after the
          opulence of the foyer to the north, is completely empty. There
          seems to be some sort of message scrawled in the sawdust on the
          floor."
    north foyer
    lit  false

    on enter
        if player holds cloak
            now bar is not lit
        else
            now bar is lit

    on each_turn when bar is not lit
        change disturbed to disturbed + 1
        say "Blundering around in the dark isn't a good idea!"


thing message in bar
    name  "scrawled message"
    words message, sawdust, floor, dust, writing
    fixed

    on examine
        if bar is not lit
            say "It is too dark to see anything."
            stop
        if disturbed < 2
            say "The message, neatly marked in the sawdust, reads:"
            finish "*** You have won ***"
        else
            say "The message has been carelessly trampled, making it hard
                 to read. You can just make out the words:"
            finish "*** You have lost ***"
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
`return`, `global`, `constant`, `let`, `change`, `to`, `now`, `is`, `not`,
`add`, `remove`, `from`, `move`, `say`, `stop`, `continue`, `finish`, `if`,
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
constant_decl  := "constant" id "=" expr
rule           := handler

statement      := let | change | now | move | add | remove | say
                | stop | continue | finish | if | while | for | switch
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
