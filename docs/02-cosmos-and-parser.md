# Arcturus Cosmos and Parser

Status: draft v2. This document defines the runtime: Cosmos (the standard
library), the parser, the action pipeline, and the banner. The language
surface is defined in 01-syntax-reference.md; this document defines the
behavior that surface drives.

Scope boundary. The compiler pipeline that turns a program plus Cosmos into a
z5 story file, the construct-to-opcode mapping, and the text-compression
implementation are owned in the implementation phase (roadmap 03 to 05). This
document is the behavioral specification those stages must satisfy. Smallest
possible z-code is a standing requirement on all of it.

The two worked examples in 01 (the Brass Lantern and Cloak of Darkness) are
the conformance cases; section 16 reconciles each with the model here.

## 1. Cosmos as an editable template

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

Overriding uses the ordinary resolution order from 01 (sections 5 and 12):
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
  (section 8, docs/05).
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

## 2. Runtime globals and story metadata

Built-in references usable in any handler or block:

- `player`: the player object, an instance of `character`.
- `here`: the room the player is in, maintained as the player moves.
- `turns`: a number, the elapsed turn count, starting at 0.
- `score`, `max_score`: numbers for games that keep score.
- `nothing`: the null object.

Cosmos owns `here` and `turns`; assigning to them is a compile error. The
author may change `score`.

Story metadata from the `game` block (01, section 4) is carried into the
story file: `title`, `headline`, `author`, `release`, `serial`, and `UUID`.
If `serial` is omitted Cosmos uses the build date in YYMMDD form. The `UUID`
is written as an IFID array in static memory, in the form Inform uses
(`UUID://<uuid>//`), so IFDB and similar tools can identify the game; the
compiler emits it without a warning.

## 3. The banner

Cosmos prints the banner at game start, before `on start` output. It carries
everything Inform's banner does, and names both the compiler and the library:

```
The Brass Lantern
An Interactive Fiction by Stefan
Release 1 / Serial number 260626 / Arcturus 0.5 / Cosmos 0.8
```

Line one is `title`. Line two is `headline` plus "by" and `author`, with
sensible defaults if either is absent. Line three carries the release number,
the serial, and then the compiler and library as a single final field,
Inform-style: the compiler name and version (Arcturus) followed by the
library name and version (Cosmos), separated by spaces rather than a slash.
The compiler and library versions are build constants, not author-set. A game
may replace the banner by handling the banner event, but the default carries
the standard information.

## 4. The object tree and the in/on relation

Containment is the Z-machine object tree: one parent per object, reached with
`in`, `move`, `holds`, and `for each`. The tree stores only parent and child.

The in-versus-on distinction is carried by the parent's kind: a child of a
`container` is in it, a child of a `supporter` is on it, a child of a
`character` or the player is carried, or worn if its `worn` property is set.
Cosmos uses the parent's kind to choose the preposition when listing or
describing contents and to decide scope.

## 5. Scope and visibility

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

Two predicates Cosmos provides for conditions: `<obj> is visible` (in scope
and the location lit; examining needs this) and `<obj> is reachable` (visible
and not behind a closed container; taking and most physical actions need
this). `hidden` removes an object from scope entirely until cleared.
`scenery` keeps it referable for examining but omits it from contents
listings and refuses taking.

## 5a. The container knowledge model

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

## 6. Light and darkness

Cosmos computes light automatically. The location is lit when the room's own
`lit` is true, or an in-scope object has `lit` true and gives light. A room's
`lit` means the room is independently lit; a thing's `lit` means it is
glowing.

When the location is dark, scope collapses to what the player carries, room
contents are not visible, and visibility-dependent actions report "It is
pitch dark, and you can see nothing." Movement is still allowed unless a room
blocks it. Because light is computed, authors rarely set it by hand; a game
that needs special behavior overrides at the room, as the Cloak bar does.

## 7. The turn loop

Each turn Cosmos runs:

1. If the player entered a new room this turn, describe it: print the room
   `name`, the `desc` if unseen or on look, then the listed contents, and
   fire the room's `on enter`.
2. Print the prompt (default ">").
3. Read a line and tokenize it (section 8).
4. Parse: identify the verb, fill slots, resolve nouns in scope,
   disambiguate. On failure, print the refusal and skip to step 7.
