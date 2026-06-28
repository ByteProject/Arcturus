# Arcturus verb set: standard or extended

Working doc for B5. Decide which verbs ship in the **standard** library (always
bundled, what the size benchmark measures) and which go in the **extended** set
(`summon.extendedverbs`, opt in).

How to use this: in the **Set** column, write **S** (standard) or **E**
(extended) for each verb. The column is pre-filled with my proposal, but change
anything. We do not need to match PunyInform's split; this is ours.

Notes:
- "flavor" = the default just prints a message, with no world effect (an author
  can still override it per object or room).
- Synonyms are listed with the canonical verb; they all map to one action.
- The sensory verbs are left in S because you want them there.
- Arcturus shows full room descriptions always, so there are no look modes
  (verbose/brief/superbrief); those verbs are dropped. The Inform meta cruft
  (notify, sorry, mild oaths) is dropped too.

## Movement and space

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| go, walk, run (+ the directions, n/s/e/w/ne/nw/se/sw/u/d/in/out) | go | move through the room's exit, else "no exit that way" | S |
| enter, get in, get on | enter | enter a door, container, or supporter | S |
| exit, out, leave, get out, get off | exit | leave what you are in or on | S |
| climb, scale | climb | climb a thing, else a refusal | S |
| look, l | look | describe the room | S |

## Observing (sensory)

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| examine, x, look at, watch | examine | print the desc, else "nothing special" | S |
| read | examine | read text, or examine | S |
| search, look in, look inside | search | list contents, else "nothing of interest" | E |
| look under | look_under | "nothing under it" | E |
| touch, feel, pat | touch | "you feel nothing unexpected" (flavor) | S |
| smell, sniff | smell | "smells about as expected" (flavor) | S |
| listen, hear | listen | "nothing answers" (flavor) | S |
| taste, lick | taste | "best not" (flavor) | S |

## Carrying and giving

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| take, get, grab, pick up, carry, hold | take | take it, with the usual refusals (fixed, scenery, already have) | S |
| drop, discard, put down | drop | drop it here | S |
| put, place, set ... on/in | put | onto a supporter or into an open container | S |
| insert ... in | insert | into an open container (a sibling of put) | S |
| give, offer, feed, pay ... to | give | offer to a living thing | S |
| show, display, present ... to | show | show to a living thing | S |
| throw ... at | throw | throw at a target, usually futile | E |
| empty, empty out, empty ... into | empty | tip a container out | E |

## Wearing

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| wear, don, put on | wear | wear a wearable thing | S |
| remove, doff, disrobe, shed, take off | take_off | take off a worn thing | S |

## Doors, containers, locks

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| open, uncover, unwrap | open | open it, with already/locked variants | S |
| close, shut, cover | close | close it | S |
| lock ... with | lock | lock with a key, with the variants | S |
| unlock ... with | unlock | unlock with a key | S |

## Operating and manipulating

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| switch on, turn on | switch_on | turn a switchable thing on | S |
| switch off, turn off | switch_off | turn it off | S |
| push, press, shove, move | push | push it, usually no effect | S |
| pull, drag, yank | pull | pull it, usually no effect | S |
| turn, rotate, twist, screw, unscrew | turn | turn it, usually no effect | S |
| set ... to | set | "set it to what?" | E |
| rub, clean, polish, wipe, scrub, dust, shine | rub | "achieves nothing" (flavor) | E |
| squeeze, crush | squeeze | "nothing happens" (flavor) | E |
| tie, attach, fasten, fix ... to | tie | "you can't tie that" | E |
| cut, chop, slice, prune | cut | "that would achieve nothing" | E |
| dig | dig | "no use digging here" | E |
| fill | fill | "nothing to fill it with" | E |
| burn, light | burn | "nothing here to burn it with" | E |
| blow | blow | "achieves nothing" (flavor) | E |

## Conversation (living things)

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| talk, talk to, greet | talk | "doesn't seem up for a conversation" | S |
| ask ... about | ask | "has nothing to say on the matter" | E |
| ask ... for | ask_for | "declines to hand it over" | E |
| tell ... about | tell | "this provokes no reaction" | E |
| answer, say ... to | answer | "no reaction" | E |
| shout, yell, scream | shout | "no one answers" (flavor) | E |

## Body, action, idle

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| attack, hit, break, kill, fight, smash, destroy | attack | "violence won't help here" | S |
| eat | eat | "that is not on the menu" | S |
| drink, sip, swallow | drink | "nothing here is worth a sip" | S |
| jump, hop | jump | flavor (your jump line) | S |
| wait, z | wait | "time slips by" | S |
| again, g | again | repeat the last command | S |
| kiss, hug, embrace | kiss | "now is hardly the moment" | S |
| wave, wave hands | wave | "you wave, to no effect" (flavor) | E |
| sit, sit on, lie | sit | "nothing here to sit on" | E |
| stand, get up | stand | "you are already standing" | E |
| sleep, nap | sleep | "no place to nod off" (flavor) | E |
| swim | swim | "no water deep enough" | E |
| swing | swing | "nothing to swing on" | E |
| sing | sing | "the room is unmoved" (flavor) | S |
| think, ponder | think | "a fine idea, in principle" (flavor) | E |
| pray | pray | "you murmur a few words" (flavor) | E |
| buy, purchase | buy | "nothing here is for sale" | E |
| consult ... about | consult | "nothing of interest there" | E |

## Meta and system

| Verb and synonyms | Action | Default behavior | Set |
|---|---|---|---|
| inventory, i, inv | inventory | list what you carry | S |
| score | score | show the score | S |
| full score, fullscore | fullscore | break the score down | E |
| save | save | save the game | S |
| restore | restore | restore a saved game | S |
| restart | restart | restart from the beginning | S |
| undo | undo | undo the last turn | S |
| quit, q | quit | confirm, then end | S |
| xyzzy | xyzzy | a wink (flavor) | S |
