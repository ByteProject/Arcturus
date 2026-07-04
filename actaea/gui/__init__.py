# __init__.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The tkinter front-end (M7 onward). It implements the io.py boundary
against real widgets and owns the event loop; no game logic lives here, and
the core never imports it (the import runs the other way, exactly the hard
boundary docs/06 section 4 demands)."""
