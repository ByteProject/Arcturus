# test_dress.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The native dressing (Actaea 2.0): the star ships in the three platform
shapes, the process claims its identity without raising anywhere, and
--install-app writes stubs that hold no logic (the core stays with the
other Arcturus tools; arcc --update keeps it current, the stub follows).
The macOS menu bar rename itself was proven live on the target machine
(probes/macdress_probe.py) before any of this was written; these tests
guard the plumbing around it."""

import os
import plistlib
import stat
import sys

from actaea.gui import dress


def _read(path, n):
    with open(path, "rb") as fh:
        return fh.read(n)


def test_the_star_ships_in_three_shapes():
    d = dress.icons_dir()
    icns = os.path.join(d, "actaea.icns")
    ico = os.path.join(d, "actaea.ico")
    png = os.path.join(d, "actaea.png")
    about = os.path.join(d, "actaea-128.png")
    for p in (icns, ico, png, about):
        assert os.path.isfile(p), p
    # Each file is truly what its platform expects, by magic number.
    assert _read(icns, 4) == b"icns"
    assert _read(ico, 4) == b"\x00\x00\x01\x00"
    assert _read(png, 8) == b"\x89PNG\r\n\x1a\n"
    assert dress.icon_path("actaea.icns") == icns
    assert dress.icon_path("no-such-icon.png") is None


def test_predress_never_raises_and_repeats_quietly():
    # On macOS this really rewrites the hosting bundle's in-memory name
    # (harmless to the test process); elsewhere it is a cheap no-op.
    # Either way the contract is the same: no exception, idempotent.
    dress.predress()
    dress.predress()


def test_core_command_names_this_source_checkout():
    core, pythonpath = dress._core_command()
    assert core[0] == sys.executable
    assert core[1:] == ["-m", "actaea"]
    # The checkout root is the PYTHONPATH the stub must carry.
    assert os.path.isdir(os.path.join(pythonpath, "actaea"))
    assert dress._core_marker(core, pythonpath) == pythonpath


def test_install_writes_a_logic_free_mac_bundle(tmp_path):
    assert dress._install_mac(str(tmp_path)) == 0
    app = tmp_path / "Actaea.app"

    with open(app / "Contents" / "Info.plist", "rb") as fh:
        plist = plistlib.load(fh)
    assert plist["CFBundleName"] == "Actaea"
    assert plist["CFBundleIdentifier"] == "org.byteproject.actaea"
    assert plist["CFBundleExecutable"] == "Actaea"
    assert plist["CFBundleIconFile"] == "actaea"
    doc = plist["CFBundleDocumentTypes"][0]
    assert doc["CFBundleTypeExtensions"] == ["z5", "z8", "zblorb"]

    shim = app / "Contents" / "MacOS" / "Actaea"
    assert os.stat(shim).st_mode & stat.S_IXUSR
    text = shim.read_text()
    assert text.startswith("#!/bin/sh")
    # The Finder launch is a bare launch plus an Apple Event; the marker
    # tells the window it may wait a beat for the double-clicked story.
    assert "ACTAEA_BUNDLE=1" in text
    # A source checkout's stub carries the import path...
    assert "PYTHONPATH=" in text
    # ...the interpreter self-heals to the PATH's python3 when the
    # recorded one is retired by an upgrade...
    assert '[ -x "$PY" ] || PY=python3' in text
    assert 'exec "$PY" ' in text
    # ...and the marker line names the path refresh_stub watches.
    marker = [ln for ln in text.splitlines()
              if ln.startswith("# core: ")]
    assert marker and os.path.exists(marker[0][len("# core: "):])

    assert (app / "Contents" / "Resources" / "actaea.icns").is_file()


def test_refresh_stub_heals_only_dead_cores(tmp_path):
    dress._install_mac(str(tmp_path))
    shim = tmp_path / "Actaea.app" / "Contents" / "MacOS" / "Actaea"

    # A dead core (the download directory moved): the stub is rewritten
    # to point at THIS interpreter.
    lines = shim.read_text().splitlines()
    lines = ["# core: /definitely/gone/actaea"
             if ln.startswith("# core: ") else ln for ln in lines]
    shim.write_text("\n".join(lines) + "\n")
    dress.refresh_stub(bases=[str(tmp_path)])
    healed = shim.read_text()
    assert "/definitely/gone/actaea" not in healed
    marker = [ln for ln in healed.splitlines()
              if ln.startswith("# core: ")][0]
    assert os.path.exists(marker[len("# core: "):])

    # A LIVE core is sacred: a second copy launching must never hijack
    # the installed stub, so nothing is rewritten (the witness survives).
    witness = healed + "# witness\n"
    shim.write_text(witness)
    dress.refresh_stub(bases=[str(tmp_path)])
    assert shim.read_text() == witness


def test_install_writes_the_linux_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert dress._install_linux() == 0
    desktop = tmp_path / "applications" / "actaea.desktop"
    text = desktop.read_text()
    assert "[Desktop Entry]" in text
    assert "Name=Actaea" in text
    assert "MimeType=application/x-zmachine;" in text
    assert "Terminal=false" in text
    # The Exec line hands the opened file through and, from a source
    # checkout, carries the import path.
    exec_line = [ln for ln in text.splitlines()
                 if ln.startswith("Exec=")][0]
    assert exec_line.endswith(" %f")
    assert "PYTHONPATH=" in exec_line
    assert (tmp_path / "icons" / "hicolor" / "512x512" / "apps"
            / "actaea.png").is_file()
