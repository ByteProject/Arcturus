# test_npcengine.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The NPC engine (summon.npcengine, Stefan's design round 2026-08-18).

The controls: every roster character starts HIBERNATED (inactive, zero
per-turn cost); resume(x)/hibernate(x) flip one, and the same calls on
npc_engine are the master gate, which PRESERVES the per-NPC mix (the
gate ruling, never a broadcast). Hibernated is a process state, not a
fiction state: a frozen character still answers the conversation verbs.
Movement: patrol (a cycle of adjacent rooms, one waypoint pause), wander
(a territory of rooms or a room kind), pursue/send (way_toward, one paid
step per turn; a reached room ends the pursuit). opens_doors opens
closed doors en route, locked still bars. Events ride the ordinary
pipeline: npc_arrives on a reached goal, npc_blocked when a step cannot
be made. Prose follows scope deterministically, in all three languages.
"""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _run(story, cmds, tail=("quit", "y")):
    io = CaptureIO(script=list(cmds) + list(tail))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except SystemExit:
        pass
    return io.text


HEAD = (
    'game\n    title "N"\n    start yard\n'
    'summon.npcengine\n'
    'room yard\n    name "Yard"\n    desc "A walled yard."\n'
    '    north gate\n    east shed\n'
    'room gate\n    name "Gatehouse"\n    desc "The gatehouse."\n'
    '    south yard\n'
    'room shed\n    name "Shed"\n    desc "A tool shed."\n    west yard\n'
)

MARSHAL = (
    'thing marshal of character in yard\n'
    '    name "marshal"\n    words marshal\n    desc "On his rounds."\n'
    '    patrol yard, gate\n'
)


def test_hibernated_by_default_nothing_moves():
    out = _run(_build(HEAD + MARSHAL), ["z", "z", "z", "look"])
    assert "heads" not in out
    assert out.count("You can see a marshal here.") >= 2


def test_resume_starts_the_patrol_with_prose():
    src = HEAD + MARSHAL + "on start\n    resume(marshal)\n"
    out = _run(_build(src), ["z", "z", "z", "z"])
    # yard -> gate ("heads north"), pause, back ("arrives from the north")
    assert "The marshal heads north." in out
    assert "The marshal arrives from the north." in out


def test_hibernate_freezes_one_character():
    src = HEAD + MARSHAL + (
        "on start\n    resume(marshal)\n"
        'verb "stopnow"\n    stopnow\n'
        "on stopnow\n    hibernate(marshal)\n    say \"Stopped.\"\n"
    )
    out = _run(_build(src), ["stopnow", "z", "z", "z", "look"])
    assert "heads" not in out
    assert "You can see a marshal here." in out


def test_master_gate_preserves_the_mix():
    src = HEAD + MARSHAL + (
        'thing cat of character in shed\n'
        '    name "black cat"\n    words black, cat\n    desc "A cat."\n'
        '    territory yard, shed\n'
        # marshal active, cat left hibernated; freeze and thaw the gate
        "on start\n    resume(marshal)\n"
        'verb "freeze"\n    freezeall\n'
        "on freezeall\n    hibernate(npc_engine)\n    say \"Held.\"\n"
        'verb "thaw"\n    thawall\n'
        "on thawall\n    resume(npc_engine)\n    say \"Released.\"\n"
    )
    story = _build(src)
    out = _run(story, ["freeze", "z", "z", "z", "thaw", "z", "z"])
    # while the gate is down nothing moves at all
    frozen = out.split("Held.")[1].split("Released.")[0]
    assert "heads" not in frozen and "arrives" not in frozen
    # after the thaw the marshal walks again, and the cat NEVER walked
    # (its own bit stayed hibernated through the gate cycle: the mix)
    after = out.split("Released.")[1]
    assert "marshal" in after and ("heads" in after or "arrives" in after)
    assert "cat heads" not in out and "cat arrives" not in out


def test_send_walks_pursuit_and_arrival_event_fires_once():
    src = HEAD + (
        'thing warden of character in gate\n'
        '    name "warden"\n    words warden\n    desc "The warden."\n'
        '    npc\n'
        'verb "whistle"\n    whistle\n'
        "on whistle\n    send(warden, shed)\n    say \"You whistle.\"\n"
        "on npc_arrives when noun is warden\n"
        '    say "[the warden made it]"\n'
    )
    out = _run(_build(src), ["whistle", "z", "z", "z", "z", "z"])
    assert out.count("[the warden made it]") == 1  # the pursuit self-clears


def test_opens_doors_really_opens_with_prose():
    src = (HEAD + (
        'thing oak_door of door in gate, yard\n'
        '    name "oak door"\n    words oak, door\n    open false\n'
        'thing warden of character in gate\n'
        '    name "warden"\n    words warden\n    desc "The warden."\n'
        '    npc\n    opens_doors\n'
        'verb "whistle"\n    whistle\n'
        "on whistle\n    send(warden, shed)\n    say \"You whistle.\"\n"
    )).replace("    north gate\n", "    north oak_door\n").replace(
        "    south yard\n", "    south oak_door\n")
    out = _run(_build(src), ["whistle", "z", "z", "z", "x oak door"])
    assert "The warden opens the oak door." in out
    assert "The warden arrives" in out
    # and the door is really open now: examining shows no closed state
    assert "(closed)" not in out.split("opens the oak door")[1]


def test_locked_door_blocks_and_the_event_reports():
    src = (HEAD + (
        'thing oak_door of door in gate, yard\n'
        '    name "oak door"\n    words oak, door\n'
        '    open false\n    lockable\n    locked\n'
        'thing warden of character in gate\n'
        '    name "warden"\n    words warden\n    desc "The warden."\n'
        '    npc\n    opens_doors\n'
        'verb "whistle"\n    whistle\n'
        "on whistle\n    send(warden, shed)\n    say \"You whistle.\"\n"
        "on npc_blocked when noun is warden\n"
        '    say "[stuck]"\n'
    )).replace("    north gate\n", "    north oak_door\n").replace(
        "    south yard\n", "    south oak_door\n")
    out = _run(_build(src), ["whistle", "z", "z"])
    assert "[stuck]" in out
    assert "The warden arrives" not in out


def test_wander_never_leaves_its_territory():
    src = HEAD + (
        'thing cat of character in shed\n'
        '    name "black cat"\n    words black, cat\n    desc "A cat."\n'
        '    territory yard, shed\n'
        "on start\n    resume(cat)\n"
    )
    # the player camps in the gatehouse; the cat roams yard/shed and can
    # never appear here (the gate is outside its territory)
    out = _run(_build(src), ["north"] + ["z"] * 12 + ["look"])
    tail = out.split("Gatehouse")[-1]
    assert "cat" not in tail


def test_territory_takes_a_room_kind():
    src = (
        'game\n    title "K"\n    start meadow\n'
        'summon.npcengine\n'
        'kind outside_room of room\n'
        'room meadow of outside_room\n    name "Meadow"\n    desc "Grass."\n'
        '    east copse\n'
        'room copse of outside_room\n    name "Copse"\n    desc "Trees."\n'
        '    west meadow\n'
        'thing hare of character in copse\n'
        '    name "hare"\n    words hare\n    desc "A hare."\n'
        '    territory outside_room\n'
        "on start\n    resume(hare)\n"
    )
    out = _run(_build(src), ["z", "z", "z", "z"])
    assert "hare" in out  # it moves between the two outside rooms
    assert "arrives" in out or "heads" in out


def test_hibernated_is_process_state_not_fiction():
    out = _run(_build(HEAD + MARSHAL), ["x marshal", "ask marshal about yard"])
    assert "On his rounds." in out
    assert "doesn't seem up for a conversation" in out


def test_patrol_needs_two_rooms():
    src = HEAD + (
        'thing m of character in yard\n    name "m"\n    words m\n'
        '    patrol yard\n'
    )
    with pytest.raises(ArcError, match="at least two rooms"):
        _build(src)


def test_patrol_rejects_a_kind():
    src = (
        'game\n    title "K"\n    start meadow\n'
        'summon.npcengine\n'
        'kind outside_room of room\n'
        'room meadow of outside_room\n    name "Meadow"\n    desc "Grass."\n'
        'thing m of character in meadow\n    name "m"\n    words m\n'
        '    patrol meadow, outside_room\n'
    )
    with pytest.raises(ArcError, match="territory"):
        _build(src)


def test_engine_behavior_needs_a_character():
    src = HEAD + (
        'thing barrel in yard\n    name "barrel"\n    words barrel\n'
        '    patrol yard, gate\n'
    )
    with pytest.raises(ArcError, match="of character"):
        _build(src)


def test_unsummoned_patrol_stays_an_ordinary_property():
    # no summon: the name is the author's own; nothing walks, no error
    src = HEAD.replace("summon.npcengine\n", "") + MARSHAL
    out = _run(_build(src), ["z", "z", "z"])
    assert "heads" not in out


def test_german_prose_speaks_natively():
    src = (
        'game\n    title "D"\n    start hof\n'
        'summon.language "german"\n'
        'summon.npcengine\n'
        'room hof\n    name "Hof"\n    desc "Ein Hof."\n    north tor\n'
        'room tor\n    name "Torhaus"\n    desc "Das Torhaus."\n'
        '    south hof\n'
        'thing wachmann of character in hof\n'
        '    name "Wachmann"\n    named\n    words wachmann\n'
        '    desc "Der Wachmann."\n'
        '    patrol hof, tor\n'
        "on start\n    resume(wachmann)\n"
    )
    out = _run(_build(src), ["warte", "warte", "warte"], tail=("ende", "j"))
    assert "Wachmann geht nach Norden." in out
    assert "Wachmann kommt von Norden." in out


def test_spanish_prose_speaks_natively():
    src = (
        'game\n    title "E"\n    start patio\n'
        'summon.language "spanish"\n'
        'summon.npcengine\n'
        'room patio\n    name "Patio"\n    desc "Un patio."\n    north porton\n'
        'room porton\n    name "Portón"\n    desc "El portón."\n'
        '    south patio\n'
        'thing guardia of character in patio\n'
        '    name "guardia"\n    words guardia\n    desc "El guardia."\n'
        '    patrol patio, porton\n'
        "on start\n    resume(guardia)\n"
    )
    out = _run(_build(src), ["espera", "espera", "espera"], tail=("fin", "s"))
    assert "La guardia se va hacia el norte." in out
    assert "La guardia llega desde el norte." in out


CMD_HEAD = HEAD + (
    'thing marshal2 of character in yard\n'
    '    name "marshal"\n    words marshal\n    desc "On his rounds."\n'
    '    npc\n'
)


def test_command_default_refusal_spends_the_turn():
    out = _run(_build(CMD_HEAD), ["marshal, go north", "look"])
    assert "The marshal has better things to do." in out
    # the player did not move
    assert "Gatehouse" not in out.split("better things")[1].split(">look")[0]


def test_command_handler_complies():
    src = HEAD + (
        'thing clerk of character in yard\n'
        '    name "clerk"\n    words clerk\n    desc "A clerk."\n'
        '    npc\n'
        '    on command\n'
        '        if ordered is action_id("go")\n'
        '            say "\\"On my way,\\" says the clerk."\n'
        '            send(self, here.(way))\n'
        '            stop\n'
        '        continue\n'
    )
    out = _run(_build(src), ["clerk, go north", "z", "look"])
    assert '"On my way," says the clerk.' in out
    assert "The clerk heads north." in out
    # and the clerk is really gone
    assert "clerk" not in out.rsplit("Yard", 1)[1]


def test_ordinary_comma_chains_still_chain():
    out = _run(_build(CMD_HEAD), ["look, look"])
    # word 0 is a verb, so the pre-pass stands aside and the chain runs both
    assert out.count("A walled yard.") >= 3  # opening look + two chained
