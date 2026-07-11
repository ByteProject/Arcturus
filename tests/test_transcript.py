# test_transcript.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The transcript meta verb (output stream 2). TRANSCRIPT / SCRIPT starts
one, TRANSCRIPT OFF / UNSCRIPT ends it; the interpreter owns the file and
reports the truth in Flags 2 bit 0, so the library's on/off/already lines
are honest. German words it MITSCHRIFT/PROTOKOLL AN/AUS; Spanish
TRANSCRIPCION and TRANSCRIPCION NO (its first particle)."""

import pytest

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

GAME = (
    'game\n    title "T"\n    start den\n'
    'room den\n    name "Den"\n    desc "A quiet den."\n'
)

GERMAN = (
    'game\n    title "T"\n    start bau\n'
    'summon.language "german"\n'
    'room bau\n    name "Bau"\n    desc "Eine stille Kammer."\n'
)

SPANISH = (
    'game\n    title "T"\n    start sala\n'
    'summon.language "spanish"\n'
    'room sala\n    name "Sala"\n    desc "Una sala tranquila."\n'
)

_STORY = {}


def _run(cmds, game=GAME, save_dir=None):
    if game not in _STORY:
        _STORY[game] = generate(analyze(cosmos.combined_program(parse(game))))
    io = CaptureIO(script=list(cmds), save_dir=save_dir)
    try:
        VM(load(_STORY[game]), io).run(max_steps=20_000_000)
    except IndexError:
        pass  # script exhausted at the next prompt
    return io.text


def test_transcript_on_off_and_state_lines(tmp_path):
    out = _run(
        ["transcript off", "transcript", "look", "transcript",
         "script off", "unscript"],
        save_dir=str(tmp_path),
    )
    # Honest state first: nothing to stop before anything started.
    assert "No transcript is running." in out
    assert "Transcript on. Everything from here is being recorded." in out
    assert "The transcript is already running." in out
    assert "Transcript off." in out
    # unscript after script off: honest again.
    assert out.count("No transcript is running.") == 2


def test_transcript_file_holds_the_session(tmp_path):
    _run(["transcript", "look", "transcript off"], save_dir=str(tmp_path))
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    text = files[0].read_text()
    assert "A quiet den." in text            # play was recorded
    assert "Transcript off." in text         # the closing line made it in


def test_particle_exception_stays_tight():
    # "jump on": the on particle compounds with nothing for jump, so the
    # extra-words honesty still refuses it.
    out = _run(["jump on"])
    assert "lost me" in out


def test_german_mitschrift(tmp_path):
    out = _run(
        ["mitschrift", "schau", "mitschrift an", "protokoll aus", "mitschrift aus"],
        game=GERMAN, save_dir=str(tmp_path),
    )
    assert "Mitschrift läuft. Ab jetzt wird alles aufgezeichnet." in out
    assert "Die Mitschrift läuft schon." in out
    assert "Mitschrift beendet." in out
    assert "Es läuft gerade keine Mitschrift." in out


def test_english_fallback_in_german(tmp_path):
    # The English meta words answer in a German game, with German replies.
    out = _run(
        ["transcript", "schau", "transcript on", "transcript off", "unscript"],
        game=GERMAN, save_dir=str(tmp_path),
    )
    assert "Mitschrift läuft. Ab jetzt wird alles aufgezeichnet." in out
    assert "Die Mitschrift läuft schon." in out
    assert "Mitschrift beendet." in out
    assert "Es läuft gerade keine Mitschrift." in out


def test_spanish_transcripcion(tmp_path):
    out = _run(
        ["transcripcion", "mira", "transcripcion", "transcripcion no",
         "transcripcion no"],
        game=SPANISH, save_dir=str(tmp_path),
    )
    assert "Transcripción en marcha. Desde aquí queda todo registrado." in out
    assert "La transcripción ya está en marcha." in out
    assert "Transcripción finalizada." in out
    assert "No hay ninguna transcripción en marcha." in out


def test_english_fallback_in_spanish(tmp_path):
    # The English meta words answer in a Spanish game, with Spanish replies.
    out = _run(
        ["transcript", "mira", "transcript on", "transcript off", "unscript"],
        game=SPANISH, save_dir=str(tmp_path),
    )
    assert "Transcripción en marcha. Desde aquí queda todo registrado." in out
    assert "La transcripción ya está en marcha." in out
    assert "Transcripción finalizada." in out
    assert "No hay ninguna transcripción en marcha." in out
