# Handover to Opus

Written 2026-07-05 by the outgoing model (Claude Fable 5), for Stefan, at the
point of handing back to Opus with milestone B10 complete. This replaces the
2026-07-02 handover that ran the other way. Same request as last time, in the
same spirit: read this, read the authoritative documents it points to, then
form your own independent assessment before starting milestone B11. Nothing
here is binding on your judgement; where you find this handover or the code
wrong, say so.

## What Arcturus is

A high-level interactive-fiction language with its own compiler, written in
Python (standard library only), that emits standard Z-machine version 5 (and,
with `--zversion 8`, version 8) story files. The standard library is Cosmos,
written in Arcturus itself and shipped as an editable template. Since this
week the project also owns the other end of the pipeline: Actaea, a Standard
1.1 conformant reference interpreter. Full charter and locked decisions are
in `CLAUDE.md` (read it first) and the specs under `docs/` (00 roadmap, 01
syntax, 02 cosmos-and-parser, 06 actaea). When code and a document disagree,
the document wins.

Author and decision-maker: Stefan Vogt (IF author: Hibernated, Ghosts of
Blackwood Manor). Expert register, no flattery. The project memory under
`~/.claude/projects/-Users-stefan-Fiction-Arcturus/memory/` (indexed by
`MEMORY.md`) carries standing preferences; honor them, and correct any that
have gone stale.

## Where the project stands

