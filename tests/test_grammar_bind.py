# test_grammar_bind.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Grammar object binding (the spell-verb idiom, a field request,
2026-09-14): a bare grammar word naming a declared object fills that slot
with the object itself, no typed word consumed, so a one-word spell verb
IS the cast action from the first instant: no redirect action, no meta,
a full ordinary turn, and every handler (patterns, the second's own, the
after pass) sees only cast. The bound line rides the positional table;
a game with no bound line is byte-identical (any_binds)."""

import pytest

from arcturus import cosmos
from arcturus import worldmodel as wm
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start lab\n'
    'room lab\n    name "Lab"\n    desc "Bare."\n'
    'kind spell of thing\n'
    'thing veznik_spell of spell in player\n    name "veznik spell"\n'
    '    words veznik, spell\n'
    'thing gate_obj in lab\n    name "iron gate"\n    words iron, gate\n'
    '    on after cast veznik_spell on self\n'
    '        say "The gate shivers."\n'
    '        stop\n'
    'verb "cast"\n    cast noun\n    cast noun on/onto/at noun\n'
    'on cast\n    say "(cast ${the noun})"\n    continue\n'
    'verb "veznik"\n    cast veznik_spell noun\n    cast veznik_spell\n'
    'on after cast\n    say "(default after)"\n'
)

_STORY = {}


def _run(cmds, game=GAME):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_bound_verb_is_the_real_action():
    out = _run(["veznik gate", "veznik", "cast veznik on gate"])
    # VEZNIK GATE and CAST VEZNIK ON GATE are the same turn: the cast
    # pre-check speaks, and the gate's pattern after fires for both.
    assert out.count("(cast the veznik spell)") == 3
    assert out.count("The gate shivers.") == 2
    # the bare bound line casts the spell alone, the default after
    assert "(default after)" in out


def test_bound_verb_ticks_the_clock():
    # The whole point over a meta redirect: a bound cast is a real turn.
    game = GAME + 'verb "clock"\n    clock\non clock\n    say "T=${turns}"\n'
    out = _run(["veznik gate", "veznik gate", "clock"], game)
    # two bound casts ticked twice (the clock prints before its own tick);
    # a meta redirect would have left it at zero
    assert "T=2" in out


def test_quoted_word_stays_vocabulary():
    # Quoting forces the word literal even when an object shares its id.
    game = GAME.replace('verb "veznik"\n    cast veznik_spell noun',
                        'verb "veznik"\n    cast "veznik_spell" noun')
    w = analyze(cosmos.combined_program(parse(game)))
    v = next(v for v in w.verbs if v.words[0] == "veznik")
    quoted_line = v.grammar[0]
    assert isinstance(quoted_line.items[0], wm.ast.Word)
    # the unquoted sibling line still binds, which is the point of the quote
    assert any(isinstance(it, wm.ast.Bind)
               for line in v.grammar for it in line.items)


def test_bind_after_a_slot_is_refused():
    game = GAME.replace("cast veznik_spell noun", "cast noun veznik_spell")
    with pytest.raises(ArcError, match="stands before the typed slot"):
        analyze(cosmos.combined_program(parse(game)))
