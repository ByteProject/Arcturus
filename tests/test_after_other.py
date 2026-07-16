# test_after_other.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""`on after other`: the after pass's catch-all (docs/02 section 9 step 6),
fixed from the field (Charles Moore Jr.): it used to ride the PLAIN catch-all
list, so it fired during the main dispatch, before the action's own report,
on refused actions, and never in the actual after band. Now it mirrors plain
`on other` exactly, one band up: it runs after any completed, unrefused
world action the object has no specific `on after` for; a specific after
shadows it; refusals and metas never reach it."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "A"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south hall\n'
    'thing pebble in hall\n    name "pebble"\n    words pebble\n'
)

ROOM_AFTERS = (
    'on after go\n    say "AFTER-GO"\n    continue\n'
    'on after other\n    say "AFTER-OTHER"\n    continue\n'
)


def _run(src, cmds):
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def _room_game():
    # The afters live on the hall (attach to the room declaration).
    return GAME.replace(
        'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n',
        'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
        '    on after go\n        say "AFTER-GO"\n        continue\n'
        '    on after other\n        say "AFTER-OTHER"\n        continue\n',
    )


def test_after_other_fires_after_the_report():
    out = _run(_room_game(), ["take pebble"]).split(">take")[-1]
    assert "AFTER-OTHER" in out
    # The action's own report comes FIRST; the after pass follows it.
    assert out.index("Got it.") < out.index("AFTER-OTHER")


def test_after_other_catches_an_intransitive_action():
    out = _run(_room_game(), ["wait"]).split(">wait")[-1]
    assert "AFTER-OTHER" in out


def test_specific_after_shadows_after_other():
    # Free handlers, so a real GO (which moves the player) still meets them:
    # the specific after answers go, the catch-all stays silent for it.
    src = GAME + (
        'on after go\n    say "AFTER-GO"\n    continue\n'
        'on after other\n    say "AFTER-OTHER"\n    continue\n'
    )
    tail = _run(src, ["north"]).split(">north")[-1]
    assert "AFTER-GO" in tail
    assert "AFTER-OTHER" not in tail


def test_refused_actions_take_no_after():
    out = _run(_room_game(), ["east"]).split(">east")[-1]  # no exit: refused
    assert "AFTER-OTHER" not in out
    assert "AFTER-GO" not in out


def test_metas_take_no_after():
    out = _run(_room_game(), ["score"]).split(">score")[-1]
    assert "AFTER-OTHER" not in out


def test_plain_other_and_after_other_keep_their_bands():
    # An `on other` alongside: it answers the MAIN band (before the default
    # runs), the after-other answers the AFTER band; neither leaks.
    src = GAME.replace(
        'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n',
        'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n'
        '    on other\n        say "MAIN-OTHER"\n        continue\n'
        '    on after other\n        say "AFTER-OTHER"\n        continue\n',
    )
    out = _run(src, ["take pebble"]).split(">take")[-1]
    assert out.index("MAIN-OTHER") < out.index("Got it.")
    assert out.index("Got it.") < out.index("AFTER-OTHER")


def test_free_after_other():
    src = GAME + 'on after other\n    say "FREE-AFTER"\n    continue\n'
    out = _run(src, ["take pebble"]).split(">take")[-1]
    assert "FREE-AFTER" in out
    assert out.index("Got it.") < out.index("FREE-AFTER")
    # And a refused action stays silent.
    out2 = _run(src, ["east"]).split(">east")[-1]
    assert "FREE-AFTER" not in out2
