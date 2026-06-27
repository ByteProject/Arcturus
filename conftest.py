# conftest.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

# Ensures the repository root is on sys.path so tests can import the
# `arcturus` package without an editable install. pytest adds the directory
# containing this conftest.py to sys.path in its default import mode.
