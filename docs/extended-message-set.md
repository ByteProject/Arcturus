# Arcturus extended message set

Working doc for the `summon.extendedverbs` granule: the default messages for the
extended verbs (docs/verb-set.md, the E column), in the same voice as the standard
set (between warm and witty, leaning witty), referring to the noun where it reads
better. Redline any wording. `${the noun}` prints the object with its article;
`${The noun}` capitalizes it; `${score}`, `${max_score}`, `${turns}` print numbers.

These ship only when the granule is summoned, and an author reskins any line by
redefining its `msg_*` block in the story. The richer topic-conversation replies
(ask/tell finding an author-defined answer, the talk menu) arrive with the topic
system; only the flat defaults are here.

## Rummaging and acting on objects

| Block | When | Wording |
|---|---|---|
| msg_search_nothing | search, nothing of note (or an empty container/supporter) | Nothing worth the effort turns up. |
| msg_search_closed | search a closed container | ${The noun} is shut. |
| msg_throw | throw something, default | You think better of it. |
| msg_rub | rub, polish, clean, default | You polish ${the noun}. It remains unimpressed. |
| msg_squeeze | squeeze, crush, default | ${The noun} keeps its counsel. |
| msg_tie | tie, attach, fasten, default | Knots won't help you here. |
| msg_cut | cut, chop, slice, default | Cutting it solves nothing. |
| msg_fill | fill, default | There's nothing here to fill ${the noun} with. |
| msg_burn | burn, ignite, default | Arson solves nothing here. |
| msg_blow | blow, default | You blow. The dust is briefly impressed. |
| msg_set | set X to Y, default | Set it to what, exactly? |
| msg_empty | empty a container, default | You up-end ${the noun}. Nothing of note falls out. |
| msg_buy | buy, purchase, default | Nothing here is for sale. |
| msg_consult | consult X about Y, default | ${The noun} has nothing to say on the matter. |

## Body and idle

| Block | When | Wording |
|---|---|---|
| msg_dig | dig | The ground keeps its secrets. |
| msg_wave | wave | You wave. The room declines to wave back. |
| msg_sit | sit | Nothing here invites sitting. |
| msg_stand | stand | You're already on your feet. |
| msg_sleep | sleep, nap | This is no place to nod off. |
| msg_swim | swim, dive | There's nowhere here to swim. |
| msg_swing | swing | There's nothing here to swing on. |
| msg_think | think, ponder | A fine idea. Nothing comes of it. |
| msg_pray | pray | You murmur a few words. The silence, at least, is respectful. |
| msg_shout | shout, yell, scream | You shout. The echo is unimpressed. |

## Conversation (flat defaults; the topic system replaces these per topic)

| Block | When | Wording |
|---|---|---|
| msg_ask | ask a person about a topic, default | ${The noun} stays mum on the subject. |
| msg_tell | tell a person about a topic, default | ${The noun} receives the news with magnificent indifference. |
| msg_answer | answer, respond, default | Your words go unanswered. |

## Meta

| Block | When | Wording |
|---|---|---|
| msg_fullscore | full score breakdown (no turn taken) | You have scored ${score} of a possible ${max_score}, in ${turns} turns. |
