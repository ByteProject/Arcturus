# errors.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea's error family. Everything the interpreter raises deliberately
derives from ActaeaError, so the console runner and the GUI can catch one
type and show a clean message; anything else escaping is a genuine bug in
Actaea itself."""


class ActaeaError(Exception):
    """Base for every deliberate Actaea error."""


class StoryFormatError(ActaeaError):
    """The file is not a story file Actaea plays: too short, a version other
    than 5 or 8, or a header that contradicts the file it sits in."""


class MemoryFault(ActaeaError):
    """An out-of-range read, or a write outside dynamic memory. A well-formed
    story never triggers one; reporting it beats silently corrupting the
    machine (the permissive-interpreter lesson of 2026-07-04: dfrotz executed
    a wild call without a word, fizmo named it, and only then was the
    compiler's sign bug findable)."""
