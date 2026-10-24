#!/usr/bin/env python3
# handbook_index.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The handbook's index (docs/01, Appendix E): every term an author looks
up, linked to the place the handbook defines it. The term list below is
curated by hand; the links are generated, never edited by hand, so the
index cannot drift from the book: tests/test_handbook_index.py runs this
in check mode and fails when a term no longer resolves or the committed
index is stale. Run `python3 tools/handbook_index.py` after editing the
handbook or the list.

A term names its definition with one or more locators:

    h:<heading text>      a heading (linked by its GitHub anchor)
    row:<name>            a definition table row that opens "| `name` |"
    p:<opening words>     a paragraph (or list item) that opens with them
    t:<phrase>            the first line that contains the phrase

A locator may end in #N to take the Nth match instead of the first. Lines
inside code blocks never match. A target that is not a heading gets a
small invisible anchor, <a id="ix-..."></a>, placed at the start of its
line (inside the first cell for a table row); the anchors are stable
across runs, so links already shared keep working."""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOOK = os.path.join(ROOT, "docs", "01-arcturus-handbook.md")

BEGIN = "<!-- index:begin -->"
END = "<!-- index:end -->"
ANCHOR_RE = re.compile(r'<a id="(ix-[a-z0-9-]+)"></a>')

# (display, locators). Display in backticks is code; plain is a concept.
# "see <term>" as the only locator makes a cross-reference.
TERMS = [
    # -- the program and its declarations ---------------------------------
    ("`game`", ["h:Chapter 2: A game and its program"]),
    ("`title`, `headline`, `author`", ["h:Runtime globals and story metadata"]),
    ("`start`", ["h:Runtime globals and story metadata"]),
    ("`release`, `serial`, `UUID`", ["h:Runtime globals and story metadata"]),
    ("banner", ["h:The banner"]),
    ("`room`", ["h:room"]),
    ("`thing`", ["h:thing"]),
    ("`kind`", ["h:Kinds of your own"]),
    ("kinds, standard", ["h:Standard kinds"]),
    ("`container`", ["h:container"]),
    ("`supporter`", ["h:supporter"]),
    ("`door`", ["h:door"]),
    ("`character`", ["h:character"]),
    ("NPC", ["see `character`"]),
    ("person", ["see `character`"]),
    ("`player`", ["h:Chapter 4: The player"]),
    ("`body`", ["t:begins in with `body` in the game block"]),
    ("`as player`", ["p:EACH BODY ITS OWN WAYS: `as player`."]),
    ("resolution order", ["p:Resolution order."]),
    ("inheritance", ["see resolution order"]),
    ("`global`", ["p:Story state comes in three declarations"]),
    ("`flag`", ["p:Story state comes in three declarations"]),
    ("`counter`", ["p:Story state comes in three declarations"]),
    ("`constant`", ["p:A CONSTANT costs no global at all"]),
    ("`catalog`", ["t:catalog"]),
    ("`matrix`", ["h:4a. matrix: a catalog you can grow (summon.matrix)", "h:matrix"]),
    ("`list`", ["p:The list type also stands free of any object"]),
    ("values and types", ["h:Values and types"]),
    ("lexical structure", ["h:Lexical structure"]),
    ("comments", ["h:Lexical structure"]),
    ("hexadecimal numbers", ["t:0x"]),
    ("decimal numbers", ["h:Values and types"]),
    # -- properties and attributes -------------------------------------------
    ("properties", ["h:Chapter 5: Properties"]),
    ("attributes, standard", ["h:Standard attributes"]),
    ("value properties, standard", ["h:Standard value properties"]),
    ("attribute folds", ["p:Cosmos predefines these boolean attributes."]),
    ("computed properties", ["p:Computed properties."]),
    ("`name`", ["row:name"]),
    ("`name block`", ["t:A computed `name block`"]),
    ("`named`", ["row:named"]),
    ("`desc`", ["row:desc"]),
    ("`desc block`", ["p:Computed properties."]),
    ("`words`", ["row:words"]),
    ("name words", ["h:Name words are vocabulary"]),
    ("`tag`", ["row:tag"]),
    ("`plural`", ["row:plural"]),
    ("`intro`", ["row:intro"]),
    ("`appearance`", ["row:appearance"]),
    ("`item_cap`", ["row:item_cap"]),
    ("`article`", ["row:article"]),
    ("`indefinite`", ["row:indefinite"]),
    ("`unseal_with`", ["row:unseal_with"]),
    ("`arc_image`", ["row:arc_image", "h:Chapter 20: Pictures: arc_image"]),
    ("`fixed`", ["row:fixed"]),
    ("`scenery`", ["row:scenery"]),
    ("`hidden`", ["row:hidden"]),
    ("`concealed`", ["row:concealed"]),
    ("`wearable`", ["row:wearable"]),
    ("`worn`", ["row:worn"]),
    ("`lit`", ["row:lit"]),
    ("`edible`", ["row:edible"]),
    ("`an`", ["row:an"]),
    ("`feminine`", ["row:feminine"]),
    ("`neutral`", ["row:neutral"]),
    ("`exposed`", ["row:exposed"]),
    ("`exposed_line`", ["t:`constant exposed_line = false`"]),
    ("`beyond`", ["row:beyond"]),
    ("`shiftable`", ["row:shiftable", "h:Pushing things between rooms (shiftable)"]),
    ("`restless`", ["row:restless"]),
    ("`pluribus`", ["row:pluribus"]),
    ("`binary`", ["row:binary"]),
    ("`switchable`", ["see `binary`"]),
    ("`active`", ["row:active"]),
    ("`openable`", ["row:openable"]),
    ("`open`", ["row:open"]),
    ("`clear`", ["row:clear"]),
    ("`seen`", ["row:seen"]),
    ("`lockable`", ["row:lockable"]),
    ("`locked`", ["row:locked"]),
    ("`scored`", ["row:scored"]),
    ("`visited`", ["row:visited"]),
    ("`moved`", ["row:moved"]),
    ("`animate`", ["row:animate"]),
    ("`component`", ["row:component"]),
    ("keys and locks", ["see `lockable`"]),
    # -- containers, scope, light, movement ------------------------------------
    ("object tree", ["h:Chapter 6: Containers, supporters, and the object tree"]),
    ("carrying", ["h:Carrying, three ways"]),
    ("knowledge model", ["h:The container knowledge model"]),
    ("`remember_contents`", ["p:The memory is the designed default."]),
    ("`contents_line`", ["t:`constant contents_line ="]),
    ("`scenery_contents`", ["t:`constant scenery_contents = true`"]),
    ("`name_contents`", ["p:`name_contents(holder)`"]),
    ("scope", ["h:Chapter 7: Scope, light, and darkness"]),
    ("`visible`, `reachable`", ["t:Two predicates Cosmos provides for conditions"]),
    ("light and darkness", ["h:Light and darkness"]),
    ("darkness", ["see light and darkness"]),
    ("`lighttopology`", ["h:Light as a level: lighttopology", "h:lighttopology"]),
    ("movement", ["h:Chapter 8: Movement and directions"]),
    ("directions", ["h:Chapter 8: Movement and directions"]),
    ("custom directions", ["p:CUSTOM DIRECTIONS."]),
    ("`direction`", ["p:CUSTOM DIRECTIONS."]),
    ("blocked directions", ["h:Movement and blocked directions"]),
    ("`on go other`", ["t:A per-room fallback: `on go other`"]),
    ("computed exits", ["p:2. A computed exit: a direction property may be a `block`"]),
    ("`exit_dest`", ["t:`exit_dest(room, direction)`"]),
    ("`way`", ["t:`way` is the global"]),
    ("way family", ["h:The way family: querying the room graph"]),
    ("`convey`", ["t:`convey(vehicle, dest)`"]),
    ("vehicles", ["see `convey`"]),
    ("`teleport`", ["t:`teleport`"]),
    ("`gain`", ["t:`gain`"]),
    # -- statements and expressions --------------------------------------------
    ("statements", ["h:Chapter 9: Statements, control flow, and expressions"]),
    ("control flow", ["h:Control flow"]),
    ("`if`, `else`", ["h:Control flow"]),
    ("`while`", ["h:Control flow"]),
    ("`for each`", ["h:Control flow"]),
    ("`switch`, `case`", ["h:Control flow"]),
    ("expressions and operators", ["h:Expressions and operators"]),
    ("`is`, `is not`", ["h:Expressions and operators"]),
    ("`holds`", ["h:Expressions and operators"]),
    ("`mod`", ["h:Expressions and operators"]),
    ("`let`", ["t:`let`"]),
    ("`change`", ["p:`change ... to ...` is the universal setter"]),
    ("`now`", ["p:`now ... is / is not ...` is boolean-set sugar"]),
    ("`move`", ["p:`move ... to ...` is the only tree operation"]),
    ("`append`, `insert`, `remove` (matrix)", ["p:The mutators are what a catalog lacks."]),
    ("`stop`", ["p:`stop` ends the current handler or block immediately"]),
    ("`continue`", ["p:`stop` ends the current handler or block immediately"]),
    ("`return`", ["t:`return` belongs in blocks, never in a handler"]),
    ("`alter`", ["p:`alter` REGISTERS an action's report"]),
    ("`success`", ["p:The counterpart is the `success` statement"]),
    ("`finish`, `death`", ["t:`finish`"]),
    ("blocks", ["h:Chapter 10: Blocks"]),
    ("`block`", ["h:Chapter 10: Blocks"]),
    ("`perform`", ["p:The general form is `perform`"]),
    # -- handlers, verbs, the turn ------------------------------------------------
    ("handlers", ["h:Chapter 11: Handlers and events"]),
    ("`on`", ["h:Chapter 11: Handlers and events"]),
    ("`when`", ["p:A `when` guard restricts a handler to a condition"]),
    ("default versus override", ["p:Default versus override."]),
    ("`on after`", ["p:After phase."]),
    ("`on other`", ["t:`on other`"]),
    ("free-standing rules", ["p:Free-standing rules."]),
    ("life-cycle events", ["p:Life-cycle events."]),
    ("`on start`", ["p:Life-cycle events."]),
    ("`on each_turn`", ["p:Life-cycle events."]),
    ("verbs", ["h:Chapter 12: Verbs, grammar, and the standard actions"]),
    ("`verb`", ["h:Chapter 12: Verbs, grammar, and the standard actions"]),
    ("grammar", ["p:EXTENDING THE STANDARD GRAMMAR."]),
    ("`enhance`, `redefine`", ["p:EXTENDING THE STANDARD GRAMMAR."]),
    ("`direction` grammar slot", ["t:One `direction` slot per line"]),
    ("`requires`", ["h:What a verb requires"]),
    ("`reachagnostic`", ["p:Bare `reachagnostic` skips the check"]),
    ("`anywhere`", ["t:`anywhere`"]),
    ("`meta`", ["t:A verb whose actions are OUT-OF-WORLD"]),
    ("new verbs", ["h:A new verb, complete"]),
    ("`action`", ["h:Verbless actions: `action`"]),
    ("standard verbs", ["h:The standard verbs, action by action"]),
    ("actions, standard", ["see standard verbs"]),
    ("`notify`", ["h:Score notification (notify), and VERSION"]),
    ("yes and no", ["h:Typed answers, and lighting things"]),
    ("commanding characters", ["h:Commanding characters: the addressed imperative"]),
    ("noun lists", ["h:Noun lists"]),
    ("turn loop", ["h:Chapter 13: The turn loop and the action pipeline"]),
    ("action pipeline", ["h:The action pipeline"]),
    ("`refused`", ["t:The signal is the `refused` global"]),
    # -- the parser ------------------------------------------------------------
    ("parser", ["h:Chapter 14: The parser"]),
    ("tokenizing", ["p:Tokenizing."]),
    ("disambiguation", ["t:Several tie at the best score"]),
    ("trigger marker (`#`)", ["p:The trigger marker."]),
    ("adjective marker (`>`)", ["p:The adjective marker, and the match classes."]),
    ("`prefer`", ["p:The prefer seam."]),
    ("`reach_unscoped`", ["h:Reaching beyond scope (the reach_unscoped seam)"]),
    ("pronouns", ["h:Pronouns"]),
    ("command chaining", ["h:Command chaining"]),
    ("chain words", ["h:Command chaining"]),
    ("positional grammar", ["h:Positional grammar"]),
    ("`letters`, `number`, `anychar`", ["h:Machines with input surfaces: letters, number, anychar"]),
    ("`text` slot", ["p:A `text` slot is the exception to resolution"]),
    ("`noise`", ["t:And so are the noise words"]),
    ("OOPS, AGAIN", ["t:Disambiguation answers, pronouns, chaining"]),
    # -- output -------------------------------------------------------------------
    ("output", ["h:Chapter 15: Output and text"]),
    ("`say`, `show`", ["t:Use `say` to finish a line, `show` to build"]),
    ("`par`", ["t:To follow a say with a paragraph break"]),
    ("paragraph breaks", ["t:To follow a say with a paragraph break"]),
    ("line breaks (`\\n`)", ["t:a forced line break is written"]),
    ("whitespace in strings", ["t:runs of"]),
    ("strings", ["t:A string is written in double quotes"]),
    ("interpolation (`${...}`)", ["p:Interpolation embeds an expression"]),
    ("articles", ["p:Interpolation embeds an expression", "p:Naming. `name` is the printed short name"]),
    ("`vary`", ["h:vary: prose that varies by itself"]),
    ("`silence`", ["t:the word `silence`"]),
    ("`vary ... show`", ["t:To vary a word or a"]),
    ("colors (`zcolor`)", ["h:Screen colors (zcolor)"]),
    ("text styles (bold, italic)", ["h:Text styles"]),
    ("standard responses", ["h:Standard responses"]),
    ("messages, library", ["see standard responses"]),
    ("`compact_rooms`", ["p:A room description is its own paragraph"]),
    ("`press_any_key`", ["t:press_any_key"]),
    ("daemons and timers", ["h:Chapter 16: Daemons, timers, and background performers"]),
    ("`after`, `every`", ["h:Chapter 16: Daemons, timers, and background performers"]),
    ("`first`", ["h:The first placement: the top of the turn"]),
    # -- conversation, grains, scoring, pictures -----------------------------------
    ("topics and conversation", ["h:Chapter 17: Topics and conversation"]),
    ("`topic`", ["h:Chapter 17: Topics and conversation"]),
    ("`you`, `reply`", ["h:Chapter 17: Topics and conversation"]),
    ("ask and tell", ["p:ASK AND TELL."]),
    ("addressing a character", ["h:The five ways to address a character"]),
    ("shared subjects", ["h:Shared subjects"]),
    ("grains", ["h:Chapter 18: Grains"]),
    ("dual-role words", ["h:Dual-role words"]),
    ("scoring", ["h:Chapter 19: Scoring"]),
    ("`award`, `reward`", ["h:Chapter 19: Scoring"]),
    ("`score_rooms`, `score_things`", ["p:Either half can be switched off"]),
    ("pictures", ["h:Chapter 20: Pictures: arc_image"]),
    ("`arc_mode`", ["p:You declare the mode once, game-wide, with a constant named `arc_mode`"]),
    ("`arc_image_dark`", ["p:DARKNESS IS A SCENE TOO."]),
    # -- languages, granules, the toolkit -----------------------------------------
    ("languages", ["h:Chapter 21: Writing in another language"]),
    ("German, Spanish", ["p:Selecting a language."]),
    ("`summon.language`", ["p:Selecting a language."]),
    ("first-person narration", ["h:First-person narration"]),
    ("`first_person`", ["h:First-person narration"]),
    ("granules", ["h:Chapter 22: Summon: the granules"]),
    ("`summon`", ["h:Summoning a granule"]),
    ("shipped granules", ["h:The shipped granules"]),
    ("`extendedverbs`", ["h:extendedverbs"]),
    ("`carryweight`", ["h:carryweight"]),
    ("`weight`", ["h:carryweight"]),
    ("`infocom_talking`", ["h:infocom_talking"]),
    ("`statusline`", ["h:statusline"]),
    ("`foresight`", ["h:foresight"]),
    ("`quotes`", ["h:quotes"]),
    ("`verbose_exits`", ["h:verbose_exits"]),
    ("`nautical`", ["h:nautical"]),
    ("`pathfinding`", ["h:pathfinding"]),
    ("`npcengine`", ["h:npcengine"]),
    ("`maniacswap`", ["h:maniacswap"]),
    ("`conversations`", ["h:conversations"]),
    ("`ambience`", ["h:ambience"]),
    ("`takeall`", ["h:takeall"]),
    ("`plurals`", ["h:plurals"]),
    ("`debug`", ["h:debug"]),
    ("debug verbs (`purloin`, `warp`, `tree`)", ["h:debug"]),
    ("`use`", ["h:use"]),
    ("hacking Cosmos", ["h:Chapter 23: Hacking Cosmos"]),
    ("overriding Cosmos", ["h:Overriding Cosmos in practice"]),
    ("forking a granule", ["h:Forking a granule"]),
    ("writing a granule", ["h:Writing your own granule"]),
    ("compiler", ["h:Chapter 24: The compiler, diagnostics, and the abbreviation set"]),
    ("diagnostics", ["h:Chapter 24: The compiler, diagnostics, and the abbreviation set"]),
    ("abbreviations", ["h:The tuned abbreviation set"]),
    ("command line (`arcc`)", ["h:Chapter 24: The compiler, diagnostics, and the abbreviation set"]),
    ("reserved words", ["h:Appendix A: Reserved words"]),
    ("grammar summary", ["h:Appendix B: Grammar summary"]),
    ("Cosmos-reserved names", ["h:Appendix C: Cosmos-reserved names"]),
    ("toolkit (intrinsics)", ["h:Appendix D: The author's toolkit"]),
    ("intrinsics", ["see toolkit (intrinsics)"]),
    ("The Brass Lantern", ["h:Chapter 25: Worked example: The Brass Lantern"]),
    ("Cloak of Darkness", ["h:Chapter 26: Worked example: Cloak of Darkness"]),
]


def slug(text: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped (hyphens and
    underscores kept), spaces to hyphens."""
    s = text.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def ix_id(term: str) -> str:
    s = re.sub(r"`", "", term).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return "ix-" + (s or "term")


