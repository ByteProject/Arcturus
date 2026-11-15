# test_takeall_put.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""PUT ALL ON or IN a holder (summon.takeall; improvmonster's report,
2026-11-10). Two parts: an ALL in the first slot of a two-noun command
used to fault as a missing object ("You see nothing of the sort here."),
so the resolvers now bind only the target and hand the sweep over; and
put_all / insert_all sweep what the player carries, each item a full put
or insert. An ALL the granule does not sweep (GIVE ALL TO) says "One thing
at a time." like EAT ALL. Every pack, both grammar models."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def _run(src, cmds):
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=40_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


GAME = (
    'summon.takeall\n'
    'game\n    title "T"\n    start kitchen\n'
    'room kitchen\n    name "Kitchen"\n    desc "Tiles."\n'
    'thing tray of supporter in kitchen\n    name "tray"\n    words tray\n'
    'thing bowl of container in kitchen\n    name "bowl"\n    words bowl\n    open\n'
    'thing tin of container in kitchen\n    name "tin"\n    words tin\n    openable\n'
    'thing cup in kitchen\n    name "cup"\n    words cup\n'
    'thing pea in kitchen\n    name "pea"\n    words pea\n'
    'thing glove in player\n    name "glove"\n    words glove\n    wearable\n    worn\n'
    'thing cook of character in kitchen\n    name "cook"\n    words cook\n'
)


def test_put_all_on_a_supporter_sweeps_what_is_carried():
    out = _run(GAME, ["take all", "put all on tray"])
    assert "cup: You put the cup on the tray." in out
    assert "pea: You put the pea on the tray." in out
    assert "bowl: You put the bowl on the tray." in out
    # the target itself and the worn glove are not swept
    assert "tray: You put" not in out and "glove:" not in out
    assert "nothing of the sort" not in out


def test_put_all_in_and_into_a_container():
    out = _run(GAME, ["take cup", "take pea", "put all in bowl",
                      "take all from bowl", "put all into bowl"])
    assert out.count("cup: You put the cup in the bowl.") == 2
    assert out.count("pea: You put the pea in the bowl.") == 2


def test_a_shut_container_or_a_non_holder_refuses_once():
    out = _run(GAME, ["take cup", "take pea", "put all in tin",
                      "put all on cup"])
    assert out.count("The tin is shut.") == 1
    assert out.count("won't hold it.") == 1
    assert "cup:" not in out


def test_empty_handed_and_unswept_verbs():
    out = _run(GAME, ["put all on tray", "give all to cook", "put all on"])
    assert "You're carrying precisely nothing." in out
    assert out.count("One thing at a time.") == 2
    assert "nothing of the sort" not in out


def test_a_story_can_hook_the_sweep():
    src = GAME + (
        'on insert_all when here is kitchen\n'
        '    say "(Into the ${noun} it all goes.)"\n'
        '    continue\n'
    )
    src = src.replace(
        'thing tray of supporter in kitchen\n    name "tray"\n    words tray\n',
        'thing tray of supporter in kitchen\n    name "tray"\n    words tray\n'
        '    on put_all\n        say "The tray wobbles; one thing at a time."\n')
    out = _run(src, ["take cup", "take pea", "put all on tray",
                     "put all in bowl"])
    # the target's own handler answers first, as TAKE ALL FROM's source does
    assert "The tray wobbles; one thing at a time." in out
    assert "cup: You put the cup on the tray." not in out
    # a room-level hook comments and continues into the sweep
    assert "(Into the bowl it all goes.)" in out
    assert "cup: You put the cup in the bowl." in out


def test_without_the_granule_nothing_changes():
    src = GAME.replace("summon.takeall\n", "")
    out = _run(src, ["take cup", "put cup on tray"])
    assert "You put the cup on the tray." in out


DE = (
    'summon.language "german"\n'
    'summon.takeall\n'
    'game\n    title "T"\n    start kueche\n'
    'room kueche\n    name "Küche"\n    desc "Fliesen."\n'
    'thing tablett of supporter in kueche\n    name "Tablett"\n    words tablett\n    das\n'
    'thing schale of container in kueche\n    name "Schale"\n    words schale\n    die\n    open\n'
    'thing tasse in kueche\n    name "Tasse"\n    words tasse\n    die\n'
    'thing erbse in kueche\n    name "Erbse"\n    words erbse\n    die\n'
)


def test_german_puts_all():
    out = _run(DE, ["nimm tasse", "nimm erbse", "leg alles auf das tablett",
                    "nimm tasse", "nimm erbse", "steck alles in die schale",
                    "nimm alles aus der schale", "untersuche tablett",
                    "leg alles darauf"])
    assert out.count("Tasse: Du legst die Tasse auf das Tablett.") == 2
    assert out.count("Erbse: Du legst die Erbse auf das Tablett.") == 2
    assert "Tasse: Du legst die Tasse in die Schale." in out
    assert "So etwas siehst du hier nicht." not in out


ES = (
    'summon.language "spanish"\n'
    'summon.takeall\n'
    'game\n    title "T"\n    start cocina\n'
    'room cocina\n    name "Cocina"\n    desc "Azulejos."\n'
    'thing bandeja of supporter in cocina\n    name "bandeja"\n    words bandeja\n    feminine\n'
    'thing cuenco of container in cocina\n    name "cuenco"\n    words cuenco\n    open\n'
    'thing taza in cocina\n    name "taza"\n    words taza\n    feminine\n'
    'thing guisante in cocina\n    name "guisante"\n    words guisante\n'
)


def test_spanish_puts_all():
    out = _run(ES, ["coge taza", "coge guisante", "pon todo sobre la bandeja",
                    "coge todo de la bandeja", "mete todo en el cuenco"])
    assert out.count("taza:") >= 3 and out.count("guisante:") >= 3
