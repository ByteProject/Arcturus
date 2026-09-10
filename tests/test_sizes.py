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

# 2026-08-24 (the walk exits the seat): +60 to +128 ONLY in games
# with a supporter or container (any_enterable): a walk that starts
# on or in something now runs the seat's own exit handlers before
# moving, exactly as GET OFF runs them, silently by default; the
# foresight example also carries the promise line ('(getting off
# the bench first)'). Enterable-free games proven byte-identical.
# 2026-08-24 (kinds are kinds): adjectives and trigger +284 each,
# their chests and crates converted from the now-refused bare
# container attribute to the real kind, the price of what they are.
# 2026-08-24 (the German posture): beispiel-deutsch +284, German
# games only: the put-to-enter redirect captures which reflexive
# verb was typed and the boarding report conjugates it back (Du
# setzt dich / legst dich / stellst dich; the climbing words keep
# Du steigst), sitting not being the same as standing on top.
# 2026-08-25 (a supporter is not a container): the listing
# parenthetical splits by kind, (on which is/are ...) against
# (contains ...), darauf liegt/liegen in the nominative against
# enthaelt, encima hay against contiene; every game with a holder
# pays a little for reading as what it is.
# 2026-08-25 (the posture, everywhere): sitting, lying, standing
# on, and climbing are different acts in every language, so every
# game pays the verb_trigger bookkeeping and the posture seam
# (Stefan: a sacrifice to make); each pack words its boardings,
# leavings, and foresight exit promises by the posture taken.
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
# 2026-07-27 (the spacing rule): +8 everywhere. Nothing starts flush
# under the status bar (Stefan's rule, superseding the July 18 flush
# look): two pending-break marks in the boot collapse to exactly one
# blank under the bar, and an on-start intro gets one blank each side
# of it, making true what an old comment only claimed.
# 2026-07-27 (exit noun): a few bytes everywhere. EXIT ENGINE and LEAVE
# ENGINE answered "You lost me after that.": the exit handler always
# had the noun path, the standard verb never declared the line. All
# three packs gained it (German also verlasse/verlassen), and the
# boarding idiom matrix is pinned as a test.
# 2026-08-20 (the bar paints what changed): a further +40 to +64, again in
# games WITH a status bar only. Painting the left side means blanking the row
# and writing the room name back over the blank, 74 character writes for a
# 40-cell row with 34 of its cells written twice; the arc_image contract asks
# for a bar paint after every image change (docs/08 3a), so a scene change did
# that twice in one turn and the name visibly flashed on a memory-mapped
# screen. The left side is now painted only when it actually changed, so an
# ordinary turn writes the numbers alone: 74 down to 11 at 40 columns. What the
# row shows is remembered (room, nesting, darkness, and the width it was laid
# out for) and forgotten through the same bar_unseated seam.
# 2026-08-20 (seat the status row once): +24, and +32 where the quote box or
# the conversations menu is also summoned, in games WITH a status bar only;
# every other example is byte-identical. Two interpreter authors reported the
# bar re-issuing its split_window on every paint instead of establishing the
# row once and repainting it. The bar now remembers its row and reserves it
# only after something took it away (the menu's taller window, the quote box,
# a full-screen erase through screen_ready, a restore that may have reset the
# screen), which is the bar_unseated seam in loop.prelude. The bytes buy one
# fewer opcode per turn forever, and on a memory-mapped 8-bit screen a split
# is not free the way it is on a modern terminal.
# 2026-09-10 (the worn seam, and the sealed-put parity): +32 to +72 in
# most games, more where the change is bigger. Marco's cursed clothes:
# drop, put, and insert of a WORN thing no longer bypass the take_off
# gate; the house rejects ("You would have to take the scarf off
# first."), summon.foresight takes it off implicitly, running the real
# take_off so an object's own refusal still rules. The gate folds behind
# any_wearable, so clothing-free games pay only the second half: put and
# insert now route their sealed case (a thing behind closed clear glass)
# through take_sealed_refused, the take's own seam, so foresight opens
# the box for a put too; that parity is core, priced everywhere, the
# same way the 2026-07-25 sealed-take seam was. The two Cloak of
# Darkness examples additionally summon foresight now (the original
# prints "(first taking the cloak off)" on HANG CLOAK ON HOOK, an
# implicit take_off, so the faithful port needs the granule), which is
# most of their larger growth. The `held` grammar slot is retired
# (never enforced; the verb contract is the one held spelling): no
# bytes, only the grammar.
# 2026-09-08 (put refuses what a take refuses): +36 to +56 everywhere.
# auraes found the couch: put and insert moved a noun the player was not
# holding unconditionally, so anything in scope rode into a chest, fixed,
# scenery, and characters included. Both handlers now gate an unheld noun
# through take_probe and refuse in the take's exact words (the one guard
# chain); a held thing skips the probe, the floor-to-container shortcut
# still moves takeable things in one command.
CEILINGS = {
    "features/yes-no.storyarc": 17944,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/press-any-key.storyarc": 18832,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/shiftable.storyarc": 18328,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/enhance-redefine.storyarc": 18684,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/consult-about.storyarc": 18800,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/session-verbs.storyarc": 18396,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/vary.storyarc": 19604,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/foresight.storyarc": 20016,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/beyond.storyarc": 20452,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/alter.storyarc": 19080,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/catalogs.storyarc": 18944,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/matrix.storyarc": 19280,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/direction-grammar.storyarc": 18356,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/scenery-contents.storyarc": 19000,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/trigger.storyarc": 17964,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/adjectives.storyarc": 18596,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/nautical.storyarc": 18836,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/npcengine.storyarc": 20924,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/maniacswap.storyarc": 19164,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "beispiel-deutsch.storyarc": 26844,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "brass-lantern.storyarc": 19740,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "cloak-of-darkness.storyarc": 21156,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "ejemplo-espanol.storyarc": 23508,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/computed-properties.storyarc": 18048,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/containers.storyarc": 18540,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/daemons-and-timers.storyarc": 19692,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/doors-and-locks.storyarc": 18176,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/appearance.storyarc": 18920,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/components.storyarc": 18264,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/whistle.storyarc": 17692,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/pathfinding.storyarc": 20684,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/perform.storyarc": 18008,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/grains.storyarc": 17812,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/handlers.storyarc": 19212,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/grammar.storyarc": 18116,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/introproperty.storyarc": 19456,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/kinds-and-inheritance.storyarc": 18008,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/on-other.storyarc": 17892,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/zcolor.storyarc": 18328,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/scoring.storyarc": 20260,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/spans.storyarc": 18128,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/vehicles.storyarc": 18668,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/success.storyarc": 18616,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/edible.storyarc": 18504,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "features/text-slot.storyarc": 19040,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/carryweight.storyarc": 18820,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/ambience.storyarc": 19920,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/conversations.storyarc": 19796,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/extended-verbs.storyarc": 21024,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/infocom-interrogation.storyarc": 19824,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/quotes.storyarc": 18064,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/take-all.storyarc": 20228,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/plurals.storyarc": 18992,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/statusline.storyarc": 18044,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
    "granules/verbose-exits.storyarc": 17988,  # 2026-09-10 repriced: the worn seam and the sealed-put parity
}

