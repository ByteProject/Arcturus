# test_alter.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""alter (a field request: default mechanics, your wording): a handler
REGISTERS the action's report, one line (`alter "..."`) or an indented
body for composed wording, then continues; the report fires at report
time, instead of the default line, ONLY when the action succeeds (the
Charles Moore Jr. timing report: the old eager print narrated success
before validation). A plain say + continue keeps today's stacking, a
refused action never fires the registration, and a game that never
alters compiles byte-identical (the untouched ceilings)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start shrine\n'
    'summon.extendedverbs\n'
    'room shrine\n    name "Shrine"\n    desc "A shrine."\n'
    'thing idol in shrine\n    name "jade idol"\n    words idol, jade\n'
    '    on take\n'
    '        alter "The idol comes free with a reluctance you can feel."\n'
    '        continue\n'
    '    on drop\n'
    '        alter block\n'
    '            show("You set the idol down")\n'
    '            if here is shrine\n'
    '                show(", and the shrine seems to sigh")\n'
    '            say "."\n'
    '        continue\n'
    '    on rub\n'
    '        alter "The jade warms under your palm."\n'
    '        continue\n'
    'thing altar of supporter in shrine\n    name "altar"\n    words altar\n'
    '    fixed\n'
    '    on take\n'
    '        alter "You heave at the altar."\n'
    '        continue\n'
    'thing candle in shrine\n    name "candle"\n    words candle\n'
    '    on take\n'
    '        say "Wax flakes under your fingers."\n'
    '        continue\n'
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


def test_alter_speaks_and_mechanics_run():
    out = _run(["take idol", "i", "drop idol"])
    assert "The idol comes free with a reluctance you can feel." in out
    assert "Got it." not in out                      # the default stayed silent
    assert "jade idol" in out                        # ...but the take HAPPENED
    assert "You set the idol down, and the shrine seems to sigh." in out
    assert "Down it goes." not in out                # block form suppressed too


def test_refusals_never_fire_the_registration():
    # The Charles Moore Jr. field report that reshaped alter: the custom
    # narration REGISTERS and fires only if the action succeeds. A refused
    # take answers with the refusal alone; the heave never lies. (Attempt
    # flavor that should print regardless is say's job, not alter's.)
    out = _run(["take altar"])
    assert "You heave at the altar." not in out
    assert "stays exactly where it is." in out       # the refusal speaks alone
    assert "altar" not in _run(["take altar", "i"]).split("carrying")[-1]


def test_plain_say_still_stacks():
    out = _run(["take candle"])
    assert "Wax flakes under your fingers." in out
    assert "Got it." in out                          # the flavor idiom survives


def test_alter_covers_a_granule_default():
    out = _run(["take idol", "rub idol"])
    assert "The jade warms under your palm." in out
    assert "Rubbing" not in out and "polish" not in out


def test_the_mark_lives_one_action():
    out = _run(["take idol", "drop idol", "take candle"])
    assert "Got it." in out                          # candle's default back


def test_no_exit_never_staggers():
    # The drunk who staggers west into a wall (the report's own example):
    # a registered alter on GO fires only after a successful move, before
    # the room description; a refused walk prints the refusal alone.
    game = (
        'game\n    title "T"\n    start cell\n'
        'room cell\n    name "Cell"\n    desc "Bare walls."\n'
        '    east yard\n'
        'room yard\n    name "Yard"\n    desc "Open sky."\n'
        'on go\n'
        '    alter "You stagger drunkenly onward."\n'
        '    continue\n'
    )
    from arcturus import cosmos as _c
    story = generate(analyze(_c.combined_program(parse(game))))
    io = CaptureIO(script=["west", "east"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    west = out.split(">west")[1].split(">")[0]
    assert "stagger" not in west          # refused: no narration
    east = out.split(">east")[1]
    assert "You stagger drunkenly onward." in east
    assert east.index("stagger") < east.index("Yard")  # before the room


def test_alter_without_continue_gets_a_note(capsys):
    # The field trap (Charles Moore Jr.): a handler that alters but never
    # continues dies at the handler level (the general handler design), so
    # it consumes the action, the library's success site never runs, and
    # the registered report can never fire, silently. The compiler says so,
    # naming the alter's line and the cure.
    game = (
        'game\n    title "T"\n    start veranda\nsummon.extendedverbs\n'
        'room veranda\n    name "Veranda"\n    desc "A veranda."\n'
        'thing swing of supporter in veranda\n    name "swing"\n    words swing\n'
        '    on climb, enter\n'
        '        alter "You settle onto the swing."\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    err = capsys.readouterr().err
    assert "alters but never continues" in err
    assert "add `continue`" in err


def test_alter_with_continue_stays_quiet(capsys):
    game = (
        'game\n    title "T"\n    start veranda\nsummon.extendedverbs\n'
        'room veranda\n    name "Veranda"\n    desc "A veranda."\n'
        'thing swing of supporter in veranda\n    name "swing"\n    words swing\n'
        '    on climb, enter\n'
        '        alter "You settle onto the swing."\n'
        '        continue\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    assert "alters but never continues" not in capsys.readouterr().err


# PUT and INSERT were the only success paths without the alter dance (a field
# report: an alter on the SECOND, the receiving container, registered and then
# msg_done spoke over it). The receiver's report must fire on success.
def test_alter_on_the_receiving_container_fires_for_put():
    game = (
        'game\n    title "T"\n    start shrine\n'
        'room shrine\n    name "Shrine"\n    desc "Quiet."\n'
        'thing coin in shrine\n    name "coin"\n    words coin\n'
        'thing bowl of container in shrine\n    name "offering bowl"\n'
        '    words bowl, offering\n    open\n    fixed\n'
        '    on put noun in self\n'
        '        alter "The coin rings against the brass."\n'
        '        continue\n'
    )
    from arcturus import cosmos as _c
    story = generate(analyze(_c.combined_program(parse(game))))
    io = CaptureIO(script=["take coin", "put coin in bowl", "look"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text.split(">put")[-1]
    assert "The coin rings against the brass." in out
    assert "Done." not in out.split("\n\n")[0]   # the report replaced msg_done


def test_alter_on_a_supporter_fires_for_put_on():
    game = (
        'game\n    title "T"\n    start shrine\n'
        'room shrine\n    name "Shrine"\n    desc "Quiet."\n'
        'thing candle in shrine\n    name "candle"\n    words candle\n'
        'thing altar of supporter in shrine\n    name "altar"\n    words altar\n'
        '    fixed\n'
        '    on put noun in self\n'
        '        alter "The candle takes its place among the wax ghosts."\n'
        '        continue\n'
    )
    from arcturus import cosmos as _c
    story = generate(analyze(_c.combined_program(parse(game))))
    io = CaptureIO(script=["take candle", "put candle on altar"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text.split(">put")[-1]
    assert "wax ghosts" in out