def _scan(lines):
    """Per line: (in_code, heading_text or None, heading_slug or None,
    chapter label). Headings inside code fences do not count."""
    out = []
    in_code = False
    seen_slugs = {}
    chapter = ""
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            out.append((True, None, None, chapter, section))
            in_code = not in_code
            continue
        if in_code:
            out.append((True, None, None, chapter, section))
            continue
        m = re.match(r"^(#{2,4}) (.+?)\s*$", line)
        if m:
            text = m.group(2)
            base = slug(ANCHOR_RE.sub("", text))
            n = seen_slugs.get(base, 0)
            seen_slugs[base] = n + 1
            sl = base if n == 0 else f"{base}-{n}"
            if m.group(1) == "##":
                chapter = text
                section = ""
            else:
                section = text
            out.append((False, text, sl, chapter, section))
            continue
        out.append((False, None, None, chapter, section))
    return out


def _chapter_label(chapter: str) -> str:
    m = re.match(r"Chapter (\d+):", chapter)
    if m:
        return f"chapter {m.group(1)}"
    m = re.match(r"Appendix ([A-Z]):", chapter)
    if m:
        return f"appendix {m.group(1)}"
    return "introduction"


def _find(lines, scan, locator, stop_at):
    kind, _, rest = locator.partition(":")
    nth = 1
    m = re.match(r"^(.*)#(\d+)$", rest)
    if m:
        rest, nth = m.group(1), int(m.group(2))
    hits = 0
    for i, line in enumerate(lines[:stop_at]):
        in_code, heading, _sl, _c, _s = scan[i]
        if in_code:
            continue
        bare = ANCHOR_RE.sub("", line)
        ok = False
        if kind == "h":
            ok = heading is not None and ANCHOR_RE.sub("", heading) == rest
        elif kind == "row":
            ok = bare.startswith(f"| `{rest}` |")
        elif kind == "p":
            ok = heading is None and re.sub(r"^\s*(?:[-*] )?", "", bare).startswith(rest)
        elif kind == "t":
            ok = heading is None and rest in bare
        else:
            raise SystemExit(f"handbook_index: unknown locator kind in '{locator}'")
        if ok:
            hits += 1
            if hits == nth:
                return i
    return None


