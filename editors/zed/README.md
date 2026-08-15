# The Arcturus extension for Zed

Syntax highlighting for the Arcturus programming language (Infocom
Z-machine), covering `.storyarc`, `.granule`, and `.prelude` files, plus an
outline: rooms, things, kinds, blocks, and topics appear as symbols in
Zed's breadcrumbs and symbol search.

The highlighting is built on a Tree-sitter grammar that lives in
[editors/tree-sitter-arcturus/](../tree-sitter-arcturus/). The grammar is
deliberately loose: declaration heads are structural (so names can be
coloured and outlined), everything else is a plain identifier, and the
keyword, attribute, property, and builtin sets are coloured in
[languages/arcturus/highlights.scm](languages/arcturus/highlights.scm).
Adding a new library word to the highlighting is one line in that file.
The word-class markers of a `words` list (`#trigger`, `>adjective`) are
highlighted distinctly.

## Install (dev extension)

Zed loads a grammar from a git repository, so a helper assembles an
installable bundle:

    python3 tools/zed_dev.py

Then in Zed: command palette, **zed: install dev extension**, and select
`build/zed-dev`. After editing the grammar or the queries, re-run the tool
and reinstall (or use **zed: rebuild dev extension**).

## Rebuilding the grammar

After editing `grammar.js`, regenerate the parser (Node is required; the
tree-sitter CLI runs from the npm cache):

    cd editors/tree-sitter-arcturus
    npx tree-sitter-cli@latest generate

The generated `src/` is committed, since Zed compiles the parser from it.

## Publishing (later)

For a public release the grammar moves to its own repository
(`ByteProject/tree-sitter-arcturus`, the Tree-sitter naming convention, so
other editors can reuse it), the `rev` in `extension.toml` pins a real
commit there, and the extension itself is submitted to the Zed extension
registry from a `zed-arcturus` repository.
