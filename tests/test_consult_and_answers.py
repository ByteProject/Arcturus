# test_consult_and_answers.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Phase 6 breadth, as ruled: CONSULT <object> ABOUT <subject> reaches the
object's own inline topics through the shared core scanner (topics parse on
ANY object; a reference book needs no conversation granule), LIGHT is a
switch_on synonym (the lamp-game phrasing), and typed YES/NO are in-world
actions a game answers with `on yes` / `on no` (the Blackwood request),
with flat flavor untended."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

BOOK = (
    'game\n    title "C"\n    start study\n'
    '{summon}'
    'room study\n    name "Study"\n    desc "A study."\n'
    'thing gazetteer in study\n    name "mining gazetteer"\n'
    '    words gazetteer, mining, book\n    fixed\n'
    '    topic mine "The Silverlode" words mine, silver, lode\n'
    '        say "The Silverlode: worked 1878 to 1902, flooded and abandoned."\n'
    '    topic owner "T. Crane" words crane, owner\n'
    '        say "T. Crane, owner of record, vanished with the payroll."\n'
    'thing lamp in study\n    name "oil lamp"\n    words lamp, oil\n'
    '    switchable\n'
    '    on switch_on\n        now lamp is lit\n        say "The lamp flares."\n'
)


def _run(cmds, summon="summon.extendedverbs consult, search\n", src=BOOK):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(
            parse(src.replace("{summon}", summon)))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_consult_reaches_the_objects_topics():
    out = _run(["consult gazetteer about the silver lode"])
    assert "flooded and abandoned" in out
    out = _run(["consult book about crane"])
    assert "vanished with the payroll" in out


def test_consult_misses_fall_to_the_granule_default():
    out = _run(["consult book about weather"])
    assert "has nothing to say on the matter" in out


def test_consult_without_a_subject_asks():
    out = _run(["consult book"])
    assert "about what?" in out


def test_consult_needs_no_conversation_granule():
    # The scanner is core: no conversations, no infocom_talking summoned.
    out = _run(["consult book about lode"])
    assert "flooded and abandoned" in out


def test_consult_coexists_with_infocom_talking():
    src = BOOK + (
        'thing keeper in study\n    name "keeper"\n    words keeper\n'
        '    named\n    animate\n'
        '    topic mine2 "The mine" words mine, silver\n'
        '        say "The keeper spits. \\"Cursed place.\\""\n'
    )
    out = _run(["consult book about silver", "ask keeper about silver"],
               summon="summon.extendedverbs consult, search\nsummon.infocom_talking\n",
               src=src)
    assert "flooded and abandoned" in out
    assert "Cursed place" in out


def test_light_is_switch_on():
    out = _run(["light lamp"])
    assert "The lamp flares." in out


def test_yes_and_no_answer_flat_untended():
    out = _run(["yes", "no"], summon="")
    assert "A firm yes" in out
    assert "Noted" in out


def test_a_game_reads_yes_and_no():
    src = BOOK + (
        'flag asked\n'
        'on yes when asked\n    say "Then it is settled."\n'
        'verb "propose"\n    propose\n'
        'on propose\n    change asked to true\n    say "Well?"\n'
    )
    out = _run(["propose", "yes"], src=src)
    assert "Then it is settled." in out
