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

# Byte ceilings per example, as of arcc 0.9.0 / Cosmos 0.13.0 (2026-07-04).
CEILINGS = {
    # 2026-07-04 (Stefan's ruling, superseding the same day's FULL move):
    # there is NO fullscore verb; SCORE is the one score verb and reports
    # score, max, turns, and rank in one line. Pool labels stay in the
    # source and ledger but never reach the story file. teleport(dest)
    # joined the standard blocks (the go handler shares its arrive(), so
    # walking pays for it; unused teleport folds away). Before that, the
    # 2026-07-03 batch: recipient dispatch (~40), the start-title skip
    # (~25), show_tag (~20); chaining, disambiguation, noun lists with
    # noise words, all core parser features every game carries.
    "beispiel-deutsch.storyarc": 20224,
    "brass-lantern.storyarc": 14512,
    "cloak-of-darkness.storyarc": 15028,
    "ejemplo-espanol.storyarc": 19444,
    "features/computed-properties.storyarc": 13356,
    "features/containers.storyarc": 13388,
    "features/daemons-and-timers.storyarc": 13692,
    "features/doors-and-locks.storyarc": 13252,
    "features/grains.storyarc": 13384,
    "features/introproperty.storyarc": 14448,
    "features/kinds-and-inheritance.storyarc": 13212,
    "features/on-other.storyarc": 13216,
    "features/zcolor.storyarc": 13740,
    "features/scoring.storyarc": 15448,
    "features/spans.storyarc": 13400,
    "granules/ambience.storyarc": 14848,
    "granules/conversations.storyarc": 15068,
    "granules/extended-verbs.storyarc": 15716,
    "granules/infocom-interrogation.storyarc": 15308,
    "granules/quotes.storyarc": 13724,
    "granules/take-all.storyarc": 15140,
    "granules/plurals.storyarc": 14372,
    "granules/statusline.storyarc": 13464,
    "granules/verbose-exits.storyarc": 13600,
}

# The z8 build of the same game: only the header version byte, the file-length
# scale, and the packed-address unit differ, so its size moves with the z5 one.
CLOAK_Z8_CEILING = 15464

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
