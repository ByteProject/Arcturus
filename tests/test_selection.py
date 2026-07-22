# test_selection.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The verb selection (the verbs overhaul, phase 4): `summon.extendedverbs
squeeze, burn, search` takes only those verb FAMILIES (a family is one verb
declaration and its synonyms, named by its action) and the story pays only
for them: unselected verbs never enter the dictionary or the grammar, their
handlers are dropped at load, and DCE sweeps their messages. The bare form
keeps meaning all of it, and the same selection works on a fork
(`summon extendedverbs.granule squeeze, burn, search`), because Stefan wants
one canonical verb library that forks carry whole and stories slice, not a
landscape of bespoke verb granules."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = (
    'game\n    title "V"\n    start hall\n'
    '{summon}'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing rope in hall\n    name "rope"\n    words rope\n'
)


def _build(summon, story_dir=None):
    src = BASE.replace("{summon}", summon)
    return generate(analyze(
        cosmos.combined_program(parse(src), story_dir=story_dir)))


def _run(summon, cmds, story_dir=None):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_build(summon, story_dir)), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_selected_families_answer_and_dropped_ones_are_unknown():
    out = _run("summon.extendedverbs squeeze, burn, search\n",
               ["squeeze rope", "burn rope", "search rope", "dig"])
    assert "squeeze" in out          # the squeeze default spoke
    assert "fire" in out             # the burn default spoke
    assert "nothing new to see" in out
    # DIG was not selected: its word is not even in the dictionary.
    assert "don't add up" in out or "doesn't know the word" in out


def test_synonyms_ride_their_family():
    out = _run("summon.extendedverbs search\n", ["frisk rope"])
    assert "nothing new to see" in out


def test_the_bare_form_still_means_everything():
    out = _run("summon.extendedverbs\n", ["dig", "pray"])
    assert "don't add up" not in out


def test_selection_pays_only_for_what_it_takes():
    full = len(_build("summon.extendedverbs\n"))
    three = len(_build("summon.extendedverbs squeeze, burn, search\n"))
    one = len(_build("summon.extendedverbs squeeze\n"))
    none = len(_build(""))
    assert none < one < three < full


def test_selection_works_on_a_fork(tmp_path):
    fork = cosmos.granule_sources()["extendedverbs.granule"]
    (tmp_path / "extendedverbs.granule").write_text(
        fork.replace(
            "You give the rope an uncomfortably long squeeze",
            "You give the rope an uncomfortably long squeeze"),
        encoding="utf-8")
    out = _run("summon extendedverbs.granule squeeze\n",
               ["squeeze rope", "dig"], story_dir=str(tmp_path))
    assert "squeeze" in out
    assert "don't add up" in out or "doesn't know the word" in out


def test_an_unknown_family_lists_the_offer():
    with pytest.raises(ArcError, match="flutter"):
        _build("summon.extendedverbs flutter\n")
    with pytest.raises(ArcError, match="squeeze"):
        _build("summon.extendedverbs flutter\n")  # the offer names squeeze


def test_a_verbless_granule_refuses_a_selection():
    with pytest.raises(ArcError, match="declares no verbs"):
        _build("summon.statusline search\n")