def build(text: str):
    """Return (new_text, problems): the handbook with anchors placed and the
    index written between the markers, plus every locator that failed."""
    if BEGIN in text:
        head = text[:text.index(BEGIN)]
        tail = text[text.index(END) + len(END):]
    else:
        head, tail = text.rstrip("\n") + "\n\n", "\n"
    lines = head.split("\n")
    scan = _scan(lines)
    problems = []
    anchors = {}                     # line index -> anchor id
    for i, line in enumerate(lines):
        m = ANCHOR_RE.search(line)
        if m and not scan[i][0]:
            anchors[i] = m.group(1)
    resolved = {}                    # display -> list of (href, label)
    terms = {d for d, _ in TERMS}
    for display, locs in TERMS:
        if len(locs) == 1 and locs[0].startswith("see "):
            target = locs[0][4:]
            if target not in terms:
                problems.append(f"{display}: cross-reference to unknown term {target}")
            continue
        links = []
        for loc in locs:
            i = _find(lines, scan, loc, len(lines))
            if i is None:
                problems.append(f"{display}: no match for '{loc}'")
                continue
            _in, heading, sl, chapter, section = scan[i]
            if heading is not None:
                href = sl
                where = _chapter_label(chapter)
                if heading != chapter:
                    where += f", {ANCHOR_RE.sub('', heading).replace('`', '')}"
            else:
                if i not in anchors:
                    aid = ix_id(display)
                    used = set(anchors.values())
                    k = 2
                    base = aid
                    while aid in used:
                        aid = f"{base}-{k}"
                        k += 1
                    anchors[i] = aid
                    line = lines[i]
                    if line.startswith("| "):
                        lines[i] = "| " + f'<a id="{aid}"></a>' + line[2:]
                    else:
                        mm = re.match(r"^(\s*(?:[-*] |\d+\. )?)(.*)$", line)
                        lines[i] = mm.group(1) + f'<a id="{aid}"></a>' + mm.group(2)
                href = anchors[i]
                where = _chapter_label(chapter)
                if section:
                    where += f", {ANCHOR_RE.sub('', section).replace('`', '')}"
            links.append((href, where))
        resolved[display] = links
    # The index itself, grouped by initial letter, sorted case-blind on the
    # term's letters (backticks and punctuation ignored).
    def key(d):
        return re.sub(r"[^a-z0-9 ]", "", d.replace("`", "").lower()).strip()
    out = [BEGIN, "## Appendix E: Index", "",
           "Every term links to the place this book defines it. The index is",
           "generated from the book itself (tools/handbook_index.py), so the",
           "links follow the text wherever it moves.", ""]
    letter = None
    for display, locs in sorted(TERMS, key=lambda t: key(t[0])):
        first = key(display)[:1].upper() or "#"
        if first.isdigit():
            first = "#"
        if first != letter:
            if letter is not None:
                out.append("")
            out.append(f"**{first}**")
            out.append("")
            letter = first
        if len(locs) == 1 and locs[0].startswith("see "):
            out.append(f"- {display}: see {locs[0][4:]}")
            continue
        parts = [f"[{where}](#{href})" for href, where in resolved.get(display, [])]
        out.append(f"- {display}: " + ", ".join(parts))
    out.append(END)
    body = "\n".join(lines).rstrip("\n") + "\n\n" + "\n".join(out)
    return body + tail if tail.strip() else body + "\n", problems


def main(argv) -> int:
    check = "--check" in argv
    with open(BOOK, encoding="utf-8") as fh:
        text = fh.read()
    new, problems = build(text)
    if problems:
        for p in problems:
            print("handbook_index:", p, file=sys.stderr)
        return 1
    if check:
        if new != text:
            print("handbook_index: the index is stale; run python3 tools/handbook_index.py",
                  file=sys.stderr)
            return 1
        return 0
    if new != text:
        with open(BOOK, "w", encoding="utf-8") as fh:
            fh.write(new)
    print(f"wrote the index into docs/01 ({len(TERMS)} terms)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
