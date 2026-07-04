# zasm.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The test-side Z-machine assembler and story builder shared by the VM-layer
test files. Deliberately independent of both actaea.decode and the Arcturus
compiler's assembler, so instruction encodings are always cross-checked by a
second implementation.

Image layout: header, the globals table at 0x40, an object-table area at
0x220 (the 63 defaults words, entries, property tables), code from 0x520
(the entry stream in a fixed 64-byte slot so routine addresses never depend
on entry length, routines 4-aligned after it). Length and checksum are
filled honestly so verify has something to verify."""

from actaea.io import CaptureIO
from actaea.loader import load
from actaea.vm import VM

LARGE, SMALL, VAR = 0, 1, 2


def L(v):
    return (LARGE, v)


def S(v):
    return (SMALL, v)


def V(n):
    return (VAR, n)


def _types_byte(ops):
    b = 0
    for i in range(4):
        t = ops[i][0] if i < len(ops) else 3  # 3 = omitted
        b |= t << (6 - 2 * i)
    return b


def _operand_bytes(ops):
    out = bytearray()
    for t, v in ops:
        if t == LARGE:
            out += bytes([(v >> 8) & 0xFF, v & 0xFF])
        else:
            out.append(v & 0xFF)
    return bytes(out)


def branch(on_true, offset):
    """A branch in the two-byte form (offset 0/1 = rfalse/rtrue, else the
    signed 14-bit jump the decoder computes against)."""
    raw = offset & 0x3FFF
    return bytes([(0x80 if on_true else 0) | (raw >> 8), raw & 0xFF])


def vop(opnum, *ops, store=None, count_2op=False):
    """A variable-form instruction (VAR count unless count_2op)."""
    first = (0xC0 if count_2op else 0xE0) | opnum
    out = bytes([first, _types_byte(ops)]) + _operand_bytes(ops)
    if store is not None:
        out += bytes([store])
    return out


def vop2(opnum, *ops, store=None):
    """call_vs2/call_vn2: the double-type-byte encoding, up to 8 operands."""
    b1 = 0
    b2 = 0
    for i in range(4):
        t = ops[i][0] if i < len(ops) else 3
        b1 |= t << (6 - 2 * i)
    for i in range(4):
        t = ops[i + 4][0] if i + 4 < len(ops) else 3
        b2 |= t << (6 - 2 * i)
    out = bytes([0xE0 | opnum, b1, b2]) + _operand_bytes(ops)
    if store is not None:
        out += bytes([store])
    return out


def long2(opnum, a, b, store=None):
    """Long-form 2OP: operands are small constants or variables only."""
    first = opnum
    if a[0] == VAR:
        first |= 0x40
    if b[0] == VAR:
        first |= 0x20
    out = bytes([first, a[1] & 0xFF, b[1] & 0xFF])
    if store is not None:
        out += bytes([store])
    return out


def short1(opnum, op, store=None):
    out = bytes([0x80 | (op[0] << 4) | opnum]) + _operand_bytes([op])
    if store is not None:
        out += bytes([store])
    return out


def short0(opnum):
    return bytes([0xB0 | opnum])


def ext(opnum, *ops, store=None):
    out = bytes([0xBE, opnum, _types_byte(ops)]) + _operand_bytes(ops)
    if store is not None:
        out += bytes([store])
    return out


# Named shorthands for readability in the tests.
QUIT = short0(0x0A)
RTRUE = short0(0x00)
RFALSE = short0(0x01)
NEWLINE = short0(0x0B)
SP = 0  # variable number 0: the stack


def print_num(op):
    return vop(0x06, op)


def routine(nlocals, *code):
    return bytes([nlocals]) + b"".join(code)


# -- the story builder ---------------------------------------------------------

GLOBALS = 0x40
OBJ = 0x220        # the object-table area: 63 defaults words, entries, props
CODE = 0x520       # 4-aligned; everything below stays dynamic (writable)

ENTRY_AREA = 64    # the entry stream's fixed slot, so routine addresses never
                   # depend on the entry's length (several tests build twice:
                   # once with a placeholder entry to learn the packed layout,
                   # then for real)


def objtable(objs, defaults=()):
    """The object-table area: `objs` is a list of dicts, object i+1 from
    objs[i], each with optional keys attrs (an iterable of attribute numbers),
    parent/sibling/child (object numbers), and props ({number: data bytes},
    laid out in the descending order the format requires; a data length above
    2 takes the two-byte size form). Returns the area blob, absolute-address
    correct for placement at OBJ."""
    blob = bytearray(63 * 2)
    for i, d in enumerate(defaults):
        blob[2 * i] = (d >> 8) & 0xFF
        blob[2 * i + 1] = d & 0xFF
    entries = len(blob)
    blob += bytes(14 * len(objs))
    for n, spec in enumerate(objs, start=1):
        e = entries + (n - 1) * 14
        attrs = bytearray(6)
        for a in spec.get("attrs", ()):
            attrs[a // 8] |= 0x80 >> (a % 8)
        blob[e:e + 6] = attrs
        for off, key in ((6, "parent"), (8, "sibling"), (10, "child")):
            v = spec.get(key, 0)
            blob[e + off] = (v >> 8) & 0xFF
            blob[e + off + 1] = v & 0xFF
        # The property table: an empty short name, properties descending.
        taddr = OBJ + len(blob)
        blob[e + 12] = (taddr >> 8) & 0xFF
        blob[e + 13] = taddr & 0xFF
        blob.append(0)  # short-name length 0 (name decoding is M5)
        for pnum in sorted(spec.get("props", {}), reverse=True):
            data = spec["props"][pnum]
            if len(data) > 2:
                # Both size bytes carry bit 7 in the two-byte form; the
                # second one's is what get_prop_len reads back (S 12.4.2.1.1).
                blob += bytes([0x80 | pnum, 0x80 | (len(data) & 0x3F)])
            elif len(data) == 2:
                blob += bytes([0x40 | pnum])
            else:
                blob += bytes([pnum])
            blob += data
        blob.append(0)  # end of the property list
    assert OBJ + len(blob) <= CODE, "object area outgrew its slot"
    return bytes(blob)


def build(entry: bytes, *routines: bytes, objects: bytes = b""):
    """A runnable story: returns (vm, io, packed) with packed[i] the packed
    address of routines[i]."""
    assert len(entry) <= ENTRY_AREA, "entry stream outgrew its fixed slot"
    body = bytearray(entry) + bytes(ENTRY_AREA - len(entry))
    packed = []
    for r in routines:
        while (CODE + len(body)) % 4:
            body.append(0)
        packed.append((CODE + len(body)) // 4)
        body += r
    img = bytearray(CODE) + body
    img[OBJ:OBJ + len(objects)] = objects
    while len(img) % 4:
        img.append(0)
    img[0x00] = 5
    img[0x04:0x06] = CODE.to_bytes(2, "big")   # high memory base
    img[0x06:0x08] = CODE.to_bytes(2, "big")   # initial PC: the entry stream
    img[0x0A:0x0C] = OBJ.to_bytes(2, "big")    # the object table
    img[0x0C:0x0E] = GLOBALS.to_bytes(2, "big")
    img[0x0E:0x10] = CODE.to_bytes(2, "big")   # static base: all tables writable
    img[0x1A:0x1C] = (len(img) // 4).to_bytes(2, "big")
    img[0x1C:0x1E] = (sum(img[0x40:]) & 0xFFFF).to_bytes(2, "big")
    io = CaptureIO()
    return VM(load(bytes(img)), io), io, packed


def run(entry: bytes, *routines: bytes, objects: bytes = b"") -> str:
    vm, io, _ = build(entry, *routines, objects=objects)
    vm.run(max_steps=10000)
    return io.text
