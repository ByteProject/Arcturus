# Arcturus message reference

Every default message Cosmos prints, listed by the block that prints it, so you
know what to redefine to change a line. Each is an overridable prelude block:
redefine `block <name>()` in your story and yours wins (a granule's own messages
are forked instead; docs/05). Interpolation: `${the noun}` prints the object with
its article, `${The noun}` capitalizes it, `${the second}` is the second noun
(give X to Y), and `${score}`, `${max_score}`, `${turns}` print numbers. The
standard messages come first; the extended-verb messages, which ship with
`summon.extendedverbs`, follow at the end. The companion verb reference is
docs/verb-set.md.

## Parser

| Block | When it fires | Wording |
|---|---|---|
| msg_no_verb | first word is not a verb or direction | Those words don't add up to anything. |
| msg_extra_words | a verb that takes no noun is given extra words (jump north, look cloak) | You lost me after that. |
| msg_cant_see | a noun was named but nothing matches in scope | You see nothing of the sort here. |
| msg_no_it | "it"/"them" with nothing to refer to | You'll have to say what you mean. |
| msg_be_specific | an ambiguous noun, after the ask got no usable answer | You'll have to be more specific. |
| line_which_open | the disambiguation question's opening | Which do you mean, |
| line_which_or | the connector before the last candidate | or |
| line_which_item | one candidate (German declines it: den Hammer) | ${the obj} |
| line_which_end | the question's close | ? |
| msg_nothing_again | "again" with no previous command | There's nothing to repeat. |
| msg_only_animate | give/show/talk aimed at a thing, not a person | If you continue talking to objects, it might be time for another therapy session. |

## Room and light

| Block | When | Wording |
|---|---|---|
| msg_dark_room | the room is unlit | Pitch black. Even your hands have gone missing. |
| msg_too_dark | acting on something in the dark | It's too dark to make anything out. |

## Movement

| Block | When | Wording |
|---|---|---|
| msg_cant_go | no exit that way | There's no exit in that direction. |
| msg_no_direction | "go" with no direction | Which way? |
| msg_cant_enter | can't enter the thing | You can't get inside ${the noun}. |
| msg_already_there | enter where you already are | You're already there. |
| msg_not_inside | "exit" while not in anything | You aren't inside anything to leave. |
| msg_cant_climb | climb something unclimbable | ${The noun} isn't for climbing. |

## Sensory

| Block | When | Wording |
|---|---|---|
| msg_examine_self | examine yourself with no player.desc set | Are we going to admire ourselves for a while or do we play an adventure game? |
| msg_nothing_special | examine, no description | Nothing about ${the noun} rewards a closer look. |
| msg_touch | touch, default | You touch ${the noun}. You feel nothing that your eyes didn't already see. |
| msg_smell | smell, default | ${The noun} smells about as you'd expect. |
| msg_listen | listen, default | You listen. Nothing answers. |
| msg_taste | taste, default | Best not. |

## Carrying and giving

| Block | When | Wording |
|---|---|---|
| msg_taken | take, success | Got it. |
| msg_fixed | take a fixed thing | ${The noun} stays exactly where it is. |
| msg_animate_refuses | take an animate thing (a character) | ${The noun} has other ideas. |
| msg_scenery | take a scenery object, or any verb a grain does not answer | Just some scenery. Don't worry about it. |
| msg_have_it | take what you already hold | You already have ${the noun}. |
| msg_take_self | take yourself | You keep a firm grip on yourself. |
| msg_dropped | drop, success | Down it goes. |
| msg_not_holding | drop what you don't hold | You aren't carrying ${the noun}. |
| msg_done | put on/in, success | Done. |
| msg_put_where | put with no destination | On what, or in what? |
| msg_cant_put | the target won't hold it | ${The second} won't hold it. |
| msg_closed | put into a closed container | ${The second} is shut. |
| msg_give | give to a person, default | ${The second} doesn't want ${the noun}. Outrageous. |
| msg_show | show to a person, default | Seems like ${the second} is not really into that. |
| msg_to_whom | give/show with no recipient named | To whom? |

