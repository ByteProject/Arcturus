# Arcturus standard message set

Working doc for B5: the default messages for the standard verbs and the parser,
in the agreed voice (between warm and witty, leaning witty), referring to the
noun where it reads better. Redline any wording. `${the noun}` prints the object
with its article; `${The noun}` capitalizes it; `${the second}` is the second
noun (give X to Y).

Only the standard set is here. The extended verbs (ask/tell/answer, kiss is
standard but squeeze/blow/burn/buy/consult/swim/etc.) get their messages with the
`summon.extendedverbs` granule.

## Parser

| Block | When it fires | Wording |
|---|---|---|
| msg_no_verb | first word is not a verb or direction | Those words don't add up to anything. |
| msg_cant_see | a noun was named but nothing matches in scope | You see nothing of the sort here. |
| msg_no_it | "it"/"them" with nothing to refer to | You'll have to say what you mean. |
| msg_be_specific | the noun is ambiguous | You'll have to be more specific. |
| msg_nothing_again | "again" with no previous command | There's nothing to repeat. |
| msg_only_animate | give/show/talk aimed at a thing, not a person | You'd do better trying that with something alive. |

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
| msg_nothing_special | examine, no description | Nothing about ${the noun} rewards a closer look. |
| msg_touch | touch, default | You touch ${the noun}. It feels just as it looks. |
| msg_smell | smell, default | ${The noun} smells about as you'd expect. |
| msg_listen | listen, default | You listen. Nothing answers. |
| msg_taste | taste, default | Best not. |

## Carrying and giving

| Block | When | Wording |
|---|---|---|
| msg_taken | take, success | Got it. |
| msg_fixed | take a fixed thing | ${The noun} stays exactly where it is. |
| msg_take_scenery | take scenery | ${The noun} is hardly worth carrying off. |
| msg_have_it | take what you already hold | You already have ${the noun}. |
| msg_take_self | take yourself | You keep a firm grip on yourself. |
| msg_dropped | drop, success | Down it goes. |
| msg_not_holding | drop what you don't hold | You aren't carrying ${the noun}. |
| msg_done | put on/in, success | Done. |
| msg_put_where | put with no destination | On what, or in what? |
| msg_cant_put | the target won't hold it | ${The noun} won't hold it. |
| msg_closed | put into a closed container | ${The noun} is shut. |
| msg_give | give to a person, default | ${The noun} doesn't want ${the second}, thanks all the same. |
| msg_show | show to a person, default | ${The noun} takes a look, unimpressed. |

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
| msg_closed_it | close, success | Shut. |
| msg_already_shut | close what's shut | ${The noun} is already shut. |
| msg_cant_close | close the uncloseable | ${The noun} doesn't close. |
| msg_locked | lock, success | Locked. |
| msg_cant_lock | lock the unlockable | ${The noun} doesn't lock. |
| msg_close_first | lock something open | You'd have to close ${the noun} first. |
| msg_wrong_key | the key doesn't fit | ${The second} doesn't fit. |
| msg_unlocked | unlock, success | Unlocked. |
| msg_cant_unlock | unlock the unlockable | ${The noun} doesn't unlock. |

## Operating

| Block | When | Wording |
|---|---|---|
| msg_no_switch | switch on/off a non-switch | ${The noun} isn't the switching kind. |
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

(talk aimed at a thing falls through to msg_only_animate, above.)

## Inventory

| Block | When | Wording |
|---|---|---|
| msg_carrying | inventory header, holding something | You're carrying: |
| msg_empty_handed | inventory, holding nothing | You're carrying precisely nothing. |
| (worn tag) | a worn item in the list | (worn) |

## Meta

| Block | When | Wording |
|---|---|---|
| msg_confirm_quit | quit | Are you sure you want to quit? |
| msg_farewell | quit confirmed | We'll leave it there. |
| msg_score | score | You have scored ${score} of a possible ${max_score}. |
| msg_saved | save ok | Saved. |
| msg_save_failed | save failed | The save didn't take. |
| msg_restore_failed | restore failed | That save couldn't be restored. |
| msg_confirm_restart | restart | Start over from the very beginning? |
| msg_undone | undo ok | Taken back. |
| msg_cant_undo | nothing to undo | There's nothing to take back. |
| msg_xyzzy | xyzzy | Nothing happens, but you feel briefly clever. |
