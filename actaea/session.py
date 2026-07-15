# session.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Record, replay, and check: the Arcturus answer to Inform's RECORDING /
REPLAY, done in the interpreter rather than the game so it costs the story
nothing and works on any file (docs/06). Three command-line flags over one
plain-text file:

  --record FILE   play normally; save the session (your commands AND the
                  game's replies) to FILE as a readable transcript.
  --replay FILE   run FILE's commands, then hand you the keyboard to keep
                  playing (the "skip ahead to where I was").
  --check FILE    re-run FILE's commands against the current game and report,
                  in plain words, whether it still plays the same. Stops at
                  the first divergence, because once the world's state moves
                  every later reply is noise.

The file is the readable playthrough: command lines start with `> `, and the
game's reply to each command sits under it. Commands are the editable spine,
so an author can add commands by hand; a command with no recorded reply (one
they typed in) is run and shown as NEW rather than checked. This all lives at
the io boundary (io.py), so it wraps any front-end without the VM knowing."""

import re

from .io import IOSystem


def _strip_prompt(text: str) -> str:
    """Remove the trailing input prompt (a paragraph break then `>`, Cosmos's
    `prompt` block) from a reply block, so the recorded transcript does not
    carry a dangling `>` before each command line."""
    return re.sub(r"\s*>\s*\Z", "", text)


def _norm(text: str) -> str:
    """The comparison form of a reply: the prompt stripped and both ends
    trimmed, so cosmetic paragraph spacing never reads as a regression but a
    real change in the words does."""
    return _strip_prompt(text).strip()


def parse_walkthrough(text: str):
    """Split a recorded file into (intro, turns), where intro is the opening
    reply before the first command and turns is a list of (command, reply).
    A reply is None when the file records a command with no reply under it (a
    hand-added command): it is run but not checked. Lines beginning with `#`
    are comments (for hand-written command files) and are dropped."""
    intro: list[str] = []
    turns: list = []  # [command, [reply lines]]
    current = intro
    for line in text.splitlines(keepends=True):
        if line.startswith("> "):
            command = line[2:].rstrip("\n")
            turns.append([command, []])
            current = turns[-1][1]
        elif line.lstrip().startswith("#"):
            continue  # a comment line (hand-written command files)
        else:
            current.append(line)
    # An empty opening (a commands-only file that an author hand-wrote) is
    # None, so check skips the opening rather than flagging a missing banner.
    intro_text = "".join(intro)
    if not intro_text.strip():
        intro_text = None
    out_turns = []
    for command, reply_lines in turns:
        reply = "".join(reply_lines)
        # A command with nothing under it (immediately followed by the next
        # command, or the end of file) has no recorded reply: mark it None so
        # check runs it but shows it as NEW instead of comparing.
        out_turns.append((command, reply if reply.strip() else None))
    return intro_text, out_turns


class SessionIO(IOSystem):
    """Wraps a real front-end IO to add record / replay / check at the input
    and output boundary. Output flows through print_text (game text only, not
    the front-end's own command echo), so a reply block is exactly what the
    game said between two reads."""

    def __init__(self, inner, record_path=None, replay=None, check=None,
                 report=None, stop_at_end=False):
        self.inner = inner
        self.record_path = record_path
        self._record_fh = None
        # replay: a list of commands to feed before handing control back to
        # the keyboard (None outside replay). check: (intro, turns) to compare
        # against; when set, play is headless and ends at the last command.
        # stop_at_end: end when the replay script runs out instead of reading
        # on (the --replay --headless regression case).
        self.replay = list(replay) if replay is not None else None
        self.check = check
        self.stop_at_end = stop_at_end
        self._report = report if report is not None else print
        self.pending: list[str] = []      # game text since the last read
        self.turn = 0                      # commands issued so far
        self.diverged = False              # a check found a difference
        self.new_commands = 0              # hand-added commands shown as NEW
        self.compared = 0                  # commands actually checked
        if record_path is not None:
            self._record_fh = open(record_path, "w", encoding="utf-8")

    # mirror the inner front-end's capabilities and file channels
    @property
    def supports_timed(self):
        return self.inner.supports_timed

    @property
    def supports_pictures(self):
        return self.inner.supports_pictures

    def print_text(self, text: str) -> None:
        self.pending.append(text)
        self.inner.print_text(text)

    def erase_lower(self) -> None:
        self.inner.erase_lower()

    def save_path(self, default):
        return self.inner.save_path(default)

    def restore_path(self, default):
        return self.inner.restore_path(default)

    def transcript_path(self, default):
        return self.inner.transcript_path(default)

    def read_char(self, timeout=0.0, on_timeout=None) -> int:
        # A press-any-key moment during a scripted run answers itself with
        # Enter, the walkthrough convention; once the script is spent, real
        # keys again.
        if self._scripted():
            return 13
        return self.inner.read_char(timeout, on_timeout)

    def read_line(self, max_len, preload="", terminators=frozenset(),
                  timeout=0.0, on_timeout=None):
        reply = "".join(self.pending)
        self.pending = []
        self._handle_reply(reply)
        line = self._next_command(max_len, preload, terminators, timeout, on_timeout)
        if line is None:
            # Replay/check exhausted with nothing to hand off to: end the run
            # the way a spent input pipe does.
            raise EOFError
        if self._record_fh is not None:
            self._record_fh.write(f"> {line}\n")
        self.turn += 1
        return (preload + line)[:max_len], 13

    # -- internals ---------------------------------------------------------

    def _scripted(self) -> bool:
        return self.replay is not None and self.turn < len(self.replay) \
            or (self.check is not None)

    def _handle_reply(self, reply: str) -> None:
        stripped = _strip_prompt(reply)
        if self._record_fh is not None:
            self._record_fh.write(stripped)
            if stripped and not stripped.endswith("\n"):
                self._record_fh.write("\n")
        if self.check is not None and not self.diverged:
            self._check_reply(reply)

    def _check_reply(self, reply: str) -> None:
        intro, turns = self.check
        if self.turn == 0:
            expected = intro
            where = "the opening"
        elif self.turn - 1 < len(turns):
            _, expected = turns[self.turn - 1]
            where = f"command {self.turn}"
        else:
            return
        if expected is None:
            return  # a NEW (hand-added) command: already run, nothing to check
        self.compared += 1
        if _norm(reply) != _norm(expected):
            self.diverged = True
            self._emit_divergence(where, expected, reply)

    def _emit_divergence(self, where, expected, got) -> None:
        cmd = ""
        if where.startswith("command"):
            idx = int(where.split()[1]) - 1
            cmd = self.check[1][idx][0]
        r = self._report
        r("")
        if cmd:
            r(f"{where.capitalize()} changed:")
            r(f"    > {cmd}")
        else:
            r(f"{where.capitalize()} changed:")
        r("    before:")
        r(_indent(_norm(expected)))
        r("    now:")
        r(_indent(_norm(got)))
        r("")
        r("The playthrough diverged here. Anything after this point is "
          "unreliable,")
        r("because the game is now in a different state. Fix this, or "
          "re-record if")
        r("the change was intended.")

    def _next_command(self, max_len, preload, terminators, timeout, on_timeout):
        if self.check is not None:
            _, turns = self.check
            if self.diverged or self.turn >= len(turns):
                return None
            return turns[self.turn][0]
        if self.replay is not None and self.turn < len(self.replay):
            cmd = self.replay[self.turn]
            # Echo the replayed command so a watcher sees it (the front-end
            # would echo a typed line; a fed one has no keystrokes to echo).
            self.inner.print_text(cmd + "\n")
            return cmd
        if self.stop_at_end:
            return None  # --replay --headless: stop at the script's end
        # No script left: hand control to the real keyboard.
        line, _term = self.inner.read_line(
            max_len, preload, terminators, timeout, on_timeout)
        return line[len(preload):]

    def close(self) -> None:
        """Flush the final reply block (the output after the last command) and
        close the record file. Called once the run ends."""
        if self._record_fh is not None:
            tail = _strip_prompt("".join(self.pending))
            if tail:
                self._record_fh.write(tail)
                if not tail.endswith("\n"):
                    self._record_fh.write("\n")
            self._record_fh.close()
            self._record_fh = None
        self.pending = []


def _indent(text: str) -> str:
    return "\n".join("      " + ln for ln in text.splitlines()) or "      (nothing)"
