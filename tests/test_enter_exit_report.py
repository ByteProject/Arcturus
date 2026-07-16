# test_enter_exit_report.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Boarding and leaving report by the world model: getting on a supporter
versus into a container, off a supporter versus out of a container (a field
request; the flat "Done." said the same for all four). The choice is made in
board_report / leave_report (actions.prelude); the wording is the language
layer's (msg_get_on / msg_get_in / msg_get_off / msg_get_out)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A bare hall."\n'
    'thing stool of supporter in hall\n    name "wooden stool"\n    words stool\n'
    'thing barrel of container in hall\n    name "oak barrel"\n    words barrel\n'
    '    open\n'
)


def _run(src, cmds):
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_supporter_reports_on_and_off():
    out = _run(GAME, ["enter stool", "exit"])
    assert "You get on the wooden stool." in out
    assert "You get off the wooden stool." in out


def test_container_reports_into_and_out_of():
    out = _run(GAME, ["enter barrel", "exit"])
    assert "You get into the oak barrel." in out
    assert "You get out of the oak barrel." in out


def test_exit_when_not_nested_still_refuses():
    out = _run(GAME, ["exit"]).split(">exit")[-1]
    assert "You aren't inside anything to leave." in out


def test_supporter_declared_as_a_bare_attribute_also_reports():
    # A supporter set as a plain attribute (not the `of supporter` kind) is not
    # seen by the any_enterable compile-time estimate, so the report path must
    # not be gated on it: boarding still works and still reports.
    src = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x."\n'
        'thing crate in hall\n    name "crate"\n    words crate\n    supporter\n'
    )
    out = _run(src, ["enter crate", "exit"])
    assert "You get on the crate." in out
    assert "You get off the crate." in out
