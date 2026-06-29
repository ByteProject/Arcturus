# test_meta.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Meta verbs (B5.4d.1): score reports, restart confirms, xyzzy winks, and a
cancelled quit does not advance the world. Also the parser's can't-see for an
object named out of scope, including a give recipient. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Meta"\n    start vault\n'
    'room vault\n    name "The Vault"\n    desc "A small vault."\n    east hall\n'
    'room hall\n    name "The Hall"\n    desc "A long hall."\n'
    'thing coin in vault\n    name "gold coin"\n    words gold, coin\n'
    'thing guard of person in vault\n    name "burly guard"\n    words burly, guard\n'
    'thing wizard of person in hall\n    name "old wizard"\n    words old, wizard\n'
)


def test_meta_compiles():
    assert generate(analyze(cosmos.combined_program(parse(GAME))))[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_meta_verbs_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    script = (
        "score\n"
        "xyzzy\n"
        "restart\n"
        "no\n"  # decline the restart
        "quit\n"
        "no\n"  # decline the quit
        "take coin\n"  # still playing after both declines
    )
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You have scored" in out
    assert "briefly clever" in out
    assert "Start over from the very beginning?" in out
    assert "Got it." in out  # the game kept running after the declines


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_unseen_recipient_cant_see_on_frotz(tmp_path):
    # The recipient is in another room: "give coin to wizard" must report can't
    # see, not run give against the in-scope guard or an empty recipient.
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take coin\ngive coin to wizard\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You see nothing of the sort here." in out
    assert "doesn't want" not in out  # give never dispatched
    assert "therapy" not in out  # nor the only-animate nudge


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_undo_rewinds_a_turn_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take coin\nundo\ninventory\n",  # undo the take, then look in hand
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Got it." in out  # the take happened
    assert "Taken back." in out  # then undo confirms
    # After undo, the coin is back in the room and the hands are empty.
    assert "You're carrying precisely nothing." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_undo_with_nothing_to_undo_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="undo\n",  # first turn, nothing done yet
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "There's nothing to take back." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_restart_confirmed_restarts_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="restart\ny\n",  # confirm: the story reboots and reprints its banner
        capture_output=True, text=True, timeout=15,
    ).stdout
    # The banner serial line appears once at boot and again after the restart.
    assert out.count("Cosmos") >= 2


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_save_restore_roundtrip_on_frotz(tmp_path):
    # save after taking the coin, drop it, then restore: the restored state has
    # the coin in hand again, and the save handler redescribes the room (the
    # do_save result-2 resume path). dfrotz prompts for a filename each time.
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    script = (
        "take coin\n"
        "save\nsnap.qzl\n"  # write the save (coin in hand)
        "drop coin\n"  # change the world
        "restore\nsnap.qzl\n"  # resumes at the save point, coin in hand again
        "inventory\n"
    )
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input=script, capture_output=True, text=True, timeout=15, cwd=tmp_path,
    ).stdout
    assert "Saved." in out  # do_save returned 1
    assert "Down it goes." in out  # the drop took effect before restore
    # After restore the coin is back in hand (the dropped state was discarded):
    # the final inventory lists it, and is not the empty-handed message.
    assert "You're carrying:" in out
    assert "precisely nothing" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_again_replays_last_command_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="jump\nagain\ng\n",  # jump, then repeat it twice via again / g
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert out.count("You hop on the spot.") == 3


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_again_with_nothing_to_repeat_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="again\n",  # first command, nothing remembered yet
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "There's nothing to repeat." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_oops_corrects_a_typo_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="take cdoin\noops coin\ninventory\n",  # fix the misspelled noun
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You see nothing of the sort here." in out  # the typo failed
    assert "Got it." in out  # oops re-ran it as "take coin"
    assert "gold coin" in out  # and the coin is now in hand


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_oops_corrects_a_misspelled_verb_on_frotz(tmp_path):
    # A mistyped verb never reaches the turn machinery, but oops still corrects it:
    # the loop snapshots the line, and oops patches word 0 (the verb).
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="tabe coin\noops take\ninventory\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "Those words don't add up to anything." in out  # the verb typo failed
    assert "Got it." in out  # oops re-ran it as "take coin"
    assert "gold coin" in out  # the coin is in hand


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_oops_with_nothing_to_correct_on_frotz(tmp_path):
    story = tmp_path / "m.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(GAME)))))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="look\noops coin\n",  # the previous command was understood
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "There's nothing to put right." in out
