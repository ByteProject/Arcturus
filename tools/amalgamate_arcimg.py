#!/usr/bin/env python3
# amalgamate_arcimg.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Build the standalone `build/arcimg` from `tools/arcimg.py`.

arcimg is already one self-contained, standard-library file, so unlike arcc and
actaea there is nothing to gather: this just stamps a build fingerprint over the
source's `__build__ = None`, makes the result executable via its shebang, and
writes it to build/arcimg. Same arrangement as the other two standalones, so
`arcimg --version` names the exact build the way `arcc` and `actaea` do.
"""

import hashlib
import os
import stat
import sys


def _fingerprint(src: str) -> str:
    """A short content hash of the source as embedded (with __build__ still
    None, so the fingerprint never depends on itself): same source in, same id
    out, a different id means a genuinely different tool."""
    return hashlib.sha256(src.encode("utf-8")).hexdigest()[:7]


def build(output_path: str) -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(here, "arcimg.py")
    with open(source_path, "r", encoding="utf-8") as fh:
        src = fh.read()

    build_id = _fingerprint(src)
    marker = "__build__ = None"
    if marker not in src:
        raise SystemExit("amalgamate_arcimg: cannot find the __build__ marker "
                         "in tools/arcimg.py")
    stamped = src.replace(marker, f"__build__ = {build_id!r}", 1)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(stamped)
    mode = os.stat(output_path).st_mode
    os.chmod(output_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"wrote {output_path} ({len(stamped)} bytes, build {build_id})")


def main(argv) -> int:
    output = argv[0] if argv else os.path.join("build", "arcimg")
    build(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
