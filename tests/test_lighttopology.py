# test_lighttopology.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""summon.lighttopology (docs/01 chapters 7 and 22): light as a level that
travels. Levels combine by maximum; a lit room spills one level less
through a doorless exit or an open door, one hop; a closed door seals it;
a thing with needs_light N is unseen below level N, carried things
excepted. The core asks is_lit and light_dims behind the any_lighttopology
fold, so a game that never summons the granule is byte-identical (the
untouched ceilings in test_sizes)."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

WORLD = (
    'summon.lighttopology\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
    '    north cellar\n    east oak_door\n'
    'room cellar\n    name "Cellar"\n    desc "Low and black."\n'
    '    lit false\n    south hall\n'
    'room study\n    name "Study"\n    desc "Books."\n'
    '    lit false\n    west oak_door\n'
    'thing oak_door of door in hall, study\n    name "oak door"\n'
    '    words door, oak\n'
    'thing scrawl in cellar\n    name "scrawl"\n    words scrawl\n'
    '    scenery\n    fixed\n    needs_light 2\n    desc "MIND THE STEP."\n'
    'thing coin in cellar\n    name "coin"\n    words coin\n'
    'thing candle in hall\n    name "candle"\n    words candle\n'
    '    binary\n    glow\n    light 1\n'
    'thing lantern in hall\n    name "lantern"\n    words lantern\n'
    '    binary\n    glow\n'
    'verb "level"\n    vlevel\n'
    'on vlevel\n    say "Level ${light_level}."\n'
)


def _run(start, cmds):
    return _run_src(f'game\n    title "LT"\n    start {start}\n' + WORLD, cmds)


def _run_src(src, cmds):
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    return io.text


def test_a_lit_room_spills_one_level_through_a_doorway():
    out = _run("hall", ["level", "north", "level", "examine scrawl",
                        "take coin"])
    assert "Level 2." in out.split(">north")[0]
    cellar = out.split(">north")[1]
    assert "Low and black." in cellar          # dimly lit, not pitch black
    assert "You can see a coin here." in cellar
    assert "Level 1." in cellar
    assert "nothing of the sort" in out.split(">examine scrawl")[1]  # too dim
    assert "You take the coin" in out


def test_levels_combine_by_maximum_and_a_threshold_lifts():
    out = _run("hall", ["take candle", "turn on candle", "north", "level",
                        "examine scrawl", "south", "take lantern",
                        "turn on lantern", "north", "level", "examine scrawl",
                        "turn off lantern", "level"])
    parts = out.split(">level")
    assert "Level 1." in parts[1]              # candle (1) adds nothing to 1
    assert "nothing of the sort" in parts[1]
    assert "Level 2." in parts[2]              # lantern (2) lifts it
    assert "MIND THE STEP." in parts[2]
    assert "Level 1." in parts[3]              # and back after switching off


def test_a_closed_door_seals_light_and_opening_it_lets_it_through():
    # Sealed: the unlit study behind the closed door is pitch dark (the
    # door itself is then out of scope, the darkness model's own rule, so
    # the opening happens from the lit side).
    out = _run("study", ["level"])
    assert "Pitch black" in out.split(">level")[0]
    assert "Level 0." in out
    out = _run("hall", ["open door", "east", "level"])
    study = out.split(">east")[1]
    assert "Books." in study                   # the chapel's light reaches in
    assert "Level 1." in study


def test_carried_things_are_never_dimmed():
    src = WORLD.replace('thing coin in cellar', 'thing coin in player')
    src = src.replace('    words coin\n', '    words coin\n    needs_light 3\n', 1)
    full = 'game\n    title "LT"\n    start cellar\n' + src
    story = generate(analyze(cosmos.combined_program(parse(full))))
    io = CaptureIO(script=["inventory"])
    try:
        VM(load(story), io).run(max_steps=30_000_000)
    except IndexError:
        pass
    assert "coin" in io.text.split(">inventory")[1]


def test_light_default_moves_the_ambient_at_runtime():
    # EdwardianDuck's suggestion (2026-10-02): the strength of a lit room
    # or source that declares no `light` is a global, so night can fall.
    src = WORLD + (
        'verb "nightfall"\n    vnight\n'
        'on vnight\n    change light_default to 1\n    say "Night falls."\n'
    )
    out = _run_src('game\n    title "LT"\n    start hall\n' + src,
                   ["level", "nightfall", "level", "north", "level"])
    parts = out.split(">level")
    assert "Level 2." in parts[1]
    assert "Level 1." in parts[2]                 # the hall's own light, now 1
    assert "Level 0." in parts[3]                 # 1 less one spills nothing
    assert "Pitch black" in out.split(">north")[1]


def test_a_clear_door_passes_light():
    src = WORLD.replace('    words door, oak\n', '    words door, oak\n    clear\n')
    out = _run_src('game\n    title "LT"\n    start study\n' + src, ["level"])
    assert "Books." in out.split(">level")[0]     # lit through the glass
    assert "Level 1." in out
