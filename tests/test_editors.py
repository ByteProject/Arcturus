# test_editors.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The two editor extensions must not drift (the UUID lesson, 2026-08-15:
a hand-audited port missed a rule; a mechanical check cannot). The word
SETS that both highlighters colour, attributes, standard properties and
metadata, builtins, constants, and library services, are extracted from
the VS Code tmLanguage and the Zed highlight queries and compared as
sets, so a word added to one extension and not the other goes red here."""

import json
import os
import re

HERE = os.path.dirname(__file__)
VSCODE = os.path.join(HERE, "..", "editors", "vscode", "syntaxes",
                      "storyarc.tmLanguage.json")
ZED = os.path.join(HERE, "..", "editors", "zed", "languages", "arcturus",
                   "highlights.scm")


def _tm_words(pattern_name):
    """The alternation words of the named tmLanguage repository rule."""
    with open(VSCODE) as f:
        tm = json.load(f)
    node = tm["repository"][pattern_name]
    matches = []
    def walk(n):
        if isinstance(n, dict):
            if "match" in n:
                matches.append(n["match"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(node)
    words = set()
    for m in matches:
        for group in re.findall(r"\(([a-zA-Z_|]+)\)", m):
            words.update(group.split("|"))
    return words


def _zed_set(capture):
    """The #any-of? word list(s) for a capture name in the Zed queries."""
    src = open(ZED).read()
    words = set()
    for m in re.finditer(
            r"#any-of\?\s+@" + re.escape(capture) + r"((?:\s+\"[^\"]+\")+)",
            src):
        words.update(re.findall(r'"([^"]+)"', m.group(1)))
    return words


def test_attributes_match():
    assert _tm_words("attributes") == _zed_set("attribute")


def test_builtins_match():
    assert _tm_words("builtins") == _zed_set("variable.special")


def test_services_match():
    assert _tm_words("services") == _zed_set("function")


def test_constants_are_covered():
    # Zed folds the compass into @constant beside true/false/nothing; the
    # tmLanguage trio must be a subset.
    assert _tm_words("constants") <= _zed_set("constant")


def test_zed_covers_the_keyword_lists():
    # The tmLanguage keyword repository mixes several scopes (control,
    # statements, conversation, word operators); Zed carries them in one
    # @keyword set. Every tmLanguage keyword must appear in the Zed set,
    # except the words Zed treats structurally (anonymous grammar tokens)
    # or resolves to another set the way VS Code's include order also did.
    structural = {
        "verb",           # verb_declaration / enhance_redefine tokens
        "block", "topic", # declaration tokens
        "clear",          # attribute wins, as in VS Code's include order
        "capacity",       # property wins, likewise
        "turns",          # the builtin everywhere (a ruled deviation)
        "hidden", "once", "idle", "about", "order", "at", "percent",
        "points", "meta", "timers",  # the modifier set lives in @property
        "title", "headline", "author", "copyright", "release", "serial",
        "UUID", "scoring", "banner",  # metadata, likewise @property
        "held", "multi",  # grammar slots live in @type
        "award",          # the statement is in @keyword; captured below
        "font", "background", "statusline", "input",  # dotted-chain tails,
        # coloured structurally by the dotted_name rule
    }
    tm = _tm_words("keywords")
    zed = (_zed_set("keyword") | _zed_set("property") | _zed_set("type")
           | _zed_set("constant"))
    missing = (tm - structural) - zed
    assert not missing, f"tmLanguage keywords absent from Zed: {sorted(missing)}"
