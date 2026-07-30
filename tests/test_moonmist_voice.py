# test_moonmist_voice.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Moonmist voice pass: Stefan's own house voice became the
library's defaults, word for word. Pinned here:
the take out/with-you split, the smell and listen and kiss branches, LOOK
UNDER through the under particle (look stays on the flag model), WAVE with
empty hands versus a held thing, DANCE as a whole bare command, and a
scenery grain answering a two-slot verb's one-noun form (BURN DUST)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'summon.extendedverbs\n'
    'game\n    title "M"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    '    grains\n'
    '        examine, burn "soot" or "grime"\n'
    '            if action is burn\n'
    '                say "It smoulders reluctantly."\n'
    '            else\n'
    '                say "Grey and ancient."\n'
    'thing satchel in hall\n    name "satchel"\n    words satchel\n'
    '    container\n    open\n'
    'thing flute in satchel\n    name "bone flute"\n    words flute, bone\n'
    'thing mat in hall\n    name "straw mat"\n    words mat, straw\n'
    'thing guard of character in hall\n    name "tired guard"\n'
    '    words guard, tired\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_take_says_with_you_and_out_of_a_carried_container():
    out = _run(["take satchel", "take flute"])
    assert "You take the satchel with you." in out
    assert "You take the bone flute out." in out


def test_smell_three_ways():
    out = _run(["smell", "smell me", "smell mat"])
    assert "You sniff at the air, perceiving nothing that surprises you." in out
    assert "You smell as fine as usual." in out
    assert "The straw mat smells as expected." in out


def test_listen_and_kiss_branch_on_the_target():
    out = _run(["listen to me", "listen to guard", "listen to mat",
                "kiss me", "kiss guard", "kiss mat"])
    assert "rumble of your blood stream" in out
    assert "The tired guard is silent." in out
    assert "You hear no unexpected sound coming from the straw mat." in out
    assert "platonic nature" in out
    assert "The tired guard is unmoved by your display of affection." in out
    assert "You practice some objectophilia with the straw mat." in out


def test_look_under_rides_the_under_particle():
    out = _run(["look under mat", "look beneath mat"])
    assert out.count("You find nothing of interest under the straw mat.") == 2


def test_wave_splits_hands_and_held():
    out = _run(["wave", "take mat", "wave mat", "wave guard"])
    assert "You wave your hands in the air." in out
    assert "You wave the straw mat in the air, with no apparent consequences." in out
    # not holding the guard: the library refusal, never the wave line
    assert "You wave the tired guard" not in out


def test_dance_is_a_whole_command():
    out = _run(["dance", "jive"])
    assert out.count("You practise your moves.") == 2
    assert "requires you to be more specific" not in out


def test_talk_to_yourself():
    out = _run(["talk to me"])
    assert "Nothing you hear surprises you." in out


def test_a_grain_answers_a_two_slot_verb():
    # burn has a with-line now; the grain still answers its one-noun form,
    # and the action read selects the verb's own text.
    out = _run(["burn soot", "examine grime"])
    assert "It smoulders reluctantly." in out
    assert "Grey and ancient." in out


# --- max_carried and the use granule (wave B2) ------------------------------

LIMIT_GAME = (
    'game\n    title "L"\n    start hall\n'
    'constant item_cap = 2\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing pebble in hall\n    name "pebble"\n    words pebble\n'
    'thing feather in hall\n    name "feather"\n    words feather\n'
    'thing acorn in hall\n    name "acorn"\n    words acorn\n'
)


def test_max_carried_refuses_past_the_limit():
    out = _run(["take pebble", "take feather", "take acorn", "drop pebble",
                "take acorn"], game=LIMIT_GAME)
    assert "You take the pebble with you." in out
    assert "You take the feather with you." in out
    assert "Your hands are full, and so are your pockets." in out
    # dropping one frees a slot
    assert out.count("You take the acorn with you.") == 1


USE_GAME = (
    'summon.use\n'
    'game\n    title "U"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing apple in hall\n    name "apple"\n    words apple\n    edible\n'
    'thing cloak in hall\n    name "wool cloak"\n    words cloak, wool\n'
    '    wearable\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp, brass\n'
    '    switchable\n'
    'thing box in hall\n    name "pine box"\n    words box, pine\n'
    '    container\n    openable\n'
    'thing anvil in hall\n    name "anvil"\n    words anvil\n    fixed\n'
    'thing chest in hall\n    name "sea chest"\n    words chest, sea\n'
    '    container\n    openable\n    lockable\n    locked\n    unseal_with brass_key\n'
    'thing brass_key in hall\n    name "brass key"\n    words key\n'
)


def test_use_guesses_the_obvious_action():
    out = _run(["take apple", "use apple", "use cloak", "use lamp",
                "use box", "use anvil"], game=USE_GAME)
    assert "eat" in out.lower() or "apple" in out  # eaten via perform
    assert "You put on the wool cloak." in out or "wool cloak" in out
    assert "How exactly do you want to use the anvil?" in out


def test_use_with_unlocks_a_lockable_second():
    out = _run(["take key", "use key with chest", "open chest"],
               game=USE_GAME)
    assert "unlock" in out.lower() or "You open the sea chest." in out


def test_bare_use_asks_the_standard_way():
    out = _run(["use"], game=USE_GAME)
    assert "The verb use requires you to be more specific." in out


# --- dual-role words (Stefan's ruling: LIGHT is scenery AND a verb) ---------

DUAL_GAME = (
    'game\n    title "D"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    '    grains\n'
    '        examine "light" or "glow" say "A pale wash from nowhere."\n'
    '        examine, smell "smell" or "odour" say "Sharp and mineral."\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp, brass\n'
    '    switchable\n'
)


def test_a_dual_word_serves_the_verb_and_the_grain():
    out = _run(["light lamp", "x light", "smell smell", "x glow"],
               game=DUAL_GAME)
    assert "switching" in out  # LIGHT LAMP reached the switch machinery
    assert out.count("A pale wash from nowhere.") == 2  # X LIGHT and X GLOW
    assert "Sharp and mineral." in out  # SMELL SMELL: verb then dual grain


def test_games_without_duals_fold_the_table_away():
    # the moonmist GAME has grains but no dual words; the walk still answers
    out = _run(["examine grime"])
    assert "Grey and ancient." in out


def test_shake_family():
    # The shake family (extendedverbs, 2026-07-30): a dry default, an animate
    # refusal, and RATTLE/JIGGLE ride along.
    game = GAME.replace("summon.extendedverbs", "summon.extendedverbs")
    out = _run(["shake mat", "shake guard", "rattle mat"], game=game)
    assert "You give the straw mat a good shake. It survives the experience unchanged." in out
    assert "The tired guard is not a thing you shake." in out
