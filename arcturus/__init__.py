# __init__.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Arcturus: a programming language and compiler for the Infocom Z-machine.

The compiler is written in Python and depends only on the standard library, so
it runs on a bare interpreter. The standard library, Cosmos, is written in
Arcturus itself and is compiled together with the author's program; the
compiler hardcodes nothing about it, including its version.
"""

__version__ = "0.11.44"

# The build fingerprint. __version__ names the intended release and only moves
# on a bump, so two amalgams built from different source between bumps carry
# the SAME version but are different tools (this confused two early testers).
# __build__ is a short content hash the amalgamator bakes into build/arcc, so
# `arcc --version` names the exact build: same id means byte-identical, a
# different id means a different tool at the same version. None here means the
# package is running from source, not the standalone.
__build__ = None


def build_id() -> str:
    """The build fingerprint for display: the amalgam's baked hash, or the
    word 'source' when running from the working tree (a source run is a dev
    build, never a distributed artifact)."""
    return __build__ or "source"
