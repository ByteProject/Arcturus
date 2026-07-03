# test_worldfeatures.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The slice-review batch (Stefan's rulings, 2026-07-03): the backstage scope
room (`in scope`), recipient dispatch (the second noun's handlers get their
say), the `scored` attribute with its room_score/object_score knobs, the
`tag` listing qualifier, and the start-screen title skip under a status bar."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    "summon.statusline\n"
    'game\n    title "W"\n    start hall\n'
    "global full = false\n"
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    "    north yard\n"
    "    scored\n"
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    "    south hall\n"
    "    scored\n"
    'thing vlad of character in scope\n    name "Vlad"\n    named\n'
    "    words vlad\n    scenery\n"
    '    desc "A metallic arachnid."\n'
    "    on give\n"
    '        say "Vlad declines the offering."\n'
    'thing servos in scope\n    name "servos"\n    words servos\n    scenery\n'
    '    desc "They whir."\n'
    'thing canister in hall\n    name "fluid canister"\n    words canister\n'
    "    scored\n"
    "    tag block\n"
    "        if full\n"
    '            show("full")\n'
    "        else\n"
    '            show("empty")\n'
    'thing coin in hall\n    name "coin"\n    words coin\n'
    'verb "fill"\n    fill noun\n'
    "on fill\n"
    "    change full to true\n"
    '    say "Filled."\n'
)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _play(tmp_path, source, commands):
    story = tmp_path / "w.z5"
    story.write_bytes(generate(analyze(cosmos.combined_program(parse(source)))))
    return subprocess.run(
        [_frotz(), "-p", str(story)],
        input=commands, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_scope_room_reachable_everywhere(tmp_path):
    # Vlad and his parts live backstage: examinable in both rooms with no
    # spans, no room placement, no scope routines.
    out = _play(tmp_path, GAME, "x vlad\nx servos\nn\nx vlad\nx servos\n")
    assert out.count("A metallic arachnid.") == 2
    assert out.count("They whir.") == 2


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_scope_room_never_listed(tmp_path):
    # Backstage things appear in no room listing.
    out = _play(tmp_path, GAME, "look\n")
    assert "You can see a Vlad" not in out and "servos" not in out.split(">")[1]


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_recipient_dispatch(tmp_path):
    # "give coin to vlad": the RECIPIENT's own handler answers, not the
    # default "doesn't want it".
    out = _play(tmp_path, GAME, "take coin\ngive coin to vlad\n")
    assert "Vlad declines the offering." in out
    assert "Outrageous" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_scored_rooms_and_objects(tmp_path):
    # Start room 5, canister 5, yard 5; revisits and retakes pay nothing.
    out = _play(
        tmp_path, GAME,
        "take canister\nn\ns\nn\ndrop canister\ntake canister\nscore\n",
    )
    assert "scored 15 " in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_tag_qualifier_in_listing_and_inventory(tmp_path):
    out = _play(tmp_path, GAME, "take canister\ni\nfill canister\ni\ndrop canister\nlook\n")
    assert "a fluid canister (empty)" in out
    assert "a fluid canister (full)" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_start_title_skipped_under_status_bar(tmp_path):
    # With the statusline summoned, the opening description omits the room
    # title (the bar names it); an explicit LOOK prints it as usual.
    out = _play(tmp_path, GAME, "look\n")
    head = out.split(">")[0]
    assert "Hall\nA hall." not in head
    assert "A hall." in head
    assert "Hall\nA hall." in out.split(">")[1]


NO_BAR = GAME.replace("summon.statusline\n", "")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_start_title_kept_without_status_bar(tmp_path):
    out = _play(tmp_path, NO_BAR, "wait\n")
    assert "Hall\nA hall." in out.split(">")[0]
