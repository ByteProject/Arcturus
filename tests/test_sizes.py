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
CEILINGS = {
    "features/beyond.storyarc": 17904,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/alter.storyarc": 16536,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/catalogs.storyarc": 16488,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/matrix.storyarc": 16852,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/direction-grammar.storyarc": 16592,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/scenery-contents.storyarc": 16532,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/nautical.storyarc": 16344,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
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
    "beispiel-deutsch.storyarc": 22704,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "brass-lantern.storyarc": 17012,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "cloak-of-darkness.storyarc": 17984,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "ejemplo-espanol.storyarc": 21644,  # 2026-07-18 bold banner and location titles (Stefan's polish ruling; four style ops)
    "features/computed-properties.storyarc": 15588,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/containers.storyarc": 15884,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/daemons-and-timers.storyarc": 15900,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/doors-and-locks.storyarc": 15476,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/appearance.storyarc": 16276,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/components.storyarc": 15752,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/perform.storyarc": 15752,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/grains.storyarc": 15632,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/handlers.storyarc": 16704,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/grammar.storyarc": 16596,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/introproperty.storyarc": 16820,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/kinds-and-inheritance.storyarc": 15448,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/on-other.storyarc": 15436,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/zcolor.storyarc": 15820,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/scoring.storyarc": 17800,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/spans.storyarc": 15628,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "features/vehicles.storyarc": 16156,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/ambience.storyarc": 17596,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/conversations.storyarc": 17228,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/extended-verbs.storyarc": 18448,  # 2026-07-19 search leaves components alone (the lootable filter)
    "granules/infocom-interrogation.storyarc": 17628,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/quotes.storyarc": 15824,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/take-all.storyarc": 17544,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/plurals.storyarc": 16476,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/statusline.storyarc": 15556,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
    "granules/verbose-exits.storyarc": 15824,  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)
}

# The z8 build of the same game: only the header version byte, the file-length
# scale, and the packed-address unit differ, so its size moves with the z5 one.
CLOAK_Z8_CEILING = 18528  # 2026-07-18 the reversed dative takes pronouns (give him coin; the probe's pronoun branch)

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
    excluded = {"arc_image/rabenstein.storyarc"}
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
    on_disk = set()
    for r, _, files in os.walk(root):
        for f in files:
            if f.endswith(".storyarc"):
                on_disk.add(os.path.relpath(os.path.join(r, f), root))
    missing = sorted(on_disk - tracked - excluded)
    assert not missing, f"examples missing from the size gate: {missing}"
