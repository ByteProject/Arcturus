# test_text.py
# part of Actaea, the Arcturus project's reference Z-machine interpreter.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Actaea M5: the text engine, the dictionary, and the print family. The
strongest cross-check in the project: the Arcturus COMPILER encodes the
strings and Actaea decodes them back, two independent implementations of
Standard 1.1 section 3 meeting in the middle. Then the milestone's real
done-test: a whole Arcturus game boots and talks."""

import pytest

from actaea.text import TextError
from zasm import L, OBJ, QUIT, S, SP, V, build, objtable, short1, vop

from arcturus import zstring


def z(text: str) -> bytes:
    """A compiler-encoded Z-string with no abbreviations (other tests in the
    suite may leave a baked set active in the module state; force none)."""
    return zstring.encode(text, abbrevs=[])


def _engine(*blobs):
    vm, io, packed = build(QUIT, *blobs)
    return vm, io, [p * 4 for p in packed]


# -- decode, against the compiler's encoder ---------------------------------------

ROUND_TRIPS = [
    "Hello, World!",
    "the quick brown fox jumps over 12 lazy dogs.",
    'say "hi" (or don\'t) -- #3/4_5:ok?',
    "line one\nline two",
    "MiXeD CaSe AbCdEfG",
    # The accent path, Stefan's hard rule made executable
    # ([[never-strip-accents]]): Spanish and German through ZSCII 155..223.
    "Mañana, señor Müller está aquí. ¡Sí!",
    "Ärger? Öl? Übermut? ßäöü",
]


@pytest.mark.parametrize("text", ROUND_TRIPS)
def test_decode_what_the_compiler_encodes(text):
    vm, _, addrs = _engine(z(text))
    decoded, end = vm.text.decode(addrs[0])
    assert decoded == text
    assert end == addrs[0] + len(z(text))


def test_zscii_boundaries_are_loud():
    vm, _, _ = _engine()
    assert vm.text.zscii_to_unicode(0) == ""    # null prints nothing
    assert vm.text.zscii_to_unicode(13) == "\n"
    # The default table ends at 223; past it is a named fault.
    with pytest.raises(TextError):
        vm.text.zscii_to_unicode(240)
    with pytest.raises(TextError):
        vm.text.zscii_to_unicode(7)  # a control code that is not output


def test_encode_word_matches_the_compilers_dictionary_form():
    vm, _, _ = _engine()
    for word in ("take", "lantern", "x", "espejo", "señor", "hyacinth"):
        assert vm.text.encode_word(word) == zstring.encode_dict_word(word), word
    # Truncation: only the first nine z-characters survive, so two long
    # words that agree that far encode identically.
    assert vm.text.encode_word("candlestick") == vm.text.encode_word("candlesticks")


# -- the dictionary and the tokeniser ------------------------------------------------

def _dict_story():
    vm, io, addrs = _engine()  # engine only, for encode_word
    words = [b"take", b"lamp", b"look"]
    blob = bytearray([2, ord("."), ord(","), 7])  # 2 separators; entries 7 long
    blob += (3).to_bytes(2, "big")
    for w in words:
        blob += vm.text.encode_word(w.decode()) + b"\x00"
    vm, io, addrs = _engine(bytes(blob))
    from actaea.dictionary import Dictionary

    return vm, Dictionary(vm.mem, addrs[0], vm.text)


def test_dictionary_lookup():
    vm, d = _dict_story()
    assert d.separators == {ord("."), ord(",")}
    assert d.entry_len == 7 and d.count == 3
    assert d.lookup_word("lamp") != 0
    assert d.lookup_word("take") != 0
    assert d.lookup_word("grue") == 0
    # Dictionary words compare through the SAME truncation as typing.
    assert d.lookup_word("lampxyz") == 0


def test_tokenise_splits_and_finds():
    from actaea.dictionary import tokenise

    vm, d = _dict_story()
    text_addr, parse_addr = OBJ + 0x100, OBJ + 0x140  # scratch, dynamic
    line = "take lamp, frotz"
    vm.mem.set_byte(text_addr, 60)
    vm.mem.set_byte(text_addr + 1, len(line))
    for i, ch in enumerate(line):
        vm.mem.set_byte(text_addr + 2 + i, ord(ch))
    vm.mem.set_byte(parse_addr, 10)
    tokenise(vm.mem, text_addr, parse_addr, d)
    m = vm.mem
    assert m.byte(parse_addr + 1) == 4  # take, lamp, the comma, frotz
    def slot(i):
        a = parse_addr + 2 + 4 * i
        return m.word(a), m.byte(a + 2), m.byte(a + 3)
    assert slot(0) == (d.lookup_word("take"), 4, 2)
    assert slot(1) == (d.lookup_word("lamp"), 4, 7)
    assert slot(2) == (0, 1, 11)   # "," splits and stands, but is no entry
    assert slot(3) == (0, 5, 13)   # frotz: unknown
    # The skip_unknown flag leaves unknown slots' addresses untouched.
    m.set_word(parse_addr + 2 + 4 * 3, 0xDEAD)
    tokenise(vm.mem, text_addr, parse_addr, d, skip_unknown=True)
    assert slot(3) == (0xDEAD, 5, 13)


# -- the print family through the VM ---------------------------------------------------

def test_print_inline_and_paddr():
    string = z("Deep in the dark.")
    vm, io, packed = build(
        bytes([0xB2]) + z("Hello from the machine! ")   # print (inline)
        + short1(0x0D, L(0))                            # print_paddr (patched)
        + QUIT,
        string,
    )
    entry = (
        bytes([0xB2]) + z("Hello from the machine! ")
        + short1(0x0D, L(packed[0]))
        + QUIT
    )
    vm, io, _ = build(entry, string)
    vm.run(max_steps=50)
    assert io.text == "Hello from the machine! Deep in the dark."


def test_print_obj_speaks_the_short_name():
    world = objtable([{"name": z("jeweled orrery")}])
    vm, io, _ = build(short1(0x0A, S(1)) + QUIT, objects=world)
    vm.run(max_steps=20)
    assert io.text == "jeweled orrery"


def test_print_ret_prints_and_returns_true():
    r = bytes([1]) + bytes([0xB3]) + z("done")   # routine: print_ret "done"
    vm, io, packed = build(QUIT, r)
    entry = (
        vop(0x00, L(packed[0]), store=SP)
        + vop(0x06, V(SP))                       # print_num of the returned 1
        + QUIT
    )
    vm, io, _ = build(entry, r)
    vm.run(max_steps=50)
    assert io.text == "done\n1"


def test_encode_text_opcode_round_trips():
    vm, io, _ = build(
        vop(0x1C, L(OBJ + 0x100), S(4), S(0), L(OBJ + 0x120))  # encode_text
        + QUIT,
    )
    for i, ch in enumerate("lamp"):
        vm.mem.set_byte(OBJ + 0x100 + i, ord(ch))
    vm.run(max_steps=20)
    got = bytes(vm.mem.mem[OBJ + 0x120:OBJ + 0x126])
    assert got == zstring.encode_dict_word("lamp")


# -- the milestone's showpiece: a real game boots and talks -----------------------------

GAME = (
    'game\n    title "Starlit Probe"\n    start deck\n'
    'room deck\n    name "Observation Deck"\n'
    '    desc "Stars wheel past the crystal dome. A brass telescope waits."\n'
    'thing telescope in deck\n    name "brass telescope"\n    words brass, telescope\n'
    "    fixed\n"
)


def test_an_arcturus_game_boots_and_plays():
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM

    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze

    story = load(generate(analyze(cosmos.combined_program(parse(GAME)))))
    io = CaptureIO(script=["examine telescope", "take telescope", "quit", "y"])
    vm = VM(story, io)
    # Since M6 the machine reads input too: a whole Arcturus game plays on
    # the real Cosmos runtime, from the banner through commands to a clean
    # quit. The compiler, the library, and the interpreter, end to end.
    vm.run(max_steps=2_000_000)
    assert vm.halted
    out = io.text
    assert "Starlit Probe" in out
    assert "Observation Deck" in out
    assert "Stars wheel past the crystal dome" in out
    assert "Cosmos" in out                       # the library banner line
    assert "Nothing about the brass telescope" in out  # examine's default
    assert "stays exactly where it is" in out    # the take refused (fixed)
    assert "We'll leave it there." in out        # the quit confirmation
