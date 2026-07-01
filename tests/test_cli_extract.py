# test_cli_extract.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The library-extraction CLI (B5): --extract-library writes the whole bundled
Cosmos library out for forking, --eject-language writes just english.prelude for
message customization. The library is embedded, but never locked away."""

from arcturus import cli


def test_extract_library_writes_all_files(tmp_path):
    rc = cli.main(["--extract-library", str(tmp_path)])
    assert rc == 0
    names = {p.name for p in tmp_path.glob("*.prelude")}
    # the core library files come out
    assert {"core.prelude", "actions.prelude", "english.prelude", "parser.prelude"} <= names


def test_eject_language_writes_english(tmp_path):
    rc = cli.main(["--eject-language", str(tmp_path)])
    assert rc == 0
    ejected = tmp_path / "english.prelude"
    assert ejected.exists()
    # it really is the language layer (carries the standard messages)
    assert "msg_taken" in ejected.read_text(encoding="utf-8")
