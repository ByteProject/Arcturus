# __init__.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea: a Standard 1.1 conformant Z-machine interpreter for versions 5 and
8, in Python with a tkinter front-end. It plays any well-formed story file,
not only Arcturus output. docs/06-actaea-design.md is the authoritative
design; this package is Arcturus milestone B10.

The architecture is two layers with a hard boundary: a headless virtual
machine core (loader, memory, decoder, executor, objects, text, dictionary,
streams, screen model, Quetzal) that talks to the world only through a small
I/O interface, and a tkinter front-end that implements that interface. The
core never imports tkinter; conformance (CZECH, Praxix) runs through the
console harness in __main__."""

__version__ = "0.12.2"


def banner() -> str:
    """The identity block: the CLI shows it for help and the info tools,
    the front-ends for their About panels. One string, one truth."""
    return (
        f"Actaea v{__version__} - Z-machine v5/8 interpreter, "
        "debugger and disassembler\n"
        "Standard 1.1 conformant | Part of Arcturus "
        "(programming language & compiler)\n"
        "Copyright (c) 2026, Stefan Vogt | "
        "https://github.com/ByteProject/Arcturus"
    )
