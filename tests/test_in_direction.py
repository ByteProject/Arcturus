# test_in_direction.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""IN is a standard direction property (docs/01 section 10), and it is also
the containment keyword (`thing lamp in cellar`), so its token is a keyword.
The parser must still admit it wherever a direction property name can stand:
a room's exit line (`in cabin`), a go-handler operand (`on go in`), and a
property access (`hall.in`). Before the fix, `in cabin` was rejected with
"expected a property ... got 'in'"."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "The hall."\n'
    '    in cabin\n'
    '    on go in\n'
    '        say "SQUEEZE."\n'
    '        continue\n'
    'room cabin\n    name "Cabin"\n    desc "The cabin."\n'
    '    out hall\n'
    'thing probe in hall\n    name "probe"\n    words probe\n'
    '    on push\n'
    '        if hall.in is cabin\n'
    '            say "PROP OK."\n'
)


def _play(cmds):
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(story, io).run(max_steps=30_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_in_and_out_exits_move_the_player():
    text = _play(["in", "out"])
    assert "Cabin" in text
    assert text.count("Hall") >= 2  # start, and back out


def test_typed_go_in_and_walk_in_move_too():
    text = _play(["go in", "out", "walk in"])
    assert text.count("Cabin") == 2


def test_on_go_in_handler_fires():
    assert "SQUEEZE." in _play(["in"])


def test_in_property_reads_by_dot_access():
    assert "PROP OK." in _play(["push probe"])


def test_in_as_an_expression_value(tmp_path):
    # perform("go", in) and `if way is in`: at expression HEAD the keyword
    # can only be the direction (infix containment needs a left operand),
    # so it reads as a plain name there (improvmonster's two-minute probe
    # of perform).
    import shutil
    import subprocess
    src = (
        'game\n    title "In"\n    start porch\n'
        'room porch\n    name "Porch"\n    desc "Boards."\n    in cabin\n'
        'room cabin\n    name "Cabin"\n    desc "Snug."\n    out porch\n'
        'on go\n'
        '    if way is in\n'
        '        say "(inward)"\n'
        '    continue\n'
        'verb "slip"\n    slip\n'
        'on slip\n    perform("go", in)\n'
    )
    story_bytes = generate(analyze(cosmos.combined_program(parse(src))))
    frotz = shutil.which("dfrotz") or shutil.which("frotz")
    if not frotz:
        import pytest
        pytest.skip("no Frotz interpreter on PATH")
    story = tmp_path / "i.z5"
    story.write_bytes(story_bytes)
    out = subprocess.run(
        [frotz, "-p", "-w", "80", str(story)],
        input="slip\nout\nin\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Cabin" in out                 # perform("go", in) moved us
    assert out.count("(inward)") == 2     # once for slip, once for typed IN
