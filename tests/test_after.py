# test_after.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The after phase (docs/02 section 9 step 6): `on after <verb>` handlers run
once the action completed, through the same chain in the same specificity
order, and never when the action was refused. Found unimplemented on
2026-07-04 (after handlers ran in the main phase and consumed the action, so
the default never happened); these pin the real semantics. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, src, script):
    story = tmp_path / "a.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(src)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15,
    ).stdout


GAME = (
    'game\n    title "After"\n    start hall\n'
    'room hall\n    name "The Hall"\n    desc "A hall."\n'
    'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
    "    on after take\n"
    '        say "The coin hums as it settles into your palm."\n'
    'thing anvil in hall\n    name "iron anvil"\n    words iron, anvil\n'
    "    fixed\n"
    "    on after take\n"
    '        say "THE ANVIL AFTER MUST NEVER PRINT."\n'
    'thing idol in hall\n    name "jade idol"\n    words jade, idol\n'
    "    on take\n"
    '        say "You pocket the idol with a practiced flourish."\n'
    "    on after take\n"
    '        say "Somewhere, a temple alarm begins to ring."\n'
    "    on other\n"
    '        say "THE IDOL CATCH-ALL MUST NOT ANSWER THE AFTER PASS."\n'
    "        continue\n"
)


def test_after_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_after_runs_after_the_default(tmp_path):
    # The default take completes first (Got it.), then the after handler.
    out = _play(tmp_path, GAME, "take coin\n")
    assert "Got it." in out
    assert "hums as it settles" in out
    assert out.index("Got it.") < out.index("hums as it settles")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_after_skipped_when_refused(tmp_path):
    # The anvil is fixed: the take is refused (refused set by the library),
    # so its after handler never fires.
    out = _play(tmp_path, GAME, "take anvil\n")
    assert "ANVIL AFTER" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_after_runs_for_an_instead_handler(tmp_path):
    # A handler that replaces the default and ends (the instead case) still
    # completed the action, so the after pass runs; but the handler replaced
    # the default, so the object never moved and "Got it." never prints.
    out = _play(tmp_path, GAME, "take idol\n")
    assert "practiced flourish" in out
    assert "temple alarm" in out
    assert out.index("practiced flourish") < out.index("temple alarm")
    assert "Got it." not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_on_other_never_answers_the_after_pass(tmp_path):
    # A room catch-all legitimately answers the take once, in the main pass
    # (it continues, so the default still runs). The after pass then climbs
    # from the coin's continuing after handler to the room react, where the
    # catch-all must NOT answer a second time: an after pass is bookkeeping,
    # not a player action.
    src = (
        'game\n    title "After3"\n    start hall\n'
        'room hall\n    name "The Hall"\n    desc "A hall."\n'
        "    on other\n"
        '        say "The hall notices."\n'
        "        continue\n"
        'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
        "    on after take\n"
        '        say "The coin hums."\n'
        "        continue\n"
    )
    out = _play(tmp_path, src, "take coin\n")
    assert "Got it." in out
    assert "The coin hums." in out
    assert out.count("The hall notices.") == 1


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_free_after_and_when_guard(tmp_path):
    # A free `on after` rule fires for any completed take; a `when` guard that
    # does not hold skips the object's own after handler that turn.
    src = (
        'game\n    title "After2"\n    start hall\n'
        'room hall\n    name "The Hall"\n    desc "A hall."\n'
        'flag alarmed\n'
        'thing coin in hall\n    name "gold coin"\n    words gold, coin\n'
        "    on after take when alarmed\n"
        '        say "A klaxon sounds."\n'
        'thing bell in hall\n    name "brass bell"\n    words brass, bell\n'
        "on after take\n"
        '    say "Your kleptomania is noted."\n'
    )
    out = _play(tmp_path, src, "take coin\ntake bell\n")
    # The guard does not hold, so the coin's own after stays quiet; the free
    # rule answers both takes.
    assert "klaxon" not in out
    assert out.count("kleptomania is noted") == 2