# The z8 build of the same game: only the header version byte, the file-length
# scale, and the packed-address unit differ, so its size moves with the z5 one.
CLOAK_Z8_CEILING = 21800  # 2026-09-10 repriced: the worn seam, sealed-put parity, and summon.foresight

# The PunyInform-equivalent Cloak of Darkness build (standard verb set only) is
# about 27K; staying strictly under it is the charter's fairness benchmark.
PUNY_CLOAK_BYTES = 27 * 1024


def _compile(name, version=5):
    path = os.path.join(EXAMPLES, name)
    with open(path, "r", encoding="utf-8") as fh:
        # story_dir: a dir-local summon (the whistle demo's own granule)
        # resolves beside its example, exactly as arcc would resolve it.
        return generate(
            analyze(cosmos.combined_program(
                parse(fh.read(), name), story_dir=os.path.dirname(path))),
            version=version,
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
    excluded = {"ghosts/ghosts.storyarc",  # the Blackwood port workspace: gitignored until Stefan moves it public
                "arc_image/rabenstein.storyarc",
                "arc_image/blorbenstein.storyarc",
                "arc_image/cloak-of-darkness.storyarc",
                "arc_image/blorb-of-darkness.storyarc"}
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
    on_disk = set()
    for r, _, files in os.walk(root):
        for f in files:
            if f.endswith(".storyarc"):
                on_disk.add(os.path.relpath(os.path.join(r, f), root))
    missing = sorted(on_disk - tracked - excluded)
    assert not missing, f"examples missing from the size gate: {missing}"
