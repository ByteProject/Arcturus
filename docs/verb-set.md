# Arcturus verb reference

Every verb Cosmos understands, its canonical action, and its default behavior.
The **Set** column marks where a verb lives: **S** is the standard library,
always present; **E** is the extended set, summoned with `summon.extendedverbs`
(docs/05). The verb-and-synonyms column lists exactly the words the library maps
to that action; the wording each verb prints is in the companion message
reference, docs/message-set.md, where every line is an overridable block.

- "flavor" means the default just prints a line, with no world effect; an object
  or room can override it for a real one (most-specific-wins).
- Synonyms are listed with the canonical verb; they all map to one action. A
  `... on/in`, `... to`, `... about` note shows the grammar, not extra words.
- Arcturus always shows full room descriptions, so there are no look modes
  (verbose/brief/superbrief), and the Inform meta cruft (notify, sorry, mild
  oaths) is not carried.

## Movement and space

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| go, walk, run (+ the directions, n/s/e/w/ne/nw/se/sw/u/d/in/out) | go | move through the room's exit, else "no exit that way" | S |
| enter, board | enter | enter a door, container, or supporter | S |
| exit, leave | exit | leave what you are in or on | S |
| climb, scale | climb | climb a thing, else a refusal | S |
| look, l | look | describe the room | S |

## Observing (sensory)

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| examine, x | examine | print the desc, else "nothing special" | S |
| read | examine | read text, or examine | S |
| search, frisk | search | list contents, else "nothing of interest" | E |
| touch, feel, pat | touch | "you feel nothing unexpected" (flavor) | S |
| smell, sniff | smell | "smells about as expected" (flavor) | S |
| listen, hear | listen | "nothing answers" (flavor) | S |
| taste, lick | taste | "best not" (flavor) | S |

## Carrying and giving

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| take, get, carry | take | take it, with the usual refusals (fixed, scenery, already have) | S |
| drop | drop | drop it here | S |
| put, place (... on/in) | put | onto a supporter or into an open container | S |
| insert (... in) | insert | into an open container (a sibling of put) | S |
| give, offer, feed, pay (... to) | give | offer to a living thing | S |
| show, display, present (... to) | show | show to a living thing | S |
| throw, chuck, toss, hurl (... at) | throw | throw at a target, usually futile | E |
| empty, drain (... into) | empty | tip a container out | E |

## Wearing

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| wear, don | wear | wear a wearable thing | S |
| remove, doff, disrobe, shed | take_off | take off a worn thing | S |

## Doors, containers, locks

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| open, uncover, unwrap | open | open it, with already/locked variants | S |
| close, shut, cover | close | close it | S |
| lock (... with) | lock | lock with a key, with the variants | S |
| unlock (... with) | unlock | unlock with a key | S |

## Operating and manipulating

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| switch, turn (+ on/off) | switch_on / switch_off | refused unless the object has an `on switch_on` / `on switch_off` handler (no built-in on/off effect) | S |
| push, press, shove | push | push it, usually no effect | S |
| pull, drag, yank | pull | pull it, usually no effect | S |
| turn, rotate, twist, screw, unscrew | turn | turn it, usually no effect | S |
| set, adjust (... to) | set | "set it to what?" | E |
| rub, polish, clean, wipe, scrub, dust, shine, buff | rub | "achieves nothing" (flavor) | E |
| squeeze, crush | squeeze | "nothing happens" (flavor) | E |
| tie, attach, fasten, secure (... to) | tie | "you can't tie that" | E |
| cut, chop, slice, prune, carve | cut | "that would achieve nothing" | E |
| dig, excavate | dig | "no use digging here" | E |
| fill | fill | "nothing to fill it with" | E |
| burn, ignite, torch, kindle | burn | "nothing here to burn it with" | E |
| blow | blow | "achieves nothing" (flavor) | E |

## Conversation (living things)

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| talk, talk to, greet | talk | "doesn't seem up for a conversation" | S |
| ask, interrogate, query (... about / for) | ask | runs the person's matching `topic`, else "stays mum on the subject" | E |
| tell, inform (... about) | tell | runs the person's matching `topic`, else "receives the news with indifference" | E |
| answer, respond | answer | "your words go unanswered" | E |
| shout, yell, scream, holler | shout | "no one answers" (flavor) | E |

ask and tell carry the Infocom-style topic dispatch: `ask <person> about
<subject>` (or `tell ... about`) scans for a `topic` the person answers to and,
if one is in view, runs its exchange; otherwise the verb speaks its flat default.
The subject is a topic word, not an object, so the grammar is one noun plus a
trailing preposition. When `summon.conversations` is present, the menu takes over
and this topic dispatch defers to it.

## Body, action, idle

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| attack, hit, break, kill, fight, smash | attack | "violence won't help here" | S |
| eat | eat | "that is not on the menu" | S |
| drink, sip, swallow | drink | "nothing here is worth a sip" | S |
| jump, hop | jump | flavor (your jump line) | S |
| wait, z | wait | "time slips by" | S |
| again, g | again | repeat the last command | S |
| kiss, hug, embrace | kiss | "now is hardly the moment" | S |
| sing | sing | "the room is unmoved" (flavor) | S |
| wave, brandish | wave | "you wave, to no effect" (flavor) | E |
| sit, rest | sit | "nothing here to sit on" | E |
| stand | stand | "you are already standing" | E |
| sleep, nap, doze | sleep | "no place to nod off" (flavor) | E |
| swim, dive, paddle | swim | "no water deep enough" | E |
| swing | swing | "nothing to swing on" | E |
| think, ponder, consider | think | "a fine idea, in principle" (flavor) | E |
| pray, worship | pray | "you murmur a few words" (flavor) | E |
| buy, purchase | buy | "nothing here is for sale" | E |
| consult, reference (... about) | consult | "nothing of interest there" | E |

## Meta and system

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| inventory, i, inv | inventory | list what you carry | S |
| score | score | show the score | S |
| fullscore, full | fullscore | break the score down | E |
| save | save | save the game | S |
| restore | restore | restore a saved game | S |
| restart | restart | restart from the beginning | S |
| undo | undo | undo the last turn | S |
| oops | oops | correct the last word you mistyped | S |
| quit, q | quit | confirm, then end | S |
| xyzzy | xyzzy | a wink (flavor) | S |
