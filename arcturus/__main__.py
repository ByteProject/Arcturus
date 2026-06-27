# __main__.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Enables `python3 -m arcturus ...` during development."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
