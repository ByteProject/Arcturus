#!/usr/bin/env python3
# intrinsic_ref.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The intrinsic reference (docs/04, the appendix): every intrinsic the
compiler exposes, with the one-line description its own dispatch branch
carries in lower.py, grouped by family. Generated, never edited by hand,
so the table cannot drift from the compiler: tests/test_intrinsic_ref.py
regenerates it and compares. Run `python3 tools/intrinsic_ref.py` to
refresh docs/04 after adding an intrinsic; an intrinsic whose branch has
no comment (or an entry below) fails the test by name."""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from arcturus import lower  # noqa: E402

BEGIN = "<!-- intrinsics:begin -->"
END = "<!-- intrinsics:end -->"

# Lines for the intrinsics whose dispatch carries no comment of its own (a
# shared branch, or a fold answered in _static_value). Kept here, beside
# the generator, so the test names any newcomer that lacks one.
CURATED = {
    "read_line": "read_line(): read a line from the player into the text buffer; returns the terminating character.",
    "word_count": "word_count(): how many words the last input line tokenized to.",
    "word_len": "word_len(i): the length of the i-th typed word.",
    "word_pos": "word_pos(i): the position of the i-th typed word in the text buffer.",
    "peek_byte": "peek_byte(addr): the byte at addr.",
    "peek_word": "peek_word(addr, i): the i-th word at addr (word-indexed).",
    "poke_word": "poke_word(addr, i, value): store value as the i-th word at addr.",
    "print_banner": "print_banner(): print the game's banner (title, author, release line) on demand (`banner false` in the game block stops the automatic one).",
    "roll": "roll(n): a random number from 1 to n.",
    "run_alter": "run_alter(): speak the report an `alter` registered for this action, then clear it (the library's success paths call it).",
    "set_colour": "set_colour(fg, bg): the raw colour opcode (0 keeps a side); author code uses zcolor and say.<colour>.",
    "carry_limit": "carry_limit(): the game's `constant item_cap`, or 0 for none.",
    "catalogs_base": "catalogs_base(): the base address of the catalog region in dynamic memory.",
    "owners_table": "owners_table(): the word-to-owners index the noun matcher consults.",
    "duals_table": "duals_table(): the table of verb words that double as nouns.",
    "thing_duals_table": "thing_duals_table(): the table of thing words that double as verbs.",
    "desc_addr": "desc_addr(obj): the address of the object's desc property, 0 if none.",
    "intro_addr": "intro_addr(obj): the address of the object's intro property, 0 if none.",
    "article_addr": "article_addr(obj): the address of the object's hand-set article, 0 if none.",
    "indefinite_addr": "indefinite_addr(obj): the address of the object's hand-set indefinite article, 0 if none.",
    "tag_addr": "tag_addr(obj): the address of the object's tag property, 0 if none.",
    "appearance_addr": "appearance_addr(obj): the address of the object's appearance property, 0 if none.",
    "beyond_why_addr": "beyond_why_addr(obj): the address of the object's beyond_why text, 0 if none.",
    "name_cap_addr": "name_cap_addr(obj): the address of a lowercase named thing's capitalized name twin, 0 if none.",
    "plural_addr": "plural_addr(obj): the address of the object's plural word array.",
    "plural_count": "plural_count(obj): how many plural words the object lists.",
    "trigger_addr": "trigger_addr(obj): the address of the object's trigger word array.",
    "trigger_count": "trigger_count(obj): how many trigger words the object lists.",
    "adjective_addr": "adjective_addr(obj): the address of the object's adjective word array.",
    "adjective_count": "adjective_count(obj): how many adjective words the object lists.",
    "req_noun_carried": "req_noun_carried(): the requirement bit for `requires noun carried`.",
    "req_noun_animate": "req_noun_animate(): the requirement bit for `requires noun animate`.",
    "req_second_carried": "req_second_carried(): the requirement bit for `requires second carried`.",
    "req_second_animate": "req_second_animate(): the requirement bit for `requires second animate`.",
    "zc_font": "zc_font(): the base font colour zcolor.font stored.",
    "zc_status": "zc_status(): the status-bar colour zcolor.statusline stored.",
    "zc_input": "zc_input(): the input colour zcolor.input stored.",
    "any_anywhere": "any_anywhere(): 1 when a verb declares `anywhere`.",
    "any_carryweight": "any_carryweight(): 1 when the carryweight granule is summoned.",
    "any_duals": "any_duals(): 1 when a verb word doubles as a noun.",
    "any_thing_duals": "any_thing_duals(): 1 when a thing word doubles as a verb.",
    "any_exposed": "any_exposed(): 1 when a thing is `exposed`.",
    "any_indefinites": "any_indefinites(): 1 when an object sets `indefinite`.",
    "any_owner_index": "any_owner_index(): 1 when the word-to-owners index is built.",
    "any_pathfinding": "any_pathfinding(): 1 when the pathfinding granule is summoned.",
    "any_reach": "any_reach(): 1 when something reaches beyond scope (the reach_unscoped seam or `anywhere`).",
    "any_requires": "any_requires(): 1 when a verb declares `requires`.",
    "any_swap": "any_swap(): 1 when the maniacswap granule is summoned.",
    "last": "last(cat): the index of the last live entry of a catalog or matrix.",
}

FAMILIES = [
    ("Compile-time folds (any_*)", lambda n: n.startswith("any_")),
    ("Output and the screen", lambda n: n in {
        "say", "show", "show_char", "new_line", "print_name", "print_packed", "par",
        "set_window", "split_window", "set_cursor", "set_colour", "set_style",
        "erase_window", "erase_line", "buffer_mode", "clear_screen", "screen_width",
        "screen_height", "mute_begin", "mute_end", "mute_buf", "zc_font", "zc_status",
        "zc_input", "print_banner", "press_any_key", "read_key", "wait_key"}),
    ("The parser buffer", lambda n: n in {
        "read_line", "word_count", "word_dict", "word_len", "word_pos", "text_char",
        "text_addr", "parse_addr", "oops_addr", "ask_addr", "tokenise_at", "retokenize",
        "dict_entry", "verb_trigger", "copy_bytes"}),
    ("Memory", lambda n: n in {"peek_byte", "peek_word", "poke_byte", "poke_word",
                               "scan_table", "band", "bor", "catalogs_base",
                               "words_addr", "words_count", "position"}),
    ("The object tree and properties", lambda n: n.endswith("_addr") or n.endswith("_count")
        or n in {"parent_of", "first_in", "next_in", "within", "object_count",
                 "is_presence", "item_count", "weight_of", "carry_weight",
                 "carry_limit", "container_cap", "spans_match"}),
    ("Dispatch and the turn", lambda n: n.startswith("ev_") or n.startswith("run_")
        or n.startswith("tick") or n in {
            "call_handler", "handler_of", "action_id", "perform", "dispatch",
            "reach_of", "anywhere_of", "requires_of", "after_of", "after_floor",
            "meta_floor", "req_noun_carried", "req_noun_animate",
            "req_second_carried", "req_second_animate", "teleport", "gain"}),
    ("Conversation", lambda n: n.startswith("topic") or n.startswith("topics")),
    ("Movement and the map", lambda n: n in {
        "exits_count", "exit_prop", "exit_name", "exit_dest", "dir_name", "way_toward",
        "way_between", "no_way", "path_buf", "patrol_addr", "patrol_count",
        "territory_addr", "territory_count", "npc_table", "scope_room"}),
    ("Pictures", lambda n: n in {"draw_image", "image_of", "pictures_available",
                                 "arc_mode", "arc_image_dark", "image_reset"}),
    ("Session", lambda n: n in {"do_save_undo", "do_restore_undo", "do_quit",
                                "do_restart", "do_save", "do_restore", "confirm_quit",
                                "transcript_open", "transcript_close", "undo_check",
                                "auto_banner", "roll"}),
    ("Scoring", lambda n: n in {"award_earned", "pools_table", "ranks_table",
                                "notify"}),
]


def _branch_comments(src: str) -> dict:
    """name -> the comment lines directly under its dispatch branch."""
    lines = src.split("\n")
    out: dict = {}
    k = 0
    while k < len(lines):
        l = lines[k]
        group = None
        m = re.match(r'\s+elif name == "([a-z_0-9]+)":', l)
        if m:
            group = [m.group(1)]
        else:
            m = re.match(r'\s+elif name in \((.*)$', l)
            if m:
                blob = l
                kk = k
                while "):" not in blob and kk + 1 < len(lines):
                    kk += 1
                    blob += lines[kk]
                group = re.findall(r'"([a-z_0-9]+)"', blob)
                k = kk
        if group:
            cm = []
            kk = k + 1
            while kk < len(lines) and lines[kk].strip().startswith("#"):
                cm.append(lines[kk].strip().lstrip("#").strip())
                kk += 1
            text = " ".join(cm)
            for n in group:
                out.setdefault(n, text)
        k += 1
    return out


def build() -> str:
    src = open(os.path.join(ROOT, "arcturus", "lower.py"), encoding="utf-8").read()
    comments = _branch_comments(src)
    rows = {}
    missing = []
    for n in sorted(lower.INTRINSICS):
        text = CURATED.get(n) or comments.get(n, "")
        text = text.split(". ")[0].rstrip(".") + "." if text else ""
        if not text:
            missing.append(n)
        rows[n] = text
    out = [BEGIN, "",
           "## Appendix: the intrinsic reference",
           "",
           "Every intrinsic the compiler exposes, with the line its own dispatch",
           "branch carries. Generated by `tools/intrinsic_ref.py` from the compiler,",
           "never edited by hand; a test keeps it level with the code. These are",
           "the library's vocabulary (docs/01 chapter 23): an author reaches for",
           "the author-facing ones (output, the parser buffer, memory, the tree,",
           "movement), and `arcc --extract` shows every use of the rest.",
           ""]
    placed = set()
    for title, pred in FAMILIES:
        members = [n for n in sorted(rows) if n not in placed and pred(n)]
        if not members:
            continue
        out += [f"### {title}", "", "| intrinsic | what it does |", "|---|---|"]
        for n in members:
            out.append(f"| `{n}` | {rows[n].replace('|', chr(92)+'|')} |")
            placed.add(n)
        out.append("")
    rest = [n for n in sorted(rows) if n not in placed]
    if rest:
        out += ["### Library tables and the rest", "", "| intrinsic | what it does |", "|---|---|"]
        for n in rest:
            out.append(f"| `{n}` | {rows[n].replace('|', chr(92)+'|')} |")
        out.append("")
    out.append(END)
    return "\n".join(out), missing


def main() -> int:
    text, missing = build()
    if missing:
        print("intrinsics without a line (add a branch comment or a CURATED entry):",
              file=sys.stderr)
        print("  " + " ".join(missing), file=sys.stderr)
    path = os.path.join(ROOT, "docs", "04-codegen-mapping.md")
    doc = open(path, encoding="utf-8").read()
    if BEGIN in doc and END in doc:
        a = doc.index(BEGIN)
        b = doc.index(END) + len(END)
        doc = doc[:a] + text + doc[b:]
    else:
        doc = doc.rstrip("\n") + "\n\n" + text + "\n"
    open(path, "w", encoding="utf-8").write(doc)
    print(f"wrote the intrinsic reference into docs/04 ({len(lower.INTRINSICS)} intrinsics)")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