| Milestone | Description | Status |
|-----------|-------------|--------|
| B0-B7 | Language, compiler, Cosmos, size pass, language packs | done |
| B8 | Port Hibernated 2 (the maturity milestone) | done: THE END at 360/360, smaller than the Inform build |
| B9 | Port Ghosts of Blackwood Manor | DROPPED 2026-07-04 (Stefan's call; H2 made its proof redundant; number stays reserved) |
| B10 | Actaea, the reference interpreter | done 2026-07-05, v1.0.0 |
| B11 | arc_image on modern systems | NEXT |
| B12 | arc_image on retro systems | pending |
| B13 | Port The Curse of Rabenstein (from DAAD) | pending |

Current facts: arcc 0.10.5, Cosmos 0.14.3, Actaea 1.0.0. 540 tests pass
(`python3 -m pytest`). Working tree clean at commit 9943a93. The living log
with per-milestone detail is `PROGRESS.md`; the B10 arc (Actaea M1 to M11
plus Stefan's polish rounds) is its second half.

## What changed since the last handover (B8 through B10, in brief)

- B8: Hibernated 2 ports completely; all four acts play to THE END at
  360/360. The port fed the toolchain: zcolor and say.<colour>, the quote
  box granule, banner control, the compile-statistics ledger, the finish
  post-mortem, the after phase, operand patterns in handler headers, and
  two deep compiler bugs found at real-game scale (a signed-compare crash
  past 128K; direction or-lists). The H2 source is Stefan's commercial
  game: `hibernated2/` is gitignored and must NEVER be committed.
- B10: Actaea, built milestone by milestone (M1 loader/memory, M2 decoder/
  disassembler, M3 executor, M4 objects, M5 text engine, M6 the conformance
  gate, M7 the tkinter shell, M8 the cell grid, M9 styles and colours, M10
  Quetzal, M11 the sweep), then five polish rounds from Stefan's play:
  the curses terminal front-end, the standalone build, CLI banner style,
  GUI menus with persistent settings, and a chain of screenshot-driven
  console fixes. `docs/06-actaea.md` is the official documentation;
  `actaea/actaea-design.md` is the design record.

## Component overview

### The compiler (`arcturus/`)
Unchanged in shape from the previous handover: clean module boundaries in
dependency order (errors, tokens, ast, lexer, parser, prelude, worldmodel,
sema, zstring, abbrev, storyfile, assembler, objects, dictionary, lower,
cosmos, codegen, astdump, irdump, cli). Design records: docs/03 and docs/04.
Notable additions since: the after phase (docs/02 section 9), operand
patterns in handler headers including direction or-lists (docs/01 section
12), the sign-bias fix for packed string addresses past 0x8000, and je's
multi-operand encoding. Amalgamated to `build/arcc` by
`tools/amalgamate.py`; regenerate at every milestone (standing habit).

### The Cosmos library (`cosmos/`)
As before: `.prelude` core (english = the language layer, parser, actions,
loop, dispatch, scope, core) plus summonable `.granule` features, all
pay-for-use (unsummoned granules are DCE'd; after-free games are
byte-identical). Language packs: Spanish and German, functionally complete;
translation QUALITY certification still awaits native review (Spanish:
Pablo; German had one native pass by Stefan). The previous handover's
honest note stands: do not trust any model's self-assessment of non-English
idiom, your own included.

### Actaea (`actaea/`), new since the last handover
A Standard 1.1 conformant z5/z8 interpreter, Python stdlib only. The
architecture is the thing to understand first: a headless VM core (loader,
memory, decode, vm, objects, text, dictionary, quetzal, screen) behind a
hard io boundary (`io.py`), with three front-ends that the core cannot tell
apart: the tkinter window (`gui/app.py`), the curses terminal
(`console.py`), and the headless pipe (`io.ConsoleIO`). Front-ends RENDER
the core-owned screen model (`screen.py`, the 80-column cell grid); io
carries events only (text out, keys in, file paths). Facts you will need:

- Conformance: CZECH 406/406 byte-matched, Praxix all-pass, TerpEtude text
  portions, dfrotz save interop both directions, five third-party games,
  H2 end to end: all in the suite. `actaea/conformance/` holds third-party
  story files, LOCAL ONLY and gitignored; tests skip where absent.
- Two deliberate leniencies real games forced: table opcodes wrap in 16-bit
  arithmetic (Anchorhead), object-0 tree reads answer 0 (Jigsaw).
- Doctrine (Stefan's rulings): Actaea is a LIGHT interpreter, black on
  white paper; a game wanting a dark screen sets its colours, and the
  erase repaints the paper. The typed line wears the game's input colour.
  The window is exactly 80 cells wide. No scrollbar.
- One Tk root per process: Tk 9.0 on macOS SIGTRAPs on a second root; the
  GUI smoke test is the only Tk test in the suite.
- The GUI persists View-menu settings in `~/.config/actaea/settings.json`;
  tests isolate via XDG_CONFIG_HOME.
- Standalone: `tools/amalgamate_actaea.py` writes `build/actaea` (embedded
  modules load through an import hook so tkinter/curses stay optional);
  regenerate at milestones, same habit as arcc's.
- The CLI house style: every tool-facing output (help, version, errors,
  --header, --disasm) starts with the banner and ends with a blank line;
  play output carries neither.
- Testing technique worth knowing: the curses front-end is driven through
  a real pty in pytest, and during B10's debugging a pyte terminal
  emulator (dev-only, in the session scratchpad venv, not a project
  dependency) turned Stefan's screenshots into per-cell assertions.
  Screenshot bugs became data; keep that trick.

### Verification workflow (the standing hand-off discipline)
Verify a milestone yourself first (pytest; headless play; dfrotz
comparison; pty for the console), then STOP and hand the artifact to
Stefan to verify visibly before advancing. Debug story files with
fizmo-console, never Frotz (fizmo names faults; dfrotz stays the pytest
harness: `-p -w 200 -h 8000`, blank line = keypress). H2's full
walkthrough lives in the session scratchpad as `wtfull.txt` (161 lines;
its first two lines are the intro keypresses; do not prepend extra blanks).

## Invariants to respect (CLAUDE.md and the memories)

- Smallest possible z-code is a primary objective, judged with correctness.
- Python standard library only, compiler and interpreter both. tkinter and
  curses count as stdlib; nothing else does.
- The document wins over the code; fix whichever is wrong in one commit.
- Plain ASCII punctuation everywhere. No em or en dashes, anywhere. Hard rule.
- Non-English text keeps proper accents, with ASCII-typeable fallbacks.
- Git: plain `git commit` (repo identity ByteProject <stefan@8-bit.info>);
  never override identity; ask before history operations. Commit per
  milestone with the done-test named. Update the co-author trailer to your
  own identity.
- `hibernated2/` is NEVER committed. `actaea/conformance/` stays local.
- Regenerate both amalgams (`build/arcc`, `build/actaea`) at milestones.
- Never explain Arcturus via Inform analogies; describe behavior in
  Arcturus's own terms. Niche power-features are pay-for-use granules.
- Keep README and docs in sync with changes, in the same step; no
  AI-process framing in public documents.

## Open items, stated as facts to verify

- Parked, explicitly deferred by Stefan: the H2 quality-sweep list (top of
  `hibernated2/hibernated2.storyarc`); the abbreviation-quality TODO
  (zabbrv on the Inform H2 beat our pass; investigate); inline emphasis
  colour (`show.<colour>`).
- Translation native review still owed (Spanish: Pablo; German: full pass).
- macOS shows "Python" as the app-menu name unless pyobjc is present; a
  real .app is packaging, out of scope here by charter.
- Native Windows has no stdlib curses; --console degrades to headless there.
  Untested on actual Windows.
- The GUI's terminating-characters and timed-input paths are unit-tested
  and etude-verified, but no real game in the local set exercises them in
  anger (Border Zone would).

## Then: milestone B11, arc_image on modern systems

The plan is `docs/00-roadmap.md` section 6 (the graphics plan) and the B11
entry in section 7. In outline: the capability guard and EXT opcode
contract (a game asks whether pictures exist and degrades to text cleanly:
the same story file must still run unchanged on Frotz), room and scene art
rendered from PNGs, and the rendering capability added to Actaea. This is
exactly why Actaea's cell grid (M8) is a Canvas with pixel-exact cell
geometry and why the model is decoupled from the front-ends: B11 is meant
to be an extension, not a rewrite. The Curse of Rabenstein (B13) is the
eventual testbed and its art already exists; The design constraint that
outranks everything: a graphics-enabled story file remains a conformant
z5/z8 file that plays textually everywhere.

Before writing code, do what Stefan asked of the last transition: an
independent assessment. Read docs/00 section 6 critically (it predates
Actaea's build; check its assumptions against the Actaea that now exists),
run the suite, play H2 on all three front-ends, and bring back a
prioritized read on the EXT opcode design before committing to it.

## Quick reference

- Compile: `arcc game.storyarc -o build/game.z5` (or `python3 -m
  arcturus.cli`); `--zversion 8` for v8.
- Play: `python3 -m actaea build/game.z5` (window), `--console`
  (terminal), `--headless` (pipe). Tools: `--header`, `--disasm`.
- Test: `python3 -m pytest` (540; dfrotz-dependent tests skip without it).
- Standalone builds: `python3 tools/amalgamate.py` (arcc),
  `python3 tools/amalgamate_actaea.py` (actaea).
- The build record: `PROGRESS.md`. The user docs: `README.md`, `docs/`.
