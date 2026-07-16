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
