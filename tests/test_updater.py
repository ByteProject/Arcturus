# test_updater.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""arcc --update: the standalone refresh. Explicit-only networking (the
fetch is injected here, so no test touches the net), amalgam-only (the
repo package refuses toward git pull), validation before replacement,
and the version report."""

import os
import sys

import arcturus
from arcturus import updater


def _fake_standalone(version: str, filler: int = 60_000) -> bytes:
    return (
        b"#!/usr/bin/env python3\n"
        + f'__version__ = "{version}"\n'.encode()
        + b"# " + b"x" * filler + b"\n"
    )


def test_repo_package_refuses(capsys):
    assert getattr(arcturus, "__build__", None) is None
    rc = updater.run_update(fetch=lambda name: b"")
    assert rc == 2
    assert "git pull" in capsys.readouterr().err


def test_update_replaces_and_reports(tmp_path, monkeypatch, capsys):
    me = tmp_path / "arcc"
    me.write_bytes(_fake_standalone("0.11.18"))
    sib = tmp_path / "arcimg"
    sib.write_bytes(_fake_standalone("1.7.0"))
    monkeypatch.setattr(arcturus, "__build__", "testbuild", raising=False)
    monkeypatch.setattr(sys, "argv", [str(me)])
    fresh = {"arcc": _fake_standalone("0.11.99"),
             "arcimg": _fake_standalone("1.8.0")}
    rc = updater.run_update(fetch=lambda name: fresh[name])
    out = capsys.readouterr().out
    assert rc == 0
    assert "arcc: v0.11.18 -> v0.11.99" in out
    assert "arcimg: v1.7.0 -> v1.8.0" in out
    assert me.read_bytes() == fresh["arcc"]
    assert sib.read_bytes() == fresh["arcimg"]


def test_already_current_stays(tmp_path, monkeypatch, capsys):
    me = tmp_path / "arcc"
    data = _fake_standalone("0.11.18")
    me.write_bytes(data)
    monkeypatch.setattr(arcturus, "__build__", "testbuild", raising=False)
    monkeypatch.setattr(sys, "argv", [str(me)])
    rc = updater.run_update(fetch=lambda name: data)
    assert rc == 0
    assert "already current" in capsys.readouterr().out


def test_garbage_download_is_refused(tmp_path, monkeypatch, capsys):
    me = tmp_path / "arcc"
    original = _fake_standalone("0.11.18")
    me.write_bytes(original)
    monkeypatch.setattr(arcturus, "__build__", "testbuild", raising=False)
    monkeypatch.setattr(sys, "argv", [str(me)])
    rc = updater.run_update(fetch=lambda name: b"<html>404 lol</html>")
    assert rc == 1
    assert me.read_bytes() == original          # untouched
    assert "keeping the current" in capsys.readouterr().err


def test_real_amalgam_passes_validation():
    # the actual published shape must pass the validator
    path = os.path.join(os.path.dirname(__file__), "..", "build", "arcc")
    with open(path, "rb") as f:
        data = f.read()
    assert updater._validate("arcc", data) == ""
    assert updater._version_in(data.decode("utf-8", "replace")) != "unknown"


def test_amalgam_embeds_every_package_module():
    # The bug this fences: updater.py was born after the amalgamator's module
    # list, so `arcc --update` shipped as a flag whose import died inside the
    # standalone. The amalgamator now refuses to build an incomplete list;
    # this asserts the same completeness from the suite's side.
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    spec = importlib.util.spec_from_file_location(
        "amalgamate", os.path.join(root, "tools", "amalgamate.py"))
    am = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(am)
    pkg = os.path.join(root, "arcturus")
    on_disk = {n[:-3] for n in os.listdir(pkg)
               if n.endswith(".py") and n not in ("__init__.py", "__main__.py")}
    assert on_disk == set(am._MODULE_ORDER), (
        "arcturus/ and tools/amalgamate.py _MODULE_ORDER disagree; "
        "a module missing there ships a broken standalone"
    )
