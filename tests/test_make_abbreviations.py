# test_make_abbreviations.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The opt-in per-game abbreviation pass (B6): `arcc --make-abbreviations` writes
an abbreviations.granule the story summons by name, which the loader reads as
compile-time data (not runtime blocks) and hands to the encoder in place of the
built-in default. The granule round-trips exactly, the dotted form is refused, and
a tuned build plays and is no larger than the default. Driven on Frotz."""

import shutil
import subprocess

import pytest

from arcturus import ast, cosmos, zstring
from arcturus.cli import main as cli_main
from arcturus.codegen import generate
from arcturus.errors import ArcError
from arcturus.parser import parse
from arcturus.sema import analyze

GAME = (
    'game\n    title "Abbrev"\n    author "Test"\n    serial "000000"\n'
    '    start cell\n'
    'room cell\n    name "The Long Room"\n'
    '    desc "A long, long room, with a long table and a long bench, running the '
    'length of the long wall, and nothing else of interest anywhere at all."\n'
)


def test_granule_round_trips_including_tricky_characters():
    tricky = ['the ', ' You', 'a "quote"', 'back\\slash', 'a $ sign', 'line\nbreak', ': "']
    src_lines = ['abbreviations'] + ['    ' + cosmos._quote(s) for s in tricky]
    got = cosmos.extract_abbreviations("\n".join(src_lines), "abbreviations.granule")
    assert got == tricky


def test_whitespace_run_is_dropped_not_corrupted(tmp_path):
    out = tmp_path / "abbreviations.granule"
    # "two  spaces" has a run the lexer would collapse; it must be dropped, and the
    # faithful entries kept in order.
    cosmos.write_abbreviations_granule(str(out), ["the ", "two  spaces", "You"], "g.storyarc")
    got = cosmos.extract_abbreviations(out.read_text(), "abbreviations.granule")
    assert got == ["the ", "You"]


def test_dotted_summon_abbreviations_is_refused():
    prog = parse(GAME + "summon.abbreviations\n", "g.storyarc")
    with pytest.raises(ArcError) as exc:
        cosmos.combined_program(prog)
    assert "make-abbreviations" in str(exc.value)


def test_make_abbreviations_writes_and_is_used(tmp_path):
    story = tmp_path / "game.storyarc"
    story.write_text(GAME)
    rc = cli_main(["--make-abbreviations", str(story)])
    assert rc == 0
    granule = tmp_path / "abbreviations.granule"
    assert granule.is_file()
    abbrevs = cosmos.extract_abbreviations(granule.read_text(), "abbreviations.granule")
    assert abbrevs  # a set was chosen
    # Summoning it by name attaches the set to the world as compile-time data.
    story.write_text(GAME + "summon abbreviations.granule\n")
    world = analyze(
        cosmos.combined_program(parse(story.read_text(), str(story)), story_dir=str(tmp_path))
    )
    assert world.abbreviations == abbrevs


def _frotz():
    return shutil.which("dfrotz") or shutil.which("frotz")


@pytest.mark.skipif(_frotz() is None, reason="no Frotz interpreter on PATH")
def test_tuned_build_plays_and_is_no_larger(tmp_path):
    story = tmp_path / "game.storyarc"
    story.write_text(GAME)
    default = generate(analyze(cosmos.combined_program(parse(GAME, str(story)))))

    assert cli_main(["--make-abbreviations", str(story)]) == 0
    story.write_text(GAME + "summon abbreviations.granule\n")
    tuned = generate(
        analyze(cosmos.combined_program(parse(story.read_text(), str(story)), story_dir=str(tmp_path)))
    )
    # A tuned set never does worse than the default on the game it was built for.
    assert len(tuned) <= len(default)

    z5 = tmp_path / "tuned.z5"
    z5.write_bytes(tuned)
    out = subprocess.run(
        [_frotz(), "-p", str(z5)], input="look\nquit\ny\n",
        capture_output=True, text=True, timeout=15,
    ).stdout
    # The compressed text decodes back to exactly the room description (the
    # interpreter word-wraps, so compare with whitespace normalized).
    assert "running the length of the long wall" in " ".join(out.split())


def test_harvest_pool_mirrors_the_shipping_file():
    # The tuner's corpus is the story, not the build process. generate() runs
    # twice (a census pass with pooling off, then the real build), and the
    # census also encodes each pooling candidate while costing it; none of
    # that text ships. Before the pause an adopter's thrice-said constant
    # entered the pool five times for its one stored string, and every
    # once-printed sentence entered twice, so max-length fragments of
    # unrepeated text outscored the real recurring words. The pool must hold
    # pooled text once and inline text once per live site, exactly what the
    # file carries.
    from arcturus.codegen import harvest_strings

    sentence = ('He vanished in a puff of smoke. That laser gun is a lot '
                'more powerful than you imagined.')

    def world_with(handlers):
        src = (f'constant puff = "{sentence}"\n' + GAME
               + 'thing wand in cell\n    name "wand"\n    words wand\n'
               + handlers)
        return analyze(cosmos.combined_program(parse(src)))

    # Long text said from three sites is pooled: stored once, harvested once.
    pool = harvest_strings(world_with(
        '    on examine\n        say puff\n'
        '    on take\n        say puff\n'
        '    on drop\n        say puff\n'))
    assert sum(1 for s in pool if sentence in s) == 1

    # Text too short to pool stays inline at each site: three copies ship,
    # three copies harvested.
    pool = harvest_strings(world_with(
        '    on examine\n        say "Zut!"\n'
        '    on take\n        say "Zut!"\n'
        '    on drop\n        say "Zut!"\n'))
    assert sum(1 for s in pool if s == "Zut!") == 3

    # And a sentence said once appears once, so its fragments can never
    # clear the tuner's two-occurrence prune on their own.
    pool = harvest_strings(world_with(
        '    on examine\n        say puff\n'))
    assert sum(1 for s in pool if sentence in s) == 1
