# test_reverse_dative_absent.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The reversed dative names an absent thing (a field report): SHOW JUGGLER
PUPPET with the puppet elsewhere answered the bare-verb ask ("The verb show
requires you to be more specific.") while SHOW THE PUPPET TO JUGGLER honestly
said "You see nothing of the sort here." The probe split only wins when both
sides resolve, so the fall-through matched the recipient alone and dropped
the fact that a thing was named. Both orders must answer alike: a real
object that is not here is a can't-see, an unknown word is spelled back,
and only a genuinely bare command keeps the ask. English and German both
grammar the reversed dative; Spanish does not (the "a" phrasing is the
grammar there) and keeps its ask."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

ABSENT = (
    'game\n    title "T"\n    start hallway\n'
    'room hallway\n    name "Hallway"\n    desc "A hallway."\n    south cellar\n'
    'room cellar\n    name "Cellar"\n    desc "A cellar."\n    north hallway\n'
    'thing juggler of character in hallway\n    name "Juggler"\n    words juggler\n'
    '    named\n    desc "A quiet fellow."\n'
    'thing puppet in cellar\n    name "cloth puppet"\n    words cloth, puppet\n'
    '    desc "A cloth puppet."\n'
)

PRESENT = ABSENT.replace("thing puppet in cellar", "thing puppet in hallway")

ABSENT_DE = (
    'game\n    title "T"\n    start hof\n'
    'summon.language "german"\n'
    'room hof\n    name "Hof"\n    desc "Ein Hof."\n    south schuppen\n'
    'room schuppen\n    name "Schuppen"\n    desc "Ein Schuppen."\n    north hof\n'
    'thing gaukler of character in hof\n    name "Gaukler"\n    article "der"\n'
    '    words gaukler\n    named\n    desc "Ein stiller Bursche."\n'
    'thing puppe in schuppen\n    name "Puppe"\n    article "die"\n'
    '    words puppe\n    desc "Eine Stoffpuppe."\n'
)

_STORY = {}


def _run(cmds, game=ABSENT):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_prepositioned_order_refuses_the_absent_thing():
    out = _run(["show the puppet to juggler"])
    assert "You see nothing of the sort here." in out


def test_reversed_dative_refuses_the_absent_thing():
    # The field report: this answered the bare-verb ask before the fix.
    out = _run(["show juggler the puppet"])
    assert "You see nothing of the sort here." in out
    assert "requires you to be more specific" not in out


def test_reversed_dative_swapped_roles_refuses_too():
    out = _run(["show puppet juggler"])
    assert "You see nothing of the sort here." in out


def test_give_shares_the_fix():
    out = _run(["give juggler the puppet"])
    assert "You see nothing of the sort here." in out
    assert "requires you to be more specific" not in out


def test_bare_recipient_keeps_the_ask():
    out = _run(["show juggler"])
    assert "The verb show requires you to be more specific." in out


def test_unknown_word_is_spelled_back():
    out = _run(["show juggler the zzqx"])
    assert 'This story doesn\'t know the word "zzqx".' in out


def test_present_thing_still_dispatches_both_orders():
    out = _run(
        ["take puppet", "show juggler the puppet", "give juggler the puppet"],
        game=PRESENT,
    )
    assert "You see nothing of the sort here." not in out
    assert "requires you to be more specific" not in out
    # The default refusals prove the actions dispatched with the roles bound.
    assert "not really into that" in out
    assert "doesn't want the cloth puppet" in out


def test_german_reversed_dative_refuses_the_absent_thing():
    out = _run(["zeig gaukler puppe"], game=ABSENT_DE)
    assert "So etwas siehst du hier nicht." in out


def test_german_articled_dative_refuses_the_absent_thing():
    out = _run(["zeig dem gaukler die puppe"], game=ABSENT_DE)
    assert "So etwas siehst du hier nicht." in out


def test_german_bare_recipient_keeps_the_ask():
    out = _run(["zeig gaukler"], game=ABSENT_DE)
    assert "Das Verb zeig verlangt eine genauere Angabe." in out
