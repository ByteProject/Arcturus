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

## Publishing

Development lives here; the standalone repositories are publishing
artifacts. `python3 tools/zed_publish.py` refreshes both siblings on disk
(`../tree-sitter-arcturus`, `../zed-arcturus`), writes their public
READMEs and LICENSE files, and pins the extension's grammar `rev` to the
grammar repo's HEAD. Review, commit, and push in each repo, THE GRAMMAR
FIRST (the pinned rev must be public before the extension referencing it).

To list the extension in Zed's registry (one-time):

1. Create the two public GitHub repositories under ByteProject:
   `tree-sitter-arcturus` and `zed-arcturus`; push both local repos.
2. Fork `zed-industries/extensions` (to the personal account), clone it
   with `--recurse-submodules`.
3. `git submodule add https://github.com/ByteProject/zed-arcturus.git
   extensions/arcturus` (HTTPS, never SSH).
4. Add to `extensions.toml`:

       [arcturus]
       submodule = "extensions/arcturus"
       version = "1.0.0"

5. `pnpm sort-extensions`, commit, open the pull request.

Updates later: push new commits to zed-arcturus (grammar first if it
changed), then in the fork `git submodule update --remote
extensions/arcturus`, bump the version in extensions.toml to match
extension.toml, and open a fresh PR.