## Wearing

| Block | When | Wording |
|---|---|---|
| msg_worn | wear, success | On it goes. |
| msg_already_worn | wear what you wear | You're already wearing ${the noun}. |
| msg_cant_wear | wear the unwearable | ${The noun} was never meant to be worn. |
| msg_removed | take off, success | Off it comes. |
| msg_not_worn | take off what you don't wear | You aren't wearing ${the noun}. |

## Doors, containers, locks

| Block | When | Wording |
|---|---|---|
| msg_opened | open, success | Open. |
| msg_already_open | open what's open | ${The noun} is already open. |
| msg_cant_open | open the unopenable | ${The noun} doesn't open. |
| msg_open_locked | open a locked thing | ${The noun} is locked. |
| msg_door_locked | walk into a locked door | ${The d} is locked. |
| msg_door_shut | walk into a shut door | ${The d} is shut. You open it first. |
| msg_closed_it | close, success | Shut. |
| msg_already_shut | close what's shut | ${The noun} is already shut. |
| msg_cant_close | close the uncloseable | ${The noun} doesn't close. |
| msg_locked | lock, success | Locked. |
| msg_cant_lock | lock the unlockable | ${The noun} doesn't lock. |
| msg_close_first | lock something open | You'd have to close ${the noun} first. |
| msg_wrong_key | the key doesn't fit | ${The second} doesn't fit. |
| msg_unlocked | unlock, success | Unlocked. |
| msg_cant_unlock | unlock the unlockable | ${The noun} doesn't unlock. |
| msg_open_first | reach for something known to be shut inside a closed container | You'll have to open ${the shut_in} first. |

## Operating

| Block | When | Wording |
|---|---|---|
| msg_no_switch | switch a thing with no `on switch_on`/`switch_off` handler (`switchable` alone adds no behavior) | ${The noun} isn't the switching kind. |
| msg_already_on | switch on what's on | ${The noun} is already on. |
| msg_already_off | switch off what's off | ${The noun} is already off. |
| msg_no_effect | push, pull, turn, default | ${The noun} holds firm. |

## Body, action, idle

| Block | When | Wording |
|---|---|---|
| msg_attack | attack, default | Hitting things rarely helps, and it won't start now. |
| msg_eat | eat the inedible | ${The noun} is not on the menu. |
| msg_drink | drink, default | Nothing here is worth a sip. |
| msg_jump | jump | You hop on the spot. Nothing comes of it, but it felt good. |
| msg_wait | wait | Time slips by. |
| msg_kiss | kiss, default | Now is hardly the moment. |
| msg_sing | sing | You manage a few bars. The room is unmoved. |

## Conversation

| Block | When | Wording |
|---|---|---|
| msg_no_talk | talk to a person, default | ${The noun} doesn't seem up for a conversation. |
| msg_ask | infocom_talking only: ask with no topic match (other games use the talk brush-off) | ${The noun} stays mum on the subject. |
| msg_tell | infocom_talking only: tell with no topic match | ${The noun} receives the news with magnificent indifference. |
| msg_answer | infocom_talking only: answer | Your words go unanswered. |
| msg_use_talk | TELL in a menu game (the hint; ASK opens the menu itself) | To get anywhere with ${the noun}, just TALK TO ${the noun}. |
| line_you | the framing of a `you "..."` topic line | You: "..." |
| line_reply | the framing of a `reply "..."` topic line | ${The speaker}: "..." |
| line_end | the close of any topic line | "... |

(talk aimed at a thing falls through to msg_only_animate, above. line_you,
line_reply, and line_end frame the `you` / `reply` conversation sugar: the
speaker label, the separator, and the auto-quotes live here, so the wording is
overridable and translatable and works whether or not the conversations granule
is summoned.)

## Inventory

| Block | When | Wording |
|---|---|---|
| msg_carrying | inventory header, holding something | You're carrying: |
| msg_empty_handed | inventory, holding nothing | You're carrying precisely nothing. |
| (worn tag) | a worn item in the list | (worn) |

