# test_pronoun_sets.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Multi-role pronoun words (docs/01 chapter 21): German distributes its
pronouns across slots the way the grammar really does. "ihm" is the dative
of masculine AND neuter, "sie" is feminine AND plural, "ihnen" plural only,
while ihn/es/ihr stay exclusive. A word with several slots takes the most
recently mentioned live referent, silently (the ruling of the German round:
pronouns are recency creatures, no ask); whether that referent is still in
scope stays the caller's judgment, so the honest refusal speaks rather than
an older referent sliding in. Pluribus things file under the them slot."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze


def _replies(src, cmds):
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


GAME = (
    'summon.language "german"\n'
    'game\n    title "C"\n    start stube\n'
    'room stube\n    name "Stube"\n    desc "Eine Stube."\n    north kammer\n'
    'room kammer\n    name "Kammer"\n    desc "Eine Kammer."\n    south stube\n'
    'thing kind_obj in stube\n    name "Kind"\n    words kind\n    das\n'
    '    animate\n'
    '    on talk\n        say "[KIND]"\n        stop\n'
    'thing mann in stube\n    name "Mann"\n    words mann\n    der\n'
    '    animate\n'
    '    on talk\n        say "[MANN]"\n        stop\n'
    'thing frau in stube\n    name "Frau"\n    words frau\n    die\n'
    '    animate\n'
    '    on talk\n        say "[FRAU]"\n        stop\n'
    'thing wachen in stube\n    name "Wachen"\n    words wachen\n    die\n'
    '    pluribus\n    animate\n'
    '    on talk\n        say "[WACHEN]"\n        stop\n'
)

ASK = "Du musst schon genau sagen, was gemeint ist."


def test_ihm_reaches_a_neuter_referent():
    # The field failure: das Kind filed under es, and "rede mit ihm" refused.
    out = _replies(GAME, ["untersuche kind", "rede mit ihm"])
    assert "[KIND]" in out


def test_ihm_takes_the_most_recent_of_masc_and_neuter():
    out = _replies(GAME, ["untersuche mann", "untersuche kind", "rede mit ihm"])
    assert "[KIND]" in out and "[MANN]" not in out
    out = _replies(GAME, ["untersuche kind", "untersuche mann", "rede mit ihm"])
    assert "[MANN]" in out and "[KIND]" not in out


def test_ihnen_reaches_the_plural_and_only_the_plural():
    # Pluribus things file under the them slot; "ihnen" is them-only, so a
    # lone feminine referent honestly refuses it.
    out = _replies(GAME, ["untersuche wachen", "rede mit ihnen"])
    assert "[WACHEN]" in out
    out = _replies(GAME, ["untersuche frau", "rede mit ihnen"])
    assert ASK in out


def test_sie_spans_feminine_and_plural_by_recency():
    out = _replies(GAME, ["untersuche frau", "untersuche wachen", "rede mit sie"])
    assert "[WACHEN]" in out
    out = _replies(GAME, ["untersuche wachen", "untersuche frau", "rede mit sie"])
    assert "[FRAU]" in out


def test_ihr_stays_feminine_only():
    # A fresher plural referent never claims the feminine dative.
    out = _replies(GAME, ["untersuche wachen", "untersuche frau", "rede mit ihr"])
    assert "[FRAU]" in out


def test_the_freshest_referent_out_of_scope_refuses():
    # Strict recency, ruled: the Kind left scope, and the pronoun refuses
    # honestly instead of sliding to an older referent.
    out = _replies(GAME, ["untersuche kind", "gehe norden", "rede mit ihm"])
    assert ASK in out


def test_single_role_words_never_pay():
    # A pack without multi-role pronouns records none, so the recency walk
    # folds away (the stub seam); English is the proof.
    w = analyze(cosmos.combined_program(parse(
        'game\n    title "E"\n    start r\nroom r\n    name "R"\n    desc "x"\n'
    )))
    assert w.uses_pronoun_sets is False and w.pronoun_sets == {}
