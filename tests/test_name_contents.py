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
    'thing rack of supporter in hall\n    name "weapon rack"\n    words rack, weapon\n'
    '    fixed\n'
    'thing sabre in rack\n    name "sabre"\n    words sabre\n'
    'thing axe in rack\n    name "iron axe"\n    words axe, iron\n'
    'thing chest of container in hall\n    name "sea chest"\n    words chest, sea\n'
    '    openable\n    fixed\n'
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
    assert "(on which are a sabre and an iron axe)" in out


GERMAN_GAME = (
    'summon.language "german"\n'
    'game\n    title "N"\n    start halle\n'
    'constant scenery_contents = 1\n'
    'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
    'thing tisch of supporter in halle\n    name "Tisch"\n    words tisch\n'
    '    fixed\n    scenery\n    das\n'
    'thing dolch in halle\n    name "Dolch"\n    words dolch\n    der\n'
)


def test_german_scenery_paragraph_says_the_accusative():
    # The dagger on the table: "siehst du einen Dolch", never "ein Dolch"
    # (the nominative slip the shared loop fixed).
    out = _run(["nimm dolch", "lege dolch auf tisch", "schau"],
               game=GERMAN_GAME)
    assert "einen Dolch" in out
    assert "du ein Dolch" not in out


# A supporter is not a container and must not read like one (Stefan's
# ruling, 2026-08-25): things rest ON it, "(on which is a coin)" in the
# classic manner with number agreement, and contains belongs to
# containers alone. German says darauf liegt/liegen with the NOMINATIVE
# (the list's case follows the governing verb, list_fall), keeping
# enthaelt + accusative for containers. Driven on the Actaea core.

def _play_actaea(src, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load as actaea_load
    from actaea.vm import VM
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(actaea_load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_a_supporter_lists_on_which_not_contains():
    src = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hallway"\n    desc "A hall."\n'
        'thing bench of supporter in hall\n    name "bench"\n'
        '    words bench\n    fixed\n'
        'thing box of container in hall\n    name "box"\n    words box\n'
        '    fixed\n    open\n'
        'thing apple in bench\n    name "apple"\n    words apple\n'
        'thing pin in box\n    name "pin"\n    words pin\n'
        'thing coin in hall\n    name "coin"\n    words coin\n'
    )
    out = _play_actaea(src, ["look", "take coin", "put coin on bench",
                             "look"])
    assert "a bench (on which is an apple)" in out       # singular agrees
    assert "(on which are a coin and an apple)" in out   # plural agrees
    assert "a box (contains a pin)" in out               # containers keep it
    assert "bench (contains" not in out


def test_german_supporter_lies_in_the_nominative():
    src = (
        'game\n    title "DE"\n    start halle\nsummon.language "german"\n'
        'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
        'thing bank of supporter in halle\n    die\n    name "Bank"\n'
        '    words bank\n    fixed\n'
        'thing kiste of container in halle\n    die\n    name "Kiste"\n'
        '    words kiste\n    fixed\n    open\n'
        'thing apfel in bank\n    der\n    name "Apfel"\n    words apfel\n'
        'thing stift in kiste\n    der\n    name "Stift"\n    words stift\n'
        'thing muenze in halle\n    die\n    name "Münze"\n'
        '    words muenze, münze\n'
    )
    out = _play_actaea(src, ["schau", "nimm die münze",
                             "leg die münze auf die bank", "schau"])
    assert "(darauf liegt ein Apfel)" in out             # nominative, singular
    assert "(darauf liegen eine Münze und ein Apfel)" in out
    assert "(enthält einen Stift)" in out                # accusative kept
    assert "Bank (enthält" not in out
