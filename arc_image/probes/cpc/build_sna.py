#!/usr/bin/env python3
# build_sna.py - wrap probe.bin into a v1 CPC snapshot (probe.sna)
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
#
# The v1 .sna: a 256-byte header ("MV - SNA", the Z80 and hardware state)
# and a 64K RAM dump. The probe is loaded at $4000 with PC there and the
# stack just below; the CRTC comes preset to the standard 40x25 screen at
# $C000 (R1=40, R6=25, R9=7, R12=$30), so the probe itself only touches
# the gate array (mode, inks) and the PPI (the keyboard). Pure Python, no
# tools: the BuildTools manner.

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ORG = 0x4000

with open(os.path.join(HERE, "probe.bin"), "rb") as f:
    code = f.read()

head = bytearray(256)
head[0:8] = b"MV - SNA"
head[0x10] = 1                      # version 1
# Z80 registers: only SP, PC, and IM matter to the probe
head[0x21] = 0xF0                   # SP = $3FF0, below the code
head[0x22] = 0x3F
head[0x23] = ORG & 0xFF             # PC = the probe
head[0x24] = ORG >> 8
head[0x25] = 1                      # IM 1 (interrupts stay disabled anyway)
# gate array: pen 0 selected, a black default palette, mode 0 + ROMs off
head[0x2E] = 0
for i in range(17):
    head[0x2F + i] = 0x54           # hardware black everywhere pre-probe
head[0x40] = 0x8C                   # mode 0, upper and lower ROM disabled
head[0x41] = 0xC0                   # standard RAM configuration
# CRTC: the standard 40x25 screen at $C000
crtc = [63, 40, 46, 0x8E, 38, 0, 25, 30, 0, 7, 0, 0, 0x30, 0, 0, 0, 0, 0]
head[0x42] = 0                      # selected register
head[0x43:0x43 + 18] = bytes(crtc)
head[0x55] = 0                      # upper ROM number
# PPI: port A output, tape motor off
head[0x56] = 0
head[0x57] = 0
head[0x58] = 0
head[0x59] = 0x82
head[0x6B] = 64                     # 64K dump follows
head[0x6C] = 0

ram = bytearray(65536)
ram[ORG:ORG + len(code)] = code

out = os.path.join(HERE, "probe.sna")
with open(out, "wb") as f:
    f.write(head)
    f.write(ram)
print(f"wrote probe.sna (code {len(code)} bytes at ${ORG:04X}, 64K dump)")
