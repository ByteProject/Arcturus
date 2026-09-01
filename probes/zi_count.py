#!/usr/bin/env python3
# zi_count.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus
"""Count executed z-instructions per command, the same metric the Varuna
cycle evaluation attributes (performance_eval.md): steps between one line
read and the next, labeled by the command. Story and command file are
arguments, so game content stays out of the tree.

    python3 probes/zi_count.py build/game.z5 commands.txt [n_commands]
"""
import sys

sys.path.insert(0, ".")
from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM


def main() -> int:
    story_path, cmd_path = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    script = open(cmd_path, encoding="utf-8").read().split("\n")

    reads = []  # (command_text, step_count_at_read)
    steps = 0

    class CountIO(CaptureIO):
        def read_line(self, max_len, preload="", terminators=frozenset(),
                      timeout=0.0, on_timeout=None):
            out = super().read_line(max_len, preload, terminators,
                                    timeout, on_timeout)
            reads.append([out[0] if isinstance(out, tuple) else out, steps])
            return out

    io = CountIO(script=list(script) + ["quit", "y"])
    # A fixed seed: ambience and every other random path must roll the same
    # way in a before/after comparison, or the wobble drowns the signal.
    vm = VM(load(open(story_path, "rb").read()), io, seed=7)
    try:
        while not vm.halted:
            vm.step()
            steps += 1
            if steps > 200_000_000:
                break
    except IndexError:
        pass  # script exhausted

    # Per-command cost: instructions between the read that ACCEPTED the
    # command and the next read (the turn it triggered).
    total = 0
    shown = 0
    print(f"{'command':<24} {'z-instructions':>14}")
    for k in range(len(reads) - 1):
        cmd, at = reads[k]
        nxt = reads[k + 1][1]
        cost = nxt - at
        if not cmd.strip():
            continue  # key-wait filler
        print(f"{cmd:<24} {cost:>14,}")
        total += cost
        shown += 1
        if shown >= limit:
            break
    if shown:
        print(f"{'TOTAL':<24} {total:>14,}   avg {total // shown:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
