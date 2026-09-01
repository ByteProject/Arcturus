#!/usr/bin/env python3
# cycle_eval.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus
"""The cycle-exact per-turn benchmark behind tests/performance_eval.md
sections 8 and 9: both Hibernated 2 builds through the sibling Varuna
interpreter in SIM6502, ten commands, cycle stamps at every line read and
every scripted menu key. Needs the Varuna checkout beside this repo and
the mads assembler on PATH; the PunyInform artifact is recovered from
Varuna's first-milestone commit (git show 523053d:tests/hibernated2.z5).
Run from the Arcturus repo root."""
import os, subprocess, sys
ROOT = os.path.abspath("../Varuna")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from simtest import Harness

CMDS = ["push grill", "push grill", "talk to vlad", "n", "take spray oil",
        "examine terminal", "talk to vlad", "e"]
KEY_AFTER = {"talk to vlad": "1"}  # the menu answer, its own stamped turn

def build(story_path, tag):
    binp = os.path.join(ROOT, "build", "test_core.bin")
    labp = os.path.join(ROOT, "build", "test_core.lab")
    r = subprocess.run(["mads", os.path.join(ROOT, "tools/sim_asm/test_core.asm"),
                       "-i:" + os.path.join(ROOT, "src"), "-o:" + binp, "-t:" + labp],
                      capture_output=True, text=True)
    assert r.returncode == 0, "assembly failed"
    atr = os.path.join(ROOT, "build", f"_eval_{tag}.atr")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools/mkatr.py"),
                    "--story", story_path, "--boot", os.path.join(ROOT, "build/boot.bin"),
                    "--out", atr, "--density", "dd"], capture_output=True)
    return binp, labp, atr

def play(story_path, tag):
    binp, labp, atr = build(story_path, tag)
    h = Harness(binp, labp, atr=atr)
    h.wword(h.sym["STORY_SECTOR"], 4)
    out = bytearray()
    stamps = []   # (label, cycles)
    q = list(CMDS)
    keys = []
    h.cpu.pc_hooks[h.sym["ZOUT_DEVICE"]] = lambda c: out.append(c.a)

    def aread(c):
        if q:
            cmd = q.pop(0)
            stamps.append((cmd, c.cycles))
            c.kbd_queue[:] = list(cmd.encode()) + [0x9B]
            if cmd in KEY_AFTER:
                keys.append(KEY_AFTER[cmd])
        else:
            stamps.append(("END", c.cycles))
            c.halted = True

    def gk(c):
        if not c.kbd_queue:
            if keys:
                k = keys.pop(0)
                stamps.append(("[menu key %s]" % k, c.cycles))
                c.kbd_queue.append(ord(k))
            else:
                c.kbd_queue.append(0x20)

    h.cpu.pc_watch[h.sym["OP_AREAD"]] = aread
    h.cpu.pc_watch[h.sym["GETKEY"]] = gk
    h.cpu.pc = h.sym["INTERP_RUN"]
    h.cpu.run(900_000_000)
    return out, stamps

def report(tag, out, stamps):
    print(f"== {tag} ==")
    total = 0
    for k in range(len(stamps) - 1):
        label, at = stamps[k]
        cost = stamps[k + 1][1] - at
        total += cost
        print(f"  {label:<20} {cost:>12,} cycles  {cost/1_789_790:>6.2f}s")
    print(f"  {'TOTAL':<20} {total:>12,} cycles  {total/1_789_790:>6.2f}s")
    return total

for tag, path in (("ARCTURUS 2.0", os.path.join(ROOT, "tests/hibernated2.z5")),
                  ("PUNYINFORM", "/tmp/h2-puny.z5")):
    out, stamps = play(path, tag.split()[0].lower())
    report(tag, out, stamps)
    txt = out.decode("latin1", "replace")
    assert "grill" in txt.lower(), "transcript sanity"
