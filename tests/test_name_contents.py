# test_name_contents.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""name_contents (Ichiro Ota's request, the PrintContents shape): the bare
composable list. It names a holder's listable contents with articles,
commas, and a final "and", marks them seen, and returns the count; zero
prints nothing at all, so the author's own sentence decides what an empty
holder deserves. The three framers (the "(contains ...)" suffix, "Inside
you find ...", and the scenery paragraph) all speak through the same loop,
and the German pack's shared loop says the accusative everywhere, which
fixes the scenery paragraph's nominative slip ("siehst du ein Dolch")."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "N"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    'thing rack in hall\n    name "weapon rack"\n    words rack, weapon\n'
    '    supporter\n    fixed\n'
    'thing sabre in rack\n    name "sabre"\n    words sabre\n'
    'thing axe in rack\n    name "iron axe"\n    words axe, iron\n'
    'thing chest in hall\n    name "sea chest"\n    words chest, sea\n'
    '    container\n    openable\n    fixed\n'
    'thing pearl in chest\n    name "pearl"\n    words pearl\n'
    'verb "arsenal"\n    arsenal\n'
    'on arsenal\n'
    '    show("Rusting on the rack you find ")\n'
    '    if name_contents(rack) is 0\n'
    '        show("nothing at all")\n'
    '    say "."\n'
    'verb "salvage"\n    salvage\n'
    'on salvage\n'
    '    show("The chest holds ")\n'
    '    if name_contents(chest) is 0\n'
    '        show("nothing you know of")\n'
    '    say "."\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_the_bare_list_composes_into_the_author_s_own_sentence():
    out = _run(["arsenal"])
    assert "Rusting on the rack you find a sabre and an iron axe." in out


def test_zero_prints_nothing_and_the_caller_frames_the_emptiness():
    # The chest is closed and opaque; the pearl has never been seen, so the
    # knowledge model lists nothing and the author's fallback speaks.
    out = _run(["salvage"])
    assert "The chest holds nothing you know of." in out
    assert "pearl" not in out


def test_the_knowledge_model_reaches_the_primitive():
    # Open the chest (revealing the pearl marks it seen), close it again:
    # the closed chest now lists what the player remembers.
    out = _run(["open chest", "close chest", "salvage"])
    assert "Inside you find a pearl." in out
    assert "The chest holds a pearl." in out


def test_the_framers_still_speak_through_the_shared_loop():
    out = _run(["look"])
    assert "(contains a sabre and an iron axe)" in out


GERMAN_GAME = (
    'summon.language "german"\n'
    'game\n    title "N"\n    start halle\n'
    'constant scenery_contents = 1\n'
    'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
    'thing tisch in halle\n    name "Tisch"\n    words tisch\n'
    '    supporter\n    fixed\n    scenery\n    das\n'
    'thing dolch in halle\n    name "Dolch"\n    words dolch\n    der\n'
)


def test_german_scenery_paragraph_says_the_accusative():
    # The dagger on the table: "siehst du einen Dolch", never "ein Dolch"
    # (the nominative slip the shared loop fixed).
    out = _run(["nimm dolch", "lege dolch auf tisch", "schau"],
               game=GERMAN_GAME)
    assert "einen Dolch" in out
    assert "du ein Dolch" not in out