5. Dispatch the action through the pipeline (section 9).
6. Run `on after` handlers if the action completed.
7. Fire active `on each_turn` handlers (the room's, and in-scope objects'),
   subject to their `when` guards, then fire any scheduled events (section
   13).
8. Increment `turns`. If a `finish` ended the game, print the final message
   and stop.
9. Loop.

The room is described once on entry. The status line (room name and score or
turns) is maintained continuously by the interpreter.

## 8. The parser

The parser turns input into an action with bound objects.

Tokenizing. Input is lowercased and split on spaces and punctuation. Noise
words ("the", "a", "an", "my") are dropped. Remaining tokens are matched
against the dictionary, which holds every verb word, every object's `words`,
and all grain words (section 14). An object's printed `name` is not matched;
matchable vocabulary comes only from `words`, which keeps the dictionary
small and under the author's control. Dictionary entries are truncated to the
Z-machine word resolution, so long words collide on their prefix; this is a
property of the format.

Verb resolution. The first verb word selects a `verb` declaration; its
grammar lines are tried in order, and the first whose shape matches wins,
producing an action and slot fillers.

Noun resolution and adjectives. Arcturus has no separate adjective type;
adjectives are ordinary entries in an object's `words`, ranked the same as
nouns. A typed noun phrase matches an in-scope object when every content word
typed appears in that object's `words`. The parser scores each candidate by
how many typed words it matches and takes the single best:

- No object matches: "You can't see any such thing.", or the darkness
  message.
- One object matches best: it fills the slot.
- Several tie: disambiguation asks "Which do you mean, the X or the Y?",
  printing the full `name` of each, and reads a reply that adds a
  distinguishing word.

So typing more adjectives narrows the result: with a brass hook and an iron
hook in scope, "hook" is ambiguous and prompts, "brass hook" resolves
directly, and after a prompt a bare "brass" selects. `held` matches the same
way but also requires the player to hold the object. The most recent match
feeds pronouns ("it", "them").

The `name`-versus-`words` split is the only lever needed: a word in `name` is
printed but not matched, a word in `words` is matched but not printed, and a
word you want both printed and typed simply appears in each. There is no "the
brass one" anaphora in v1; that advanced parser feature is deferred.

Multi and all. A `multi` slot matches several objects; "all" expands to the
reasonable set for the verb, minus any named after "except". The action runs
once per object.

Unknown words. A token in no dictionary entry gives "I don't know the word
'<token>'." A known word used where no grammar line accepts it gives "You
can't do that." These are Cosmos strings and are overridable.

Grains. When a `noun` slot finds no real object but the typed word is a grain
word on `here` or an in-scope object, and the action's verb is one the grain
answers, Cosmos runs the grain's response (a `say`, a `do` block, or its
inline body) and treats the action as handled. Grains are checked after real
objects, so a real object always wins. See section 14.

Language seam. The parser is written in Arcturus, split into a language
agnostic skeleton (reading the line, computing scope, dispatching the action,
the turn loop) and language-specific routines (tokenizing and normalizing
words, resolving the verb, matching a noun phrase, and applying word order).
The English routines are the default; a language pack (section 14) overrides
the language-specific routines through ordinary resolution to handle a
language's morphology and grammar, without forking the skeleton. The skeleton
makes no English-specific assumption about word order, articles, or inflection.

## 9. The action pipeline

An action carries its verb, `noun`, and optional `second`. Cosmos dispatches
it as one chain of handlers, most specific first:

1. the `noun` object's own `on <verb>` handler,
2. the `noun` object's own `on other` handler,
3. its kind chain, nearest kind first, each kind's `on <verb>` before its
   `on other`,
4. the room's `on <verb>` handler, then the room's `on other`,
5. any free-standing top-level `on <verb>` rule,
6. the Cosmos default `on <verb>` handler.

`on other` is the catch-all (01, section 12): at each level a specific
`on <verb>` is tried before that level's `on other`, so an object's own
`on other` is its private default, sitting below its specific handlers but
above the kind chain. A handler that lists several verbs (`on attack, push,
pull`) is a specific handler for each of those verbs.

