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
    +14  2  reserved, 0

SECTION TABLE, section-count entries of 6 bytes, at offset 16:

    +0   1  section type
    +1   1  flags (0 unless the target chapter defines bits)
    +2   2  uncompressed length
    +4   2  compressed length (includes the end sentinel)

The compressed section streams follow the table immediately, in table
order, each RLE-packed. A loader locates section N's stream by summing the
compressed lengths before it.

Section types: 1 bitmap, 2 screen matrix, 3 color matrix, 4 attributes,
5 palette, 6 line table, 7 registers. Which sections a target carries, and
their exact meaning, is per target (part C); two rules hold everywhere:

- Section payloads are in the machine's NATIVE memory order. The loader
  never reorders, shuffles, or converts anything; it unpacks bytes to where
  they live.
- Palette payloads are in the machine's NATIVE hardware encoding and are
  written to the hardware verbatim.

THE RLE SCHEME (shared by every target; control byte c):

    c = 0x00..0x7F   literal: copy the next c+1 bytes to the output
    c = 0x81..0xFF   run: repeat the next byte 257-c times (2..128)
    c = 0x80         end of section

The uncompressed length in the table is authoritative; the 0x80 sentinel
lets a streaming loader run without a counter. Reference decoders, both
about a dozen instructions:

x86 (16-bit, ds:si = stream, es:di = destination; from the DOS probe):

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

68000 (a0 = stream, a1 = destination; from the ST probe). Mind the dbra
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

6502 and Z80 reference decoders land with their waves' chapters.

## Part C: the targets

Each chapter gives the target id and tag, the video setup, the sections and
their native layouts, the loader recipe (against the probe source), the
asset naming, and the verified-on line. Chapters appear as their probes are
proven; the ledger of all fourteen planned targets is docs/08 section 2.

### C.1 DOS (target id 3, tag DOS, files `<id>.DOS`)

Verified: DOSBox-X, both modes, 2026-07-08 (probe:
`arc_image/probes/dos/probe.asm`, `nasm -f bin probe.asm -o PROBE.COM`).

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

LOADER RECIPE (the probe's shape): verify the magic; walk the section table
twice, palette pass first (so the picture never flashes in wrong colors),
bitmap pass second; each pass RLE-decodes its section to its destination.
Under 120 instructions all told. Clear the band region before drawing a
new image only if the new image is narrower than the old (they never are;
a mode change between draws is the one case, and re-entering mode 13h
clears the screen anyway).

ASSETS. `<id>.DOS` beside the story file (8.3-safe by construction: the id
is decimal, at most five digits). The standard test pair: 90.DOS (mode 9),
100.DOS (mode 12).

MEMORY. Both the bitmap and the palette decode into VRAM and ports; the
loader needs no buffer beyond the 768-byte palette staging (and even that
can stream). Conventional-memory cost: effectively zero.

### C.2 Atari ST (target id 2, tag AST, files `<id>.AST`)

Verified: Hatari, both modes, 2026-07-08 (probe:
`arc_image/probes/ast/probe.s`, build with
`vasmm68k_mot -Ftos -o PROBE.PRG probe.s`).

Two 68000 lessons the probe paid for, so an implementer does not: an .arc
file can be ODD-length, so anything embedding or loading one to memory
must align it (an even boundary) before touching the header with word or
long reads, or the 68000 answers with an address error; and the RLE
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

LOADER RECIPE: verify magic; walk the table; palette section to
Setpalette, bitmap section RLE-decoded to Physbase(). The probe is ~90
lines of 68k including the TOS scaffolding.

ASSETS. `<id>.AST` beside the story (GEMDOS 8.3-safe). Test pair: 90.AST,
100.AST.

### C.3 Amiga (target id 1, tag AMI, files `<id>.AMI`)

PENDING: the chapter is written with its probe (in progress). Layout
facts an implementer can already rely on, from the format spec:

- bitmap (type 1): 5 bitplanes, row-interleaved ILBM-style (row of plane
  0, row of plane 1, ..., 40 bytes each; 200 bytes per pixel row in
  total). Display with 5 bitplane pointers offset 40 bytes apart and a
  modulo of 160 on each, and the interleave displays in place: no
  de-interleaving, no copying.
- palette (type 5): 32 words of $0RGB (OCS 4-bit guns), COLOR00..COLOR31
  verbatim.
- The band is the top of the display; text below is the interpreter's
  business (Eris renders its own text plane; a copper split can give the
  text area independent colors).

## Change log

- 2026-07-08: first cut: the contract, the format, the DOS chapter
  (verified), the ST chapter (provisional), the Amiga layout facts.
- 2026-07-08 (later): the ST chapter verified in Hatari, both modes, with
  the odd-length alignment lesson recorded.
