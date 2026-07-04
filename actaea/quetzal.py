# quetzal.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Quetzal 1.4, the portable saved-game format (M10): an IFF FORM of type
IFZS. Actaea writes the compact form (CMem, the dynamic memory XORed against
the pristine story image and run-length coded) and reads both CMem and UMem,
so saves interoperate with Frotz and every other Quetzal interpreter, in
both directions. That interop IS the milestone's done-test.

The three chunks that matter:

- IFhd identifies the story the save belongs to: release, serial, checksum
  (all read from the PRISTINE image, since a game can scribble on its own
  dynamic header), and the resume PC. By long-standing convention the PC
  stored for a v5 save points AT the save instruction's store byte; the
  restoring interpreter reads the variable number there, writes 2 into it
  ("this save has just been restored"), and resumes at the following byte.
- CMem or UMem carries dynamic memory. CMem stores dynamic memory XOR the
  original image, with runs of zero bytes coded as 0x00 followed by
  (run length - 1); trailing zeros may be omitted entirely, so an early
  save is a few hundred bytes instead of tens of kilobytes.
- Stks carries the call stack, outermost frame first, beginning with the
  dummy frame that stands for the entry instruction stream (a v5 story
  starts in a bare stream, not a routine; Actaea's base pseudo-frame is
  exactly that dummy). Each frame: return PC (3 bytes), a flags byte
  (bit 4 set = call discarded its result, low nibble = local count), the
  store variable, a bitmask of arguments supplied, the frame's own
  evaluation-stack depth in words, then the locals and the stack words.

Unknown chunks (IntD, ANNO, AUTH, and whatever else a writer added) are
skipped on read, as the spec instructs. Everything here is pure data in and
data out: no VM import, no file handling. The VM hands over its memory and
frames and gets plain tuples back, which keeps this module testable byte by
byte and free of import cycles."""

from .errors import ActaeaError


class QuetzalError(ActaeaError):
    """The file is not a usable save: not IFZS at all, truncated, or a save
    of a different story. The message says which, plainly, because it is
    shown to a player who just tried to restore."""


# -- IFF plumbing --------------------------------------------------------------


def _chunk(tag: bytes, data: bytes) -> bytes:
    """One IFF chunk: tag, big-endian length, data, and the pad byte that
    keeps the next chunk even-aligned (the length field excludes the pad)."""
    pad = b"\x00" if len(data) & 1 else b""
    return tag + len(data).to_bytes(4, "big") + data + pad


def _chunks(data: bytes):
    """Iterate (tag, payload) over an IFF body, honouring pad bytes."""
    pos = 0
    while pos + 8 <= len(data):
        tag = bytes(data[pos:pos + 4])
        length = int.from_bytes(data[pos + 4:pos + 8], "big")
        payload = data[pos + 8:pos + 8 + length]
        if len(payload) < length:
            raise QuetzalError("save file is truncated mid-chunk")
        yield tag, payload
        pos += 8 + length + (length & 1)


# -- CMem coding ---------------------------------------------------------------


def compress(dynamic: bytes, initial: bytes) -> bytes:
    """Dynamic memory as CMem data: XOR against the pristine image, zero
    runs coded as 0x00 + (count - 1), trailing zeros dropped. A run longer
    than 256 is simply coded as several runs."""
    xored = bytes(a ^ b for a, b in zip(dynamic, initial))
    end = len(xored)
    while end and xored[end - 1] == 0:
        end -= 1
    out = bytearray()
    i = 0
    while i < end:
        if xored[i]:
            out.append(xored[i])
            i += 1
        else:
            j = i
            while j < end and xored[j] == 0 and j - i < 256:
                j += 1
            out += bytes((0, j - i - 1))
            i = j
    return bytes(out)


def decompress(data: bytes, initial: bytes, size: int) -> bytes:
    """CMem data back to dynamic memory, given the pristine image and the
    dynamic-memory size the story declares. Bytes beyond the coded data are
    unchanged from the image (the omitted trailing zeros)."""
    out = bytearray(initial[:size])
    addr = 0
    i = 0
    while i < len(data):
        b = data[i]
        i += 1
        if b == 0:
            if i >= len(data):
                # A lone trailing zero byte: one more unchanged byte, which
                # some writers emit instead of dropping it. Harmless.
                addr += 1
                break
            addr += data[i] + 1  # a run of (length byte + 1) zeros
            i += 1
        else:
            if addr >= size:
                raise QuetzalError(
                    "save file's memory does not fit this story "
                    "(more dynamic memory than the story has)"
                )
            out[addr] ^= b
            addr += 1
    if addr > size:
        raise QuetzalError(
            "save file's memory does not fit this story "
            "(more dynamic memory than the story has)"
        )
    return bytes(out)


# -- the save itself -----------------------------------------------------------


def write(mem, frames, pc: int) -> bytes:
    """The complete IFZS file for the given machine state. pc is the byte
    address of the save instruction's store byte (the resume convention).
    frames are objects with return_pc, store (None = discard), locals,
    argc, and stack; the base pseudo-frame comes first and is written as
    the spec's dummy frame."""
    initial = mem.initial
    ifhd = (
        initial[0x02:0x04]      # release
        + initial[0x12:0x18]    # serial
        + initial[0x1C:0x1E]    # checksum
        + pc.to_bytes(3, "big")
    )
    cmem = compress(bytes(mem.mem[:mem.static_base]), initial)
    stks = bytearray()
    for i, f in enumerate(frames):
        if i == 0:
            # The dummy frame: all fields zero except its own stack.
            stks += bytes(6)
        else:
            flags = len(f.locals) | (0x10 if f.store is None else 0)
            stks += f.return_pc.to_bytes(3, "big")
            stks += bytes((flags, f.store or 0, (1 << f.argc) - 1))
        stks += len(f.stack).to_bytes(2, "big")
        for v in f.locals:
            stks += v.to_bytes(2, "big")
        for v in f.stack:
            stks += v.to_bytes(2, "big")
    body = (
        b"IFZS"
        + _chunk(b"IFhd", ifhd)
        + _chunk(b"CMem", cmem)
        + _chunk(b"Stks", bytes(stks))
    )
    return b"FORM" + len(body).to_bytes(4, "big") + body


