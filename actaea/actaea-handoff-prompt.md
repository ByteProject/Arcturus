# Actaea continuation prompt (Arcturus milestone B10)

Paste this to the Arcturus Claude Code instance once the updated CLAUDE.md and
actaea/actaea-design.md are in the repo. This is not a new project; it is a
new workstream in the repo you already have.

---

We are starting Arcturus milestone B10: Actaea, the reference Z-machine
interpreter, built inside this repository under actaea/. It is a Standard 1.1
conformant z5 and z8 interpreter in Python with a tkinter GUI, and it plays any
well-formed story file, not only Arcturus output.

Read actaea/actaea-design.md in full, and the Actaea section of CLAUDE.md. It
is authoritative; where code and it disagree, it wins, and a real correction
updates the document in the same commit.

Hold these from the design:
- z5 and z8 only. Full text styles and colours. A true monospace cell grid for
  the upper window, modeled as a renderer-agnostic cell buffer. Quetzal save
  and restore, in-memory undo, restart. No sound. No arc_image.
- arc_image is not part of Actaea. It is later work, milestones B11 and B12, in
  this same project. Do not build or stub graphics now; only keep the cell
  model decoupled, as the design specifies.
- Headless core first. The VM loads, decodes, executes, and passes CZECH and
  Praxix through a console harness before any tkinter exists. The boundary
  between the VM core and the GUI front-end is hard.
- Plain ASCII punctuation, no em dashes, in all code, comments, and docs.

Setup:
- git is already in this repo; branch or commit per milestone as usual, naming
  the done-test in the message.
- Use subagents to fetch and install tooling: pytest, the CZECH and Praxix
  story files and their reference transcripts, the TerpEtude assets, and a
  reference interpreter (Frotz) for Quetzal save interoperability tests. Keep
  the interpreter itself dependency-free.

Work the milestones from docs/06 section 13, each with its done-test, not
advancing until green. M1 to M6 are headless; the GUI begins at M7; M6 (CZECH
and Praxix clean) is the correctness gate; M8 (the cell grid) has its own
visible done-test.

Before writing any code for M1, restate your plan: the module breakdown of the
headless core (loader, memory and addressing, decoder, executor, objects, text,
dictionary), how the I/O interface is shaped so the GUI can implement it later
without the core knowing about tkinter, and how the conformance harness will
run. Wait for my confirmation, then proceed.
