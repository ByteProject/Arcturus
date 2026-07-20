# arc_image for interpreter authors: the contract, the format, the loaders

This is the implementer's book for arc_image, Arcturus's optional picture
band. It is written to be sufficient ALONE: an interpreter author (or a
fresh working session inside an interpreter's own repository) implements a
target from this document, the reference probe source, and the test assets,
without ever opening the Arcturus repository. The design record behind it is
arc_image/reference/design.md; nothing there is required reading.

The pipeline, in one paragraph, because the first question every
implementer asks is what is authored and what is derived: the author
paints ONE MASTER PNG per picture (320x72 or 320x96; nobody ever edits a
.arc). The `arcimg` tool derives each machine's native version from that
master as `<id>.<TAG>` (8.C64, 8.CPC, ...), each a small .arc container
whose payload is already in the machine's own memory order. An
interpreter loads only its own tag's files and never converts anything;
the modern path (Actaea) ships the PNGs themselves in an .arcres zip
instead. Masters are the single source; .arc files are per-machine
DELIVERY, regenerated at build time.

The handover package for a target is:

- this document (part A, part B, and the target's chapter in part C);
- `arc_image/probes/<target>/` : a working reference loader for the machine,
  commented against this spec, plus its build command;
- the standard test assets, `9.<TAG>` (mode 9) and `12.<TAG>` (mode 12), named for the band
  modes themselves (the ids in the headers match),
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

3. THE BAND. On a fixed-screen interpreter (the retro machines, and any
   modern one that models the classic Z-machine screen) the picture
   occupies the top of the screen; the interpreter's text screen model
   (including the Z-machine upper window and status line) lives strictly
   below it. Both modes must work. The band persists across turns until the
   next draw_image call replaces or clears it; the story's library already
   deduplicates (a re-LOOK issues no draw), so the interpreter needs no
   redraw caching of its own.

   PRESENTATION IS THE MODERN INTERPRETER'S OWN. The band is the contract
   only where a fixed screen makes it one. A modern interpreter, free of
   the cell grid, may present the picture however suits it: a transcript
   that scrolls the picture inline with the prose (the storybook flow, with
   earlier scenes still visible above), a resizable panel, a fade between
   scenes. What every presentation must preserve is the meaning: the mode's
   aspect (mode x 8 rows over the platform width; a modern terp may scale
   freely but not distort), the picture belonging to the moment it was
   drawn, and clear (id 0) taking the current picture down. How and where it
   sits on screen is the author's discretion. This latitude is deliberate:
   the same draw_image stream drives a pinned band on an 8-bit and a
   flowing gallery in a browser, and both are conformant.

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

## The modern desktop (the .arcres path)

A modern interpreter needs Part A and this section, nothing else:
everything from Part B on (the .arc container, the codecs, the per-target
chapters) is the retro machines' business. On the desktop there is no
container and no codec: the pictures ship as the master PNGs themselves.

RESOURCES, two envelopes, one model. Beside the story file sits a pack
of the numbered master PNGs, and the picture id in the opcode is the
resource number in the pack, nothing else:

- `.arcres` (mygame.z5, mygame.arcres): a plain zip holding `<id>.png`
  (picture 8 is 8.png). No manifest; the names are the index.
- Blorb: the same pictures as `Pict` resources (picture 8 is Pict 8,
  a `PNG ` chunk holding the master bytes verbatim). `mygame.blorb`
  accompanies a separate story file; `mygame.zblorb` embeds the story
  itself as Exec 0 (a `ZCOD` chunk), the single-file shape the
  Gargoyle family opens directly. arcimg writes both (`pack --blorb`,
  `pack --zblorb STORY`).

An interpreter that already speaks Blorb needs nothing new: resource
number = arc_image id, and the mode still arrives in the opcode. One
that speaks neither can pick the zip, which is the smaller parse. A
loose directory of numbered PNGs beside the story is the DEBUGGING
fallback (Actaea checks pack first, then the story's directory);
released games ship a pack. Master resolution: any size at the band's
aspect ratio (40:9 mode 9, 10:3 mode 12); 320-wide is the reference,
not a ceiling, and the interpreter scales to its band.

THE DECLARATION CHUNK, and it is MANDATORY in a Blorb. Every Blorb
carrying arc_image art also carries an `ARCI` chunk, so an interpreter
knows before executing a single instruction whether this game wants a
picture band:

    'ARCI'  length 2
    +0  1  extension version (currently 1)
    +1  1  band mode: 9, 12, or 0 = not declared

    ABSENCE IS MEANINGFUL. A Blorb with no ARCI chunk makes NO arc_image
    promise: an interpreter may treat it as a plain story file and need
    not reserve a band or raise the capability bit for it. This is a
    guarantee interpreters may rely on, so that the question "does this
    game use arc_image" is decidable up front rather than speculative.

Two things this does NOT change. The chunk is a Blorb packaging rule
only: a plain `.z5`/`.z8` beside a loose `.arcres` or an images
directory involves no Blorb and needs nothing new, so Part A alone
remains the whole runtime contract. And the chunk is never a second
source of truth for the band: the mode operand of each `draw_image`
call stays authoritative (part A, point 2), so a declared 0, or a game
that ever varied its mode, still renders correctly. The declaration is
advance notice, not instruction.

`arcimg` writes the chunk into every Blorb it produces, so an author
never has to think about it.

RENDERING. Present the picture however suits your interpreter (Part A,
point 3: on a modern terp the fixed band is a default, not a mandate).
Actaea pins it as a band above the text; another interpreter scrolls it
inline with the transcript, storybook-style, and that is equally
conformant. What to keep: the mode's aspect (mode x 8 rows over the
width, scaled freely but not distorted), the picture tied to the moment
it was drawn, and id 0 clearing it. Pixel art scales crispest on integer
factors, so a nearest-neighbour or integer zoom keeps it sharp; a
smooth scale is your call. draw_image with an id you cannot resolve:
ignore silently and play on.

REFERENCE IMPLEMENTATION. Actaea's window front-end is the working
desktop loader this section was written from: `actaea/vm.py` (the opcode
and the capability bit), `actaea/screen.py` (the band in the screen
model), `actaea/gui/` (the rendering). The whole path is a few dozen
lines; the protocol was designed so that it stays that way.

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
anything else is honest behavior. (A short-lived codec 3 was reserved
and retired unreleased on 2026-07-17; its purpose, a bounded lookback
window, became a guarantee on codec 1 itself, see the window guarantee
below. No file ever carried codec 3.) The assignment (rulings
2026-07-08, the bake-off and the speed amendment, and 2026-07-17, the
window guarantee, all in arc_image/reference/design.md):

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
decompression is a plain byte loop that reads back into its own output.

THE WINDOW GUARANTEE (ruled 2026-07-17; the number every retro loader
depends on). arcimg packs every codec-1 stream so that NO match offset
exceeds 2048 bytes. This is a hard promise of the format, not a hint: on
the corpus it costs nothing (the packed sizes are byte-identical to the
older unbounded quick window on C64, CPC, and Spectrum alike), and in
exchange a decoder never has to reach further back than 2048 bytes of
its own output. Two memory models satisfy the format, and a target
chapter in part C names which one it uses:

- STAGING (the plentiful-RAM model, the 16-bit chapters and any 8-bit
  machine with room to spare). Decompress a whole section into a
  contiguous buffer with a published dzx0, then blit the buffer to the
  screen. Fastest (block moves), simplest, and it wants source + a full
  band resident at once.
- RING (the tight-RAM and write-only-video model, the 8-bit cell
  chapters). Keep a single 2048-byte ring in main RAM holding the last
  2048 output bytes; decode one byte at a time, writing each to the ring
  AND straight out to the screen, and serve every back-reference from
  the ring. The window guarantee is what makes this sufficient: 2048
  bytes of history is all a codec-1 stream can ask for. The compressed
  source is read strictly forward, so it may itself be streamed from
  disk in sector bites. This is the model for a machine that cannot
  afford a staging band beside a running Z-machine (a 64K profile), and
  the ONLY model for a machine whose video memory cannot be read back at
  all (a port-addressed graphics board, a serial VDP): the per-byte
  screen write is the one platform-specific step. Cost is per-byte emits
  instead of block moves, paid once per room entry.

Both models decode the identical bitstream; a ring loader and a staging
loader reading the same .arc file produce the same pixels. The published
Z80 and 6502 dzx0 routines implement the staging model as written. The
ring model's Z80 reference is
[arc_image/probes/dzx0r_z80.asm](../arc_image/probes/dzx0r_z80.asm):
about 110 bytes, built as the smallest possible delta on the standard
dzx0 (only the two LDIR copy paths are re-plumbed; the Elias gamma
reader, the negative-offset bookkeeping, and the end-marker detection
are carried verbatim), with a single platform-supplied `emit` routine as
the only port point. It is executed instruction-by-instruction against
the corpus in the test suite (tests/test_dzx0r.py), so a port starts
from decoder logic that is already proven; the CPC chapter (C.6) is the
reference ring loader built on it. The 6502 ring reference lands with
the C64 probe rebuild.

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
proven; the ledger of all fourteen planned targets is arc_image/reference/design.md section 2.

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
assets 9.DOS and 12.DOS, and the built PROBE.COM. Build:
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
is decimal, at most five digits). The standard test pair: 9.DOS (mode 9),
12.DOS (mode 12).

MEMORY. Both the bitmap and the palette decode into VRAM and ports; the
loader needs no buffer beyond the 768-byte palette staging (and even that
can stream). Conventional-memory cost: effectively zero.

### C.2 Atari ST (target id 2, tag AST, files `<id>.AST`)

Verified: Hatari, both modes, 2026-07-08; re-verified with the LZSA2
codec 2026-07-09.

Probe: [arc_image/probes/ast/](../arc_image/probes/ast/), source
`probe.s` with the embedded test assets 9.AST and 12.AST. Build:
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

ASSETS. `<id>.AST` beside the story (GEMDOS 8.3-safe). Test pair: 9.AST,
12.AST.

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

Verified (ring loader): VICE x64sc, both modes, 2026-07-17. The full
probe is executed end to end on a mini-6502 with a scripted keypress
before any emulator pass (bitmap, matrix, color RAM, and background
byte-exact for both images), the decoder against the corpus on every
test run (tests/test_dzx0r6502.py), and the live pass confirmed matrix
and color RAM byte-exact through the remote monitor with both images
approved on screen by Stefan. (The staged R3 loader was verified
2026-07-09.)

Probe: [arc_image/probes/c64/](../arc_image/probes/c64/), source
`probe.asm` with the ring decoder `dzx0r_6502.asm` beside it and the
embedded test assets 9.C64 and 12.C64. Build (ACME):
`acme -f cbm -o probe.prg probe.asm`.

VIDEO. Multicolor bitmap mode: $D011 = $3B, $D016 = $D8, $D018 = $18
(VIC bank 0, matrix at $0400, bitmap at $2000). 160x200 wide pixels,
2:1; the band is the top 9 or 12 cell rows. Per 4x8 cell: three free
colors (matrix high nibble = pixel code 1, low nibble = code 2, color
RAM = code 3) plus one global background (code 0, $D021).

CODEC. ZX0 (part B) under the 2048 window guarantee, decoded by the
RING model: `dzx0r_6502.asm`, a clean transcription of the reference
state machine (about 230 bytes, machine-verified), with a 2K-aligned
ring as its only working memory and a single JMP vector as the emit.
Every C64 section is contiguous in native order, so the one emit the
machine needs is a linear store-and-advance. Entry: X = source lo, A =
source hi; it owns zero page $08-$12. Each stream ends at its own end
marker, so the loader never counts output bytes. (A RAM-rich setup may
still stage with the bitfire routine, `dzx0_6502.asm`, kept beside it;
the stream is identical.)

THE LAYOUT RULE the ring build must honor: the bitmap section DECODES
INTO $2000-$3FFF, so nothing the loader still needs may sit there. The
probe parks its embedded images at $4000, above the canvas; the first
ring build placed them across $2000 and watched the bitmap decode
overwrite its own yet-undecoded color stream. An interpreter loading
sections from disk has no such hazard (the compressed data arrives in
buffers it controls), but any embedded-asset arrangement does.

SECTIONS, in file order, every payload already in native memory order:

- bitmap (type 1): cell-ordered rows for $2000 (2880 bytes in mode 9,
  3840 in mode 12). Decode straight to $2000.
- screen (type 2): the video matrix cell colors for $0400 (360 / 480).
- color (type 3): the color RAM nibbles for $D800 (360 / 480).
- registers (type 7): one byte, the shared background; write to $D021.

Z-COLOURS. The fixed 16 carry every Z-machine colour; the interpreter's
text lives in the cells BELOW the band (its own matrix and color RAM
rows), so text colours and art never share a register except $D021, the
global background. The screen model is the interpreter's choice of two
classic constructions: a raster split at the band boundary (bitmap mode
above, cheap text mode below; the VIC's stable raster interrupt makes
this easier than the CPC's rupture) or a full-screen bitmap with the
font rendered into it. Either honors this chapter unchanged. An interpreter that lets the player recolour the
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

ASSETS. `<id>.C64` beside the story. The standard test pair: 9.C64
(mode 9), 12.C64 (mode 12).

MEMORY. The 2K ring: the entire decode working set (this machine never
staged, but the R3 build used a decoder that reads back its own output,
which the ring retires). Bitmap and matrix emit into the VIC bank,
color RAM into $D800, one byte for the register section. Zero page:
$08-$12 for the decoder, $02-$07 and $13/$14 for the walk and emit.
The compressed source is read strictly forward, so it may be streamed
from disk in sector bites rather than held whole.

### C.5 ZX Spectrum +3 (target id 9, tag ZX3, files `<id>.ZX3`)

Verified (ring loader): ZEsarUX, Spectrum +3 (ROM 4.1), both modes,
2026-07-17, via the machine-exact injection route below, byte-exact:
the frozen machine's bitmap and attribute file were read back over ZRCP
and compared against the expected decodes, pixel-exact for both images.
The probe is also executed end to end on a mini-Z80 with scripted keys
before any emulator pass, and the decoder against the corpus on every
test run (tests/test_dzx0r.py). (The staged R3 loader was verified the
same way on 2026-07-10.)

Probe: [arc_image/probes/zx3/](../arc_image/probes/zx3/), source
`probe.asm` with the ring decoder
[arc_image/probes/dzx0r_z80.asm](../arc_image/probes/dzx0r_z80.asm) and
the embedded test assets. Build: `sjasmplus probe.asm` (emits both
probe.sna, the 128K snapshot, and probe.bin, the raw image).

VIDEO. The ULA screen, identical on every model from the 48K to the +3:
bitmap at $4000 in the interleaved thirds, the attribute file at $5800.
The band is the top 72 or 96 pixel rows (9 or 12 attribute rows); below
it everything stays paper black, the interpreter's text area.

CODEC. ZX0 (part B) under the 2048 window guarantee, decoded by the
RING model: dzx0r_z80.asm with a 2K ring, no staging buffer, each byte
emitted straight to the ULA screen. Reuse the decoder; do not write
your own. (A RAM-rich setup may still stage with the classic dzx0; the
stream is identical.)

SECTIONS, in file order:

- bitmap (type 1): the band's 32-byte pixel rows in ASCENDING ULA
  ADDRESS order (third, line-in-char, char-row). That order is linear
  runs with hops, which is exactly what the ring loader's screen emit
  implements: within one line-in-char the destination walks rmax*32
  contiguous bytes (rmax = this third's char-row bound, height/8 capped
  at 8), then hops one $100 page to the next line, and after 8 lines
  hops to the next $800 third. A write, a countdown, and a hop (the
  probe's emit_scr plus thirdinit; take them). A PARTIAL third (the
  band's tail) spans only rows/8 char-rows: bound the run per third
  from the header's height, never assume 8.
- attributes (type 4): one byte per cell, row-major, contiguous: decode
  STRAIGHT to $5800 through the plain buffer emit. Mind the number:
  type 4 is SEC_ATTR; type 2 is the C64's color matrix, and the probe's
  first build checked 2 and painted a perfect picture in black on
  black.

Z-COLOURS. The fixed 15 carry every Z-machine colour. The interpreter's
text lives in the attribute rows below the band; the art's attributes
are never shared with text, so nothing needs aligning.

LESSONS THE PROBE PAID FOR (beyond the type-4 one above):

- A bare-metal program must claim its own stack FIRST: sjasmplus's 48K
  SAVESNA parks SP inside the screen area, and clearing the screen then
  wipes the return addresses (the first black-screen build).
- Snapshot formats carry a MACHINE: loading a 48K .sna downgrades the
  emulated machine to a 48K Spectrum, and the 128K .sna runs as a plain
  128k. For machine-exact +3 verification use ZEsarUX's remote protocol
  instead: `--enable-remoteprotocol`, then `enter-cpu-step`,
  `load-binary <absolute path> 32768 0`, `set-register PC=8000H`,
  `exit-cpu-step`. Register values are HEX WITH THE H SUFFIX (decimal
  parses wrong), paths must be absolute (ZEsarUX chdirs into its app
  bundle), and send ONE command per connection: a multi-command pipe
  races the parser.
- A probe should loop its pictures (9, 12, 9, ...): a bare Spectrum has
  no OS to return to, and a final freeze reads as a crash.

ASSETS. `<id>.ZX3` beside the story. The standard test pair: 9.ZX3
(mode 9), 12.ZX3 (mode 12).

MEMORY. The 2K ring: the entire decode working set (the R3 staging
buffer of 3072 bytes is retired); attributes decode straight to the
attribute file. The compressed section is read strictly forward, so it
may be streamed from disc in sector bites rather than held whole.

### C.6 Amstrad CPC (target id 6, tag CPC, files `<id>.CPC`)

Verified (ring loader): ZEsarUX, CPC 464, both modes, 2026-07-17, via
the ZRCP injection route, and byte-exact rather than by eye: the frozen
machine's screen blocks and palette buffer were read back over ZRCP and
compared against the expected decodes, pixel-exact for both images.
The embedded test pair is the current-pipeline beach conversion (its
mode-12 render is pixel-identical to the approved stress preview), art
gate passed by Stefan the same day.
(ZEsarUX has NO CPC snapshot support: its .sna reader is Spectrum-only
and answers "corrupt file"; the crafted v1 snapshot the build also
emits is for the WinAPE family. The staged R3 loader was verified the
same way on a 6128, 2026-07-10.) The decoder is additionally executed
against the corpus on every test run (tests/test_dzx0r.py), and the
probe end to end on a mini-Z80 with scripted keys before the emulator
ever saw it.

Probe: [arc_image/probes/cpc/](../arc_image/probes/cpc/), source
`probe.asm` with the ring decoder
[arc_image/probes/dzx0r_z80.asm](../arc_image/probes/dzx0r_z80.asm) and
`build_sna.py` (a hand-built v1 snapshot, pure Python). Build:
`sjasmplus probe.asm` then `python3 build_sna.py`.

VIDEO. Mode 0, 160x200 fat pixels, 16 pens from the 27-color cube. OWN
THE CRTC: program the standard 40x25 screen at $C000 yourself (R0-R13:
63, 40, 46, $8E, 38, 0, 25, 30, 0, 7, 0, 0, $30, 0); an injected or
firmware-scrolled machine has a nonzero display offset in R12/R13 and
the picture wraps and shifts. Clear the full 16K before the first draw:
whatever was on screen shows through the sub-band area otherwise.

CODEC. ZX0 (part B) under the 2048 window guarantee, decoded by the RING
model: this chapter is the reference ring loader (R5, 2026-07-17). The
decoder is dzx0r_z80.asm, about 110 bytes, and its whole working memory
is one 2K-aligned ring; each decoded byte goes to the ring and out
through an `emit` the probe points at the screen writer or a buffer
writer per section. No staging band exists. This is the 64K posture the
CPC 464 aim requires: an interpreter holds the Z-machine, the story, the
compressed section, and 2K, nothing more. (A 6128-class setup with RAM
to spare may still stage with the classic dzx0_z80.asm; the stream is
identical either way.)

SECTIONS, in file order:

- bitmap (type 1): Mode 0 bytes in SUB-BLOCK order. The screen's eight
  $800 blocks each hold every 8th raster line, and the band's rows land
  contiguously at each block's START: the ring loader's screen emit
  writes linearly into block 0 until height*10 bytes have landed, hops
  to the next block base ($C000 + s*$800), and repeats. A write, a
  counter, and a hop; no other math exists.
- palette (type 5): 16 ink indices IN THE 27-CUBE, r*9+g*3+b with gun
  levels 0..2. This is NOT the firmware's ink numbering: the cube is
  RGB-ordered, the firmware order is luminance-grouped, and a loader
  built with the familiar firmware table paints systematically wrong
  colors (this probe's second build did). The cube-indexed hardware
  table, verbatim:

      54 44 55 56 46 57 52 42 53   ; r=0: g=0,1,2 x b=0,1,2
      5C 58 5D 5E 40 5F 5A 59 5B   ; r=1
      4C 45 4D 4E 47 4F 4A 43 4B   ; r=2

  Program pens 0-15 through the gate array (pen select, then color with
  bit 6 set).
- registers (type 7): one byte, the border ink as a cube index.

Z-COLOURS. The 27-cube contains every Z-machine colour at full
saturation (as cube indices: black 0, blue 2, green 6, cyan 8, red 18,
magenta 20, yellow 24, white 26). The art's sixteen pens are never
modified; the TEXT region is mode 1, four concurrent pens, reloaded per
frame by the split below, so the interpreter allocates text pens to the
Z-colours a game actually requests and degrades gracefully past four in
one frame (an IF page rarely wants more than paper, ink, and an
emphasis). This is Haumea's one real colour-design point; nothing else
on the machine constrains it.

THE SPLIT SCREEN (the interpreter's screen model). Mode 0 and mode 1
fetch the SAME 80 bytes per scanline: the memory layout is identical,
only the gate array's pixel interpretation differs. So an interpreter
keeps ONE linear screen and switches mode at the band boundary with a
raster-timed gate-array write (the classic rupture, off the 300Hz
interrupt): band rows render mode 0 in 16 colors, the text below
renders mode 1 at 320 wide. The same interrupt may reload pens 0-3 for
the text region and restore the art's palette at frame top, giving text
its own paper and ink without touching the picture: below the band the
probe's pen 0 wears the image's first palette entry (grey for one test
image, purple for the other), and the region pen reload is how a real
interpreter makes that area its own. This is the CPC's equivalent of
the Amiga chapter's copper clause; DAAD's CPC games shipped exactly
this construction.

ASSETS. `<id>.CPC` beside the story. The standard test pair: 9.CPC
(mode 9), 12.CPC (mode 12).

MEMORY. The 2K ring plus 17 bytes of palette/register buffers: the
entire decode working set (the R3 probe's 7680-byte staging band is
retired). The compressed section is read strictly forward, so it may be
streamed from disc in sector bites rather than held whole. The keyboard
is read through the PPI/AY row scan (the probe's anykey is the
reference).

### C.7 TRS-80 Model 4 (target id 15, tag TRSM4, files `<id>.TRSM4`)

The first target whose interpreter lives outside the family: Shawn
Sijnstra builds and maintains the Model 4 engine. The TARGET is
first-class arc_image regardless (ruled 2026-07-17): arcimg converts,
packs, and renders it like any other, this chapter is its blueprint,
and the test assets ship with the family.

Probe: [arc_image/probes/trsm4/](../arc_image/probes/trsm4/), source
`probe.asm` with the ring decoder
[arc_image/probes/dzx0r_z80.asm](../arc_image/probes/dzx0r_z80.asm)
carried unchanged (THIS is the machine the ring model was built for:
the board cannot be read back, so the ring is the only model) and
`build_cmd.py` (a /CMD load module, pure Python). Build: `sjasmplus
probe.asm` then `python3 build_cmd.py probe.bin probe.cmd 3000`; run:
`trs80gp -m4 -gt -vs probe.cmd` (Model 4, Tandy hi-res board, sharp
display). The full probe is executed end to end on a mini-Z80 with a
port model of the board (X/Y/data, X auto-inc on write, no Y wrap) and
a scripted keystroke: both images byte-exact in the modeled graphics
RAM, the area below the band clean. One hardware assumption is a
single equate (CTRL, the port $83 option byte), CALIBRATED against
trs80gp's Tandy board by VRAM readback: bit 7 selects the X axis for
the write clock (clear = the clock steps Y instead), bit 2 reverses X,
bit 3 reverses Y, bit 6 changes the addressing mode (avoid), bits 4-5
inert in this emulation; the probe ships $83. THE HARDWARE QUESTION,
ANSWERED (via Shawn Sijnstra and trs80gp's author, 2026-07-18): the
real Tandy boards NEVER drop a write; they insert wait states on
video memory access (1 to 4 per access, sometimes more), and with
wait states disabled a conflict shows as white hash on screen, never
as a lost byte. Interpreters therefore need NO write pacing. The
single dropped write our verification caught (one byte of the first
image, boot-phase-locked, reproducible) is a trs80gp emulation bug,
reported upstream with a byte-exact repro; synthetic fills at every
write spacing do not trigger it, only the probe's full boot sequence
does.

VIDEO. The hi-res board: 640x240 1bpp on a 4:3 screen, so pixels are
half as wide as tall. The band is 640x72 (mode 9) or 640x96 (mode 12):
the 320-wide master doubles horizontally, which restores the aspect
AND doubles the dither grid; a monochrome target's whole quality
budget is its halftone, so the doubling is not an upscale but a
resolution purchase. Text is 80x24 in an 8x10 font; the band's 72/96
pixel rows sit above the text area (the 8-pixel row contract of part A
governs band SIZE; how the 10-pixel font rows flow below it is the
interpreter's screen model).

CODEC. ZX0 (part B) under the 2048 window guarantee, decoded by the
RING model; on this machine the ring is not an option but the ONLY
model, since the board's memory is port-addressed and cannot be read
back. dzx0r_z80.asm is the reference; the emit is a port write.

SECTIONS: one.

- bitmap (type 1): 80 bytes per row, top to bottom, bit 7 the LEFTMOST
  pixel (132 lights x....x..), 5760 bytes in mode 9, 7680 in mode 12.
  No palette, no attributes, no registers: monochrome is monochrome.

CONVERSION (the arcimg side, for the record): luminance, a
percentile-anchored contrast stretch (a mono image lives on its tonal
range), then ordered Bayer dither at the full 640 grid.

Z-COLOURS. None. A game's colour requests degrade to nothing, per the
part A contract; the interpreter renders its text in the machine's one
ink.

ASSETS. `<id>.TRSM4` beside the story (the interpreter's own disk
layout may rename; the .arc header id is authoritative). The standard
test pair: 9.TRSM4, 12.TRSM4.

MEMORY. The 2K ring: the entire decode working set. The compressed
source is read strictly forward and may be streamed from disk in
sector bites.

## Change log

- 2026-07-19 (presentation latitude): Part A point 3 now makes the fixed
  top-of-screen band the contract only for fixed-screen interpreters; a
  modern interpreter may present the picture however suits it (a
  transcript that scrolls pictures inline, a resizable panel), preserving
  only the mode aspect, the picture's moment, and clear. Presentation on
  modern systems is the interpreter author's discretion.
- 2026-07-20 (the ARCI declaration chunk): every Blorb arcimg writes now
  carries a two-byte `ARCI` chunk (extension version, band mode), and its
  absence is a defined state: a Blorb without it promises no arc_image
  graphics, so the question is decidable before execution rather than
  speculative. Mandatory in Blorb; the bare story-plus-pack path and the
  runtime contract are untouched.
- 2026-07-19 (Blorb): the modern chapter gains the second envelope, on
  the interpreter community's ask: arcimg writes .blorb (pictures as
  Pict N) and .zblorb (story embedded as Exec 0) alongside .arcres,
  same numbering everywhere; Actaea opens both. Master resolution
  ruled flexible at the band aspect (320 is the reference, not a
  ceiling).
- 2026-07-19 (the modern desktop): the .arcres path gets its own chapter,
  placed directly after Part A and before the retro container, so a
  desktop terp author reads the contract, the pack (a zip of numbered
  band-shaped PNGs beside the story), and stops; the retro codec
  chapters are explicitly not their reading. Prompted by
  interpreter-author questions on the announcement thread.
- 2026-07-17 (TRSM4, the first external-interpreter target): target id
  15, the TRS-80 Model 4 hi-res board, 640x72/96 1bpp, one bitmap
  section, ring-decoded (the board cannot read back its memory, so the
  ring model is the only model). Requested and implemented by Shawn
  Sijnstra on the interpreter side; the target, blueprints, and assets
  are family. Chapter C.7.
- 2026-07-17 (the C64 ring probe, verified): C.4 joins the ring model,
  completing the 8-bit cell trio. The 6502 ring decoder dzx0r_6502.asm
  lands beside the staged bitfire routine (a clean transcription of the
  reference state machine, not a bitfire re-plumb: that decoder's
  self-modifying speed structure is tied to a readable linear
  destination). Every C64 section is contiguous native memory, so the
  probe's one emit is a linear store; the layout rule (nothing needed
  may live under the $2000 bitmap canvas) is documented after the first
  build broke it. MEMORY (C.4) now reads: the 2K ring, source
  streamable.
- 2026-07-17 (the test pair is 9 and 12): the standard test assets are
  renamed for coherence with the band modes they carry: `9.<TAG>` is
  the mode-9 image (infocom, 72 rows), `12.<TAG>` the mode-12 image
  (DAAD, 96 rows); the header ids match. The former 90/100 ids were an
  undocumented convention and are gone; every probe was rebuilt with
  the renamed assets.
- 2026-07-17 (the ZX3 ring probe, verified): C.5 joins the ring model.
  The staging buffer is gone; the ULA's third/line/char-row interleave
  turns out to be the ring loader's natural shape (linear runs with two
  levels of hop), and attributes stream straight to $5800. Verified
  byte-exact on ZEsarUX (+3 ROM 4.1, both modes, frozen bitmap and
  attribute file read back and compared). MEMORY (C.5) now reads: the
  2K ring, source streamable.
- 2026-07-17 (the CPC ring probe, verified): C.6 is the first ring
  chapter proven end to end. The ring decoder dzx0r_z80.asm landed
  beside the classic dzx0 (part B), the CPC probe dropped its staging
  band for the 2K ring with per-section emit vectors, and verification
  was byte-exact on ZEsarUX (CPC 464, both modes, frozen screen and
  palette read back over ZRCP and compared). The probe's test pair was
  regenerated with the current conversion pipeline and art-approved.
  MEMORY (C.6) now reads: 2K ring + 17 bytes, no staging, source
  streamable.
- 2026-07-17 (the window guarantee): codec-1 streams are packed with no
  match offset beyond 2048 bytes, at zero measured cost on the corpus,
  and part B now specifies the two decode memory models (staging and
  ring). The ring model retires the both-copies-resident assumption for
  the 8-bit cell targets: a 2K ring plus a per-byte emit to the native
  screen replaces the staging band, which also serves machines whose
  video memory cannot be read back. Cell-target chapters migrate as
  their probes are rebuilt; reference ring decoders land with them.
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
- 2026-07-10: the Spectrum +3 probe, verified by Stefan in ZEsarUX on
  the +3 itself (the ZRCP injection route; snapshots switch machines).
  Chapter C.5 with the stack, machine, and type-4 lessons.
- 2026-07-10 (later): the CPC probe, verified by Stefan in ZEsarUX on
  the 6128 (ZRCP; ZEsarUX has no CPC snapshot support). Chapter C.6
  with the cube-vs-firmware ink trap, the CRTC-ownership and
  clear-first lessons, and the split-screen clause. R3'S PROBE ROW IS
  COMPLETE: six machines, six proven blueprints.
