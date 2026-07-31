#!/usr/bin/env python3
# amalgamate_proteus.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Build the standalone `build/proteus` from `tools/proteus.py`.

proteus is one standard-library file, but unlike arcimg it carries a
payload: the Proteus single-file web template (built by the node toolchain
in proteus/, see proteus/PROVENANCE.md). This gathers the built template,
gzips it into the source's `TEMPLATE_B64 = None` slot, stamps the build
fingerprint over `__build__ = None`, and writes the executable result to
build/proteus. Regenerate it whenever the web interpreter changes, in the
same breath as the other standalones:

    cd proteus && node build.js && node tools/make-single-file.js --out dist/single-file
    python3 tools/amalgamate_proteus.py
"""

import base64
import gzip
import hashlib
import os
import stat
import sys


def _fingerprint(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()[:7]


def build(output_path: str) -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    source_path = os.path.join(here, "proteus.py")
    template_path = os.path.join(root, "proteus", "dist", "single-file",
                                 "proteus.html")

    with open(source_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    if not os.path.isfile(template_path):
        raise SystemExit(
            "amalgamate_proteus: no built template at proteus/dist/"
            "single-file/proteus.html; build it first (see the module "
            "docstring)")
    with open(template_path, "rb") as fh:
        template = fh.read()

    packed = base64.b64encode(gzip.compress(template, 9)).decode("ascii")
    marker = "TEMPLATE_B64: str | None = None"
    if marker not in src:
        raise SystemExit("amalgamate_proteus: cannot find the TEMPLATE_B64 "
                         "marker in tools/proteus.py")
    build_id = _fingerprint(src.encode("utf-8") + template)
    stamped = src.replace(marker, f'TEMPLATE_B64: str | None = "{packed}"', 1)
    bmarker = "__build__ = None"
    if bmarker not in stamped:
        raise SystemExit("amalgamate_proteus: cannot find the __build__ "
                         "marker in tools/proteus.py")
    stamped = stamped.replace(bmarker, f"__build__ = {build_id!r}", 1)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(stamped)
    mode = os.stat(output_path).st_mode
    os.chmod(output_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"wrote {output_path} ({len(stamped)} bytes, template "
          f"{len(template)} bytes, build {build_id})")


def main(argv) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    out = argv[1] if len(argv) > 1 else os.path.join(root, "build", "proteus")
    build(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
