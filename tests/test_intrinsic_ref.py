# test_intrinsic_ref.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The intrinsic reference in docs/04 is generated from the compiler
(tools/intrinsic_ref.py) and must stay level with it: every intrinsic has
a line, and the committed appendix equals a fresh generation (auraes's
ask, 2026-09-28: the undocumented intrinsics)."""

import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tool():
    spec = importlib.util.spec_from_file_location(
        "intrinsic_ref", os.path.join(ROOT, "tools", "intrinsic_ref.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_intrinsic_has_a_line():
    text, missing = _tool().build()
    assert not missing, f"intrinsics without a line: {missing}"


def test_the_committed_appendix_is_current():
    tool = _tool()
    text, _ = tool.build()
    doc = open(os.path.join(ROOT, "docs", "04-codegen-mapping.md"), encoding="utf-8").read()
    assert tool.BEGIN in doc and tool.END in doc, "docs/04 carries no reference section"
    a = doc.index(tool.BEGIN)
    b = doc.index(tool.END) + len(tool.END)
    assert doc[a:b] == text, "docs/04 is stale: run python3 tools/intrinsic_ref.py"
