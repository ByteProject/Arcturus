# test_restless.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""restless, and the timer stops (Stefan's design, 2026-07-26). Work follows
the performer's nature; prose follows scope: a restless object's `on
each_turn` fires every turn wherever the object is, its output discarded
while out of scope (the mute buffer, z-machine stream 3) and spoken normally
in scope, never fired twice. The attribute arms by declaration or by a bare
`now ... is restless` with no declaration anywhere. Timers stop by their
full triple, `stop after/every N turns do block`: the kind and interval
must match what is armed, a mismatch is a no-op, and `stop all timers`
clears the whole schedule."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "R"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north den\n'
    'room den\n    name "Den"\n    desc "A den."\n    south hall\n'
    'thing mouse of character in den\n    name "clockwork mouse"\n'
    '    words mouse, clockwork\n    restless\n'
    '    on each_turn\n'
    '        say "The mouse whirs."\n'
    '        change steps to steps + 1\n'
    'thing imp of character in den\n    name "bottled imp"\n    words imp\n'
    '    on each_turn\n        change imp_ticks to imp_ticks + 1\n'
    'global steps = 0\n'
    'global imp_ticks = 0\n'
    'block drip()\n    say "Drip."\n'
    'block pop()\n    say "POP."\n'
    'on start\n    every 2 turns do drip\n'
    'verb "tally"\n    tally\n'
    'on tally\n    say "S${steps} I${imp_ticks}."\n'
    'verb "possess"\n    possess\n'
    'on possess\n    now imp is restless\n    say "Stirred."\n'
    'verb "banish"\n    banish\n'
    'on banish\n    now mouse is not restless\n    say "Stilled."\n'
    'verb "fixdrip"\n    fixdrip\n'
    'on fixdrip\n    stop every 2 turns do drip\n    say "Fixed."\n'
    'verb "wrongfix"\n    wrongfix\n'
    'on wrongfix\n    stop every 3 turns do drip\n    say "Fumbled."\n'
    'verb "fuse"\n    fuse\n'
    'on fuse\n    after 2 turns do pop\n    say "Lit."\n'
    'verb "snip"\n    snip\n'
    'on snip\n    stop after 2 turns do pop\n    say "Snipped."\n'
    'verb "hush" \n    hush\n'
    'on hush\n    stop all timers\n    say "Hushed."\n'
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


def test_offstage_work_happens_and_offstage_prose_does_not():
    out = _run(["wait", "wait", "tally"])
    # The mouse is in the den; the player never left the hall.
    assert "The mouse whirs." not in out
    # But it worked both waited turns (the pulse fires after dispatch, so
    # the tally turn's own step is not yet counted when tally prints).
    assert "S2 I0." in out


def test_in_scope_a_restless_pulse_speaks_normally_and_once():
    out = _run(["north", "wait"])
    at = out.rindex(">wait")
    assert out[at:].count("The mouse whirs.") == 1


def test_now_arms_an_undeclared_restless_and_now_not_disarms():
    # The imp never declares restless: before possess it only ticks in
    # scope (never, from the hall); after, every turn. Banish stills the
    # mouse back to an ordinary in-scope pulse.
    out = _run(["tally", "possess", "wait", "tally"])
    assert "S0 I0." in out  # nothing offstage before the possess
    # The possess turn's own pulse already sees the restless imp, then the
    # wait: two ticks when the second tally prints.
    assert "S3 I2." in out
    out = _run(["banish", "wait", "wait", "tally"])
    at = out.index("Stilled.")
    # The banish turn's pulse already sees the stilled mouse: no step is
    # ever counted again while the player stays out of its scope.
    assert "S0 I0." in out[at:]


def test_stop_matches_the_exact_triple():
    out = _run(["wrongfix", "wait", "wait"])
    assert "Drip." in out  # every 3 cannot stop an every 2
    out = _run(["fixdrip", "wait", "wait", "wait", "wait"])
    at = out.index("Fixed.")
    assert "Drip." not in out[at:]


def test_stop_after_matches_the_armed_interval_and_one_shot_stays_dead():
    out = _run(["fuse", "wait", "wait", "wait", "wait"])
    assert out.count("POP.") == 1  # fires once, never reloads
    out = _run(["fuse", "snip", "wait", "wait", "wait"])
    at = out.index("Snipped.")
    assert "POP." not in out[at:]


def test_stop_all_timers_clears_the_schedule():
    out = _run(["fuse", "hush", "wait", "wait", "wait", "wait"])
    at = out.index("Hushed.")
    assert "POP." not in out[at:]
    assert "Drip." not in out[at:]


# --- the debug granule's unmute tap ----------------------------------------

UNMUTE_GAME = GAME.replace(
    'game\n    title "R"\n    start hall\n',
    'game\n    title "R"\n    start hall\nsummon.debug\n',
)


def test_unmute_speaks_offstage_prose_behind_a_name_tag():
    # Muted by default even with debug summoned; UNMUTE lets the offstage
    # voice through, tagged with the performer's name; UNMUTE again stills
    # it. The silent worker (the possessed imp says nothing) never prints
    # a bare tag.
    out = _run(["wait", "unmute", "wait", "unmute", "wait"], game=UNMUTE_GAME)
    first = out.index(">unmute")
    assert "The mouse whirs." not in out[:first]
    assert "Offstage voices unmuted." in out
    loud = out[first:out.rindex(">unmute")]
    assert "[clockwork mouse] The mouse whirs." in loud
    assert "Offstage voices muted again." in out
    assert "The mouse whirs." not in out[out.rindex(">wait"):]


def test_unmute_never_tags_a_silent_performer():
    out = _run(["possess", "unmute", "wait"], game=UNMUTE_GAME)
    # The imp works every turn but says nothing: no [bottled imp] tag.
    assert "[bottled imp]" not in out
    assert "[clockwork mouse] The mouse whirs." in out
