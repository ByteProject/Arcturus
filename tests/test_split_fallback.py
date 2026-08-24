# test_split_fallback.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The one-noun retry in the German two-noun resolver (a field report,
2026-08-14): a separator word can be part of ONE object's name ("Tuer aus
Eiche"), and the positional split then read the words after it as an
instrument nobody meant, asking "Was meinst du" about a slot the player
never filled. When a split slot comes up ambiguous or empty and the verb's
grammar does not require a second noun, the whole typed range gets one try
as a single noun; a clean resolve wins. A failed retry restores the split's
own outcome exactly, ask and all."""

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


# Both the chest and the door answer to "eiche", the field game's shape: the
# bare second slot of the split ("oeffne tuer AUS eiche") tied between them.
GAME = (
    'summon.language "german"\n'
    'game\n    title "W"\n    start schenke\n'
    'room schenke\n    name "Schenke"\n    desc "Eine Schenke."\n'
    'thing truhe of container in schenke\n    name "Truhe aus Eiche"\n'
    '    words truhe, eiche\n    die\n'
    '    openable\n'
    '    on open\n        say "[TRUHE]"\n        stop\n'
    'thing tuer in schenke\n    name "Tür aus Eiche"\n'
    '    words tuer, tür, eiche\n    die\n'
    '    openable\n'
    '    on open\n        say "[TUER]"\n        stop\n'
    'thing muenze in schenke\n    name "Münze"\n    words muenze\n    die\n'
    'thing bob in schenke\n    name "Bob"\n    words bob\n    der\n    animate\n'
    '    on give\n        say "[BOB]"\n        stop\n'
    'thing schluessel in schenke\n    name "Schlüssel"\n'
    '    words schluessel\n    der\n'
)


def test_separator_inside_one_name_resolves():
    # The repro: "aus" splits the phrase, the bare "eiche" ties between the
    # Truhe and the Tuer, and the ask was about the instrument slot. The
    # retry reads the whole range as one noun: the Tuer scores 2 (tuer,
    # eiche) against the Truhe's 1, and the door opens without a question.
    out = _replies(GAME, ["oeffne tuer aus eiche"])
    assert "[TUER]" in out
    assert "[TRUHE]" not in out
    assert "Was meinst du" not in out


def test_dative_particle_split_still_binds_two_nouns():
    # "gib muenze an bob": both slots of the split resolve, so the retry
    # never runs and the particle keeps doing its two-noun job.
    out = _replies(GAME, ["nimm muenze", "gib muenze an bob"])
    assert "[BOB]" in out


def test_genuine_ambiguity_still_asks_and_takes_the_answer():
    # "oeffne eiche mit schluessel": the first slot ties, and the whole
    # range ties just the same (the schluessel words are foreign to both
    # candidates), so the retry fails and restores the split's ask, range
    # and weave point included: the answer narrows and the door opens.
    out = _replies(GAME, ["oeffne eiche mit schluessel"])
    assert "Was meinst du" in out
    out = _replies(GAME, ["oeffne eiche mit schluessel", "tuer"])
    assert "[TUER]" in out


def test_empty_second_slot_falls_back_to_one_noun():
    # "oeffne tuer aus holz": "holz" is a known word, but its owner (the
    # Brett) is in another room, so the split's second slot resolves to
    # nothing in scope; the retry reads the whole range as one noun and the
    # known-but-foreign "holz" dilutes harmlessly, as it always has in the
    # one-noun path.
    src = GAME + (
        'room hof\n    name "Hof"\n    desc "Ein Hof."\n'
        'thing brett in hof\n    name "Brett aus Holz"\n'
        '    words brett, holz\n    das\n'
    )
    out = _replies(src, ["oeffne tuer aus holz"])
    assert "[TUER]" in out
    assert "Was meinst du" not in out
