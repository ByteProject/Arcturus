# test_turn_first.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The `first` placement on the turn clock (EdwardianDuck's field report,
2026-09-19): `on each_turn first` fires at the TOP of the turn, before the
command is read and parsed, so a rule can refresh derived state (a hidden
flag computed from light) in time for the parser to see it, the pipeline
position PunyInform authors abused InScope for. `after/every N turns first
do X` moves a timer's firing before the action dispatches, with the meta
band excluded (SCORE burns no fuse). Games using neither compile
byte-identical (the untouched ceilings in test_sizes). Alongside: the
computed-block-on-an-attribute refusal (`hidden block` used to be accepted
and silently ignored)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "TF"\n    start stair\n'
    'room stair\n    name "Stair"\n    desc "Steep and dim."\n'
    '    lightlevel 2\n'
    'thing graffito in stair\n    name "message"\n    words message, graffito\n'
    '    scenery\n    fixed\n    desc "Mind the step."\n'
    'verb "dim"\n    vdim\n'
    'verb "brighten"\n    vbrighten\n'
    'on vdim\n    change stair.lightlevel to 0\n    say "The bulb dies."\n'
    'on vbrighten\n'
    '    change stair.lightlevel to 2\n    say "The bulb flares back."\n'
    'on each_turn first\n'
    '    if here.lightlevel is 0\n'
    '        now graffito is hidden\n'
    '    else\n'
    '        now graffito is not hidden\n'
    'block fuse_pops()\n    say "A fuse pops somewhere below."\n'
    'on start\n'
    '    after 2 turns first do fuse_pops\n'
    '    say "You start on the stair."\n'
)

_STORY = {}


def _run(cmds):
    if "s" not in _STORY:
        _STORY["s"] = generate(analyze(cosmos.combined_program(parse(GAME))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY["s"]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_pulse_refreshes_state_before_the_parse():
    # The parser itself refuses the graffito once the light is gone: the
    # pulse ran between the commands, so the noun never resolves (the
    # InScope effect), and it resolves again when the light returns.
    out = _run(["examine message", "dim", "examine message",
                "brighten", "examine message"])
    first, dark, lit = out.split(">examine message")[1:4]
    assert "Mind the step." in first        # pulse ran before the FIRST command
    assert "nothing of the sort" in dark
    assert "Mind the step." in lit


def test_pulse_runs_between_chained_segments():
    # "dim then examine message": segment two parses under the new light.
    out = _run(["dim then examine message"])
    tail = out.split("The bulb dies.")[1]
    assert "nothing of the sort" in tail


def test_first_timer_fires_before_the_action():
    # Armed `after 2 turns first` at start: due at the top of turn 2, the
    # fuse speaks BEFORE the action's own report, not after it.
    out = _run(["examine message", "dim"])
    seg = out.split(">dim")[1]
    assert "A fuse pops" in seg
    assert seg.index("A fuse pops") < seg.index("The bulb dies.")


def test_meta_commands_burn_no_fuse():
    # Two SCOREs consume nothing: the two-turn fuse still needs two REAL
    # commands, and fires at the top of the second.
    out = _run(["score", "score", "examine message", "examine message"])
    a, b = out.split(">examine message")[1:3]
    assert "A fuse pops" not in a
    assert "A fuse pops" in b


def test_first_on_an_action_handler_is_refused():
    with pytest.raises(ArcError) as e:
        parse('game\n    title "T"\n    start r\n'
              'room r\n    name "R"\n    desc "x"\n'
              'on take first\n    say "no"\n')
    assert "marks the turn clock only" in str(e.value)


def test_mixed_placement_for_one_block_is_refused():
    src = (
        'game\n    title "T"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'block pulse()\n    say "x"\n'
        'on start\n'
        '    after 2 turns first do pulse\n'
        '    every 3 turns do pulse\n'
    )
    with pytest.raises(ArcError) as e:
        analyze(parse(src))
    assert "both with and without 'first'" in str(e.value)


def test_stop_accepts_the_first_spelling():
    src = (
        'game\n    title "T"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'block pulse()\n    say "tick"\n'
        'on start\n    every 2 turns first do pulse\n'
        'verb "calm"\n    vcalm\n'
        'on vcalm\n'
        '    stop every 2 turns first do pulse\n'
        '    say "Calmed."\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=["wait", "wait", "calm", "wait", "wait", "wait"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "tick" in io.text.split(">calm")[0]
    assert "tick" not in io.text.split("Calmed.")[1]


def test_hidden_block_is_refused_loudly():
    # The silent no-op that opened this: a computed block on an attribute
    # parsed clean and did nothing. Now it names itself and the cure.
    src = (
        'game\n    title "T"\n    start r\n'
        'room r\n    name "R"\n    desc "x"\n'
        'thing g in r\n    name "g"\n    words gee\n'
        '    hidden block\n'
        '        return 1\n'
    )
    with pytest.raises(ArcError) as e:
        analyze(parse(src))
    assert "attribute" in str(e.value)
    assert "each_turn" in str(e.value)


def test_first_pulse_never_falls_into_on_other():
    # The field report (EdwardianDuck, 2026-09-21): a scenery kind with an
    # `on other` refusal answered the top-of-turn pulse with it, once per
    # item, because the react routine's catch-all knew only the fixed
    # events. each_turn_first is an event wherever events are told from
    # verbs: object catch-alls and free `on other` rules alike stay silent.
    src = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "Bare."\n'
        'kind mute_scenery of thing\n    scenery\n'
        '    on examine\n        continue\n'
        '    on other\n        say "LEAK: ${the noun}."\n'
        'thing pillar of mute_scenery in hall\n    name "pillar"\n'
        '    words pillar\n    desc "Stone."\n'
        'global ticks = 0\n'
        'on each_turn first\n    change ticks to ticks + 1\n'
        'on other\n    say "FREE LEAK."\n    continue\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=["wait", "wait", "push pillar"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "LEAK: " not in io.text.split(">push")[0]
    assert "FREE LEAK." not in io.text.split(">push")[0]
    assert "LEAK: the pillar." in io.text.split(">push")[1]  # on other still works
