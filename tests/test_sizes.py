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
CEILINGS = {
    "features/yes-no.storyarc": 17192,  # 2026-08-14 repriced: the version banner grew a character (Cosmos 1.10)
    "features/press-any-key.storyarc": 18040,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/shiftable.storyarc": 17552,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/enhance-redefine.storyarc": 17916,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/consult-about.storyarc": 18032,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/session-verbs.storyarc": 17632,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/vary.storyarc": 18812,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/foresight.storyarc": 18992,  # 2026-08-17 repriced: the existence form (docs/01 chapter 3); a two-sided door is now present on both sides (~264 bytes of presence walk, the two language examples also pay the 1-byte both-forms marker)
    "features/beyond.storyarc": 19524,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/alter.storyarc": 18204,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/catalogs.storyarc": 18152,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/matrix.storyarc": 18472,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/direction-grammar.storyarc": 17584,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/scenery-contents.storyarc": 18064,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/trigger.storyarc": 16948,
    "features/adjectives.storyarc": 17528,  # 2026-08-15 first pin: the adjective marker showcase (>red, the ZIL match classes; games without the marker stay byte-identical)  # 2026-08-14 repriced: the version banner grew a character (Cosmos 1.10)
    "granules/nautical.storyarc": 18072,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "beispiel-deutsch.storyarc": 25456,  # 2026-08-17 repriced: the existence form (docs/01 chapter 3); a two-sided door is now present on both sides (~264 bytes of presence walk, the two language examples also pay the 1-byte both-forms marker)
    "brass-lantern.storyarc": 18964,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "cloak-of-darkness.storyarc": 19596,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "ejemplo-espanol.storyarc": 22500,  # 2026-08-17 repriced: the existence form (docs/01 chapter 3); a two-sided door is now present on both sides (~264 bytes of presence walk, the two language examples also pay the 1-byte both-forms marker)
    "features/computed-properties.storyarc": 17316,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/containers.storyarc": 17652,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/daemons-and-timers.storyarc": 18880,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/doors-and-locks.storyarc": 17464,  # 2026-08-17 repriced: the existence form (docs/01 chapter 3); a two-sided door is now present on both sides (~264 bytes of presence walk, the two language examples also pay the 1-byte both-forms marker)
    "features/appearance.storyarc": 17988,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/components.storyarc": 17468,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/whistle.storyarc": 16956,  # 2026-08-11 repriced: the combined room listing (one sentence for plain items, Cosmos 1.5.0; the adopters' request)
    "features/pathfinding.storyarc": 19856,  # 2026-08-17 repriced: its door migrated to the existence form (`in hall, library`), so it pays the presence walk like every door game
    "features/perform.storyarc": 17260,  # 2026-08-14 repriced: the version banner grew a character (Cosmos 1.10)
    "features/grains.storyarc": 17144,  # 2026-08-14 repriced: the version banner grew a character (Cosmos 1.10)
    "features/handlers.storyarc": 18404,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/grammar.storyarc": 17356,  # 2026-08-14 repriced: the version banner grew a character (Cosmos 1.10)
    "features/introproperty.storyarc": 18492,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/kinds-and-inheritance.storyarc": 17284,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/on-other.storyarc": 17176,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/zcolor.storyarc": 17544,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/scoring.storyarc": 19420,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/spans.storyarc": 17400,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "features/vehicles.storyarc": 17824,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/ambience.storyarc": 19148,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/conversations.storyarc": 18852,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/extended-verbs.storyarc": 20180,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/infocom-interrogation.storyarc": 19104,  # 2026-08-11 repriced: the combined room listing (one sentence for plain items, Cosmos 1.5.0; the adopters' request)
    "granules/quotes.storyarc": 17300,  # 2026-08-14 repriced: the version banner grew a character (Cosmos 1.10)
    "granules/take-all.storyarc": 19196,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/plurals.storyarc": 18140,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/statusline.storyarc": 17280,  # 2026-08-15 repriced: the adjective sweep (>markers arm the ZIL classes per example)
    "granules/verbose-exits.storyarc": 17320,  # 2026-08-11 repriced: the combined room listing (one sentence for plain items, Cosmos 1.5.0; the adopters' request)
}

# The z8 build of the same game: only the header version byte, the file-length
# scale, and the packed-address unit differ, so its size moves with the z5 one.
CLOAK_Z8_CEILING = 20224  # 2026-08-11 repriced: the combined room listing (one sentence for plain items, Cosmos 1.5.0; the adopters' request)

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
