# test_unruled_refusal.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The dispatcher's refusal tail (Stefan's ruling): a custom verb nothing
claims must answer, never end the turn in silence. Pinned: the one-noun and two-noun refusals, the nounless form, a game
free rule outranking the tail, the any_unruled fold (a game whose verbs all
carry rules stays byte-identical), and the quoted-vocabulary escape hatch
(words "obsidian-black") that rode along in the same commit."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "U"\n    start lab\n'
    'room lab\n    name "Laboratory"\n    desc "A bare room."\n'
    'thing bench in lab\n    name "workbench"\n'
    '    words workbench, bench, "work-bench"\n'
    '    fixed\n    desc "Sturdy."\n'
    'verb "oil", "lubricate"\n'
    '    oil noun with noun\n'
    '    oil noun\n'
    'verb "meow"\n'
    '    meow\n'
)

RULED = GAME + (
    'on oil\n    change refused to 1\n    say "Not something you can oil."\n'
    'on meow\n    change refused to 1\n    say "You meow."\n'
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


def test_unclaimed_one_noun_refuses():
    out = _run(["oil bench"])
    assert "You can't do that to the workbench." in out


def test_unclaimed_two_noun_refuses():
    out = _run(["oil bench with bench"])
    assert "You can't do that to the workbench." in out


def test_unclaimed_bare_verb_refuses_nounless():
    out = _run(["meow"])
    assert "You can't do that." in out


def test_game_free_rule_outranks_the_tail():
    out = _run(["oil bench", "meow"], game=RULED)
    assert "Not something you can oil." in out
    assert "You meow." in out
    assert "You can't do that" not in out


def test_quoted_vocab_word_matches():
    out = _run(["examine work-bench"])
    assert "Sturdy." in out


ELSEWHERE = (
    'game\n    title "E"\n    start here_room\n'
    'room here_room\n    name "Here"\n    desc "A bare room."\n'
    '    east there_room\n'
    'room there_room\n    name "There"\n    desc "Another room."\n'
    '    grains\n'
    '        examine "mural" say "A faded mural."\n'
)


def test_out_of_scope_grain_word_says_cant_see():
    # A grain word from ANOTHER room names a thing that is not here: the
    # answer is the can't-see refusal, never the bare-verb ask (the Amy
    # Briggs find: X TRAIN from the next room over asked "The verb x
    # requires you to be more specific.").
    out = _run(["x mural"], game=ELSEWHERE)
    assert "You see nothing of the sort here." in out
    assert "requires you to be more specific" not in out


DUALWORD = (
    'game\n    title "D"\n    start front\n'
    'room front\n    name "Front"\n    desc "A bare room."\n'
    '    east back\n'
    'room back\n    name "Back"\n    desc "Another room."\n'
    'thing sprayer in back\n    name "spray can"\n'
    '    words spray, can, oil, grease\n'
    '    desc "A can of oil."\n'
    'verb "oil", "grease"\n'
    '    oil noun with noun\n'
    '    oil noun\n'
    'on oil\n    change refused to 1\n    say "Nothing to oil."\n'
)


def test_thing_dual_word_out_of_scope_says_cant_see():
    # OIL the verb and OIL the spray both live (Stefan's ruling): out of the
    # spray's room, X OIL and X GREASE name a thing that is not here, never
    # the bare-verb ask.
    out = _run(["x oil", "x grease", "take oil"], game=DUALWORD)
    assert out.count("You see nothing of the sort here.") >= 3
    assert "requires you to be more specific" not in out


def test_thing_dual_word_in_scope_still_resolves():
    out = _run(["e", "x oil", "x grease"], game=DUALWORD)
    assert "A can of oil." in out


def test_pure_verb_word_still_asks():
    out = _run(["x grab"], game=DUALWORD)
    assert "requires you to be more specific" in out


EXACTNAME = (
    'game\n    title "X"\n    start deck\n'
    'room deck\n    name "Deck"\n    desc "A bare deck."\n'
    'thing bluep in deck\n    name "blue planet"\n'
    '    words blue, planet\n    fixed\n    desc "Blue whole."\n'
    'thing deepp in deck\n    name "deep blue planet"\n'
    '    words deep, blue, planet\n    fixed\n    desc "Deep and dim."\n'
)


def test_full_name_match_beats_partial_at_equal_score():
    # The exact-name tie-break (Stefan's ruling): "blue planet" covers every
    # word the blue planet owns and only part of the deep blue planet, so it
    # resolves without asking; the longer name still reachable in full.
    out = _run(["x blue planet", "x deep blue planet"], game=EXACTNAME)
    assert "Blue whole." in out
    assert "Deep and dim." in out
    assert "Which do you mean" not in out


def test_partial_against_partial_still_asks():
    out = _run(["x planet"], game=EXACTNAME)
    assert "Which do you mean" in out


ACTIONIS = (
    'game\n    title "AI"\n    start yard2\n'
    'room yard2\n    name "Yard"\n    desc "A yard."\n'
    '    grains\n'
    '        examine, open "gate" or "wicket"\n'
    '            if action is open\n'
    '                say "It swings a hand-width and jams."\n'
    '            else\n'
    '                say "A low wooden gate."\n'
)


def test_action_is_compares_actions_not_attributes():
    # `if action is open` in a grain compares the ACTION, even though open is
    # also a boolean attribute (the playtest find: the branch silently became
    # an attribute test on a number and always fell to else).
    out = _run(["x gate", "open gate"], game=ACTIONIS)
    assert "A low wooden gate." in out
    assert "It swings a hand-width and jams." in out
