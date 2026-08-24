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

from . import banner, version_text
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


def _resolve_images(story_path: str, images_arg):
    """Where the story's arc_image pictures live. An arc_image id is the
    resource slot, so a front-end loads picture N directly; there is no name
    manifest. Returns (images_dir, images_pack): a loose directory of
    numbered PNGs, or a Blorb pack. Priority: an explicit --images
    directory; else a .zblorb story serving its own pictures; else a
    sibling .blorb pack; else the story's own directory (the loose debug
    default). The .arcres zip was retired (2026-07-31); the Blorb is the
    one pack."""
    if images_arg:
        return images_arg, None
    # A .zblorb serves its own pictures (Pict N inside the same file).
    try:
        from .loader import is_blorb
        with open(story_path, "rb") as fh:
            if is_blorb(fh.read(12)):
                return None, story_path
    except OSError:
        pass
    blb = os.path.splitext(story_path)[0] + ".blorb"
    if os.path.isfile(blb):
        return None, blb
    return os.path.dirname(os.path.abspath(story_path)), None


def _tk_hint() -> str:
    """The exact way to get tkinter on THIS platform, one copy-paste away.
    tkinter is part of the Python build, not a pip package, so Actaea
    cannot install it; the best it can do is name the remedy precisely
    (the Fos report, 2026-08-11: a tkinter-less Windows Python fell
    silently through to the bare pipe, which read as Actaea being
    broken while Windows Frotz worked beside it)."""
    if sys.platform == "win32":
        return ("tkinter ships with the python.org installer: re-run the "
                "installer, choose Modify, and tick 'tcl/tk and IDLE', "
                "then start Actaea the same way again (py actaea story.z5)")
    if sys.platform == "darwin":
        return ("a Homebrew Python gets it with 'brew install python-tk'; "
                "the python.org installer includes it already")
    return ("most Linux systems ship it as a package: "
            "'sudo apt install python3-tk' on Debian, Ubuntu, and "
            "Raspberry Pi OS, 'sudo dnf install python3-tkinter' on Fedora")


def _play_window(story, title: str, images_dir=None, images_zip=None,
                 seed=None, root=None, story_path=None) -> bool:
    try:
        from .gui.app import play
    except ImportError:
        return False  # no tkinter on this Python
    play(story, title, images_dir, images_zip, seed=seed, root=root,
         story_path=story_path)
    return True


def _play_terminal(story, title: str, seed=None) -> bool:
    if not sys.stdin.isatty():
        return False  # curses needs a real terminal
    try:
        from .console import play
    except ImportError:
        return False  # no curses on this platform (native Windows)
    play(story, title, seed=seed)
    return True


def _play_headless(story, seed=None) -> int:
    from .io import ConsoleIO
    from .vm import VM

    vm = VM(story, ConsoleIO(), seed=seed)
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


def _play_terminal_session(story, title, record_path, replay_path, seed=None) -> bool:
    """--console with --record / --replay: the curses terminal, wrapped in the
    same session recorder. Returns False (to fall back to the plain console)
    when there is no terminal or no curses."""
    if not sys.stdin.isatty():
        return False
    try:
        from .console import play
        from .session import parse_walkthrough
    except ImportError:
        return False
    replay_commands = None
    if replay_path is not None:
        with open(replay_path, "r", encoding="utf-8") as fh:
            _intro, turns = parse_walkthrough(fh.read())
        replay_commands = [cmd for cmd, _reply in turns]
    play(story, title, record_path=record_path, replay_commands=replay_commands,
         seed=seed)
    return True


def _play_session(story, record_path, replay_path, headless, seed=None) -> int:
    """--record and/or --replay: play through the plain console, recording the
    session and/or feeding a recorded file's commands first. A recording or
    replay is a debugging activity, so it runs on the plain console (io.py),
    interactive in a terminal, piped otherwise; the fancy window is not
    involved. When --replay runs out of commands it hands control to the
    keyboard, unless --headless asked it to stop at the end."""
    from .io import ConsoleIO
    from .session import SessionIO, parse_walkthrough
    from .vm import VM

    replay_commands = None
    if replay_path is not None:
        with open(replay_path, "r", encoding="utf-8") as fh:
            _intro, turns = parse_walkthrough(fh.read())
        replay_commands = [cmd for cmd, _reply in turns]

    inner = ConsoleIO()
    io = SessionIO(inner, record_path=record_path, replay=replay_commands,
                   stop_at_end=(replay_commands is not None and headless))
    vm = VM(story, io, seed=seed)
    try:
        vm.run()
    except EOFError:
        pass  # the script (or a piped stdin) ended; a normal scripted ending
    except ActaeaError as e:
        io.close()
        print(f"\nactaea: {e}", file=sys.stderr)
        return 3
    io.close()
    if record_path is not None:
        print(f"\nactaea: recorded {io.turn} commands to {record_path}",
              file=sys.stderr)
    return 0


