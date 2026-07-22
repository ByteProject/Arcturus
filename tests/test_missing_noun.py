# test_missing_noun.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""A two-noun verb (give/show/put/...) whose FIRST noun does not resolve must not
run, and must not dispatch to the recipient's own handler with a nothing noun.
Before the fix, `give sdlfkj to bob` (an unknown word) slid past the parser with
noun = nothing and ran Bob's `on give`, which then read the noun and printed
garbage or crashed. The parser now faults a named-but-unresolved noun, and
dispatch withholds the recipient's handler when there is no first noun at all."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

# Bob reacts to give/show, and the box (a container) to put; each handler READS
# the noun, so a nothing noun would crash if the handler ever ran wrongly.
GAME = (
    'game\n    title "T"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "x"\n'
    'thing coin in hall\n    name "coin"\n    words coin\n'
    'thing box of container in hall\n    name "box"\n    words box\n    open\n'
    '    on put\n        say "PUT ${the noun}. "\n'
    'thing bob of character in hall\n    name "Bob"\n    words bob\n    named\n'
    '    on give\n        say "GIVE ${the noun}. "\n'
    '    on show\n        say "SHOW ${the noun}. "\n'
)


def _run(cmd):
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=[cmd])
    try:
        VM(story, io).run(max_steps=5_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    at = io.text.rindex(">" + cmd)
    return io.text[at:at + 90].split("\n")[1]


def test_garbage_first_noun_does_not_run_the_recipient_handler():
    # An unknown word in the thing slot: rejected, the recipient never reacts.
    for cmd in ("give sdlfkj to bob", "show sdlfkj to bob", "put sdlfkj in box"):
        out = _run(cmd)
        assert 'know the word "sdlfkj"' in out, cmd
        assert "GIVE" not in out and "SHOW" not in out and "PUT" not in out, cmd


def test_empty_first_noun_does_not_run_the_recipient_handler():
    # "give to bob": nothing is being given, so Bob has nothing to react to and
    # never sees a nothing noun.
    out = _run("give to bob")
    assert "GIVE" not in out
    assert "sort" in out or "what" in out.lower()


def test_garbage_recipient_faults():
    # A named-but-unresolved recipient is rejected, not treated as "to whom".
    out = _run("give coin to sdlfkj")
    assert 'know the word "sdlfkj"' in out
    assert "GIVE" not in out


def test_valid_two_noun_still_dispatches_to_the_recipient():
    # The coin starts in the room and the contract requires a carried gift
    # (requires give noun carried, phase 2), so take it first. _run scripts
    # one command per entry; the helper splits on the last prompt.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=["take coin", "give coin to bob"])
    try:
        VM(story, io).run(max_steps=5_000_000)
    except IndexError:
        pass
    assert "GIVE the coin." in io.text
    io = CaptureIO(script=["take coin", "show coin to bob"])
    try:
        VM(story, io).run(max_steps=5_000_000)
    except IndexError:
        pass
    assert "SHOW the coin." in io.text
    # PUT declares no requirement (its default handler asks its own
    # questions), so the original single-command shape still holds.
    assert "PUT the coin." in _run("put coin in box")
