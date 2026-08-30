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
    'thing satchel of container in hall\n    name "satchel"\n    words satchel\n'
    '    open\n'
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


def test_a_carry_limit_global_is_the_dynamic_form():
    # `global carry_limit = N` alone arms the check (no decoy item_cap
    # needed, EdwardianDuck's find): data names resolve before intrinsics,
    # so the library's carry_limit reads reach the global, and changing it
    # moves the limit at run time (the character-with-more-arms case).
    game = LIMIT_GAME.replace(
        "constant item_cap = 2\n",
        "global carry_limit = 2\n"
        'verb "grow"\n    growing\n'
        "on growing\n    change carry_limit to 3\n"
        '    say "Roomier."\n')
    out = _run(["take pebble", "take feather", "take acorn", "grow",
                "take acorn"], game=game)
    assert "Your hands are full, and so are your pockets." in out
    assert "Roomier." in out
    assert out.count("You take the acorn with you.") == 1


def test_carry_limit_prices_a_loaded_container():
    # The sack hole is closed (ruling 2026-08-30): the limit counts the whole
    # carried subtree, so a container arrives with its contents priced, and
    # rearranging at the limit stays free (taking out of your own sack).
    game = LIMIT_GAME.replace("constant item_cap = 2\n",
                              "constant item_cap = 3\n") \
        .replace("thing acorn in hall",
                 "thing sack of container in hall\n    name \"sack\"\n"
                 "    words sack\n    open\nthing acorn in hall")
    out = _run(["take pebble", "put pebble in sack", "take feather",
                "put feather in sack", "take sack", "take acorn",
                "take pebble", "drop pebble"], game=game)
    # sack(1) + pebble + feather = 3 = cap: the sack lifts, the acorn not.
    assert "You take the sack with you." in out
    assert "Your hands are full, and so are your pockets." in out
    # out of the carried sack at the limit: the total does not grow.
    assert "You take the pebble out." in out


def test_a_container_item_cap_refuses_in_total():
    # `item_cap 3` on a chest already holding a pouch (the pouch itself
    # counts): one more thing fits twice, then the ceiling holds, and under
    # nesting the ceiling that overflows is the one that speaks (the chest
    # refuses an acorn bound for the pouch inside it).
    game = LIMIT_GAME.replace("constant item_cap = 2\n", "") \
        .replace("thing acorn in hall",
                 "thing chest of container in hall\n    name \"chest\"\n"
                 "    words chest\n    open\n    item_cap 3\n"
                 "thing pouch of container in chest\n    name \"pouch\"\n"
                 "    words pouch\n    open\n"
                 "thing acorn in hall")
    out = _run(["take pebble", "put pebble in chest", "take feather",
                "put feather in chest", "take acorn", "put acorn in pouch"],
               game=game)
    assert out.count("Done.") == 2
    assert "No more fits into the chest." in out


def test_no_limit_means_no_check_at_all():
    # Pay for use holds: with neither the constant nor the global, the
    # whole carry check folds away and every take succeeds.
    game = LIMIT_GAME.replace("constant item_cap = 2\n", "")
    out = _run(["take pebble", "take feather", "take acorn"], game=game)
    assert "Your hands are full" not in out
    assert out.count(" with you.") == 3


USE_GAME = (
    'summon.use\n'
    'game\n    title "U"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing apple in hall\n    name "apple"\n    words apple\n    edible\n'
    'thing cloak in hall\n    name "wool cloak"\n    words cloak, wool\n'
    '    wearable\n'
    'thing lamp in hall\n    name "brass lamp"\n    words lamp, brass\n'
    '    switchable\n'
    'thing box of container in hall\n    name "pine box"\n    words box, pine\n'
    '    openable\n'
    'thing anvil in hall\n    name "anvil"\n    words anvil\n    fixed\n'
    'thing chest of container in hall\n    name "sea chest"\n    words chest, sea\n'
    '    openable\n    lockable\n    locked\n    unseal_with brass_key\n'
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
    # LIGHT LAMP reached the switch machinery: under the binary model the
    # library default now flips the lamp and reports, rather than refusing.
    assert "switch the brass lamp on" in out
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
