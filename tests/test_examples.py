# test_examples.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The B1 done-test: both conformance example games parse cleanly, plus
structural checks that the parse captured the right shapes. Also the B4 done-test
(below): each game compiles and is winnable start to finish on Frotz."""

import os
import shutil
import subprocess

import pytest

from arcturus import ast, cosmos, storyfile
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def load(name):
    path = os.path.join(EXAMPLES, name)
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read(), path)


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _compile_example(name, version=5):
    with open(os.path.join(EXAMPLES, name), "r", encoding="utf-8") as fh:
        return generate(
            analyze(cosmos.combined_program(parse(fh.read(), name))), version=version
        )


def _play(name, commands, tmp_path, version=5):
    story = tmp_path / "game.z5"
    story.write_bytes(_compile_example(name, version))
    return subprocess.run(
        [_frotz(), "-p", str(story)], input="".join(c + "\n" for c in commands),
        capture_output=True, text=True, timeout=20,
    ).stdout


def objects(prog):
    return {d.name: d for d in prog.decls if isinstance(d, ast.ObjectDecl)}


def test_brass_lantern_parses_cleanly():
    prog = load("brass-lantern.storyarc")
    # game, on start, 2 rooms, 4 things = 8 declarations (the pull verb the
    # example once declared joined the standard set and the relic was removed
    # when `redefine`/`enhance` made stated intent the norm, 2026-07-22).
    assert len(prog.decls) == 8
    assert isinstance(prog.decls[0], ast.GameBlock)

    objs = objects(prog)
    assert set(objs) >= {"hallway", "cellar", "lantern", "pedestal", "lever", "ruby"}
    assert objs["hallway"].category == "room"
    assert objs["lantern"].category == "thing"

    # The lever's pull handler ends by exposing the ruby and printing.
    lever = objs["lever"]
    pull = next(m for m in lever.members if isinstance(m, ast.Handler))
    assert pull.events == ["pull"]

    # The ruby's take handler finishes with an interpolated message (${turns}).
    ruby = objs["ruby"]
    take = next(m for m in ruby.members if isinstance(m, ast.Handler))
    finish = next(s for s in take.body if isinstance(s, ast.Finish))
    interps = [p for p in finish.message.parts if isinstance(p, ast.StringInterp)]
    assert any(getattr(p.expr, "ident", None) == "turns" for p in interps)

    # The cellar each_turn handler carries a `when` guard.
    cellar = objs["cellar"]
    guarded = [
        m
        for m in cellar.members
        if isinstance(m, ast.Handler) and "each_turn" in m.events
    ]
    assert guarded and guarded[0].when is not None


def test_cloak_of_darkness_parses_cleanly():
    prog = load("cloak-of-darkness.storyarc")
    # game, summon.statusline, global, on start, 4 rooms, 3 things, 1 verb =
    # 11 (the read relic went when the standard set took read over).
    assert len(prog.decls) == 11
    assert any(isinstance(d, ast.GlobalDecl) and d.name == "disturbed" for d in prog.decls)

    objs = objects(prog)
    assert set(objs) >= {"foyer", "cloakroom", "bar", "hook", "cloak", "message"}

    # The hook is a supporter; its examine handler uses `hook holds cloak`.
    hook = objs["hook"]
    assert hook.parent == "supporter"

    # The foyer overrides `go north`; the 1:1 port has no grains anywhere.
    foyer = objs["foyer"]
    go_north = [
        m
        for m in foyer.members
        if isinstance(m, ast.Handler) and "go" in m.events
    ]
    assert go_north and go_north[0].pattern[0].names == ["north"]
    assert not any(isinstance(m, ast.GrainsBlock) for m in foyer.members)

    # The message's examine handler reaches both finish endings.
    message = objs["message"]
    examine = next(m for m in message.members if isinstance(m, ast.Handler))
    finishes = _collect_finishes(examine.body)
    assert len(finishes) == 2


def _collect_finishes(stmts):
    found = []
    for s in stmts:
        if isinstance(s, ast.Finish):
            found.append(s)
        elif isinstance(s, ast.If):
            for clause in s.clauses:
                found.extend(_collect_finishes(clause.body))
        elif isinstance(s, (ast.While, ast.ForEach)):
            found.extend(_collect_finishes(s.body))
        elif isinstance(s, ast.Switch):
            for case in s.cases:
                found.extend(_collect_finishes(case.body))
    return found


# -- B4 done-test: both games compile and are winnable on Frotz ---------------


def test_examples_compile_to_v5():
    assert _compile_example("brass-lantern.storyarc")[0x00] == 5
    assert _compile_example("cloak-of-darkness.storyarc")[0x00] == 5


def test_z8_target_header():
    # --zversion 8: the header version byte is 8 and the stored file length is the
    # real length divided by 8 (the z8 scale), the only image-level differences.
    img = _compile_example("cloak-of-darkness.storyarc", version=8)
    assert img[0x00] == 8
    length = (img[storyfile.H_LENGTH] << 8) | img[storyfile.H_LENGTH + 1]
    assert length * 8 == len(img)


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_brass_lantern_winnable_on_frotz(tmp_path):
    out = _play(
        "brass-lantern.storyarc",
        # Light the lantern, descend, reveal the ruby, take it.
        ["take lantern", "switch on lantern", "north", "pull lever", "take ruby"],
        tmp_path,
    )
    assert "The lantern catches with a soft hiss." in out  # the lantern's switch_on
    assert "The lever grinds down" in out  # the lever reveals the ruby
    assert "You carry the blood ruby home" in out  # the winning finish


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_cloak_of_darkness_winnable_on_frotz(tmp_path):
    out = _play(
        "cloak-of-darkness.storyarc",
        # Hang the cloak so the bar is lit, then read the message.
        ["west", "hang cloak on hook", "east", "south", "read message"],
        tmp_path,
    )
    assert "*** You have won ***" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_cloak_of_darkness_winnable_on_frotz_z8(tmp_path):
    # The same game built for z8 plays identically; the interpreter reads the
    # version from the header, so the packed-address scale must be right.
    out = _play(
        "cloak-of-darkness.storyarc",
        ["west", "hang cloak on hook", "east", "south", "read message"],
        tmp_path,
        version=8,
    )
    assert "*** You have won ***" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_cloak_scores_like_the_original(tmp_path):
    # MAX_SCORE 2, as in Firth's cloak.inf: one point for the first hang on
    # the hook, one for the winning read; the max self-sums from the two
    # award sites and the ending reports it.
    out = _play(
        "cloak-of-darkness.storyarc",
        ["west", "hang cloak on hook", "score", "east", "south", "read message"],
        tmp_path,
    )
    assert "scored 1 of a possible 2" in out
    assert "*** You have won ***" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_cloak_dark_bar_mechanics(tmp_path):
    # The original's two-tier disturbance: a wrong-way GO in the dark costs
    # two, any other action one; LOOK and INVENTORY are free; the meta verbs
    # are out-of-world and never touch the sawdust. One stray jump keeps the
    # count at 1: the message still reads clean.
    out = _play(
        "cloak-of-darkness.storyarc",
        ["south", "look", "inventory", "score", "jump", "north",
         "west", "hang cloak on hook", "east", "south", "read message"],
        tmp_path,
    )
    assert out.count("In the dark? You could easily disturb something!") == 1
    assert "Blundering" not in out
    assert "*** You have won ***" in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_cloak_losable_on_frotz(tmp_path):
    # Blundering the wrong way in the dark costs two disturbances at once:
    # the message is trampled and the game is lost.
    out = _play(
        "cloak-of-darkness.storyarc",
        ["south", "east", "north",
         "west", "hang cloak on hook", "east", "south", "read message"],
        tmp_path,
    )
    assert "Blundering around in the dark isn't a good idea!" in out
    assert "carelessly trampled" in out
    assert "*** You have lost ***" in out
