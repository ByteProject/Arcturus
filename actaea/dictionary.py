# dictionary.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Dictionary parsing, lookup, and the buffer tokeniser (M5; Standard 1.1
section 13).

A dictionary begins with its word-separator list (a count byte, then that
many ZSCII codes), the entry length, and the entry count, then the entries:
6 bytes of encoded text (9 z-characters, v4+) followed by whatever data the
game keeps per word. A negative count marks an unsorted user dictionary
(tokenise's optional third operand); the header dictionary is sorted, but a
linear scan is correct for both and Actaea favors the simple truth here.

The tokeniser fills a v5 parse buffer from a v5 text buffer: text holds max
at byte 0, typed length at byte 1, characters from byte 2; parse holds max
words at byte 0, found words at byte 1, then per word the dictionary entry
address (a word), the letter count, and the position of the word's first
character within the text buffer. Spaces split and vanish; the dictionary's
separators split AND stand as words of their own."""

from .memory import to_signed


class Dictionary:
    def __init__(self, mem, addr: int, text_engine):
        self.mem = mem
        self.text = text_engine
        n = mem.byte(addr)
        self.separators = {mem.byte(addr + 1 + i) for i in range(n)}
        self.entry_len = mem.byte(addr + 1 + n)
        self.count = to_signed(mem.word(addr + 2 + n))
        self.entries = addr + 4 + n

    def lookup(self, encoded: bytes) -> int:
        """The address of the entry whose text matches, or 0. Sorted or not,
        the scan is linear; dictionaries are small and this cannot be wrong."""
        for i in range(abs(self.count)):
            addr = self.entries + i * self.entry_len
            if bytes(self.mem.mem[addr:addr + 6]) == encoded:
                return addr
        return 0

    def lookup_word(self, word: str) -> int:
        return self.lookup(self.text.encode_word(word))


def tokenise(mem, text_addr: int, parse_addr: int, dictionary: Dictionary,
             skip_unknown: bool = False) -> None:
    """Split the text buffer into words against the dictionary's separators
    and write the parse buffer. With skip_unknown (tokenise's flag operand),
    a word the dictionary lacks leaves its parse slot untouched instead of
    writing 0, so a game can merge two dictionaries in two passes (S 15)."""
    length = mem.byte(text_addr + 1)
    chars = [mem.byte(text_addr + 2 + i) for i in range(length)]

    # Split: (position-in-buffer, [codes]) per word. Positions count from
    # the buffer start, so the first typed character sits at 2.
    words = []
    current: list = []
    start = 0
    for i, c in enumerate(chars):
        if c == 32:  # space: splits, is nothing
            if current:
                words.append((start + 2, current))
                current = []
        elif c in dictionary.separators:  # splits AND is a word itself
            if current:
                words.append((start + 2, current))
                current = []
            words.append((i + 2, [c]))
        else:
            if not current:
                start = i
            current.append(c)
    if current:
        words.append((start + 2, current))

    max_words = mem.byte(parse_addr)
    n = min(len(words), max_words)
    mem.set_byte(parse_addr + 1, n)
    for i in range(n):
        pos, codes = words[i]
        token = "".join(self_char(dictionary, c) for c in codes)
        addr = dictionary.lookup_word(token)
        slot = parse_addr + 2 + 4 * i
        if addr == 0 and skip_unknown:
            # Leave the address word alone; length and position still tell
            # the game where the unmatched word sits.
            mem.set_byte(slot + 2, len(codes))
            mem.set_byte(slot + 3, pos)
            continue
        mem.set_word(slot, addr)
        mem.set_byte(slot + 2, len(codes))
        mem.set_byte(slot + 3, pos)


def self_char(dictionary: Dictionary, code: int) -> str:
    """A typed ZSCII code as the character the encoder should see."""
    return dictionary.text.zscii_to_unicode(code)
