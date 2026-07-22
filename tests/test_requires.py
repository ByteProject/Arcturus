# test_requires.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The declarative verb contract (the verbs overhaul, phase 2). A verb states
what it requires of its operands (`requires give noun carried`, the agnostic
top-level form actions.prelude uses; `requires noun carried` inside a verb
body, the author sugar bound to that verb's actions), compiled onto the
ACTION into requires_map and enforced by the loop BEFORE dispatch. So an
object's handler override owns the response and never the validation: the
field report was an `on give,show` answering for gifts the player did not
hold. Empty slots pass through, their asks belong to the handlers."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "R"\n    start plaza\n'
    'room plaza\n    name "Plaza"\n    desc "A plaza."\n'
    'thing merchant in plaza\n    name "merchant"\n    words merchant\n'
    '    animate\n'
    '    on give,show\n'
    '        say "He is not interested in ${the noun}."\n'
    'thing pebble in plaza\n    name "pebble"\n    words pebble\n'
    'thing ruby in scope\n    name "ruby"\n    words ruby\n'
    'thing anvil in plaza\n    name "anvil"\n    words anvil\n    fixed\n'
)


def _run(src, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_an_unheld_gift_never_reaches_the_handler():
    out = _run(GAME, ["give ruby to merchant"])
    assert "You aren't carrying the ruby." in out
    assert "not interested" not in out


def test_a_held_gift_reaches_the_handler_in_both_orders():
    out = _run(GAME, ["take pebble", "give pebble to merchant"])
    assert "not interested in the pebble" in out
    out = _run(GAME, ["take pebble", "give merchant pebble"])
    assert "not interested in the pebble" in out


def test_an_inanimate_recipient_is_refused_before_dispatch():
    out = _run(GAME, ["take pebble", "give pebble to anvil"])
    assert "not interested" not in out  # no handler spoke
    # the library's animate line did (whatever its current wording)
    assert "aren't carrying" not in out


def test_empty_slots_still_ask_through_the_handler():
    out = _run(GAME, ["take pebble", "give pebble"])
    assert "To whom?" in out


def test_show_shares_the_contract():
    out = _run(GAME, ["show merchant the ruby"])
    assert "You aren't carrying the ruby." in out
    assert "not interested" not in out


def test_the_in_verb_sugar_binds_to_the_verbs_action():
    src = (
        'game\n    title "S"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing idol in hall\n    name "jade idol"\n    words idol, jade\n'
        'verb "sacrifice"\n'
        '    sacrifice noun\n'
        '    requires noun carried\n'
        'on sacrifice\n    say "The idol accepts your devotion."\n'
    )
    out = _run(src, ["sacrifice idol"])
    assert "You aren't carrying the jade idol." in out
    assert "devotion" not in out
    out = _run(src, ["take idol", "sacrifice idol"])
    assert "devotion" in out


def test_the_top_level_form_works_for_author_verbs():
    src = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing drum in hall\n    name "drum"\n    words drum\n'
        'verb "bang"\n'
        '    bang noun\n'
        'requires bang noun carried\n'
        'on bang\n    say "Boom."\n'
    )
    out = _run(src, ["bang drum"])
    assert "aren't carrying" in out and "Boom" not in out


def test_an_unknown_requirement_kind_is_a_clear_error():
    from arcturus.errors import ArcError
    src = (
        'game\n    title "E"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x"\n'
        'verb "lick"\n    lick noun\n    requires noun shiny\n'
        'on lick\n    say "Salty."\n'
    )
    with pytest.raises(ArcError, match="carried"):
        analyze(cosmos.combined_program(parse(src)))


def test_worn_counts_as_carried():
    # Stefan's ruling: `carried` means anywhere on you, worn included.
    src = GAME.replace(
        'thing pebble in plaza\n    name "pebble"\n    words pebble\n',
        'thing cloak in plaza\n    name "velvet cloak"\n    words cloak\n'
        '    wearable\n',
    )
    out = _run(src, ["take cloak", "wear cloak", "give cloak to merchant"])
    assert "not interested in the velvet cloak" in out
