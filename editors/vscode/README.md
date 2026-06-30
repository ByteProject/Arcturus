# Arcturus for Visual Studio Code

The official syntax highlighter for the **Arcturus** programming language for
Infocom's Z-machine, by Stefan Vogt.

## About Arcturus

Arcturus is a programming language and compiler for writing interactive fiction
that runs on the Infocom Z-machine, the virtual machine behind classics like
*Zork* and the modern interpreters that still play them. You write a high-level,
readable description of a world (rooms, things, verbs, and the behavior that
hangs off them) and the compiler produces a standard Z-machine story file.

The compiler is written in Python; the standard library, Cosmos, is written in
Arcturus itself. The full project and its documentation live at
[github.com/ByteProject/Arcturus](https://github.com/ByteProject/Arcturus).

## What this extension does

- A TextMate grammar for Arcturus source: comments, strings with `${...}`
  interpolation, articles and escapes, numbers, UUID literals, declaration heads
  (`game`, `room`, `thing`, `kind`, `verb`, `block`, `topic`), the three `summon`
  forms, the standard Cosmos vocabulary (kinds such as `container` and `person`,
  attributes such as `wearable` and `openable`, properties such as `desc` and
  `intro`), the conversation sugar (`topic`, `you`, `reply`, `reveal`, `hide`),
  keywords, operators, and built-in references.
- A language configuration: the `//` line comment, bracket matching, and
  indentation rules for the indentation-based block structure.

It activates for the three Arcturus source extensions:

- `.storyarc` — a story (an Arcturus game).
- `.prelude` — a Cosmos library file.
- `.granule` — an Arcturus extension.

## Installing

Install the packaged extension (`arcturus-0.2.0.vsix`) one of two ways:

- In VS Code, open the Extensions view, click the `...` menu, choose
  **Install from VSIX...**, and select the `.vsix` file.
- Or from a terminal:

  ```
  code --install-extension arcturus-0.2.0.vsix
  ```

This works the same on macOS, Windows, and Linux. After installing, open any
`.storyarc`, `.prelude`, or `.granule` file and highlighting is active.

To rebuild the `.vsix` from source after editing the grammar, run
`python3 tools/build_vsix.py` from the repository root.