Each handler runs until it ends or calls `continue`. Ending consumes the
action and stops the chain; `continue` passes to the next handler. If the
chain reaches the Cosmos default and it ends, the action took its standard
effect.

After phase. If the action completed, Cosmos runs `on after <verb>` handlers
in the same specificity order. A `when` guard that does not hold makes a
handler skipped, and the chain continues as if it were absent.

This is leaner than Inform's rulebooks: one ordered chain, an explicit
`continue`, and an `after` pass, expressing instead, before-with-continue,
and after without further machinery.

## 10. Standard kinds

`thing` (base): `name`, `words`, `desc`; booleans `fixed`, `scenery`,
`hidden`, `concealed`, `wearable`, `worn`, `lit`, `edible`, `named`. Default
handlers for examine, take, drop, push, pull, turn, and the like (section
12).

`room`: `name`, `desc`, `lit` (true by default; a dark room declares `lit
false`), `visited`, and the direction properties (`north`, `south`, `east`,
`west`, `northeast`, `northwest`, `southeast`, `southwest`, `up`, `down`, `in`,
`out`), each an object defaulting `nothing`. A direction may name a room or a
door. Default `go <direction>` reads the matching property and moves the player,
or, when there is no exit, prints "You can't go that way." A room overrides one
direction with its own `on go <direction>`. The full movement model, including
computed exits and the blocked-direction fallback, is section 11a.

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
and a `key` to make it lock. A door joins two rooms with the `in A, B` sugar: it
lives in one room in the object tree and spans the other (section 5), so it is
referable and operable from both sides. When a room's exit names the door (`east
oak_door`), crossing it is gated on the door being open and unlocked and lands
the player on its far side, with no author code. Default open, close, lock,
unlock, and the movement gate.

`character of thing`: `animate`; holds and wears objects; refuses being taken
(an animate object answers TAKE with its own line, not the scenery `fixed` one)
and routes the talk verb (section 11). `player` is the distinguished instance.

## 11. Standard verbs

The core set, each with the action a handler matches. Words after the action
are alternative inputs.

- look (l): describe `here`.
- examine (x), look at, read: print `desc`. Needs visibility.
- search noun: describe a container's or supporter's contents.
- take (get, pick up): move to player; refuse if fixed.
- drop: move to `here`; refuse if worn until removed.
- put noun in noun, put noun on noun.
- wear (don) noun; take off (remove, doff) noun.
- inventory (i, inv).
- go direction (n, s, e, w, ne, nw, se, sw, u, d, in, out).
- enter noun, exit (out).
- open noun, close (shut) noun.
- lock noun with noun, unlock noun with noun.
- switch on noun, switch off noun (turn on, turn off).
- push, pull, turn noun: default "Nothing obvious happens." unless handled.
- give noun to noun, show noun to noun.
- talk to noun (talk, speak to): the conversation action (below).
- wait (z), again (g).

The talk action. `talk to <person>` dispatches the `talk` action on the
person. Without the conversations feature, the Cosmos default routes to the
person's own `on talk` handler, or prints "There is no reply." With
`summon.conversations` (section 14), `talk to <person>` opens that person's
topic menu instead.

Meta verbs: save, restore, undo, quit, score, and a verbose-or-brief toggle,
using the corresponding Z-machine facilities.

Every default message is a Cosmos string, overridable globally by replacing
the Cosmos default or locally by handling the verb on an object or kind.

## 11a. Movement and blocked directions

The `go` verb reads the room's direction property for the chosen direction and
moves the player to the room it names. The model has four tiers, from most
specific to least, with no per-room boilerplate required:

1. A static exit: `north cellar` names the destination room directly.
2. A computed exit: a direction property may be a `block` (01, section 6), so
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
   `verbose_exits` in section 14), direction blocks must be free of side
   effects: reading an exit may happen more than once per turn.
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
`summon.verbose_exits` (section 14), an automatically listed set of the room's
available exits.

## 12. Standard responses

Representative defaults, all overridable: take a fixed object, "${The noun}
is fixed in place."; take something held, "You already have ${the noun}.";
take success, "Taken."; drop, "Dropped."; examine with no desc, "You see
nothing special about ${the noun}."; no exit, "You can't go that way."; a
closed container, "${The noun} is closed."; darkness, "It is pitch dark, and
you can see nothing."; an unhandled push, pull, or turn, "Nothing obvious
happens."

## 13. Naming, articles, daemons, and timers

Naming. `name` is the printed short name; the object identifier is never
printed. Article helpers: `${a noun}` chooses a or an by sound, `${the
noun}`, and capitalized `${A noun}` and `${The noun}` for sentence starts. An
object with `named` set takes no article. When Cosmos lists several objects
it joins them with commas and a final "and", each with its indefinite
article.

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
an object) runs every turn. Several each_turn handlers may be live at once; they
fire the room's first, then the free-standing rules.

Scheduled events fire a block after a set number of turns. `after` fires it once;
`every` fires it again and again:

```
after 3 turns do collapse_tunnel     // once, three turns from now
every 5 turns do tide_shifts         // every five turns, indefinitely
```

`do` names a `block` (01, section 11), which runs with no arguments when the timer
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
with the new period, which is how you extend, shorten, or restart a running timer.
A count of 0 disarms it, so `after 0 turns do temple_collapses` cancels a pending
collapse. A scheduled block may even schedule itself, arming its next fire with a
fresh count, for a timer whose period changes over its life.

Between them, `on each_turn` and `after`/`every` cover the whole range: a
condition-gated daemon, a one-shot fuse, and a fixed-period timer, all written in
ordinary Arcturus with no timer objects and no hand-kept turn counters.

## 14. Summonable features

These ship with Cosmos but are off until summoned (01, section 13). Each is a
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

This is the same `topic` construct the Infocom-style ask/tell path uses (docs/01
section 14, the extendedverbs verbs): `words` are the ask/tell subject words,
`when` gates visibility, `hidden` plus `reveal`/`hide` unlock by name, `once`
retires after use, and `you`/`reply`/`say` form the exchange. The two are two
views of one model and are mutually exclusive: when conversations is summoned the
menu owns talking and the ask/tell topic dispatch steps aside.

`summon.language "<name>"`. Localization. A language pack is a granule (for
example `cosmos/lang/spanish.granule`) selected by this directive, English
being the default. Cosmos messages are held as a resource table keyed by
message id, and the pack supplies translated strings and localized standard
vocabulary, including direction and verb words. A pack may also override the
parser's grammar logic, not only its strings: inflected languages parse
differently from English (verb conjugation, gender and number agreement, clitic
pronouns, contractions, freer word order), so a pack replaces the language
specific parser routines through ordinary resolution (section 8). An author's
own strings are written in whatever language they choose. Spanish is the first
planned pack; packs are maintained alongside the main Cosmos sources.

`summon.debug`. Developer verbs for testing, catalogued in 05: `tree` (the whole
object tree), `scope` (what is reachable here), `fetch`/`purloin` (pull any object
to you), `warp`/`gonear` (teleport to an object's room), and `inspect`/`showobj`
(an object's location and attributes). They reach objects out of scope, which the
parser normally refuses, through the `reach_unscoped` parser seam the granule
overrides. There is no separate release build to strip them: not summoning the
granule leaves them out entirely, which is the exclusion.

`summon.verbose_exits`. Helpful blocked-direction messages, game-wide. When a
player tries a direction with no exit, instead of the default "You can't go
that way." Cosmos lists the room's available exits, for example "You can only
go north or east from here." The list is computed from the room's live
direction properties each time, so it stays correct as exits open and close;
computed direction blocks (section 11a) are read to build it, which is why they
must be side-effect free. The phrasing is an ordinary overridable Cosmos
string, and a room's own `on go other` (section 11a) takes precedence over the
listed message. This replaces hand-writing a blocked message in every room.

## 15. Overriding Cosmos in practice

Four patterns, in increasing scope: change one message by handling the verb
on the object; change a verb everywhere with a top-level `on <verb>` rule;
add a verb with a `verb` declaration plus its `on <verb>` default (as the
Brass Lantern's pull and the Cloak's hang); or fork a Cosmos file by copying
it into the project and editing it, so the build uses the local copy. Most
games use only the first three; the fourth exists so Cosmos is never a
ceiling.

## 16. How the examples use Cosmos

The Brass Lantern:

- The cellar uses automatic light: with no `lit` of its own it is dark until
  the player brings the switched-on lantern, whose `lit` lights the room. The
  example's `on enter` additionally bounces the player back, a stricter
  custom behavior than standard darkness; both are valid.
- `switch_on` and `switch_off` are Cosmos verbs; the lantern's handlers
  replace the default messages, consuming the action.
- `pull` is an added verb; the lever's handler consumes it, so the default
  "Nothing obvious happens." never runs.
- `${turns}` reads the Cosmos turn counter, and the foyer's grain shows cheap
  scenery answering examine without an object.

Cloak of Darkness:

- The foyer blocks north with `on go north`, a room-level override at pipeline
  step 3, and carries a grain for the chandeliers.
- The cloak is `wearable` and starts `worn`; Cosmos's wear and take-off verbs
  manage `worn`, and putting it on the hook clears `worn` as part of put-on.
- The hook is a `supporter`; its child the cloak is on it and in scope, so
  `hook holds cloak` is the test the hook's examine uses.
- The bar overrides automatic light at the room: its `on enter` sets the room
  dark while the player holds the cloak and lit otherwise.
- The `disturbed` global, the each_turn counter, and the two `finish` endings
  are all language-level and need nothing from Cosmos beyond the turn loop.

## Appendix A: Cosmos-reserved names

Direction names: `north`, `south`, `east`, `west`, `northeast`, `northwest`,
`southeast`, `southwest`, `up`, `down`, `in`, `out`. The `go` verb also
reserves `other` as the blocked-direction fallback operand (`on go other`,
section 11a); it is not itself a direction.

Standard kinds: `thing`, `room`, `container`, `supporter`, `door`, `character`.

Standard boolean properties: `fixed`, `scenery`, `hidden`, `concealed`,
`wearable`, `worn`, `lit`, `edible`, `named`, `an`, `clear`, `seen`, `switchable`,
`openable`, `open`, `lockable`, `locked`, `visited`, `moved`, `animate`. The full
table with each one's usage is in 01 section 6.

Standard value properties: `name`, `words`, `desc`, `capacity`, `key`,
`score`, `max_score`, `turns`.

Standard action names: `look`, `examine`, `search`, `take`, `drop`, `put`,
`wear`, `take_off`, `inventory`, `go`, `enter`, `exit`, `open`, `close`,
`lock`, `unlock`, `switch_on`, `switch_off`, `push`, `pull`, `turn`, `give`,
`show`, `talk`, `wait`, `again`.

Summonable features: `extendedverbs`, `statusline`, `verbose_exits`,
`conversations`, `debug`, and `language`. Text compression is not a summonable
feature: the standard abbreviation set is always applied, and a story tunes it
with its own `abbreviations.granule` (`arcc --make-abbreviations`, then summoned by
name), which the text encoder reads as data rather than loading as runtime blocks
(docs/05 section 7).

## Appendix B: standard grammar lines

```
verb "look", "l"                  -> look
verb "examine", "x", "look at"    -> examine noun
verb "read"                       -> examine noun
verb "search"                     -> search noun
verb "take", "get", "pick up"     -> take noun
verb "drop", "put down"           -> drop noun
verb "put", "place"               -> put noun in noun
                                     put noun on noun
verb "wear", "don"                -> wear noun
verb "take off", "remove", "doff" -> take_off noun
verb "inventory", "i", "inv"      -> inventory
verb "go"                         -> go direction
verb "enter"                      -> enter noun
verb "exit", "out"                -> exit
verb "open"                       -> open noun
verb "close", "shut"              -> close noun
verb "lock"                       -> lock noun with noun
verb "unlock"                     -> unlock noun with noun
verb "switch on", "turn on"       -> switch_on noun
verb "switch off", "turn off"     -> switch_off noun
verb "push", "press"              -> push noun
verb "pull", "yank"               -> pull noun
verb "turn", "rotate"             -> turn noun
verb "give"                       -> give noun to noun
verb "show"                       -> show noun to noun
verb "talk to", "talk", "speak to" -> talk noun
verb "wait", "z"                  -> wait
verb "again", "g"                 -> again
```

The direction slot is special to GO: it matches a direction name and reads
the matching room property rather than resolving an object.
