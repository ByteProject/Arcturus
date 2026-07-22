# test_twonoun.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Two-noun grammar (B4.5e.4c): put noun on noun. The parser resolves a second
noun, and the default put handler moves the object onto a supporter, on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n'
    '    title "Put Test"\n'
    '    start hall\n'
    'room hall\n'
    '    name "The Hall"\n'
    '    desc "A wide hall."\n'
    'thing book in hall\n'
    '    name "red book"\n'
    '    words red, book\n'
    'thing table of supporter in hall\n'
    '    name "oak table"\n'
    '    words oak, table\n'
    '    fixed\n'
    '    on examine\n'
    '        if table holds book\n'
    '            say "The book rests on the table."\n'
    '        else\n'
    '            say "A bare oak table."\n'
    '        stop\n'
)


def test_twonoun_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_put_on_supporter_on_frotz(tmp_path):
    story = tmp_path / "pt.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="examine table\nput book on table\nexamine table\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "A bare oak table." in out  # before: nothing on it
    assert "Done." in out  # put book on table
    assert "The book rests on the table." in out  # after: the book moved onto it


OPEN_WITH_KEY = (
    'game\n    title "Open Test"\n    start r\n'
    'room r\n    name "R"\n    desc "A room."\n    north f\n'
    'room f\n    name "F"\n    desc "F."\n    south r\n'
    'thing gate of door in r, f\n    name "oak door"\n    words door, gate\n'
    '    lockable\n    locked\n    unseal_with key\n'
    'thing key in r\n    name "brass key"\n    words key\n'
    'thing stone in r\n    name "grey stone"\n    words stone\n'
)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_open_with_key_unlocks_then_opens_on_frotz(tmp_path):
    # "open the door with the key": the open action, given a second noun (the key),
    # unlocks a locked thing and then opens it. A wrong key does not fit.
    story = tmp_path / "ow.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(OPEN_WITH_KEY)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take key\ntake stone\nopen door with stone\nopen door with key\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "entirely unimpressed" in out  # wrong key: refused, still locked
    assert "Unlocked." in out  # right key: unlocked
    assert "Open." in out  # and then opened, in one command


# --- unknown words can no longer dissolve into a noun phrase ----------------
#
# The field report (improvmonster, 2026-07-22): GIVE MERCHANT THE XYZZYPLUGH
# resolved to noun = merchant and the garbage vanished, so an `on give,show`
# override fired on gibberish. The scoring matcher tolerates KNOWN words an
# object does not carry (articles, a stray adjective), but a word the
# dictionary has never heard of now faults the phrase (parse_fault 4, the
# word named), in every position: the trailing reversed-dative slot was the
# one that leaked. The idiom fillers this exposed ("of"; takeall's "from")
# are declared noise words now, not tolerated garbage.

GIVE_GAME = (
    'game\n    title "G"\n    start plaza\n'
    'room plaza\n    name "Plaza"\n    desc "A plaza."\n'
    'thing merchant in plaza\n    name "merchant"\n    words merchant\n'
    '    animate\n'
    '    on give,show\n'
    '        say "He is not interested in ${the noun}."\n'
    'thing pebble in plaza\n    name "pebble"\n    words pebble\n'
    'thing coin in plaza\n    name "gold coin"\n    words gold, coin\n'
)


def _replies(src, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_trailing_unknown_word_is_reported_not_swallowed():
    out = _replies(GIVE_GAME, ["give merchant the xyzzyplugh"])
    assert 'know the word "xyzzyplugh"' in out
    assert "not interested" not in out


def test_unknown_word_still_reported_before_the_preposition():
    out = _replies(GIVE_GAME, ["give xyzzyplugh to merchant"])
    assert 'know the word "xyzzyplugh"' in out


def test_reversed_dative_still_resolves():
    out = _replies(GIVE_GAME, ["take coin", "give merchant coin"])
    assert "not interested in the gold coin" in out


def test_articles_still_dilute_a_phrase():
    out = _replies(GIVE_GAME, ["take the pebble", "give the pebble to merchant"])
    assert "not interested in the pebble" in out


def test_get_out_of_survives_the_stricter_matcher():
    # "of" is a declared noise word now; the idiom must keep working.
    src = (
        'game\n    title "B"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing crate in hall\n    name "packing crate"\n    words crate, packing\n'
        '    container\n    open\n    fixed\n'
    )
    out = _replies(src, ["get in crate", "get out of crate"])
    assert "You get out of the packing crate" in out or "out of" in out.lower()
