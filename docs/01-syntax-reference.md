# Arcturus Syntax Reference

Status: draft v2. This is the authoritative definition of the Arcturus
language surface and its semantics, at the level an author or Claude Code
needs to write correct programs.

Scope boundary. This document defines the language. The runtime behavior the
language drives, the standard library (named Cosmos), the parser, the action
pipeline, the banner, and the optional summonable features are defined in
02-cosmos-and-parser.md. The lowering of each construct to z5 is owned in the
Claude Code phase (03 and 04). Where this document says "Cosmos provides X",
X is specified in 02.

The worked examples in sections 17 and 18, the Brass Lantern and the iconic
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

Source is UTF-8; the compiler maps text to ZSCII at build time.

Comments start with `//` and run to end of line. There are no block comments.

Identifiers begin with a letter and contain letters, digits, and
underscores, and are case sensitive. Convention is lower_snake_case.
Reserved words (appendix A) cannot be identifiers.

Indentation defines block structure: an indent opens a body, a dedent closes
it. Use a consistent unit, four spaces recommended, and never mix tabs and
spaces. An inconsistent indent is a compile error.

Newlines are significant: one statement or declaration per line. A quoted
string may span several physical lines (section 15).

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
banner. The banner also names the compiler (Arcturus) and the library
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
```

`of <kind>` sets the parent kind; `in <location>` sets the initial tree
position. The body is property settings, `on` handlers, and an optional
`grains` block (section 14).

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
running the block when the property is read. The block may `say` text
directly or `return` a value; when Cosmos prints such a property (for example
a room `desc`), it prints the returned text, or relies on the block's own
`say` if the block returns nothing.

```
room cellar
    name "Cellar"
    desc block
        if here is lit
            return "A damp cellar of black stone."
        return "Pitch black. You feel cold stone underfoot."
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

`say` prints text or a value; printing a number prints digits, an object
prints its `name`: `say "Score: ${score}."`.

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

Disambiguation: when the right operand is a bare identifier naming a boolean
property of the left operand's kind, `is` is a property test; otherwise it is
equality. A name that is both a boolean property and an object used with `is`
is a compile-time clash to rename.

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

A `when` guard restricts a handler to a condition:

```
on each_turn when ruby is hidden
    say "Water ticks against stone."
```

Default versus override. A matching handler replaces the verb's default
behavior, with the most specific winning (the section 5 resolution order).
Ending the handler, by its end or `stop`, consumes the action, so the default
does not run; this is the common "instead" case. To run your code and then
also let the next, more general handler or the Cosmos default run, end with
`continue`. To react after the action completes, use `on after <verb> ...`.
The full ordering is in 02.

Core events Cosmos fires, defined in 02: `on start`, `on enter`,
`on each_turn`, and the action events named by verbs.

## 13. Summon

`summon` brings external code or an optional built-in feature into the build.

Importing an extension, a separate Arcturus source file written by you or a
third party:

```
summon "extensions/lockpicking.storyarc"
summon weather
```

An extension is ordinary Arcturus source exposing kinds, verbs, blocks, and
grains. It may define its own summonable sub-features.

The dotted form enables a built-in feature that ships with Cosmos or the
compiler but is off by default:

```
summon.conversations          // the talk-menu system (02)
summon.debug                  // debugging verbs, excluded from release builds
summon.language "Spanish"     // select a Cosmos language pack
summon.abbreviations "game.abbr"  // use a custom abbreviation set for text
```

`summon.conversations` and `summon.debug` are described in 02.
`summon.language` swaps the Cosmos message strings for a language pack.
`summon.abbreviations` overrides the compiler's default abbreviation table
with a file, typically produced by the arcabbr tool, for maximum text
compression.

## 14. Grains

Grains are built-in cheap scenery: words that respond to a few verbs without
the cost of a full object. They replace the cheap_scenery pattern and are
part of the language, not an import.

A `grains` block lists grain lines. Each line names the verbs it answers, the
scenery words it matches (one or more, joined by `or`), and a response, which
is a one-line `say`, a `do` of a named block, or an indented body.

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

A grain matches when the player applies one of its verbs to one of its words
and no real object in scope matches that word. The parser handling of grains
is defined in 02. Grains cost only dictionary words and a small table, never
an object entry.

## 15. Output and text

A string is written in double quotes and may span physical lines; runs of
whitespace, including line breaks, collapse to a single space, so
continuation lines may be indented:

```
desc "A damp cellar of black stone. A squat pedestal stands at its
      centre, a rusted lever set into the base."
```

Interpolation embeds an expression with `${ }`; printing an object prints its
`name`. Article helpers: `${the ruby}`, `${a ruby}`, and the capitalized
`${The ruby}`, `${A ruby}`; an object with `proper` set takes no article.
Their full behavior is in 02. Escapes: `\"`, `\\`, `\$`, and `\n`.

## 16. Diagnostics

Representative compile-time errors:

- Mutating an undeclared property.
- Property type clash across sites.
- A non-boolean condition (`if n`).
- Unknown verb or action in a handler header.
- Inconsistent indentation or mixed tabs and spaces.
- A `switch` mixing number and string cases.
- A name clash between a boolean property and an object used with `is`.
- A `summon` of a missing file or unknown built-in feature.

## 17. Worked example: The Brass Lantern

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

## 18. Worked example: Cloak of Darkness

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
`release`, `serial`, `UUID`, `start`.

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
handler        := "on" [ "after" ] event [ "when" expr ]
                  INDENT { statement } DEDENT
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
