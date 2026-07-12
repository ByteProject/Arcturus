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
    "beispiel-deutsch.storyarc": 22116,  # 2026-07-11 the held tiebreak
    "brass-lantern.storyarc": 16352,  # 2026-07-12 death vs finish: cloak dies, so it pays
    "cloak-of-darkness.storyarc": 17260,  # 2026-07-12 death vs finish: cloak dies, so it pays
    "ejemplo-espanol.storyarc": 21148,  # 2026-07-11 the held tiebreak
    "features/computed-properties.storyarc": 14924,  # 2026-07-11 the held tiebreak
    "features/containers.storyarc": 15200,  # 2026-07-11 the held tiebreak
    "features/daemons-and-timers.storyarc": 15236,  # 2026-07-11 the held tiebreak
    "features/doors-and-locks.storyarc": 14812,  # 2026-07-11 the held tiebreak
    "features/appearance.storyarc": 15604,  # 2026-07-11 the held tiebreak
    "features/components.storyarc": 15076,  # 2026-07-11 the held tiebreak
    "features/perform.storyarc": 15160,  # 2026-07-11 the held tiebreak
    "features/grains.storyarc": 14968,  # 2026-07-11 the held tiebreak
    "features/grammar.storyarc": 15932,  # 2026-07-11 the held tiebreak
    "features/introproperty.storyarc": 16124,  # 2026-07-11 the held tiebreak
    "features/kinds-and-inheritance.storyarc": 14772,  # 2026-07-11 the held tiebreak
    "features/on-other.storyarc": 14772,  # 2026-07-11 the held tiebreak
    "features/zcolor.storyarc": 15144,  # 2026-07-11 the held tiebreak
    "features/scoring.storyarc": 17124,  # 2026-07-11 the held tiebreak
    "features/spans.storyarc": 14964,  # 2026-07-11 the held tiebreak
    "features/vehicles.storyarc": 15464,  # 2026-07-11 the held tiebreak
    "granules/ambience.storyarc": 16256,  # 2026-07-11 the held tiebreak
    "granules/conversations.storyarc": 16552,  # 2026-07-11 the held tiebreak
    "granules/extended-verbs.storyarc": 17532,  # 2026-07-11 the held tiebreak
    "granules/infocom-interrogation.storyarc": 16964,  # 2026-07-11 the held tiebreak
    "granules/quotes.storyarc": 15120,  # 2026-07-11 the held tiebreak
    "granules/take-all.storyarc": 16848,  # 2026-07-11 the held tiebreak
    "granules/plurals.storyarc": 15800,  # 2026-07-11 the held tiebreak
    "granules/statusline.storyarc": 14880,  # 2026-07-11 the held tiebreak
    "granules/verbose-exits.storyarc": 15160,  # 2026-07-11 the held tiebreak
}

# The z8 build of the same game: only the header version byte, the file-length
# scale, and the packed-address unit differ, so its size moves with the z5 one.
CLOAK_Z8_CEILING = 17752  # 2026-07-12 death vs finish: cloak dies, so it pays

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
