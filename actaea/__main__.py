# __main__.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The entry point: `python3 -m actaea <story>` plays the story. Three ways
to play, one headless core behind all of them:

- the window (default on a desktop): the tkinter front-end;
- --console: a full terminal interpreter in the manner of fizmo-ncursesw,
  with the game-drawn status bar, colours, [MORE] paging, and timed input,
  on the standard library's curses;
- --headless: the plain stdin/stdout pipe in the manner of dumb frotz, what
  debuggers, walkthrough scripts, and build tools drive.

--header reports the parsed header; --disasm prints the reachable routines.
When a requested front-end cannot exist here (no tkinter, no curses, no
tty), the choice degrades one honest step at a time and says so."""

import argparse
import os
import sys

from . import banner
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


def _play_window(story, title: str) -> bool:
    try:
        from .gui.app import play
    except ImportError:
        return False  # no tkinter on this Python
    play(story, title)
    return True


def _play_terminal(story, title: str) -> bool:
    if not sys.stdin.isatty():
        return False  # curses needs a real terminal
    try:
        from .console import play
    except ImportError:
        return False  # no curses on this platform (native Windows)
    play(story, title)
    return True


def _play_headless(story) -> int:
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="actaea",
        description=banner(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("story", help="a .z5 or .z8 story file")
    ap.add_argument(
        "--console",
        action="store_true",
        help="play in the terminal: status bar, colours, [MORE] paging, "
        "timed input (stdlib curses)",
    )
    ap.add_argument(
        "--headless",
        action="store_true",
        help="plain stdin/stdout pipe, dumb-terminal style: for debuggers, "
        "walkthrough scripts, and build tools (automatic when input is piped)",
    )
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
    ap.add_argument("--version", action="version", version=banner())
    args = ap.parse_args(argv)

    try:
        story = load_file(args.story)
    except (OSError, ActaeaError) as e:
        print(f"actaea: {e}", file=sys.stderr)
        return 2

    try:
        if args.disasm:
            print(banner() + "\n")
            try:
                from .decode import disassemble

                print(disassemble(story))
            except ActaeaError as e:
                print(f"actaea: {e}", file=sys.stderr)
                return 2
            return 0

        if args.header:
            print(banner() + "\n")
            print(_report(story))
            return 0

        if args.headless:
            return _play_headless(story)

        if args.console:
            if _play_terminal(story, os.path.basename(args.story)):
                return 0
            print("actaea: no terminal for --console here; "
                  "playing headless", file=sys.stderr)
            return _play_headless(story)

        # The default ladder: the window on a desktop; the terminal when
        # tkinter is absent; the pipe when input is piped or nothing
        # screen-like exists at all.
        if sys.stdin.isatty():
            if _play_window(story, os.path.basename(args.story)):
                return 0
            if _play_terminal(story, os.path.basename(args.story)):
                return 0
        return _play_headless(story)
    except BrokenPipeError:
        return _pipe_closed()


if __name__ == "__main__":
    sys.exit(main())
