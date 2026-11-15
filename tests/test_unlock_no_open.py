# test_unlock_no_open.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""UNLOCK opens only what opens (improvmonster's report, 2026-11-15).
Unlocking an unlocked or lockless thing opens it as a convenience, which
suits a chest or a door; a thing that cannot be opened at all (a phone, a
rock) used to be promised the open and then refused it ("so you just open
it." / "The rock doesn't open."). Now it just says so; a LOCKED one still
takes its key. Every pack."""

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
           io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


WORLD = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "{hall}"\n    desc "{desc}"\n'
    'thing key in player\n    name "{key}"\n    words {keyw}\n{keyg}'
    'thing phone in hall\n    name "{phone}"\n    words {phonew}\n{phoneg}'
    '    lockable\n    unseal_with key\n'
    'thing safe in hall\n    name "{safe}"\n    words {safew}\n{safeg}'
    '    lockable\n    locked\n    unseal_with key\n'
    'thing rock in hall\n    name "{rock}"\n    words {rockw}\n{rockg}'
    'thing chest of container in hall\n    name "{chest}"\n    words {chestw}\n{chestg}'
    '    openable\n    lockable\n    unseal_with key\n'
    'thing crate of container in hall\n    name "{crate}"\n    words {cratew}\n{crateg}'
    '    openable\n'
)

EN = WORLD.format(hall="Hall", desc="A hall.", key="key", keyw="key", keyg="",
                  phone="phone", phonew="phone", phoneg="",
                  safe="wall safe", safew="safe", safeg="",
                  rock="rock", rockw="rock", rockg="",
                  chest="chest", chestw="chest", chestg="",
                  crate="crate", cratew="crate", crateg="")


def test_a_thing_that_does_not_open_is_never_promised_the_open():
    out = _run(EN, ["unlock phone", "unlock phone with key", "unlock rock"])
    assert out.count("The phone is already unlocked.") == 2
    assert "Nothing about the rock needs unlocking." in out
    assert "open it" not in out and "doesn't open" not in out


def test_a_locked_thing_that_does_not_open_still_takes_its_key():
    out = _run(EN, ["unlock safe", "unlock safe"])
    assert "You unlock the wall safe with the key." in out
    assert "The wall safe is already unlocked." in out


def test_things_that_open_keep_the_convenience_open():
    out = _run(EN, ["unlock chest", "unlock crate"])
    assert "The chest is already unlocked, so you skip the suspense and open it." in out
    assert "Nothing about the crate needs unlocking, so you just open it." in out
    assert out.count("Open.") == 2


DE = 'summon.language "german"\n' + WORLD.format(
    hall="Halle", desc="Eine Halle.", key="Schlüssel", keyw="schlüssel", keyg="    der\n",
    phone="Telefon", phonew="telefon", phoneg="    das\n",
    safe="Wandtresor", safew="wandtresor, tresor", safeg="    der\n",
    rock="Stein", rockw="stein", rockg="    der\n",
    chest="Truhe", chestw="truhe", chestg="    die\n",
    crate="Kiste", cratew="kiste", crateg="    die\n")


def test_german():
    out = _run(DE, ["schließ telefon auf", "schließ stein auf",
                    "schließ tresor auf", "schließ tresor auf"])
    assert "Das Telefon ist gar nicht abgeschlossen." in out
    assert "Der Stein lässt sich nicht aufschließen." in out
    assert "Der Wandtresor ist gar nicht abgeschlossen." in out
    assert "lässt sich nicht öffnen" not in out


ES = 'summon.language "spanish"\n' + WORLD.format(
    hall="Sala", desc="Una sala.", key="llave", keyw="llave", keyg="    feminine\n",
    phone="teléfono", phonew="teléfono, telefono", phoneg="",
    safe="caja fuerte", safew="caja", safeg="    feminine\n",
    rock="piedra", rockw="piedra", rockg="    feminine\n",
    chest="baúl", chestw="baúl, baul", chestg="",
    crate="cajón", cratew="cajón, cajon", crateg="")


def test_spanish_agrees_in_gender():
    out = _run(ES, ["destranca teléfono", "destranca piedra",
                    "destranca caja", "destranca caja"])
    assert "El teléfono no está cerrado con llave." in out
    assert "La piedra no se puede abrir con llave." in out
    assert "La caja fuerte no está cerrada con llave." in out
