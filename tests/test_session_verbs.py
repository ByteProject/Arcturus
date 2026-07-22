# test_session_verbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The last of the phase 6 roster. VERSION prints the banner mid-game (the
bug-report verb), always in. NOTIFY is the COUPLED rule, Stefan's design:
off by default, the author enables it (change notify to true, usually in
on start), and enabling it anywhere brings the player verb along
automatically; a game that never writes the global has no bracket lines,
no verb, and not even the dictionary word. The profanity responses are the
oldest Easter egg in the medium, an extendedverbs family (swear)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = (
    'game\n    title "Notch"\n    scoring\n    start hall\n'
    '{extra}'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing gem in hall\n    name "gem"\n    words gem\n    scored\n'
)

ENABLED = 'on start\n    change notify to true\n'


def _run(extra, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(
            parse(BASE.replace("{extra}", extra)))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_an_enabled_game_announces_the_score():
    out = _run(ENABLED, ["take gem"])
    assert "[Your score has just gone up by 5.]" in out


def test_the_player_can_toggle_it_off_and_on():
    out = _run(ENABLED, ["notify", "take gem", "notify"])
    assert "[Score notification is off.]" in out
    assert "gone up" not in out.split("notification is off")[-1].split("notify")[0]
    assert "[Score notification is on.]" in out


def test_an_untouched_game_has_no_verb_and_no_lines():
    out = _run("", ["take gem", "notify"])
    assert "[" not in out.split(">take gem")[-1].split(">notify")[0]
    tail = out.split(">notify")[-1].strip().splitlines()
    assert tail and ("don't add up" in tail[0] or "doesn't know" in tail[0])


def test_version_prints_the_banner():
    out = _run("", ["version"])
    tail = out.split(">version")[-1]
    assert "Notch" in tail
    assert "Arcturus" in tail


def test_the_swear_family_answers_when_selected():
    src = (
        'game\n    title "S"\n    start hall\n'
        'summon.extendedverbs swear\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
    )
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=["damn", "hell"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert io.text.count("declines to transcribe") == 2
