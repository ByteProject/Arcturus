# test_pathfinding.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The pathfinding granule (docs/01 chapter 22): GO TO a visited room by
name, FIND a thing you know of, LOOK <direction>. Knowledge is the visited
set: unvisited places are as unknown as places that do not exist, the walk
routes only through rooms the player has seen, and LOOK names only visited
destinations. Every step of a walk is a real turn (daemons and the clock
run), intermediate rooms pass in one breadcrumb line, and the walk stops the
moment the world pushes back. Summoning the granule turns room names into
room vocabulary; `words` on a room overrides. The direction word in LOOK's
answers is spoken as typed, so the nautical granule's AFT answers 'Aft lies
your cabin.'"""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "G"\n    start plaza\n'
    'summon.pathfinding\n'
    'room plaza\n    name "Plaza"\n    desc "A sunlit plaza."\n'
    '    north arcade\n    east alley\n'
    'room arcade\n    name "Arcade"\n    desc "A shaded arcade."\n'
    '    south plaza\n    north attic\n'
    'room attic\n    name "Dusty Attic"\n    desc "A dusty attic."\n'
    '    south arcade\n'
    'room alley\n    name "Alley"\n    desc "A narrow alley."\n'
    '    west plaza\n    north oak_door\n'
    'room cellar\n    name "Cellar"\n    desc "A cold cellar."\n'
    '    south oak_door\n'
    'thing oak_door of door in alley\n    name "oak door"\n'
    '    words oak, door\n    desc "Solid oak."\n    spans cellar\n'
    '    openable\n'
    'thing locket in attic\n    name "silver locket"\n'
    '    words silver, locket\n    desc "A silver locket."\n'
    'counter beats\n'
    'on each_turn\n    beats++\n'
    'verb "beats" meta\n    tally\n'
    'on tally\n    say "beats:${beats}"\n'
)

NAUTICAL = (
    'game\n    title "N"\n    start bridge\n'
    'summon.pathfinding\nsummon.nautical\n'
    'room bridge\n    name "Bridge"\n    desc "The bridge."\n    aft cabin\n'
    'room cabin\n    name "Your Cabin"\n    desc "Your cabin."\n'
    '    fore bridge\n'
)