def _run_check(story, check_path, seed=None) -> int:
    """--check: re-run a recorded file's commands against the current game and
    report whether it still plays the same, in plain words, stopping at the
    first divergence. Exit 0 when everything matched, 1 when it diverged."""
    from .io import CaptureIO
    from .session import SessionIO, parse_walkthrough
    from .vm import VM

    try:
        with open(check_path, "r", encoding="utf-8") as fh:
            intro, turns = parse_walkthrough(fh.read())
    except OSError as e:
        print(f"actaea: {e}", file=sys.stderr)
        return 2
    if not turns:
        print(f"actaea: {check_path} has no commands to check", file=sys.stderr)
        return 2

    report_lines: list[str] = []
    io = SessionIO(CaptureIO(), check=(intro, turns),
                   report=report_lines.append)
    vm = VM(story, io, seed=seed)
    print(f"Checking {check_path} against the game ... {len(turns)} commands.")
    try:
        vm.run()
    except EOFError:
        pass
    except ActaeaError as e:
        print(f"actaea: the game stopped with an error during check: {e}",
              file=sys.stderr)
        return 3
    io.close()

    if io.diverged:
        for ln in report_lines:
            print(ln)
        return 1
    new = sum(1 for _cmd, reply in turns if reply is None)
    if new:
        print(f"Everything recorded still plays the same. ({new} newly added "
              f"command(s) had no saved reply to check; re-record to save "
              f"them.)")
    else:
        print("Everything plays the same. Nothing broke.")
    return 0


class _Cli(argparse.ArgumentParser):
    """The house style for every tool-facing output: the banner on top
    (help, usage errors, all of it) and a blank line at the end, so the
    shell prompt never sits flush against the text."""

    def format_help(self):
        return banner() + "\n\n" + super().format_help() + "\n"

    def format_usage(self):
        return banner() + "\n\n" + super().format_usage()

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n\n")


class _Version(argparse.Action):
    """--version in the house style: the banner plus the exact build, then the
    trailing blank line (argparse's own version action strips it away, and
    reflows the text besides)."""

    def __call__(self, parser, namespace, values, option_string=None):
        print(version_text() + "\n")
        parser.exit(0)


