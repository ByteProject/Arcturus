# test_moonmist_voice.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Moonmist voice pass (H2 step 1, wave B): Stefan's Hibernated 2
customisations became the library's defaults, word for word. Pinned here:
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
    '        examine, burn "dust" or "grime"\n'
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
    out = _run(["burn dust", "examine grime"])
    assert "It smoulders reluctantly." in out
    assert "Grey and ancient." in out
