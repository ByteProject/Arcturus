# test_sizes.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The size-regression gate. Smallest possible z-code is a charter objective
(docs/00 section 5), so every example's story-file size is pinned here as a
ceiling. A build that comes in SMALLER passes (lower the ceiling when an
improvement lands, so the win is locked in); a build that comes in LARGER fails,
and the ceiling may only be raised consciously, in the same commit as the change
that grew the story and with the growth explained in the commit message. That
keeps size regressions from landing silently, the same way the walkthrough tests
keep behavior regressions out.

The two conformance games are additionally checked against the PunyInform
benchmark (docs/00 section 5; the Puny Cloak of Darkness build is ~27K,
standard verb set only)."""

import os

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")

# Byte ceilings per example, as of arcc 0.9.0 / Cosmos 0.13.2 (2026-07-04).
# 2026-07-22 (foresight act two): the shut-container and shut-door refusal
# seams (two small core blocks and their calls) plus open_probe, the open
# handler's factored guard chain. The repairs themselves cost only
# foresight summoners.
# 2026-07-22 (buffers): +228 everywhere, pure dynamic memory. The input
# buffers grew from 60 chars / 12 words to 120 / 24 (with the oops and
# disambiguation backups that shadow them): chained lines and noun lists
# made long commands ordinary, and a German chain died at the old wall
# mid-word (the field report).
# 2026-07-22 (session verbs): +12 to +20, the VERSION verb in every game
# (the bug-report command). NOTIFY costs only games that enable it (the
# coupled rule drops the verb, the handler, and the dictionary word
# otherwise); the swear family costs only its extendedverbs selectors.
# 2026-07-22 (shiftable, pick up): +12 to +24. PICK joined the take family
# (with the up-direction remap), and the push-travel path folds away in
# games with nothing shiftable; push stays on the flag model, no direction
# grammar line needed (way binds globally), so ASK remains the one tabled
# standard verb.
# 2026-07-22 (phase 6 breadth): +160 to +228 everywhere. subject_typed is
# core now (CONSULT and infocom_talking share one scanner), typed YES/NO
# landed as standard actions with their flavor lines, and LIGHT joined the
# switch family. Consult itself costs only extendedverbs summoners.
# 2026-07-22 (noun lists): "put coin and nail in box", +508 to +636
# everywhere: the list-aware chain splitter, the per-item runner, and
# sweep_one now living in every game (each listed item is a full turn,
# the chain rule). Core grammar, no fold: put/give/show are standard.
# 2026-07-22 (foresight): the take probe, +152 to +328 everywhere. The take
# handler now refuses through take_probe + speak_take_refusal, ONE guard
# chain shared with the foresight repair so the two can never drift (the
# design ruling); every game carries the factored routines whether or not
# it summons foresight. The granule itself costs only its summoners.
# 2026-07-22 (later): the verb contract (requires, the overhaul phase 2),
# +104 to +128 everywhere: give and show declare their requirements in every
# game (requires_map, the check, minus the relocated inline animate tests).
# Unused requirement kinds fold per bit (req_*), which halved the first cut.
# 2026-07-22: every ceiling +24 to +36. The noun matcher no longer dissolves
# unknown words into the best-scoring object (GIVE MERCHANT THE XYZZYPLUGH
# resolved to the merchant; the field report), so every game carries the
# check, and the idiom fillers ("of", takeall's "from") are now declared
# dictionary words instead of tolerated garbage.
# 2026-07-25 (the sealed-take seam): +44 to +48 everywhere. The take
# handler routes its why-4 refusal through take_sealed_refused, the seam
# summon.foresight overrides to open a closed CLEAR container on the same
# promise discipline the give-chain always had (the direct take owed the
# player the same manners; the gap was found writing the foresight
# example). Unsummoned behavior is the exact old refusal; the seam block
# and one branch are the cost.
# 2026-07-26 (the bare-command ask): -260 to -444 EVERYWHERE, repriced
# down to lock the win in. The verbs overhaul's second half: the ask
# moved into the loop (one central "The verb <word> requires you to be
# more specific.", echoing the verb as typed), and the 40+ per-handler
# noun/second ask stanzas were deleted with msg_put_where and
# msg_to_whom. Custom verbs now ask like standard ones (the silence
# bug), and verb_trigger costs nothing in a game that never reads it
# (the any_verb_read fold).
# 2026-07-26 (restless, and timer stops): +4 to +8 ONLY in games that
# arm a timer (the reload word now carries the armed identity, a
# one-shot's interval negated, so `stop after/every N turns do block`
# can match the exact triple), and -4 on two examples (branch luck).
# Every game without a restless object stays byte-identical: the
# performer walk, the mute buffer, and the scope-walk skip all fold
# away behind any_restless.
# 2026-07-26 (the light watch): +90 to +110 ONLY in games where
# darkness can happen (any_dark): a turn that lifts darkness without
# moving describes the room the player can suddenly see, and a turn
# that kills the light says so (the field report: LIGHT LANTERN in
# the dark answered only the lantern's line). Always-lit games are
# byte-identical: the snapshot rides the spent undo local behind the
# fold, and DCE reclaims the watch block.
CEILINGS = {
    "features/yes-no.storyarc": 17824,  # 2026-07-25 new example (typed answers, when-guarded questions)
    "features/press-any-key.storyarc": 18456,  # 2026-07-25 new example (read_key as gate and as value)
    "features/shiftable.storyarc": 17964,  # 2026-07-25 new example (push the barrel north, the player follows)
    "features/enhance-redefine.storyarc": 18264,  # 2026-07-25 new example (grow a family, replace one whole)
    "features/consult-about.storyarc": 18464,  # 2026-07-25 new example (reference books via inline topics)
    "features/session-verbs.storyarc": 18152,  # 2026-07-25 new example (VERSION, coupled NOTIFY, the swear family)
    "features/vary.storyarc": 19324,  # 2026-07-25 new example (the vary showcase incl. varied topic replies)
    "features/foresight.storyarc": 19208,  # 2026-07-25 new example (the foresight showcase; its writing found the sealed-take gap)
    "features/beyond.storyarc": 20084,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/alter.storyarc": 18676,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/catalogs.storyarc": 18616,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/matrix.storyarc": 18972,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/direction-grammar.storyarc": 18008,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/scenery-contents.storyarc": 18660,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/nautical.storyarc": 18472,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    # 2026-07-04 (Stefan's ruling, superseding the same day's FULL move):
    # there is NO fullscore verb; SCORE is the one score verb and reports
    # score, max, turns, and rank in one line. Pool labels stay in the
    # source and ledger but never reach the story file. teleport(dest)
    # joined the standard blocks (the go handler shares its arrive(), so
    # walking pays for it; unused teleport folds away). Before that, the
    # 2026-07-03 batch: recipient dispatch (~40), the start-title skip
    # (~25), show_tag (~20); chaining, disambiguation, noun lists with
    # noise words, all core parser features every game carries.
    # 2026-07-07 (pronouns): the parser now binds a pronoun for the SECOND noun
    # too, so after "show coin to bob" HIM refers to Bob. +4 to +20 bytes/game.
    # 2026-07-07 (reversed dative): GIVE/SHOW accept the reversed order (GIVE BOB
    # COIN), with the reverse split (inline per pack) and the shared probe_noun.
    # +~196 bytes for a pack that declares a reverse line. English got it first;
    # German followed (gib Bob die Muenze, its natural dative), +196 here. Spanish
    # is UNCHANGED: its dative uses the mandatory personal "a" (da a Maria la
    # moneda) or clitics, not the adjacent-noun form, so no reverse line applies.
    # 2026-07-07 (self fix): an owned handler now takes its self object as an
    # argument so a kind handler sees the right instance (docs/01 9); +0 to +20
    # bytes/game for the per-call argument.
    # 2026-07-07 (positional grammar, docs/02 8c): a verb the flag model cannot
    # represent (dig in noun with held; look_under under noun) compiles to a
    # grammar table and a positional matcher. Every ceiling here is UNCHANGED:
    # the whole path folds away (any_tables) unless a game declares such a
    # verb. features/grammar.storyarc is the one that does, and its ceiling
    # (14340 vs the ~13400 feature baseline) is the matcher's full price.
    # 2026-07-08 (total articles): ${the x} and ${a x} print "nothing"
    # (nichts, nada) for an unresolved object instead of an illegal
    # print_obj 0 (Actaea halts on those; the same field game). A few
    # bytes per pack.
    # 2026-07-08 (total containment): `X in Y` and `X holds Y` gate the
    # child operand on nothing BEFORE the @jin (and before Y evaluates), so
    # a handler testing an unresolved noun is false instead of an illegal
    # object-0 @jin (a field game warned on every turn). Compile-time
    # object children skip the gate.
    # 2026-07-08 (move-safe for each): the tree loop caches the next sibling
    # BEFORE its body runs, so `for each x in box / move x to ...` (emptying a
    # container, the classic shape) terminates instead of following the moved
    # object's rewritten sibling pointer forever (a field report caught the
    # PLAYER swept into a bucket's iteration). +52 to +68 bytes per game, one
    # cached-next per for-each site; correctness over bytes.
    # 2026-07-07 (GET idioms): English reads GET IN/INTO X as enter, GET
    # ON X as enter (the take+on particle), GET OUT OF/DOWN FROM X and GET
    # OFF X-you-are-in as exit, and a bare GET IN/OUT/UP/DOWN as go; "into"
    # joined the in-direction vocabulary, which also splits PUT X INTO Y
    # properly. All in remap_action/compound in the English pack: +68 to +84
    # bytes per English game; German and Spanish are UNCHANGED (idioms are
    # language, each pack writes its own).
    # 2026-07-07 (enter consumes): `on enter` on a THING is the ENTER verb, an
    # ordinary consumable action, no longer mistaken for the room-arrival
    # event (whose results are ignored). react_free's enter branch gains the
    # consume checks: +8 on the one ceiling that had zero slack
    # (features/grammar 14340 -> 14348); every other example absorbed it.
    "beispiel-deutsch.storyarc": 24160,  # 2026-07-21 the status bar names darkness (In the dark / Im Dunkeln / A oscuras) instead of spoiling an unseen room's name, +40 in games where darkness is reachable (any_dark); always-lit games are byte-identical (the fold test); previously 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "brass-lantern.storyarc": 19240,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "cloak-of-darkness.storyarc": 20280,  # 2026-07-21 the status bar names darkness (In the dark / Im Dunkeln / A oscuras) instead of spoiling an unseen room's name, +40 in games where darkness is reachable (any_dark); always-lit games are byte-identical (the fold test); previously 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "ejemplo-espanol.storyarc": 23000,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/computed-properties.storyarc": 17712,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/containers.storyarc": 18012,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/daemons-and-timers.storyarc": 19308,  # 2026-07-26 the showcase pays for what it shows: a second room, the restless apprentice, the performer walk, the mute buffer, TURN OFF CLOCK
    "features/doors-and-locks.storyarc": 17624,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/appearance.storyarc": 18392,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/components.storyarc": 17816,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/perform.storyarc": 17880,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/grains.storyarc": 17760,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/handlers.storyarc": 18856,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/grammar.storyarc": 18024,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/introproperty.storyarc": 18940,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/kinds-and-inheritance.storyarc": 17680,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/on-other.storyarc": 17560,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/zcolor.storyarc": 17952,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/scoring.storyarc": 19916,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/spans.storyarc": 17748,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "features/vehicles.storyarc": 18288,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/ambience.storyarc": 19724,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/conversations.storyarc": 19380,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/extended-verbs.storyarc": 20452,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/infocom-interrogation.storyarc": 19896,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/quotes.storyarc": 17956,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/take-all.storyarc": 19608,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/plurals.storyarc": 18540,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/statusline.storyarc": 17684,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
    "granules/verbose-exits.storyarc": 17952,  # 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing
}

# The z8 build of the same game: only the header version byte, the file-length
# scale, and the packed-address unit differ, so its size moves with the z5 one.
CLOAK_Z8_CEILING = 20896  # 2026-07-21 the status bar names darkness (In the dark / Im Dunkeln / A oscuras) instead of spoiling an unseen room's name, +40 in games where darkness is reachable (any_dark); always-lit games are byte-identical (the fold test); previously 2026-07-20 ASK rides the grammar table (ask/ask_for chosen by wording, both with a text slot): the positional matcher now ships in every English game, +828; German and Spanish phrase requests with their own verb and table nothing

# The PunyInform-equivalent Cloak of Darkness build (standard verb set only) is
# about 27K; staying strictly under it is the charter's fairness benchmark.
PUNY_CLOAK_BYTES = 27 * 1024


def _compile(name, version=5):
    with open(os.path.join(EXAMPLES, name), "r", encoding="utf-8") as fh:
        return generate(
            analyze(cosmos.combined_program(parse(fh.read(), name))), version=version
        )


@pytest.mark.parametrize("name", sorted(CEILINGS))
def test_example_size_ceiling(name):
    size = len(_compile(name))
    ceiling = CEILINGS[name]
    assert size <= ceiling, (
        f"{name} grew: {size} bytes against a ceiling of {ceiling}. If the growth "
        f"is intended, raise the ceiling in tests/test_sizes.py in this same "
        f"commit and say why in the commit message; otherwise find the regression."
    )
    if size < ceiling:
        # Not a failure: a smaller build is the objective. The reminder prints in
        # pytest's verbose output so the win gets locked in.
        print(f"{name}: {size} < ceiling {ceiling}; lower the ceiling to keep the win.")


def test_cloak_z8_size_ceiling():
    size = len(_compile("cloak-of-darkness.storyarc", version=8))
    assert size <= CLOAK_Z8_CEILING, (
        f"cloak z8 grew: {size} bytes against {CLOAK_Z8_CEILING}; see the ceiling "
        f"policy at the top of this file."
    )


def test_cloak_beats_the_punyinform_benchmark():
    # The charter check (docs/00 section 5): the golden game stays strictly under
    # its PunyInform-equivalent build.
    assert len(_compile("cloak-of-darkness.storyarc")) < PUNY_CLOAK_BYTES


def test_every_example_is_ceiling_tracked():
    # A new example must join the size gate in the same commit (the wave of
    # 2026-07 grew four examples that quietly skipped it). rabenstein is the
    # arc_image showcase and stays untracked, as found.
    import os
    import re as _re
    src = open(os.path.abspath(__file__)).read()
    tracked = set(_re.findall(r'"([^"]+\.storyarc)"', src))
    # The two arc_image showcases stay untracked: their size is dominated by
    # the art pipeline they demonstrate, not by library codegen.
    excluded = {"arc_image/rabenstein.storyarc",
                "arc_image/blorbenstein.storyarc"}
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
    on_disk = set()
    for r, _, files in os.walk(root):
        for f in files:
            if f.endswith(".storyarc"):
                on_disk.add(os.path.relpath(os.path.join(r, f), root))
    missing = sorted(on_disk - tracked - excluded)
    assert not missing, f"examples missing from the size gate: {missing}"