def _alert(text: str) -> None:
    """A Finder-visible message for stub launches: stderr goes nowhere
    when there is no terminal, and a silent death reads as a broken app
    (the 2.0.0 field report: the app "pops up and closes immediately").
    osascript is macOS-only, which is exactly where the stub exists."""
    if sys.platform != "darwin":
        return
    import subprocess
    quoted = '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    try:
        subprocess.run(
            ["osascript", "-e", "display alert \"Actaea\" message " + quoted],
            capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pass


def _startup_story():
    """A story for a bare GUI launch, per the window's On Launch setting:
    "last" reopens the previous story when it still exists, otherwise (and
    as the default, "ask") a native open dialog. Returns (path, root): the
    dialog's withdrawn Tk root rides along to BECOME the window's root,
    because this platform's Tk does not survive a second one.

    A FINDER LAUNCH is a bare launch too: the .app stub execs `actaea`
    with no arguments, and the double-clicked story arrives moments later
    as an Apple Event (Tk's ::tk::mac::OpenDocument). So under the stub
    (ACTAEA_BUNDLE in the environment) the event gets a short grace
    before the On Launch preference speaks; a plain Dock-icon click has
    no document and falls through after the grace."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        from .gui.app import _load_settings
    except ImportError:
        return None, None
    root = None
    if os.environ.get("ACTAEA_BUNDLE"):
        import time
        try:
            root = tk.Tk()
        except tk.TclError:
            return None, None
        root.withdraw()
        docs: list = []
        try:
            root.createcommand("::tk::mac::OpenDocument",
                               lambda *paths: docs.extend(paths))
            for _ in range(12):
                root.update()
                if docs:
                    break
                time.sleep(0.05)
        except tk.TclError:
            pass
        opened = next((p for p in docs if p and os.path.isfile(p)), None)
        if opened:
            return opened, root
    st = _load_settings()
    if st.get("on_launch") == "last":
        last = st.get("last_story")
        if last and os.path.isfile(last):
            return last, root
    if root is None:
        try:
            root = tk.Tk()
        except tk.TclError:
            return None, None
        root.withdraw()
    # The panel must NOT anchor to the withdrawn root: an unmapped parent
    # has no frame, and the panel landed half off the bottom of the
    # desktop, unmovable (Stefan, 2026-08-21). The root is still placed
    # mid-screen first, so any toolkit that anchors to it regardless
    # anchors to the middle; without a parent the system centers the
    # panel itself.
    try:
        root.update_idletasks()
        root.geometry("+%d+%d" % (root.winfo_screenwidth() // 2,
                                  root.winfo_screenheight() // 3))
    except tk.TclError:
        pass
    path = filedialog.askopenfilename(
        title="Open a story",
        filetypes=[("Z-machine stories", "*.z5 *.z8 *.zblorb"),
                   ("All files", "*")],
    )
    return (path or None), root


def main(argv=None) -> int:
    ap = _Cli(prog="actaea")
    ap.add_argument(
        "story", nargs="?", default=None,
        help="a .z5, .z8, or .zblorb story file. Optional for the window: a "
        "bare 'actaea' asks for one, or reopens the last story, per the "
        "window's View > On Launch setting. Every terminal-facing mode "
        "still requires it",
    )
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
    ap.add_argument(
        "--images", metavar="DIR",
        help="directory of the story's numbered picture files (arc_image, GUI "
        "only); defaults to a sibling .blorb pack, then the story's own "
        "directory",
    )
    ap.add_argument(
        "--record", metavar="FILE",
        help="save this session (your commands and the game's replies) to FILE "
        "as a readable playthrough you can replay or check later",
    )
    ap.add_argument(
        "--replay", metavar="FILE",
        help="run FILE's commands, then hand you the keyboard to keep playing "
        "(skip ahead to where you were); with --headless, run and stop",
    )
    ap.add_argument(
        "--check", metavar="FILE",
        help="re-run a recorded FILE against this game and report, in plain "
        "words, whether it still plays the same (exit 1 if it diverged)",
    )
    ap.add_argument(
        "--seed", type=int, metavar="N",
        help="seed the random generator with N for a reproducible session "
        "(dice, shuffled ambience; restart rewinds the generator too). "
        "Pairs with --record/--replay/--check to make walkthroughs of "
        "games with random flavor deterministic; never implied, always "
        "explicit",
    )
    ap.add_argument(
        "--install-app", action="store_true",
        help="install the thin native launcher (a macOS Actaea.app stub, "
        "a Linux .desktop entry, Windows Start Menu and story "
        "associations) pointing at THIS copy of actaea, then exit. The "
        "core stays where it was downloaded, kept current by arcc "
        "--update; the stub holds no logic and follows automatically",
    )
    ap.add_argument("--version", action=_Version, nargs=0,
                    help="show the version banner and exit")
    args = ap.parse_args(argv)

    if args.install_app:
        print(banner() + "\n")
        from .gui import dress
        code = dress.install_app()
        print()
        return code

    # A Finder/stub launch (ACTAEA_BUNDLE, set by the .app shim) has NO
    # terminal at all: stdin is the void, isatty says no. That is not a
    # developer piping input, it is the most window-shaped launch there
    # is, so the bundle mark counts as a screen everywhere isatty does.
    # Without this the stub died at birth on a usage error nobody saw
    # (Stefan's install, 2026-08-21: "launches for a second, then
    # nothing").
    bundle = bool(os.environ.get("ACTAEA_BUNDLE"))

    gui_root = None
    if args.story is None:
        # A bare launch. Every terminal-facing mode is a developer at a
        # prompt and keeps the old contract; only the window may resolve a
        # story by itself (the dock-icon launch: double-click, play).
        if (args.console or args.headless or args.header or args.disasm
                or args.record or args.replay or args.check
                or not (sys.stdin.isatty() or bundle)):
            ap.error("the following arguments are required: story")
        # A bare launch with no tkinter must SAY so, not vanish: the
        # ImportError path used to return quietly, which from the stub
        # reads as the app popping up and closing (the 2.0.0 field
        # report; the reporter had Homebrew's tcl-tk but not python-tk).
        try:
            import tkinter  # noqa: F401
        except ImportError:
            msg = ("This Python has no tkinter, so the window cannot "
                   "open. " + _tk_hint() + ".")
            print(f"{banner()}\n\nactaea: {msg}\n", file=sys.stderr)
            if bundle:
                _alert(msg)
            return 2
        # The identity is claimed before the FIRST Tk root anywhere: the
        # menu bar name is snapshotted when Tk brings NSApplication up,
        # and the startup dialog's root is that moment on a bare launch.
        from .gui import dress
        dress.predress()
        resolved, gui_root = _startup_story()
        if resolved is None:
            if gui_root is not None:
                gui_root.destroy()
            return 0        # the player closed the dialog: a quiet non-start
        args.story = resolved

    try:
        story = load_file(args.story)
    except (OSError, ActaeaError) as e:
        print(f"{banner()}\n\nactaea: {e}\n", file=sys.stderr)
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
            print()
            return 0

        if args.header:
            print(banner() + "\n")
            print(_report(story))
            print()
            return 0

        if args.check is not None:
            if args.record or args.replay:
                print("actaea: --check runs on its own (not with --record or "
                      "--replay)", file=sys.stderr)
                return 2
            return _run_check(story, args.check, seed=args.seed)

        if args.record is not None or args.replay is not None:
            # In the terminal (--console): record and replay with the full
            # screen. Otherwise the plain console (piped, or a bare terminal).
            if args.console and not args.headless:
                if _play_terminal_session(
                        story, os.path.basename(args.story),
                        args.record, args.replay, seed=args.seed):
                    return 0
                print("actaea: no terminal for --console here; recording on "
                      "the plain console", file=sys.stderr)
            return _play_session(story, args.record, args.replay, args.headless, seed=args.seed)

        if args.headless:
            return _play_headless(story, seed=args.seed)

        if args.console:
            if _play_terminal(story, os.path.basename(args.story), seed=args.seed):
                return 0
            print("actaea: no terminal or no curses for --console here "
                  "(native Windows has no curses; WSL does); "
                  "playing headless", file=sys.stderr)
            return _play_headless(story, seed=args.seed)

        # arc_image resources for the window (the terminal and headless modes
        # cannot show pictures, so they ignore them).
        images_dir, images_zip = _resolve_images(args.story, args.images)
        story_path = os.path.abspath(args.story)

        # The default ladder: the window on a desktop; the terminal when
        # tkinter is absent; the pipe when input is piped or nothing
        # screen-like exists at all. Every step DOWN the ladder says so
        # (docs/06 section 1 has always promised it; only --console kept
        # the promise until the Fos report showed what silence costs).
        if sys.stdin.isatty() or bundle:
            # Identity before the root exists (idempotent; the bare-launch
            # path already claimed it), and heal an installed stub whose
            # core path went dead (the download directory moved).
            from .gui import dress
            dress.predress()
            dress.refresh_stub()
            if _play_window(story, os.path.basename(args.story),
                            images_dir, images_zip, seed=args.seed,
                            root=gui_root, story_path=story_path):
                return 0
            if gui_root is not None:
                gui_root.destroy()
            print("actaea: this Python has no tkinter, so the window "
                  "cannot open; " + _tk_hint() + ".", file=sys.stderr)
            if bundle:
                _alert("This Python has no tkinter, so the window cannot "
                       "open. " + _tk_hint() + ".")
            if _play_terminal(story, os.path.basename(args.story), seed=args.seed):
                return 0
            print("actaea: no curses here either (native Windows has "
                  "none); playing headless, a plain text pipe with no "
                  "status line.", file=sys.stderr)
        return _play_headless(story, seed=args.seed)
    except BrokenPipeError:
        return _pipe_closed()


if __name__ == "__main__":
    sys.exit(main())
