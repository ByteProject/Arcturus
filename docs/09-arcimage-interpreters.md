# arc_image for interpreter authors: the contract, the format, the loaders

This is the implementer's book for arc_image, Arcturus's optional picture
band. It is written to be sufficient ALONE: an interpreter author (or a
fresh working session inside an interpreter's own repository) implements a
target from this document, the reference probe source, and the test assets,
without ever opening the Arcturus repository. The design record behind it is
docs/08-arcimage-retro.md; nothing there is required reading.

The handover package for a target is:

- this document (part A, part B, and the target's chapter in part C);
- `arc_image/probes/<target>/` : a working reference loader for the machine,
  commented against this spec, plus its build command;
- the standard test assets, `90.<TAG>` (mode 9) and `100.<TAG>` (mode 12),
  the same picture in both band shapes;
- the `arcimg` standalone tool: `arcimg render X.arc -o X.png` produces the
  ground-truth PNG any correct loader must match on screen, and `arcimg
  convert` produces fresh assets from band-shaped master PNGs.

## Part A: the interpreter contract

arc_image adds a PICTURE BAND to a conformant Z-machine version 5/8
interpreter: a picture across the top of the screen, the text area (status
line included) below it. A story that uses pictures remains a conformant
story file; an interpreter that knows nothing of arc_image plays it
unchanged, text-only. The contract:

1. CAPABILITY. If and only if the interpreter can show pictures, it sets
   Flags 1 bit 1 (the Standard's "picture displaying available" bit) at
   boot, and re-stamps it after restart and restore (the Z-machine rewrites
   the header on both). A text-only build leaves the bit alone. The story's
   library reads this bit at run time and never issues a draw when it is
   clear, so the draw opcode is structurally unreachable on unaware
   interpreters; and even if it were reached, unknown EXT opcodes are to be
   skipped (Standard 1.1 section 14.2).

2. THE OPCODE. EXT:0x80 (extended opcode 128, in the range the Standard
   reserves for private use), named `draw_image`, two operands, no store, no
   branch:

       draw_image image-id mode

   - `image-id` is the resource slot: the picture to show is the asset
     numbered image-id for this platform (the file naming is per target,
     part C). id 0 means CLEAR the band.
   - `mode` is 9 or 12 and is AUTHORITATIVE for the band height: the band is
     mode x 8 pixel rows of the machine's own pixels (72 or 96 on every
     shipped target). The interpreter sizes its screen layout from the mode
     operand alone; it never measures a picture to lay out the screen. A
     game keeps one mode throughout in practice, but the interpreter honors
     the operand each call.
   - An unknown id, a missing or unreadable asset: IGNORE the call silently
     and play on. A picture is presentation, never game state.

3. THE BAND. The picture occupies the top of the screen; the interpreter's
   text screen model (including the Z-machine upper window and status line)
   lives strictly below it. Both modes must work. The band persists across
   turns until the next draw_image call replaces or clears it; the story's
   library already deduplicates (a re-LOOK issues no draw), so the
   interpreter needs no redraw caching of its own.

4. DEGRADATION. A text-only interpreter needs NOTHING: bit unset, opcode
   never reached, and a decoded-anyway EXT:0x80 skipped per the Standard.
   This is verified behavior, not aspiration: the same story file must play
   identically on a picture build and a text build, pictures aside.

5. Z-MACHINE COLOURS. The band's palette belongs to the ART and is never
   modified by the interpreter; a game's set_colour requests concern the
   TEXT AREA only, and each chapter says how its machine honors them
   (a reserved system range on DOS, a per-frame palette split on the
   Amiga, a declared-or-approximated choice on the ST). The general rule:
   pictures must never change what a game's colour requests mean, and
   colour requests must never repaint a picture.

## Part B: the .arc file format, version 1

One file per image id per target. Everything is BIG-ENDIAN. All offsets in
bytes.

HEADER, 16 bytes:

    +0   4  magic "ARCI" (0x41 0x52 0x43 0x49)
    +4   1  container version, 1
    +5   1  target id (part C: each chapter names its own)
    +6   1  mode, 9 or 12
    +7   1  section count
    +8   2  native width in pixels
    +10  2  native height in pixels (mode x 8)
    +12  2  image id (matches the filename; a cheap sanity check)
    +14  1  codec: 0 = RLE, 1 = ZX0, 2 = LZSA2 (fixed per target, part C)
    +15  1  provenance: 0 converted, 1 hand-authored. Loaders IGNORE it
            (it protects an author's native edits from reconversion)

SECTION TABLE, section-count entries of 6 bytes, at offset 16:

    +0   1  section type
    +1   1  flags (0 unless the target chapter defines bits)
    +2   2  uncompressed length
    +4   2  compressed length (includes the end sentinel)

The compressed section streams follow the table immediately, in table
order, each packed with the file's codec. A loader locates section N's
stream by summing the compressed lengths before it.

Section types: 1 bitmap, 2 screen matrix, 3 color matrix, 4 attributes,
5 palette, 6 line table, 7 registers. Which sections a target carries, and
their exact meaning, is per target (part C); two rules hold everywhere:

- Section payloads are in the machine's NATIVE memory order. The loader
  never reorders, shuffles, or converts anything; it unpacks bytes to where
  they live.
- Palette payloads are in the machine's NATIVE hardware encoding and are
  written to the hardware verbatim.

THE CODEC (header byte 14): 0 = RLE, 1 = ZX0, 2 = LZSA2. Every target
chapter in part C mandates exactly ONE codec, so a real interpreter
carries exactly one decoder; reading the codec byte and refusing
anything else is honest behavior. The assignment (both rulings
2026-07-08, the bake-off and the speed amendment in docs/08):

- ZX0 (Einar Saukas) for the 8-bit cell targets (C64, Spectrum +3, CPC,
  and the rest of the small-machine family). Best ratio of the field,
  and the smallest decompressors in the business: the canonical Z80
  decoder is about 70 bytes, the 6502 port about 130. These pictures
  share a floppy with the story; every byte counts.
- LZSA2 (Emmanuel Marty) for the 16-bit big-disk targets (Amiga, ST,
  DOS; later MSX2, Next, MEGA65). About 5% larger than ZX0 on the
  corpus, but it packs two orders of magnitude faster (the author's
  regeneration loop) and decompresses faster on 68000/8086. Those disks
  have room; a z5 story caps at 256K either way.

ZX0 IN ONE PARAGRAPH (the full executable specification is
zx0_decompress in arcimg, a verbatim port of the reference dzx0): the
stream interleaves single indicator bits, interlaced Elias gamma values,
and plain bytes. Three block kinds: LITERALS (gamma length, then that
many bytes), REPEAT (gamma length, copy from the last offset), and NEW
OFFSET (gamma-inverted MSB where 256 marks the end of the stream, an LSB
byte, then gamma length-minus-one whose FIRST bit rides bit 0 of that
LSB byte: the backtrack trick every decoder must honor). After literals
the next bit chooses repeat (0) or new offset (1); after any copy it
chooses literals (0) or new offset (1). offset = MSB*128 - (LSB >> 1);
decompression is a plain byte loop with one 2176-byte-max lookback into
its own output, no window buffer needed since sections decompress whole
into their destination.

THE RLE SCHEME (codec 0; control byte c):

    c = 0x00..0x7F   literal: copy the next c+1 bytes to the output
    c = 0x81..0xFF   run: repeat the next byte 257-c times (2..128)
    c = 0x80         end of section

The uncompressed length in the table is authoritative; the 0x80 sentinel
lets a streaming loader run without a counter. RLE reference decoders,
both about a dozen instructions:

x86 (16-bit, ds:si = stream, es:di = destination; from the R2 DOS probe,
kept as the codec-0 reference):

    unrle:  lodsb
            cmp  al, 80h
            je   .end
            jb   .lit
            mov  cl, al
            not  cl            ; 255 - c
            add  cl, 2         ; 257 - c
            xor  ch, ch
            lodsb
            rep  stosb
            jmp  unrle
    .lit:   mov  cl, al
            xor  ch, ch
            inc  cx
            rep  movsb
            jmp  unrle
    .end:   ret

68000 (a0 = stream, a1 = destination; from the R2 ST probe, kept as the
codec-0 reference). Mind the dbra
trap: it leaves $FFFF in the counter word, so clear the register EVERY
iteration before the byte load:

    unrle:
    .next:  moveq   #0,d0
            move.b  (a0)+,d0
            cmp.b   #$80,d0
            beq     .end
            blo     .lit
            neg.b   d0
            addq.b  #1,d0          ; 257 - c
            move.b  (a0)+,d1
            subq.w  #1,d0
    .run:   move.b  d1,(a1)+
            dbra    d0,.run
            bra     .next
    .lit:                          ; c+1 literals
    .cl:    move.b  (a0)+,(a1)+
            dbra    d0,.cl
            bra     .next
    .end:   rts

LZSA2 IN ONE PARAGRAPH (the full executable specification is
lzsa2_decompress in arcimg, ported from BlockFormat_LZSA2.md and
verified byte-identical against the reference tool over the corpus;
sections are RAW blocks, no stream header): a block is consecutive
commands, each a token byte XYZ|LL|MMM plus optional extensions. LL
(bits 4-3) literals follow the token: 0-2 direct, 3 means read a nibble
(0-14 adds to 3; 15 means read a byte: 0-237 adds to 18, 239 means a
little-endian 16-bit absolute count follows). Then the match offset by
XYZ (bits 7-5), stored NEGATIVE, unexpressed high bits set to 1: 00Z a
nibble is offset bits 1-4 and NOT Z is bit 0; 01Z a byte is bits 0-7
and NOT Z is bit 8; 10Z a nibble is bits 9-12, NOT Z is bit 8, a byte
is bits 0-7, then subtract 512; 110 two bytes big-to-little are a full
16-bit offset; 111 reuses the previous offset. Then the match length:
MMM+2 direct for 0-6, else read a nibble (0-14 adds to 9; 15 means read
a byte: 24 plus it, 233 means 16-bit absolute follows, and 232 is END
OF DATA). Nibbles come from a one-byte buffer, high half first. The EOD
test is the documented tri-state: add 24 to the byte and branch on
overflow. Reference assembly decompressors for Z80, 6502, and 8088 ship
in the lzsa repository under a permissive license; the probes carry
adapted 8086 and 68000 versions as they convert to the codec.

6502 and Z80 RLE decoders land with their waves' chapters if a target
chooses codec 0; for ZX0 use the published decompressors (the official
Z80 versions ship with ZX0 itself; 6502 and Z80 versions land in the
probes with wave 2's chapters).

## Part C: the targets

Each chapter gives the target id and tag, the video setup, the sections and
their native layouts, the loader recipe (against the probe source), the
asset naming, and the verified-on line. Chapters appear as their probes are
proven; the ledger of all fourteen planned targets is docs/08 section 2.

The probe directory linked in each chapter is PART OF THE HANDOVER, not an
appendix: it carries the working reference loader this chapter was written
from (source, embedded test assets, the built binary, and any build
script). Read the two side by side; where prose and probe could ever
disagree, the probe is the machine-checked half.

### C.1 DOS (target id 3, tag DOS, files `<id>.DOS`)

Verified: DOSBox-X, both modes, 2026-07-08; re-verified with the LZSA2
codec 2026-07-09.

Probe: [arc_image/probes/dos/](../arc_image/probes/dos/), source
`probe.asm` (the LZSA2 decompressor carried verbatim), the embedded test
assets 90.DOS and 100.DOS, and the built PROBE.COM. Build:
`nasm -f bin probe.asm -o PROBE.COM`.

VIDEO. VGA/MCGA mode 13h, 320x200, 256 colors, chunky (one byte per pixel,
linear at A000:0000). This is the ONLY DOS target: no EGA or CGA variants
exist or are planned (Infocom's own precedent: of their CGA/EGA/MCGA
picture sets, only MCGA is worth honoring). The interpreter draws its own
text in graphics mode below the band; an 8x8 font gives 40x25 cells, rows
9..24 (mode 9) or 12..24 (mode 12) for text.

PIXEL SHAPE. The art is square-pixel. Present it unscaled or
integer-scaled, WITHOUT CRT aspect correction: mode 13h pixels on a period
monitor are ~1.2x tall, and correcting for that (e.g. an emulator's
aspect=true) vertically stretches the art. Square presentation is the
contract (found the hard way: the probe's sun was an egg under DOSBox-X
aspect correction).

SECTIONS, in file order:

- bitmap (type 1): width x height bytes, row-major from the band's top-left.
  Decode straight to A000:0000; the band starts at screen row 0, so no
  offset math exists at all.
- palette (type 5): 768 bytes, 256 entries x 3 bytes R,G,B, each already a
  6-bit DAC value (0..63). Write verbatim: OUT 3C8h, 0 then 768 OUTs to
  3C9h. Never rescale. Palette entries 0..15 are a standard text palette
  (the interpreter may use them for its text colors); the art occupies 16
  upward.

Z-COLOURS: entries 0..15 are the standard PC palette and carry every
Z-machine colour; the interpreter's text uses them and never touches the
art's 16..255. Nothing to align, nothing to approximate.

LOADER RECIPE (the probe's shape): verify the magic; walk the section table
twice, palette pass first (so the picture never flashes in wrong colors),
bitmap pass second; each pass decodes its section to its destination.
The chapter's codec is LZSA2 (part B); do not write the decompressor
yourself: Emmanuel Marty's space-efficient 8088 routine from the lzsa
distribution (zlib license) is carried verbatim in the probe source and
drops in as published, with the probe's own calling convention (ds:si =
raw block, es:di = destination; trashes ax/bx/cx/dx/bp). Everything
around it stays under 120 instructions. Clear the band region before
drawing a new image only if the new image is narrower than the old (they
never are; a mode change between draws is the one case, and re-entering
mode 13h clears the screen anyway).

ASSETS. `<id>.DOS` beside the story file (8.3-safe by construction: the id
is decimal, at most five digits). The standard test pair: 90.DOS (mode 9),
100.DOS (mode 12).

MEMORY. Both the bitmap and the palette decode into VRAM and ports; the
loader needs no buffer beyond the 768-byte palette staging (and even that
can stream). Conventional-memory cost: effectively zero.

### C.2 Atari ST (target id 2, tag AST, files `<id>.AST`)

Verified: Hatari, both modes, 2026-07-08; re-verified with the LZSA2
codec 2026-07-09.

Probe: [arc_image/probes/ast/](../arc_image/probes/ast/), source
`probe.s` with the embedded test assets 90.AST and 100.AST. Build:
`vasmm68k_mot -Ftos -o PROBE.PRG probe.s`.

CODEC. LZSA2 (part B). The decompressor is the shared 68000 routine
[arc_image/probes/lzsa2_68k.s](../arc_image/probes/lzsa2_68k.s), written
from the part B spec (the lzsa distribution has no 68000 routine) and
proven byte-exact under vamos on real sections from both packers before
it reached an emulator; reuse it rather than writing your own. Register
convention: a0 = raw block, a1 = destination, trashes d0-d5/a2, register
only (no absolute addresses, so it rides position-independent code
unchanged). Its one constraint: match offsets apply as sign-extended
16-bit adds, correct because no .arc section exceeds 32K uncompressed.

Two 68000 lessons the probe paid for, so an implementer does not: an .arc
file can be ODD-length, so anything embedding or loading one to memory
must align it (an even boundary) before touching the header with word or
long reads, or the 68000 answers with an address error; and the
decoder's counter register must be cleared EVERY iteration (dbra leaves
$FFFF in the counter word; part B's listing has it right).

VIDEO. ST low resolution, 320x200, 16 colors from 512 (STF; 4096 on the
STE), 4 bitplanes, the fixed hardware interleave: per 16-pixel group, 4
consecutive words hold planes 0..3; 160 bytes per row; the screen is one
32000-byte block at Physbase(). Text below the band with the 8x8 system
font: 40x25 cells, rows 9..24 or 12..24.

SECTIONS, in file order:

- bitmap (type 1): height x 160 bytes, the native word-interleaved rows,
  top-left first. Decode straight to Physbase(); the band is the top of the
  screen, offset zero.
- palette (type 5): 16 words, STF hardware format (0x0RGB, 3 bits per gun).
  Hand the whole block to Setpalette() (XBIOS 6) or write to 0xFF8240
  verbatim. An STE build may also honor a second palette section with
  flags bit 0 set (4-bit guns, STE-shuffled); none is emitted today.

THE TEXT COLORS. The palette is luminance-sorted by the converter: entry 0
is the art's darkest color and entry 15 its lightest, and the converter
guarantees entry 15 is readable ink (it trades one art slot for white only
when the art has no light color). The interpreter prints its text in
ink 15 on paper 0 and never needs palette entries of its own.

Z-COLOURS: the STF has one palette per frame and no reliable raster split,
so while a picture is displayed an interpreter chooses one of two
conformant answers: declare colours unavailable (Flags 1 bit 0 is the
interpreter's own declaration; text runs ink 15 on paper 0), or honor
set_colour approximately by mapping each requested colour to its nearest
art-palette entry. Either way the art palette itself is never modified.

LOADER RECIPE: verify magic; walk the table; palette section to
Setpalette, bitmap section decoded to Physbase(). The probe is ~90
lines of 68k including the TOS scaffolding.

ASSETS. `<id>.AST` beside the story (GEMDOS 8.3-safe). Test pair: 90.AST,
100.AST.

### C.3 Amiga (target id 1, tag AMI, files `<id>.AMI`)

Verified: FS-UAE (A500, Kickstart 1.3), both modes, 2026-07-08;
re-verified with the LZSA2 codec 2026-07-09.

Probe: [arc_image/probes/ami/](../arc_image/probes/ami/), sources
`boot.s` and `payload.s` with the embedded test assets. Build:
`python3 build_adf.py` assembles both with vasm and lays the bootable
ADF; no filesystem, no Workbench: a bootblock trackload.

CODEC. LZSA2 (part B), decoded by the same shared 68000 routine as the
ST, [arc_image/probes/lzsa2_68k.s](../arc_image/probes/lzsa2_68k.s):
register-only, so the bootblock's position-independent world needs no
relocation for it; see C.2 for the convention and the 32K offset
constraint. The facts:

- bitmap (type 1): 5 bitplanes, row-interleaved ILBM-style (row of plane
  0, row of plane 1, ..., 40 bytes each; 200 bytes per pixel row in
  total). Display with 5 bitplane pointers offset 40 bytes apart and a
  modulo of 160 on each, and the interleave displays in place: no
  de-interleaving, no copying.
- palette (type 5): 32 words of $0RGB (OCS 4-bit guns), COLOR00..COLOR31
  verbatim.
- The band is the top of the display; text below is the interpreter's
  business.
- Z-COLOURS AND THE SPLIT: the copper list that ends the band (the same
  wait the probe uses to switch the planes off) is where the interpreter
  reloads the colour registers for its text area, EVERY frame: the art
  keeps all 32 entries above the line, and below it the interpreter
  aligns the Z-machine colours onto registers it owns outright. The
  probe's one-frame lesson applies to the restore direction too: whatever
  the bottom of the frame changes, the top of the list must set back.
- As a courtesy to implementations that do not split, the converter
  luminance-sorts the palette: entry 0 is the art's darkest (a stable
  dark paper) and entry 31 a guaranteed-readable light ink.

### C.4 Commodore 64 (target id 4, tag C64, files `<id>.C64`)

Verified: VICE x64sc, both modes, 2026-07-09; the decode path was also
proven byte-exact against the packer's sections through VICE's remote
monitor before the visual pass.

Probe: [arc_image/probes/c64/](../arc_image/probes/c64/), source
`probe.asm` with the decoder `dzx0_6502.asm` beside it and the embedded
test assets 90.C64 and 100.C64. Build (ACME):
`acme -f cbm -o probe.prg probe.asm`.

VIDEO. Multicolor bitmap mode: $D011 = $3B, $D016 = $D8, $D018 = $18
(VIC bank 0, matrix at $0400, bitmap at $2000). 160x200 wide pixels,
2:1; the band is the top 9 or 12 cell rows. Per 4x8 cell: three free
colors (matrix high nibble = pixel code 1, low nibble = code 2, color
RAM = code 3) plus one global background (code 0, $D021).

CODEC. ZX0 (part B), the standard v2 stream. Do not write the
decompressor: Tobias Bindhammer's bitfire routine decodes it as
published (BSD 3-Clause, carried verbatim as `dzx0_6502.asm` with one
documented adaptation: the caller preloads the destination in the
zero-page pointer instead of a hardwired address). Entry: X = source
lo, A = source hi; it owns zero page $F8-$FC. Each stream ends at its
own end marker, so the loader never counts output bytes.

SECTIONS, in file order, every payload already in native memory order:

- bitmap (type 1): cell-ordered rows for $2000 (2880 bytes in mode 9,
  3840 in mode 12). Decode straight to $2000.
- screen (type 2): the video matrix cell colors for $0400 (360 / 480).
- color (type 3): the color RAM nibbles for $D800 (360 / 480).
- registers (type 7): one byte, the shared background; write to $D021.

Z-COLOURS. The fixed 16 carry every Z-machine colour; the interpreter's
text lives in the cells BELOW the band (its own matrix and color RAM
rows), so text colours and art never share a register except $D021, the
global background. An interpreter that lets the player recolour the
background must accept that the band's code-0 pixels recolour with it
(the same global-register nature the Amiga chapter documents for
COLOR00); keeping the story's background equal to the art's register is
the simple answer.

LOADER RECIPE (the probe's shape): clear the canvas (bitmap, matrix,
color RAM) so the sub-band area sits flat; verify the magic; walk the
section table once, dispatching each type to its native destination and
advancing the data cursor by the table's compressed lengths. Under 120
instructions around the decoder. The probe waits on KERNAL GETIN
between the two images; a real interpreter draws its text below the
band instead.

ASSETS. `<id>.C64` beside the story. The standard test pair: 90.C64
(mode 9), 100.C64 (mode 12).

MEMORY. Bitmap and matrix decode into the VIC bank, color RAM into
$D800: no staging buffers at all beyond one byte for the register
section. The decoder's zero page is $F8-$FC plus the walk's $02-$07.

## Change log

- 2026-07-08: first cut: the contract, the format, the DOS chapter
  (verified), the ST chapter (provisional), the Amiga layout facts.
- 2026-07-08 (later): the ST chapter verified in Hatari, both modes, with
  the odd-length alignment lesson recorded.
- 2026-07-08 (later still): the Amiga chapter verified in FS-UAE, both
  modes; the Z-machine colours clause (part A.5) and the per-target
  colour answers; the AMI text contract (sorted palette) after the
  brown-to-pink background finding; wave 1 complete.
- 2026-07-08 (the codec rulings): header byte 14 grows codec 2, LZSA2,
  mandated for the 16-bit trio (and later MS2, NXT, M65); ZX0 stays the
  8-bit cell targets' codec. Part B carries both one-paragraph specs;
  arcimg's zx0_decompress and lzsa2_decompress are the executable ones.
  The wave-1 probes still speak RLE against pre-ruling assets; their
  LZSA2 rebuild (8086 and 68000 decoders adapted from the lzsa
  repository) is the next probe step and re-verification.
- 2026-07-09: the DOS probe rebuilt on LZSA2 (Marty's 8088 decompressor
  carried verbatim, zlib license) and re-verified in DOSBox-X, both
  modes; chapter C.1 updated probe-after-probe. The ST and Amiga
  rebuilds follow with the 68000 decompressor, written from part B's
  spec (the lzsa repository has no 68000 routine); their chapters and
  the change log record it when their probes are re-verified.
- 2026-07-09 (later): the shared 68000 LZSA2 decompressor
  (arc_image/probes/lzsa2_68k.s) written from the part B spec and
  proven byte-exact under vamos (real AST and AMI sections, both
  packers, plus a corruption control); the ST probe rebuilt on it and
  re-verified in Hatari, both modes. C.2 updated probe-after-probe.
- 2026-07-09 (later still): the Amiga probe rebuilt on the shared
  routine and re-verified in FS-UAE, both modes; C.3 updated. THE
  WAVE-1 BACKPORT IS COMPLETE: all three 16-bit probes decode LZSA2
  against current assets, and every chapter's codec matches its files.
- 2026-07-09 (evening): the C64 probe (the first cell-class target):
  ZX0 via the bitfire 6502 decoder carried verbatim, proven byte-exact
  through VICE's remote monitor in warp before the visual pass, then
  verified by Stefan in x64sc, both modes. Chapter C.4.