TWINS = (
    'game\n    title "T"\n    start hub\n'
    'summon.pathfinding\n'
    'room hub\n    name "Hub"\n    desc "A hub."\n'
    '    north north_landing\n    south south_landing\n    east loft\n'
    'room north_landing\n    name "North Landing"\n    desc "A landing."\n'
    '    south hub\n'
    'room south_landing\n    name "South Landing"\n    desc "A landing."\n'
    '    north hub\n'
    'room loft\n    name "Loft"\n    words hayloft\n    desc "A loft."\n'
    '    west hub\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=40_000_000)
    except IndexError:
        pass
    return io.text


def test_unvisited_rooms_are_unknown_places():
    out = _run(["go to attic", "go to nowhere"])
    assert out.count("You don't know that place.") == 2


def test_the_walk_breadcrumbs_and_arrives():
    out = _run(["north", "north", "go to plaza"])
    assert "(through the Arcade)" in out
    # Arrival is an ordinary description, not a breadcrumb.
    assert "A sunlit plaza." in out[out.rindex("(through"):]


def test_every_step_is_a_real_turn():
    # north, north, walk of 2 steps, tally: the walk's two steps each beat.
    out = _run(["north", "north", "go to plaza", "beats"])
    assert "beats:4" in out


def test_already_there_and_bare_ask():
    out = _run(["go to plaza", "go to"])
    assert "You're already there." in out
    assert "The verb go requires you to be more specific." in out


def test_no_known_path_through_a_shut_door():
    # Visit the cellar the honest way, come back, shut the door: the walk
    # then knows no way (closed doors bar, Dialog's rule, ours too).
    out = _run([
        "east", "open oak door", "north", "south", "close oak door",
        "west", "go to cellar",
    ])
    assert "You don't know the way there." in out


def test_look_direction_speaks_knowledge():
    out = _run(["north", "south", "look north", "look east", "look west"])
    assert "North lies the Arcade." in out
    assert "The way east is open, but you haven't been that way yet." in out
    assert "Nothing lies that way." in out


def test_look_at_a_shut_door_names_it():
    out = _run(["east", "look north"])
    assert "North lies the oak door, closed." in out


def test_find_walks_to_the_thing():
    out = _run(["north", "north", "south", "south", "find locket"])
    assert "(setting off for the Dusty Attic)" in out
    assert "You can see a silver locket here." in out


def test_find_in_hand_and_unknown():
    out = _run(["north", "north", "take locket", "find locket", "find grail"])
    assert "The silver locket is right here." in out
    assert "You don't know of any such thing." in out


def test_nautical_directions_speak_as_typed():
    out = _run(["look aft", "aft", "look fore", "go to bridge"], game=NAUTICAL)
    assert "The way aft is open, but you haven't been that way yet." in out
    assert "Fore lies the Bridge." in out
    assert "The bridge." in out.rsplit(">go to bridge", 1)[1]


def test_ambiguous_room_names_ask():
    out = _run(
        ["north", "south", "south", "north", "go to landing"], game=TWINS
    )
    assert "You'll have to be more specific." in out


def test_room_words_override_the_name():
    # The loft declares `words hayloft`: the name word stops matching.
    out = _run(["east", "west", "go to loft", "go to hayloft"], game=TWINS)
    assert "You don't know that place." in out
    assert "A loft." in out.rsplit(">go to hayloft", 1)[1]


# The language companions (the half-arsed lesson, 2026-08-08): summoning
# pathfinding in a German or Spanish game loads the granule's language
# twin (pathfinding_german/_spanish.granule) beside it, grammar and
# wording alike; English loads the _english twin. The logic granule
# itself carries no player-facing words at all.
GERMAN = (
    'summon.language "german"\n'
    'game\n    title "P"\n    start hof\n'
    'summon.pathfinding\n'
    'room hof\n    name "Hof"\n    desc "Ein Hof."\n    north halle\n'
    'room halle\n    name "Halle"\n    die\n    desc "Eine Halle."\n'
    '    south hof\n    north kapelle\n'
    'room kapelle\n    name "Kapelle"\n    die\n    desc "Eine Kapelle."\n'
    '    south halle\n'
    'thing kerze in kapelle\n    name "Kerze"\n    die\n    words kerze\n'
    '    desc "Eine Kerze."\n'
)

SPANISH = (
    'summon.language "spanish"\n'
    'game\n    title "P"\n    start patio\n'
    'summon.pathfinding\n'
    'room patio\n    name "Patio"\n    desc "Un patio."\n    north sala\n'
    'room sala\n    name "Sala"\n    la\n    desc "Una sala."\n'
    '    south patio\n    north capilla\n'
    'room capilla\n    name "Capilla"\n    la\n    desc "Una capilla."\n'
    '    south sala\n'
    'thing vela in capilla\n    name "vela"\n    la\n    words vela\n'
    '    desc "Una vela."\n'
)


def test_german_companion_speaks_german():
    out = _run(
        ["geh zur kapelle", "schau norden", "norden", "norden",
         "schau nach sueden", "geh zum hof", "suche kerze"],
        game=GERMAN,
    )
    assert "Diesen Ort kennst du nicht." in out
    assert "Der Weg in Richtung Norden ist offen" in out
    assert "In Richtung Sueden liegt die Halle." in out
    assert "(durch die Halle)" in out
    assert "(du machst dich auf den Weg zu der Kapelle)" in out


def test_spanish_companion_speaks_spanish():
    out = _run(
        ["ve a la capilla", "mira al norte", "norte", "norte",
         "mira hacia el sur", "ve al patio", "busca vela"],
        game=SPANISH,
    )
    assert "No conoces ese lugar." in out
    assert "El camino hacia el norte está abierto" in out
    assert "Hacia el sur queda la Sala." in out
    assert "(pasas por la Sala)" in out
    assert "(te encaminas hacia la Capilla)" in out
