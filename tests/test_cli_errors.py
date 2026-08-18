# test_cli_errors.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Load-time summon errors reach the author as one clean line.

Every compile stage prints an ArcError as `file:line: error: ...` and
returns 1; the Cosmos loader (granule resolution, selections, the
language gate) must behave the same, never escape as a traceback. Found
in the field: `summon missing.granule` crashed arcc with a raw Python
traceback because the loader ran outside the CLI's error handler.
"""

from arcturus import cli

GAME = """\
game
    title  "ErrTest"
    author "Test"
    UUID   7f3a9c20-1e44-4b8a-9d51-6c2f0b9a7e13
    start  foyer

summon missing.granule

room foyer
    name "Start"
    desc "A room."
"""


def test_summon_error_is_one_clean_line(tmp_path, capsys):
    src = tmp_path / "game.storyarc"
    src.write_text(GAME)
    # A raised ArcError here IS the bug (pytest would report it as an
    # error, not a failure); rc 1 plus the formatted message is the fix.
    rc = cli.main([str(src), "-o", str(tmp_path / "t.z5")])
    assert rc == 1
    err = capsys.readouterr().err
    assert "cannot find granule 'missing.granule'" in err
    assert "Traceback" not in err
