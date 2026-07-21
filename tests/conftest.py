# conftest.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Shared test configuration.

The suite is CPU-bound: almost every test compiles a whole game against the
standard library, which is around 117ms of parse, analyze and codegen, and there
are hundreds of them. The tests are independent, so they run in parallel
(pytest-xdist, configured in pyproject.toml), which is what keeps a full run in
the tens of seconds rather than minutes.

Two kinds of test cannot share that freedom. The tkinter front-end needs a
display and the curses front-end needs a terminal, and neither tolerates a
second copy of itself running at the same moment: contending for the display is
how a test goes from failing to HANGING, which is worse. Both are therefore
pinned to a single worker, so they run one after another while everything else
spreads out.
"""

import pytest

# Test modules that touch a display or a terminal, by path fragment.
_DISPLAY_BOUND = (
    "actaea/test_console.py",
    "actaea/unit/test_gui.py",
)


def pytest_collection_modifyitems(items):
    for item in items:
        path = str(getattr(item, "fspath", "")).replace("\\", "/")
        if any(frag in path for frag in _DISPLAY_BOUND):
            # One xdist group means one worker, so these never run concurrently
            # with each other. Harmless when xdist is absent.
            item.add_marker(pytest.mark.xdist_group("display"))