## Meta

| Block | When | Wording |
|---|---|---|
| confirm_quit | quit confirmation | Are you sure you want to quit? |
| msg_farewell | quit confirmed | We'll leave it there. |
| msg_score | score | You have scored ${score} of a possible ${max_score}, in ${turns} turns. ("in 1 turn" for the first; with a `ranks` ladder, ", which earns you the rank of <rank>" before the period.) |
| msg_saved | save ok | Saved. |
| msg_save_failed | save failed | Something went wrong with that save. |
| msg_restore_failed | restore failed | That save couldn't be restored. |
| msg_confirm_restart | restart | Start over from the very beginning? |
| msg_undone | undo ok | Taken back. |
| msg_cant_undo | nothing to undo | There's nothing to take back. |
| msg_cant_oops | oops with nothing to correct | There's nothing to put right. |
| msg_xyzzy | xyzzy | Nothing happens, but you feel briefly clever. |

## Take all (summon.takeall)

Granule messages, changed by forking the granule (docs/05). The per-item
lines are the standard take/drop responses after the item's name ("brass
lamp: Got it.").

| Block | When it fires | Wording |
|---|---|---|
| msg_all_none | take all, nothing worth taking here | There's nothing here worth taking. |
| msg_all_none_in | take all from X, nothing inside worth taking | There's nothing in ${the source} worth taking. |
| msg_all_verb | "all" with a verb that cannot sweep (eat all) | One thing at a time. |
| (reused) | drop all with empty hands | msg_empty_handed |
| (reused) | take all from a shut container | msg_closed |

## Extended verbs (summon.extendedverbs)

These ship only when the granule is summoned, and (being a granule's own blocks)
are changed by forking the granule rather than redefining in a story.

| Block | When | Wording |
|---|---|---|
| msg_search_nothing | search, nothing of note (or an empty container/supporter) | Nothing worth the effort turns up. |
| msg_search_closed | search a closed container | Schroedinger's loot remains safe, mostly because ${the noun} is completely shut. |
| msg_throw | throw something, default | Gravity has already been discovered; there is no need for you to test it again. |
| msg_rub | rub, polish, clean, default | You give ${the noun} a thorough buffing. It continues to judge you in silence. |
| msg_squeeze | squeeze, crush, default | You give ${the noun} an uncomfortably long squeeze. Let's just move on. |
| msg_tie | tie, attach, fasten, default | Stringing things together won't help you unravel this particular problem. |
| msg_cut | cut, chop, slice, default | ${The noun} seems firmly opposed to being cut. |
| msg_fill | fill, default | ${The noun} remains empty, mostly because you don't have anything to put in it. |
| msg_burn | burn, ignite, default | Starting a fire here seems like a quick way to create a much bigger problem. |
| msg_blow | blow, default | You unleash a mighty breath. The local climate remains entirely unaffected. |
| msg_set | set X to Y, default | Set it to what, exactly? |
| msg_empty | empty a container, default | You up-end ${the noun}. Nothing of note falls out. |
| msg_buy | buy, purchase, default | Your wealth is profoundly useless in this exact situation. |
| msg_consult | consult X about Y, default | ${The noun} has nothing to say on the matter. |
| msg_dig | dig | The ground keeps its secrets. |
| msg_wave | wave | You wave. The room declines to wave back. |
| msg_sit | sit | Nothing here invites sitting. |
| msg_stand | stand | You're already on your feet. |
| msg_sleep | sleep, nap | You consider curling up into a ball and ignoring the plot, but your sense of duty rudely keeps you awake. |
| msg_swim | swim, dive | There's nowhere here to swim. |
| msg_swing | swing | There's nothing here to swing on. |
| msg_think | think, ponder | A fine idea. Nothing comes of it. |
| msg_pray | pray | You ask the heavens for a hint. The heavens remain conspicuously silent. |
| msg_shout | shout, yell, scream | You test the location's acoustics with a loud yell. The results are entirely underwhelming. |

