# test_seatwalk.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A walk that begins on or in something leaves it for real (Stefan's
ruling, 2026-08-24, the field reports): the seat's own on exit handlers
run and may stop the walk, exactly as GET OFF runs them; the report is
silence, or foresight's promise line spoken before the handler
(promise-then-run, the granule's doctrine). And the German reflexive
SETZ DICH AUF X, which arrives through the put family, forwards to
enter so the seat's on enter fires (the Erledigt report). Driven on the
Actaea core."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

EN = (
    'game\n    title "EN"\n    start hall\n%s'
    'room hall\n    name "Hallway"\n    desc "A hall."\n    north yard\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n'
    'thing bench of supporter in hall\n    name "bench"\n    words bench\n'
    '    fixed\n'
    '    on enter\n        say "Ahhh, nice to sit here..."\n        continue\n'
    '    on exit\n        say "You stretch as you rise."\n        continue\n'
)

DE = (
    'game\n    title "DE"\n    start halle\nsummon.language "german"\n%s'
    'room halle\n    name "Halle"\n    desc "Eine Halle."\n    north hof\n'
    'room hof\n    name "Hof"\n    desc "Ein Hof."\n'
    'thing bank of supporter in halle\n    die\n    name "Bank"\n'
    '    words bank\n    fixed\n'
    '    on enter\n        say "ENTER GEFEUERT"\n        continue\n'
    '    on exit\n        say "EXIT GEFEUERT"\n        continue\n'
)


def _play(src, cmds):
    story = generate(analyze(cosmos.combined_program(parse(src))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_a_walk_exits_the_seat_with_its_handlers():
    out = _play(EN % "", ["sit on bench", "look", "n"])
    # The seat's handlers fire on the way in and on the walk out...
    assert "Ahhh, nice to sit here..." in out
    assert "You stretch as you rise." in out
    # ...the walk lands (the yard describes), with no get-off chatter...
    assert "A yard." in out
    assert "You get off" not in out
    # ...the look title nests, and the player never lists as contents.
    assert "Hallway (on the bench)" in out
    assert "contains yourself" not in out


def test_a_blocking_exit_handler_stops_the_walk():
    src = (EN % "").replace(
        '    on exit\n        say "You stretch as you rise."\n'
        '        continue\n',
        '    on exit\n        say "The bench refuses to let go."\n'
        '        stop\n')
    out = _play(src, ["sit on bench", "n", "look"])
    assert "The bench refuses to let go." in out
    assert "A yard." not in out                    # the walk never happened
    assert "Hallway (on the bench)" in out         # still seated


def test_foresight_promises_before_the_seat_speaks():
    out = _play(EN % "summon.foresight\n", ["sit on bench", "n"])
    promise = out.index("(getting up from the bench first)")
    handler = out.index("You stretch as you rise.")
    assert promise < handler                       # promise-then-run
    assert "A yard." in out


def test_german_setz_dich_reaches_enter():
    out = _play(DE % "", ["setz dich auf die bank", "schau",
                          "gehe nach norden"])
    assert "ENTER GEFEUERT" in out                 # the seat's own handler
    assert "Erledigt." not in out                  # never the put report
    assert "Halle (auf der Bank)" in out           # the nested title
    assert "EXIT GEFEUERT" in out                  # the walk exits for real
    assert "Ein Hof." in out


def test_german_foresight_speaks_the_dative():
    out = _play(DE % "summon.foresight\n",
                ["setz dich auf die bank", "gehe nach norden"])
    assert "(zuerst stehst du von der Bank auf)" in out
    assert out.index("(zuerst stehst du") < out.index("EXIT GEFEUERT")


def test_german_reports_the_posture_typed():
    """Sitting and being on top of something are not the same (Stefan,
    2026-08-24): the German report conjugates the player's own verb
    back. The posture is captured in the pack's put-to-enter redirect,
    BEFORE the perform (which rightly clears verb_trigger: an enter
    nobody typed has no typed word)."""
    src = (
        'game\n    title "DE"\n    start halle\nsummon.language "german"\n'
        'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
        'thing bank of supporter in halle\n    die\n    name "Bank"\n'
        '    words bank\n    fixed\n'
        'thing kiste of container in halle\n    die\n    name "Kiste"\n'
        '    words kiste\n    fixed\n    open\n'
    )
    out = _play(src, [
        "setz dich auf die bank", "verlasse die bank",
        "leg dich auf die bank", "verlasse die bank",
        "stell dich auf die bank", "verlasse die bank",
        "besteige die bank", "verlasse die bank",
        "setz dich in die kiste"])
    assert "Du setzt dich auf die Bank." in out
    assert "Du legst dich auf die Bank." in out
    assert "Du stellst dich auf die Bank." in out
    assert "Du steigst auf die Bank." in out      # the climbing word keeps it
    assert "Du setzt dich in die Kiste." in out


def test_posture_speaks_in_every_language():
    """Posture is a core concept (Stefan's ruling, 2026-08-25): each pack
    maps its own sitting words in posture_note, the value lives while the
    seat is occupied, and boarding, leaving, and foresight's exit promise
    all word it. Sitting is not standing on top."""
    en = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hallway"\n    desc "A hall."\n'
        'thing bench of supporter in hall\n    name "bench"\n'
        '    words bench\n    fixed\n'
    )
    out = _play(en, ["sit on bench", "get off bench", "mount bench",
                     "get off bench"])
    assert "You sit down on the bench." in out
    assert "You get up from the bench." in out
    assert "You get on the bench." in out          # mounting stays a climb
    assert "You get off the bench." in out

    es = (
        'game\n    title "ES"\n    start sala\nsummon.language "spanish"\n'
        'room sala\n    name "Sala"\n    desc "Una sala."\n'
        'thing banca of supporter in sala\n    name "banca"\n'
        '    words banca\n    fixed\n'
    )
    out = _play(es, ["siéntate en la banca", "sal de la banca",
                     "entra en la banca", "sal de la banca"])
    assert "Te sientas en la banca." in out
    assert "Te levantas de la banca." in out
    assert "Te subes a la banca." in out
    assert "Te bajas de la banca." in out

    de = (
        'game\n    title "DE"\n    start halle\nsummon.language "german"\n'
        'room halle\n    name "Halle"\n    desc "Eine Halle."\n'
        'thing bank of supporter in halle\n    die\n    name "Bank"\n'
        '    words bank\n    fixed\n'
    )
    out = _play(de, ["setz dich auf die bank", "verlasse die bank",
                     "stell dich auf die bank", "verlasse die bank",
                     "besteige die bank", "verlasse die bank"])
    assert "Du stehst von der Bank auf." in out         # after sitting
    assert "Du steigst von der Bank herunter." in out   # after standing
    assert out.index("Du stehst von der Bank auf.") < out.index(
        "Du stellst dich auf die Bank.")
