# memory.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Z-machine memory map: one flat byte array with three regions and two
access disciplines.

Dynamic memory runs from address 0 up to (not including) the static-memory
base named in the header at 0x0E; the game may read and write it, and it is
what Quetzal saves and undo snapshots. Static memory runs from that base up
to the end of the file (at most 0xFFFF is byte-addressable); readable, never
writable. High memory, from the header's high-memory base at 0x04, holds
routines and strings; it is not byte-addressed by the game at all but reached
through PACKED addresses, which multiply out to byte offsets that may exceed
0xFFFF. The regions may overlap (high memory usually sits inside or beyond
static); the discipline is per-operation, not per-address.

Everything here is UNSIGNED. The Z-machine stores 16-bit words big-endian and
leaves signedness to individual opcodes, so the memory layer hands out plain
0..0xFFFF values, and the two helpers to_signed/from_signed are THE one place
the whole interpreter converts. Every opcode that compares or does signed
arithmetic must go through them; scattering ad-hoc sign math is how the
compiler's print-or-run bug happened (2026-07-04, packed address 0x8000 read
as negative), and Actaea does not repeat it."""

from .errors import MemoryFault

# Header offsets the memory layer itself needs; loader.py owns the full map.
_HIGH_BASE = 0x04
_STATIC_BASE = 0x0E


def to_signed(value: int) -> int:
    """A raw 16-bit word as the signed -32768..32767 the branch and
    arithmetic opcodes see."""
    return value - 0x10000 if value >= 0x8000 else value


def from_signed(value: int) -> int:
    """A Python integer (any sign) wrapped to the 16-bit word the machine
    stores; arithmetic opcodes wrap modulo 0x10000 by definition."""
    return value & 0xFFFF


class Memory:
    """The story's memory: bounds-checked byte and word access, the dynamic
    write barrier, and packed-address resolution (x4 for v5, x8 for v8, the
    only version-dependent arithmetic in Actaea)."""

    def __init__(self, data: bytes, scale: int):
        self.mem = bytearray(data)
        self.scale = scale
        self.static_base = (data[_STATIC_BASE] << 8) | data[_STATIC_BASE + 1]
        self.high_base = (data[_HIGH_BASE] << 8) | data[_HIGH_BASE + 1]
        # The pristine image, for restart and for Quetzal's XORed CMem form.
        self.initial = bytes(data)

    # -- reads ---------------------------------------------------------------

    def byte(self, addr: int) -> int:
        if not 0 <= addr < len(self.mem):
            raise MemoryFault(f"byte read at {addr:#06x}, beyond the story")
        return self.mem[addr]

    def word(self, addr: int) -> int:
        if not 0 <= addr < len(self.mem) - 1:
            raise MemoryFault(f"word read at {addr:#06x}, beyond the story")
        return (self.mem[addr] << 8) | self.mem[addr + 1]

    # -- writes: dynamic memory only ------------------------------------------

    def set_byte(self, addr: int, value: int) -> None:
        if not 0 <= addr < self.static_base:
            raise MemoryFault(
                f"byte write at {addr:#06x}, outside dynamic memory "
                f"(static base {self.static_base:#06x})"
            )
        self.mem[addr] = value & 0xFF

    def set_word(self, addr: int, value: int) -> None:
        # Both bytes must be dynamic; a word straddling the barrier is a fault.
        if not 0 <= addr < self.static_base - 1:
            raise MemoryFault(
                f"word write at {addr:#06x}, outside dynamic memory "
                f"(static base {self.static_base:#06x})"
            )
        self.mem[addr] = (value >> 8) & 0xFF
        self.mem[addr + 1] = value & 0xFF

    # -- packed addresses ------------------------------------------------------

    def unpack(self, packed: int) -> int:
        """A packed routine or string address as a byte offset. v5 and v8 use
        a bare multiplier (the v6/v7 routine/string offsets do not exist
        here), so one method serves both kinds."""
        return packed * self.scale

    # -- restart ----------------------------------------------------------------

    def reset(self) -> None:
        """Back to the pristine story image (restart, or a failed restore).
        The standard preserves two flags-2 bits across restart (transcribing
        and fixed-pitch); the VM layer reapplies them after calling this."""
        self.mem[:] = self.initial
