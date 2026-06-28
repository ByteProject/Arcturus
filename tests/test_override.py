# test_override.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Override-by-block (B5): a block defined in the game overrides a Cosmos library
block of the same name (most-specific-wins), so an author can replace a standard
message without unpacking the library. Two same-name game blocks are still a
duplicate error."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

OVERRIDE = (
    'game\n    title "Override"\n    start r\n'
    'block msg_taken()\n    say "Snagged it!"\n'
    'room r\n    name "Room"\n    desc "A room."\n'
    'thing coin in r\n    name "coin"\n    words coin\n'
)


def test_game_block_overrides_library_block():
    world = analyze(cosmos.combined_program(parse(OVERRIDE)))
    # The surviving msg_taken is the game's, not the library's.
    assert world.blocks["msg_taken"].origin == "game"
    assert generate(world)[0x00] == 5


def test_duplicate_game_blocks_still_error():
    src = (
        'block foo()\n    say "one"\n'
        'block foo()\n    say "two"\n'
        'room r\n    name "R"\n'
    )
    with pytest.raises(ArcError):
        analyze(cosmos.combined_program(parse(src)))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_overridden_message_on_frotz(tmp_path):
    story = tmp_path / "o.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(OVERRIDE)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)], input="take coin\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Snagged it!" in out  # the override fired
    assert "Taken." not in out  # the library default did not
