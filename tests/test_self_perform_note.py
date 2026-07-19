# test_self_perform_note.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The self-perform note (docs/01, perform): perform re-enters the whole
handler chain, the calling handler included, so an UNGUARDED `on burn` that
performs "burn" dispatches back into itself forever (the field symptom: the
interpreter dies at the prompt). The compiler notes that shape and names the
cure (`continue`, or a guard the re-entry fails). A `when` guard or operand
pattern exempts the handler: the re-entry can fail it, the legitimate
re-dispatch shape."""

from arcturus import cosmos
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = (
    'game\n    title "T"\n    start camp\n'
    'summon.extendedverbs\n'
    'room camp\n    name "Camp"\n    desc "x."\n'
    'thing torch in camp\n    name "torch"\n    words torch\n'
    'thing match in camp\n    name "match"\n    words match\n'
)


def _notes(src, capsys):
    analyze(cosmos.combined_program(parse(src)))
    return capsys.readouterr().err


def test_unguarded_self_perform_gets_the_note(capsys):
    src = BASE + (
        'verb "burn", "ignite"\n    burn noun\n    burn noun with noun\n'
        'on burn\n'
        '    if second is nothing\n'
        '        say "With what?"\n'
        '        change refused to 1\n'
        '        stop\n'
        '    perform("burn", noun, second)\n'
    )
    err = _notes(src, capsys)
    assert "performs its own action" in err
    assert "continue" in err


def test_when_guarded_self_perform_is_quiet(capsys):
    # The legitimate re-dispatch: the re-entry fails the guard and falls
    # through to the next handler.
    src = BASE + (
        'on burn when second is nothing\n'
        '    perform("burn", noun, match)\n'
    )
    err = _notes(src, capsys)
    assert "performs its own action" not in err


def test_cross_action_perform_is_quiet(capsys):
    # Redirecting to a DIFFERENT action is the everyday use; no note.
    src = BASE + (
        'verb "lash"\n    lash noun\n'
        'on lash\n'
        '    perform("take", noun)\n'
    )
    err = _notes(src, capsys)
    assert "performs its own action" not in err


def test_after_self_perform_gets_the_note(capsys):
    # An `on after burn` performing burn loops the same way: the performed
    # burn completes and runs its own after pass, which re-enters.
    src = BASE + (
        'on after burn\n'
        '    perform("burn", noun)\n'
    )
    err = _notes(src, capsys)
    assert "performs its own action" in err


def test_instance_redirect_to_another_object_is_quiet(capsys):
    # The narrowing (Stefan's ruling, 2026-07-19, the field pushback): an
    # INSTANCE handler redirecting its own action at an explicit different
    # object can never re-enter itself, so the note stays silent. The risky
    # shapes keep it: a room or free handler (runs for any noun), an
    # explicit self, and a dynamic target nobody can prove.
    game = (
        'game\n    title "T"\n    start hall\n'
        'verb "zap"\n    zap noun\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing wand in hall\n    name "wand"\n    words wand\n'
        '    on zap\n'
        '        perform("zap", idol)\n'
        '        stop\n'
        'thing idol in hall\n    name "idol"\n    words idol\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    assert "performs its own" not in capsys.readouterr().err


def test_room_and_dynamic_self_performs_still_note(capsys):
    game = (
        'game\n    title "T"\n    start hall\n'
        'verb "zap"\n    zap noun\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        '    on zap\n'
        '        perform("zap", idol)\n'
        '        stop\n'
        'thing idol in hall\n    name "idol"\n    words idol\n'
        'thing orb in hall\n    name "orb"\n    words orb\n'
        '    on zap\n'
        '        perform("zap", noun)\n'
        '        stop\n'
    )
    analyze(cosmos.combined_program(parse(game)))
    err = capsys.readouterr().err
    assert err.count("performs its own") == 2
