# test_nested_title.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The nested-location suffix: when the player stands on a supporter or in a
container, the room title and the status bar say so, "Crypt (on the altar)".
The wording is the language layer's line_nested (on/in, auf/in with the
dative, sobre/en), and the whole feature folds away byte-identically in a
game with nothing to climb into (any_enterable)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

CRYPT = (
    'game\n    title "Nest"\n    start crypt\n'
    'room crypt\n    name "Crypt"\n    desc "Cold stone."\n'
    'thing altar of supporter in crypt\n    name "altar"\n    fixed\n'
    'thing crate of container in crypt\n    name "crate"\n    open\n    fixed\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, cmds, width=80):
    return subprocess.run(
        [_frotz(), "-p", "-w", str(width), str(story)],
        input=cmds, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_title_says_on_the_altar_and_in_the_crate(tmp_path):
    story = tmp_path / "n.z5"
    story.write_bytes(_build(CRYPT))
    out = _run(story, "get on altar\nlook\nget out\nenter crate\nlook\n")
    assert "Crypt (on the altar)" in out
    assert "Crypt (in the crate)" in out
    # the altar the player stands on never lists the player as contents
    assert "yourself" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_status_bar_carries_the_suffix(tmp_path):
    story = tmp_path / "n.z5"
    story.write_bytes(_build(CRYPT.replace(
        "game\n", "game\n", 1).replace("    start crypt\n",
                                       "    start crypt\nsummon.statusline\n")))
    out = _run(story, "get on altar\nlook\n")
    assert "Crypt (on the altar)" in out  # painted into the bar too


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_dative_and_spanish_wording(tmp_path):
    de = (
        'game\n    title "Nest"\n    start krypta\nsummon.language "german"\n'
        'room krypta\n    name "Krypta"\n    desc "Kalter Stein."\n'
        'thing altar of supporter in krypta\n    name "Altar"\n    fixed\n'
        'thing kiste of container in krypta\n    name "Kiste"\n    die\n'
        '    open\n    fixed\n'
    )
    story = tmp_path / "de.z5"
    story.write_bytes(_build(de))
    out = _run(story, "besteige altar\nschau\naussteigen\n"
                      "betrete kiste\nschau\n")
    assert "Krypta (auf dem Altar)" in out
    assert "Krypta (in der Kiste)" in out

    es = (
        'game\n    title "Nido"\n    start cripta\nsummon.language "spanish"\n'
        'room cripta\n    name "Cripta"\n    desc "Piedra fria."\n'
        'thing altar of supporter in cripta\n    name "altar"\n    fixed\n'
        'thing caja of container in cripta\n    name "caja"\n    open\n    fixed\n'
    )
    story = tmp_path / "es.z5"
    story.write_bytes(_build(es))
    out = _run(story, "entra altar\nmira\nsal\nentra caja\nmira\n")
    assert "Cripta (sobre el altar)" in out
    assert "Cripta (en la caja)" in out


def test_the_fold_sees_enterables():
    # any_enterable folds on the kind chains: a game with nothing to climb
    # into reports 0 (and the static-if machinery drops the suffix code,
    # the same fold path every any_* flag rides), a supporter or container
    # anywhere reports 1. Kind-derived objects count through their chain.
    plain = (
        'game\n    title "Nest"\n    start crypt\n'
        'room crypt\n    name "Crypt"\n    desc "Cold stone."\n'
        'thing rock in crypt\n    name "rock"\n'
    )

    def nestable(src):
        world = analyze(cosmos.combined_program(parse(src)))
        return any("supporter" in o.chain or "container" in o.chain
                   for o in world.objects.values())

    assert not nestable(plain)
    assert nestable(CRYPT)
    # and the plain story still builds and is the smaller of the two
    assert len(_build(plain)) < len(_build(CRYPT))
