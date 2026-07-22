# __init__.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea: a Standard 1.1 conformant Z-machine interpreter for versions 5 and
8, in Python with a tkinter front-end. It plays any well-formed story file,
not only Arcturus output. docs/06-actaea.md is the official documentation and
actaea-design.md (beside this package) the design record; this package is
Arcturus milestone B10, complete.

The architecture is two layers with a hard boundary: a headless virtual
machine core (loader, memory, decoder, executor, objects, text, dictionary,
streams, screen model, Quetzal) that talks to the world only through a small
I/O interface, and a tkinter front-end that implements that interface. The
core never imports tkinter; conformance (CZECH, Praxix) runs through the
console harness in __main__."""

__version__ = "1.3.4"

# The build fingerprint. __version__ names the intended release; __build__ is a
# short content hash the amalgamator bakes into build/actaea, so two standalones
# at the same version but built from different source are still told apart (see
# arcturus/__init__.py for the full rationale). None means running from source.
__build__ = None


def build_id() -> str:
    """The build fingerprint for display: the amalgam's baked hash, or 'source'
    when running from the working tree."""
    return __build__ or "source"


def banner() -> str:
    """The identity block: the CLI shows it for help and the info tools,
    the front-ends for their About panels. One string, one truth. It carries
    no build id, so the About panel and help stay clean; --version appends the
    build itself (version_text)."""
    return (
        f"Actaea v{__version__} - Z-machine v5/8 interpreter, "
        "debugger and disassembler\n"
        "Standard 1.1 conformant | Part of Arcturus "
        "(programming language & compiler)\n"
        "Copyright (c) 2026, Stefan Vogt | "
        "https://github.com/ByteProject/Arcturus"
    )


def version_text() -> str:
    """The banner plus the exact build, for `actaea --version`. The banner
    alone (help, About) stays build-free."""
    return f"{banner()}\nBuild {build_id()}"
