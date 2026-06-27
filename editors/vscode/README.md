# Arcturus for VS Code

Syntax highlighting and basic editor support for the Arcturus interactive-
fiction language (`.storyarc`).

## Features

- TextMate grammar covering comments, strings with `${...}` interpolation and
  escapes, numbers, UUID literals, declaration heads (`game`, `room`, `thing`,
  `kind`, `verb`, `block`), keywords, operators, and built-in references.
- A language configuration providing the `//` line comment, bracket matching,
  and indentation rules for the indentation-based block structure.

## Installing locally

Copy or symlink this `vscode` directory into your VS Code extensions folder:

```
ln -s "$PWD/editors/vscode" ~/.vscode/extensions/arcturus
```

Then reload VS Code. Opening any `.storyarc` file activates the grammar.
