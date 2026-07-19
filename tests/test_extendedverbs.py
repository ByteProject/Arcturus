# test_extendedverbs.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The extendedverbs granule (B5.5b v1): the E-side verbs parse and speak their
defaults when summoned; SEARCH works on any object with a neutral default the
author overrides per object (a real search reveals by making something
reachable); an object overrides a default; ask addresses a living thing.
Unsummoned, the verbs are unknown. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

ROOMS = (
    'room cell\n    name "The Cell"\n    desc "A bare cell."\n'
    'thing chest of container in cell\n    name "iron chest"\n    words iron, chest\n    open\n'
    'thing coin in chest\n    name "gold coin"\n    words gold, coin\n'
    'thing pebble in cell\n    name "grey pebble"\n    words grey, pebble\n'
    'thing guard of character in cell\n    name "burly guard"\n    words burly, guard\n'
)
# The guard's `on rub` override is only valid when extendedverbs defines `rub`.
GUARD_OVERRIDE = '    on rub\n        say "The guard does not enjoy that."\n'
WITH = 'game\n    title "EV"\n    start cell\nsummon.extendedverbs\n' + ROOMS + GUARD_OVERRIDE
WITHOUT = 'game\n    title "EV"\n    start cell\n' + ROOMS


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def test_with_and_without_compile():
    assert _build(WITH)[0x00] == 5
    assert _build(WITHOUT)[0x00] == 5


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_extended_verbs_on_frotz(tmp_path):
    story = tmp_path / "e.z5"
    story.write_bytes(_build(WITH))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="search chest\ndig\nthink\nrub pebble\nask guard about pebble\nrub guard\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    assert "You find a gold coin." in out  # search lists an open container's contents
    assert "The ground keeps its secrets." in out  # an intransitive flavor verb (dig)
    assert "A fine idea. Nothing comes of it." in out  # think
    assert "You give the grey pebble a thorough buffing." in out  # rub default on an object
    # With no conversation granule, asking IS talking: the shared brush-off
    # (the richer flat defaults exist only in infocom_talking games).
    assert "doesn't seem up for a conversation" in out
    assert "The guard does not enjoy that." in out  # the guard's own on rub overrides


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_unsummoned_verbs_are_unknown_on_frotz(tmp_path):
    story = tmp_path / "e.z5"
    story.write_bytes(_build(WITHOUT))
    out = subprocess.run(
        [_frotz(), "-p", str(story)],
        input="dig\n", capture_output=True, text=True, timeout=15,
    ).stdout
    assert "keeps its secrets" not in out  # the dig verb is not in the build
    assert "don't add up" in out  # the standard unknown-verb reply


def test_search_defaults_by_object_type():
    # SEARCH's shape (two field reports via Charles Moore Jr., and Stefan's
    # ruling of 2026-07-19): search tells you what is there, and makes
    # findable what wasn't. A living thing gets the social rebuff, a shut
    # container keeps its secrets, an empty thing gets the neutral line, an
    # open container LISTS its contents, and a plain thing's authored cache
    # is listed, marked seen, and spilled to the room so it is truly
    # takeable. search_loot is the same engine public, for the compliant
    # frisk of a still-animate character.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\nsummon.extendedverbs\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing statue in hall\n    name "statue"\n    words statue\n'
        'thing box of container in hall\n    name "shut box"\n    words shut, box\n'
        'thing guard of character in hall\n    name "guard"\n    words guard\n'
        'thing corpse in hall\n    name "corpse"\n    words corpse\n'
        'thing coin in corpse\n    name "gold coin"\n    words coin, gold\n'
        'thing warden of character in hall\n    name "warden"\n    words warden\n'
        '    on search\n'
        '        search_loot(self)\n'
        'thing pass in warden\n    name "stamped pass"\n    words pass, stamped\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["search statue", "search box", "frisk guard",
                           "search corpse", "take coin",
                           "search warden", "take pass",
                           "search corpse"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "nothing new to see here" in out        # empty thing: neutral line
    assert "Schroedinger" in out                   # a shut container
    assert "look that says" in out                 # a living thing: the rebuff
    assert "You find a gold coin." in out          # the cache lists itself
    assert "Got it." in out.split("take coin")[-1]  # ... and is truly takeable
    assert "You find a stamped pass." in out       # search_loot on an animate
    assert "Got it." in out.split("take pass")[-1]
    # The emptied corpse searches clean the second time.
    assert "nothing new to see here" in out.split("search corpse")[-1]


def test_search_alter_rewords_but_the_loot_still_lands():
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\nsummon.extendedverbs\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing corpse in hall\n    name "corpse"\n    words corpse\n'
        '    on search\n'
        '        alter "A quick professional pat-down."\n'
        '        continue\n'
        'thing coin in corpse\n    name "gold coin"\n    words coin, gold\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["search corpse", "take coin"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "A quick professional pat-down." in out
    assert "You find" not in out                   # the default report stayed silent
    assert "Got it." in out.split("take coin")[-1]  # the mechanics ran anyway


def test_search_leaves_components_alone():
    # A `component` is an attached part, not loot (the field report: a
    # component was listed, yielded to the room, and then answered "that's
    # part of the Dock" on take). Search neither lists nor moves it; a body
    # whose only content is a component searches clean.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\nsummon.extendedverbs\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing sleeper in hall\n    name "sleeper"\n    words sleeper\n'
        'thing scar in sleeper\n    name "long scar"\n    words scar, long\n'
        '    component\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["search sleeper", "take scar"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "nothing new to see here" in out
    assert "You find" not in out


def test_sit_is_standard_and_means_enter():
    # SIT/REST moved to the standard set mapped onto enter (the field
    # request: SIT ON X is common IF currency). No granule needed; the
    # particle machinery swallows ON/IN like GET ON always did.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing chair of supporter in hall\n    name "chair"\n    words chair\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["sit on chair", "exit", "rest on chair"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert io.text.count("You get on the chair.") == 2
    assert "You get off the chair." in io.text


def test_stand_is_standard_exit_and_boarding():
    # STAND completes the pair (Stefan's go): bare STAND and STAND UP leave
    # the seat through exit's ordinary path; STAND ON X boards it like SIT
    # ON; standing on solid ground gets exit's normal refusal.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing stool of supporter in hall\n    name "stool"\n    words stool\n'
    )
    story = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=["stand on stool", "stand up", "sit on stool",
                           "stand", "stand"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert out.count("You get on the stool.") == 2
    assert out.count("You get off the stool.") == 2
    assert "aren't inside anything" in out
