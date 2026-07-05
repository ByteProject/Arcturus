# objects.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The v4+ object table (M4; Standard 1.1 sections 12.1 to 12.4).

The table sits at the header's object address: first the property defaults,
63 words, one per property number; then the objects, 14 bytes each, numbered
from 1. An entry is 48 attribute bits (6 bytes), the parent, sibling, and
child object numbers (a word each), and the address of the object's property
table.

A property table begins with the short name (a length byte counting words of
encoded text, then that text), followed by properties in DESCENDING number
order, each with one or two size bytes:
- one byte, bit 7 clear: the property number in bits 0..5, and bit 6 gives
  the data length, clear = 1 byte, set = 2.
- two bytes, bit 7 set: the number in the first byte's bits 0..5; the second
  byte's bits 0..5 give the length, where 0 means 64 (S 12.4.2.1.1).
A zero size byte ends the list.

Object number 0 is "nothing": no entry exists for it, and an opcode touching
object 0's entry is a fault here, named and located, rather than a silent
read of bytes that belong to no object (the strictness doctrine; permissive
interpreters paper over exactly this and the bug surfaces three rooms
later)."""

from .errors import ActaeaError

_DEFAULTS_WORDS = 63
_ENTRY = 14           # v4+: 6 attribute bytes + 3 words + the property pointer
_ATTRS = 48


class ObjectError(ActaeaError):
    """An object or property operation no well-formed story performs."""


class ObjectTable:
    """Bounds-checked access to objects, attributes, the tree words, and
    property tables. All writes go through the Memory layer, so its dynamic
    write barrier stands here too."""

    def __init__(self, mem, objects_addr: int):
        self.mem = mem
        self.base = objects_addr
        self.entries = objects_addr + _DEFAULTS_WORDS * 2

    # -- entries and attributes ------------------------------------------------

    def _entry(self, obj: int) -> int:
        if obj < 1 or obj > 0xFFFF:
            raise ObjectError(f"object {obj} does not exist (0 is 'nothing')")
        return self.entries + (obj - 1) * _ENTRY

    def _attr_site(self, obj: int, attr: int):
        if not 0 <= attr < _ATTRS:
            raise ObjectError(f"attribute {attr} out of 0..47 on object {obj}")
        return self._entry(obj) + attr // 8, 0x80 >> (attr % 8)

    def test_attr(self, obj: int, attr: int) -> bool:
        addr, bit = self._attr_site(obj, attr)
        return bool(self.mem.byte(addr) & bit)

    def set_attr(self, obj: int, attr: int) -> None:
        addr, bit = self._attr_site(obj, attr)
        self.mem.set_byte(addr, self.mem.byte(addr) | bit)

    def clear_attr(self, obj: int, attr: int) -> None:
        addr, bit = self._attr_site(obj, attr)
        self.mem.set_byte(addr, self.mem.byte(addr) & ~bit)

    # -- the tree ------------------------------------------------------------------
    # Asking about object 0 answers "nothing" rather than faulting: real
    # games do it (Jigsaw calls get_child(0) at boot), the convention among
    # interpreters is that nothing's relatives are nothing, and only the
    # MUTATING operations on 0 stay hard errors.

    def parent(self, obj: int) -> int:
        return 0 if obj == 0 else self.mem.word(self._entry(obj) + 6)

    def sibling(self, obj: int) -> int:
        return 0 if obj == 0 else self.mem.word(self._entry(obj) + 8)

    def child(self, obj: int) -> int:
        return 0 if obj == 0 else self.mem.word(self._entry(obj) + 10)

    def _set_parent(self, obj: int, to: int) -> None:
        self.mem.set_word(self._entry(obj) + 6, to)

    def _set_sibling(self, obj: int, to: int) -> None:
        self.mem.set_word(self._entry(obj) + 8, to)

    def _set_child(self, obj: int, to: int) -> None:
        self.mem.set_word(self._entry(obj) + 10, to)

    def remove(self, obj: int) -> None:
        """Detach obj from its parent (children ride along, S 15 remove_obj).
        The old parent's child chain is stitched around it."""
        parent = self.parent(obj)
        if parent == 0:
            return
        first = self.child(parent)
        if first == obj:
            self._set_child(parent, self.sibling(obj))
        else:
            prev = first
            while prev != 0 and self.sibling(prev) != obj:
                prev = self.sibling(prev)
            if prev == 0:
                raise ObjectError(
                    f"object tree corrupt: {obj} claims parent {parent} "
                    f"but is not among its children"
                )
            self._set_sibling(prev, self.sibling(obj))
        self._set_parent(obj, 0)
        self._set_sibling(obj, 0)

    def insert(self, obj: int, dest: int) -> None:
        """Make obj the FIRST child of dest (insert_obj), detaching it from
        wherever it was."""
        if obj == dest:
            raise ObjectError(f"insert_obj of {obj} into itself")
        self.remove(obj)
        self._set_sibling(obj, self.child(dest))
        self._set_child(dest, obj)
        self._set_parent(obj, dest)

    # -- property tables ---------------------------------------------------------

    def prop_table(self, obj: int) -> int:
        return self.mem.word(self._entry(obj) + 12)

    def name_addr(self, obj: int):
        """The encoded short name: (address, length-in-bytes). Decoding it is
        text.py's job (M5); print_obj waits there."""
        t = self.prop_table(obj)
        return t + 1, self.mem.byte(t) * 2

    def _first_prop(self, obj: int) -> int:
        t = self.prop_table(obj)
        return t + 1 + self.mem.byte(t) * 2  # skip the short name

    def _prop_info(self, addr: int):
        """At a size byte: (number, data_addr, data_len), or None at the
        terminating zero."""
        b = self.mem.byte(addr)
        if b == 0:
            return None
        number = b & 0x3F
        if b & 0x80:
            length = self.mem.byte(addr + 1) & 0x3F
            if length == 0:
                length = 64  # S 12.4.2.1.1
            return number, addr + 2, length
        return number, addr + 1, (2 if b & 0x40 else 1)

    def _find_prop(self, obj: int, prop: int):
        addr = self._first_prop(obj)
        while True:
            info = self._prop_info(addr)
            if info is None:
                return None
            number, data, length = info
            if number == prop:
                return info
            if number < prop:
                return None  # descending order: passed where it would sit
            addr = data + length

    def get_prop(self, obj: int, prop: int) -> int:
        """The property value: a byte or a word of the object's own table,
        or the defaults-table word when absent. Reading a longer property
        this way is illegal (S 15 get_prop)."""
        if not 1 <= prop <= _DEFAULTS_WORDS:
            raise ObjectError(f"property {prop} out of 1..63 on object {obj}")
        info = self._find_prop(obj, prop)
        if info is None:
            return self.mem.word(self.base + (prop - 1) * 2)
        _, data, length = info
        if length == 1:
            return self.mem.byte(data)
        if length == 2:
            return self.mem.word(data)
        raise ObjectError(
            f"get_prop of property {prop} on object {obj}: "
            f"{length} bytes long; only 1 and 2 are legal reads"
        )

    def put_prop(self, obj: int, prop: int, value: int) -> None:
        info = self._find_prop(obj, prop)
        if info is None:
            raise ObjectError(
                f"put_prop: object {obj} has no property {prop}"
            )
        _, data, length = info
        if length == 1:
            self.mem.set_byte(data, value & 0xFF)
        elif length == 2:
            self.mem.set_word(data, value)
        else:
            raise ObjectError(
                f"put_prop of property {prop} on object {obj}: "
                f"{length} bytes long; only 1 and 2 are legal writes"
            )

    def get_prop_addr(self, obj: int, prop: int) -> int:
        info = self._find_prop(obj, prop)
        return 0 if info is None else info[1]

    def get_prop_len(self, data_addr: int) -> int:
        """From a property DATA address back to its length, reading the size
        byte just before it; get_prop_len(0) is 0 by Standard 1.1."""
        if data_addr == 0:
            return 0
        b = self.mem.byte(data_addr - 1)
        if b & 0x80:
            length = b & 0x3F
            return length if length else 64
        return 2 if b & 0x40 else 1

    def get_next_prop(self, obj: int, prop: int) -> int:
        """0 asks for the first (highest-numbered) property; otherwise the
        one after prop in the table; 0 past the last. Asking after a property
        the object lacks is a fault (S 15 get_next_prop)."""
        if prop == 0:
            info = self._prop_info(self._first_prop(obj))
            return 0 if info is None else info[0]
        info = self._find_prop(obj, prop)
        if info is None:
            raise ObjectError(
                f"get_next_prop after property {prop}, "
                f"which object {obj} does not have"
            )
        _, data, length = info
        nxt = self._prop_info(data + length)
        return 0 if nxt is None else nxt[0]
