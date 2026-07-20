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


# --- The fork stamp -------------------------------------------------------
#
# A fork wins over the bundled copy silently and forever, so a fork taken today
# keeps compiling long after its base has moved on (the field report: a search
# fork three releases old, read and believed, and the library reported broken).
# Every file arcc writes out now carries the fingerprint of the pristine source
# it came from, and the check compares fingerprints, never version numbers, so
# a fork of a file that has not changed stays quiet however old its version
# reads. The false-positive test below is the whole point of that choice.

def test_ejected_files_carry_a_fork_stamp(tmp_path, monkeypatch):
    from arcturus import cosmos
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--eject-granule", "extendedverbs"]) == 0
    text = (tmp_path / "extendedverbs.granule").read_text(encoding="utf-8")
    stamp = cosmos.read_stamp(text)
    assert stamp is not None
    version, fingerprint = stamp
    assert version == cosmos.COSMOS_VERSION
    # The fingerprint is of the PRISTINE source, not of the stamped file.
    assert fingerprint == cosmos.base_fingerprint(
        cosmos.granule_sources()["extendedverbs.granule"])


def test_extract_library_stamps_every_file(tmp_path):
    from arcturus import cosmos
    assert cli.main(["--extract-library", str(tmp_path)]) == 0
    for p in list(tmp_path.glob("*.prelude")) + list(tmp_path.glob("*.granule")):
        assert cosmos.read_stamp(p.read_text(encoding="utf-8")) is not None, p.name


def test_a_fork_of_an_unchanged_file_is_never_called_aged():
    # THE false-positive guard. The stamp says 0.36.5 and the author has edited
    # the file heavily, but the base it was taken from is byte-identical to the
    # bundled copy, so there is nothing to report. Comparing versions instead of
    # fingerprints would cry wolf here, and a warning that cries wolf is worse
    # than no warning at all.
    from arcturus import cosmos
    pristine = cosmos.granule_sources()["extendedverbs.granule"]
    edited = pristine.replace("You find", "You spot")
    forked = f"// cosmos 0.36.5 base {cosmos.base_fingerprint(pristine)}\n{edited}"
    status, was, now = cosmos.fork_status("extendedverbs.granule", forked)
    assert status == "current"
    assert was == "0.36.5"


def test_a_fork_whose_base_moved_is_aged():
    from arcturus import cosmos
    forked = "// cosmos 0.36.5 base 000000000000\non search\n    stop\n"
    status, was, _ = cosmos.fork_status("extendedverbs.granule", forked)
    assert status == "moved"
    assert was == "0.36.5"


def test_an_unstamped_fork_reports_unknown_age():
    from arcturus import cosmos
    status, was, _ = cosmos.fork_status(
        "extendedverbs.granule", "on search\n    stop\n")
    assert status == "unstamped"
    assert was is None


def test_an_authors_own_granule_is_not_a_fork():
    # Nothing bundled goes by that name, so it is the author's own file and no
    # business of the fork check.
    from arcturus import cosmos
    status, _, _ = cosmos.fork_status("mygame.granule", "block x()\n    return 0\n")
    assert status is None


def test_library_status_lists_forks(tmp_path, capsys):
    from arcturus import cosmos
    pristine = cosmos.granule_sources()["extendedverbs.granule"]
    (tmp_path / "extendedverbs.granule").write_text(
        f"// cosmos 0.36.5 base {cosmos.base_fingerprint(pristine)}\n{pristine}",
        encoding="utf-8")
    (tmp_path / "statusline.granule").write_text(
        "// cosmos 0.36.5 base 000000000000\nblock x()\n    return 0\n",
        encoding="utf-8")
    (tmp_path / "mygame.granule").write_text(
        "block y()\n    return 0\n", encoding="utf-8")
    assert cli.main(["--library-status", str(tmp_path), "-q"]) == 0
    out = capsys.readouterr().out
    assert "extendedverbs.granule" in out and "current" in out
    assert "statusline.granule" in out and "AGED" in out
    assert "mygame.granule" not in out       # not ours, not listed


def test_an_aged_fork_notes_itself_at_compile_time(tmp_path, capsys):
    from arcturus import cosmos
    monkey = tmp_path / "extendedverbs.granule"
    monkey.write_text(
        "// cosmos 0.36.5 base 000000000000\nverb \"search\"\n    search noun\n",
        encoding="utf-8")
    (tmp_path / "g.storyarc").write_text(
        'game\n    title "T"\n    start hall\n'
        'summon extendedverbs.granule\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n',
        encoding="utf-8")
    cosmos._FORK_NOTED.clear()
    rc = cli.main([str(tmp_path / "g.storyarc"), "-o", str(tmp_path / "g.z5"), "-q"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "was forked from Cosmos 0.36.5" in err
