# test_error_provenance.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Error provenance (EdwardianDuck's report, 2026-09-10): the combined
program is analyzed under one filename, the story's, so an error inside
a summoned granule reported the story's name with the granule's line
number, sending the author to a blank line in the wrong file. The
combiner now stamps every declaration with the file it was parsed from,
and sema and codegen attribute errors through the stamp: a granule's
error names the granule, the story's names the story, in both the
semantic and the lowering phase."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

STORY = (
    'summon ed_holders.granule\n'
    'game\n    title "H"\n    start hall\n'
    'room hall\n    name "Hall"\n    desc "A hall."\n'
)


def _compile(tmp_path, granule_src):
    (tmp_path / "ed_holders.granule").write_text(granule_src)
    story = tmp_path / "holders.storyarc"
    story.write_text(STORY)
    program = cosmos.combined_program(
        parse(STORY, str(story)), story_dir=str(tmp_path))
    world = analyze(program, filename=str(story))
    return generate(world)


def test_a_sema_error_names_the_granule(tmp_path):
    granule = (
        'thing shelfthing in hall\n'
        '    name "shelf"\n'
        '    words shelf\n'
        '    on push\n'
        '        msg_putunderdone\n'
    )
    with pytest.raises(ArcError) as err:
        _compile(tmp_path, granule)
    assert err.value.filename == "ed_holders.granule"
    assert err.value.line == 5
    assert "msg_putunderdone" in err.value.message


def test_a_lowering_error_names_the_granule(tmp_path):
    granule = (
        'thing gadget in hall\n'
        '    name "gadget"\n'
        '    words gadget\n'
        '    real\n'
        '    on push\n'
        '        if noun.real is true\n'
        '            say "x"\n'
    )
    with pytest.raises(ArcError) as err:
        _compile(tmp_path, granule)
    assert err.value.filename == "ed_holders.granule"
    assert err.value.line == 6


def test_a_story_error_still_names_the_story(tmp_path):
    story = STORY.replace(
        '    desc "A hall."\n',
        '    desc "A hall."\n    on push\n        msg_notathing\n')
    (tmp_path / "ed_holders.granule").write_text('// empty\n')
    p = tmp_path / "holders.storyarc"
    p.write_text(story)
    with pytest.raises(ArcError) as err:
        analyze(cosmos.combined_program(
            parse(story, str(p)), story_dir=str(tmp_path)),
            filename=str(p))
    assert err.value.filename == str(p)
    assert "msg_notathing" in err.value.message