def read(data: bytes, mem) -> tuple:
    """Parse a save and check it belongs to this story. Returns
    (dynamic_memory, frames, pc) where frames is a list of plain tuples
    (return_pc, store_or_None, locals, argc, stack), dummy frame first;
    the VM rebuilds its own Frame objects from them. Raises QuetzalError
    for anything unusable, with the reason."""
    if len(data) < 12 or data[:4] != b"FORM" or data[8:12] != b"IFZS":
        raise QuetzalError("not a Quetzal save file")
    length = int.from_bytes(data[4:8], "big")
    if length + 8 > len(data):
        raise QuetzalError("save file is truncated")
    ifhd = cmem = umem = stks = None
    for tag, payload in _chunks(data[12:8 + length]):
        if tag == b"IFhd":
            ifhd = payload
        elif tag == b"CMem":
            cmem = payload
        elif tag == b"UMem":
            umem = payload
        elif tag == b"Stks":
            stks = payload
        # Anything else (IntD, ANNO, AUTH...) is legitimately skipped.
    if ifhd is None or stks is None or (cmem is None and umem is None):
        raise QuetzalError("save file is missing a required chunk")
    if len(ifhd) < 13:
        raise QuetzalError("save file's story identification is malformed")

    initial = mem.initial
    if ifhd[0:2] != initial[0x02:0x04] or ifhd[2:8] != initial[0x12:0x18] \
            or ifhd[8:10] != initial[0x1C:0x1E]:
        raise QuetzalError("this save belongs to a different story")
    pc = int.from_bytes(ifhd[10:13], "big")

    if umem is not None and cmem is None:
        if len(umem) != mem.static_base:
            raise QuetzalError(
                "save file's memory does not fit this story "
                f"({len(umem)} bytes of dynamic memory, "
                f"story has {mem.static_base})"
            )
        dynamic = bytes(umem)
    else:
        dynamic = decompress(cmem, initial, mem.static_base)

    frames = []
    pos = 0
    while pos < len(stks):
        if pos + 8 > len(stks):
            raise QuetzalError("save file's stack is truncated")
        return_pc = int.from_bytes(stks[pos:pos + 3], "big")
        flags, store, argmask = stks[pos + 3], stks[pos + 4], stks[pos + 5]
        depth = int.from_bytes(stks[pos + 6:pos + 8], "big")
        nlocals = flags & 0x0F
        pos += 8
        need = 2 * (nlocals + depth)
        if pos + need > len(stks):
            raise QuetzalError("save file's stack is truncated")
        locals_ = [int.from_bytes(stks[pos + 2 * i:pos + 2 * i + 2], "big")
                   for i in range(nlocals)]
        pos += 2 * nlocals
        stack = [int.from_bytes(stks[pos + 2 * i:pos + 2 * i + 2], "big")
                 for i in range(depth)]
        pos += 2 * depth
        if not frames:
            # The dummy frame stands for the entry stream: no return, no
            # store. Its stack words are real and kept.
            frames.append((0, None, [], 0, stack))
        else:
            frames.append((
                return_pc,
                None if flags & 0x10 else store,
                locals_,
                bin(argmask).count("1"),
                stack,
            ))
    if not frames:
        raise QuetzalError("save file has no stack frames")
    return dynamic, frames, pc
