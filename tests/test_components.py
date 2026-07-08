# test_components.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Component objects: a thing declared `component` and placed in another
thing is PART OF it (a lever in a machine), our equivalent of Dialog's
#partof. The part is in scope whenever the whole is (a plain thing's
insides never are), take answers that it is part of it, it never lists as
the whole's contents, and the tree carries the relation so the part
follows the whole. Everything folds away without components
(any_components)."""

import shutil
import subprocess

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

MACHINE = (
    'game\n    title "Parts"\n    start lab\n'
    'room lab\n    name "Lab"\n    desc "A lab."\n    east store\n'
    'room store\n    name "Store"\n    desc "Shelves."\n    west lab\n'
    'thing machine in lab\n    name "machine"\n    desc "A humming machine."\n'
    'thing lever in machine\n    name "lever"\n    desc "A brass lever."\n'
    '    component\n'
)


def _build(src):
    return generate(analyze(cosmos.combined_program(parse(src))))


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


def _run(story, cmds, width=80):
    return subprocess.run(
        [_frotz(), "-p", "-w", str(width), str(story)],
        input=cmds, capture_output=True, text=True, timeout=15,
    ).stdout


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_component_is_in_scope_and_stays_attached(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(_build(MACHINE))
    out = _run(story, "x lever\ntake lever\ni\n")
    assert "A brass lever." in out              # in scope through the machine
    assert "That's part of the machine." in out  # take refused, named whole
    assert "lever" not in out.split("part of the machine.")[-1] \
        or "carrying" in out                     # never ended up in inventory


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_component_never_lists_as_contents(tmp_path):
    story = tmp_path / "p.z5"
    story.write_bytes(_build(MACHINE))
    out = _run(story, "look\n")
    assert "machine" in out
    assert "(contains" not in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_component_follows_the_whole(tmp_path):
    # The story moves the machine; the lever must be there too, in scope.
    src = MACHINE + (
        'verb "shove"\n    shove\n'
        'on shove\n    move machine to store\n    say "Shoved."\n'
    )
    story = tmp_path / "p.z5"
    story.write_bytes(_build(src))
    out = _run(story, "shove\neast\nx lever\n")
    assert "A brass lever." in out


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_german_and_spanish_part_of(tmp_path):
    de = (
        'game\n    title "Teile"\n    start labor\nsummon.language "german"\n'
        'room labor\n    name "Labor"\n    desc "Ein Labor."\n'
        'thing maschine in labor\n    name "Maschine"\n    die\n'
        '    desc "Eine Maschine."\n'
        'thing hebel in maschine\n    name "Hebel"\n    desc "Ein Hebel."\n'
        '    component\n'
    )
    story = tmp_path / "de.z5"
    story.write_bytes(_build(de))
    out = _run(story, "untersuche hebel\nnimm hebel\n")
    assert "Ein Hebel." in out
    assert "Das gehört zu der Maschine." in out

    es = (
        'game\n    title "Partes"\n    start taller\nsummon.language "spanish"\n'
        'room taller\n    name "Taller"\n    desc "Un taller."\n'
        'thing maquina in taller\n    name "maquina"\n    feminine\n'
        '    desc "Una maquina."\n'
        'thing palanca in maquina\n    name "palanca"\n    feminine\n'
        '    desc "Una palanca."\n'
        '    component\n'
    )
    story = tmp_path / "es.z5"
    story.write_bytes(_build(es))
    out = _run(story, "examina palanca\ncoge palanca\n")
    assert "Una palanca." in out
    assert "Eso es parte de la maquina." in out


def test_the_fold_sees_components():
    def has(src):
        world = analyze(cosmos.combined_program(parse(src)))
        from arcturus.lower import _any_components
        return _any_components(world)

    plain = MACHINE.replace("    component\n", "")
    assert has(MACHINE) == 1
    assert has(plain) == 0
    # a component-free game does not pay for the feature
    assert len(_build(plain)) < len(_build(MACHINE))


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_plain_thing_insides_still_disappear(tmp_path):
    # The pre-existing rule stands: a non-component inside a plain thing is
    # out of scope (that is what `component` is for).
    plain = MACHINE.replace("    component\n", "")
    story = tmp_path / "p.z5"
    story.write_bytes(_build(plain))
    out = _run(story, "x lever\n")
    assert "A brass lever." not in out
