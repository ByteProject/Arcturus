# __main__.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The console entry: `python3 -m actaea <story>` PLAYS the story on the
console (the headless runner that carried CZECH and Praxix through the M6
gate). --header reports the parsed header; --disasm prints the reachable
routines. From M7 this hands off to the tkinter front-end unless asked to
stay on the console."""

import argparse
import os
import sys

from . import __version__
from .errors import ActaeaError
from .loader import load_file


def _pipe_closed() -> int:
    """The reader of our stdout (a `| head`, say) went away: that is a normal
    ending for an info tool, not an error. Point stdout at the void so the
    interpreter's exit-time flush does not raise a second time, and leave."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    return 0


def _report(story) -> str:
    h = story.header
    lines = [
        f"version   z{h.version} (packed addresses x{story.memory.scale})",
        f"release   {h.release} / serial {h.serial}",
        f"length    {h.file_length} bytes",
        f"checksum  {h.checksum:#06x} "
        + ("(verified)" if story.checksum_ok() else "(MISMATCH)"),
        f"start     {h.initial_pc:#06x} (initial program counter)",
        f"memory    dynamic below {h.static_base:#06x}, "
        f"high from {h.high_base:#06x}",
        f"tables    dictionary {h.dictionary:#06x}, objects {h.objects:#06x}, "
        f"globals {h.globals_:#06x}, abbreviations {h.abbreviations:#06x}",
    ]
    extras = []
    if h.alphabet:
        extras.append(f"alphabet {h.alphabet:#06x}")
    if h.terminating:
        extras.append(f"terminating chars {h.terminating:#06x}")
    if h.header_ext:
        extras.append(f"header extension {h.header_ext:#06x}")
    if extras:
        lines.append("extras    " + ", ".join(extras))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="actaea",
        description="Actaea, the Arcturus reference Z-machine interpreter "
        "(versions 5 and 8).",
    )
    ap.add_argument("story", help="a .z5 or .z8 story file")
    ap.add_argument(
        "--header",
        action="store_true",
        help="load and validate the story, print its header, and exit",
    )
    ap.add_argument(
        "--disasm",
        action="store_true",
        help="disassemble every routine reachable from the entry point",
    )
    ap.add_argument("--version", action="version", version=f"actaea {__version__}")
    args = ap.parse_args(argv)

    try:
        story = load_file(args.story)
    except OSError as e:
        print(f"actaea: {e}", file=sys.stderr)
        return 2
    except ActaeaError as e:
        print(f"actaea: {e}", file=sys.stderr)
        return 2

    try:
        if args.disasm:
            from .decode import disassemble

            try:
                print(disassemble(story))
            except ActaeaError as e:
                print(f"actaea: {e}", file=sys.stderr)
                return 2
            return 0

        if args.header:
            print(_report(story))
            return 0

        # The default: play the story on the console.
        from .io import ConsoleIO
        from .vm import VM

        vm = VM(story, ConsoleIO())
        try:
            vm.run()
        except EOFError:
            # The input pipe ended before the story quit: a normal ending
            # for scripted play (walkthrough files end where they end).
            return 0
        except ActaeaError as e:
            print(f"\nactaea: {e}", file=sys.stderr)
            return 3
        return 0
    except BrokenPipeError:
        return _pipe_closed()


if __name__ == "__main__":
    sys.exit(main())
