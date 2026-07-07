# arc_image on retro systems (B12): charter, targets, and roadmap

Status: APPROVED 2026-07-07 (R0 complete; every open decision ruled by
Stefan the same day, rulings folded into section 8). This is the design
record for B12, the way actaea-design.md was for B10; it grows the format
spec and the per-target blueprints as they land.

## 1. Charter

B11 ended with pictures on modern systems and a promise: the same numbered
picture, on the 8-bit and 16-bit machines. B12 keeps that promise, and its
center of gravity is not the file format. It is the CONVERSION INTELLIGENCE:

- An author paints ONE master picture per image id, at the quality of the
  least constrained targets (Amiga/ST/DOS class). arcimg derives the IDEAL
  native version for every supported machine automatically: the right
  resolution and aspect, the right palette, the machine's attribute and
  cell constraints respected and color clashes resolved gracefully, detail
  reduced where the hardware demands it, so the result looks composed for
  the machine rather than degraded to it. Hand-painting fourteen versions
  of every picture is the eight-month cost this feature exists to abolish.
- As an option only, an author hand-paints a native version for a specific
  target (a PNG in that machine's exact geometry and palette); arcimg then
  encodes it 1:1 to the native format and lints it against the machine's
  constraints instead of converting.
- Every target ships as a PROVEN BLUEPRINT: the format specification, the
  converter back-end, the interpreter contract, and a verification probe
  that demonstrably loads and shows the picture on the machine (in its
  emulator), in both band modes, before the target is handed to an
  interpreter build. Most of the target interpreters do not exist yet;
  the blueprints are written so each can be built directly on top of the
  proven Standard 1.1 core family (Ceres, Varuna, Eris, Haumea, and the
  family members to come), and so third-party interpreters (Vezza has
  announced adoption) can implement the same contract from the documents
  alone. The blueprints are public-facing.

Unchanged from B11, and non-negotiable: the story file stays a conformant
z5/z8; the one identifier is the numeric image id; the mode travels in the
opcode (`draw_image id mode`, EXT:0x80); the capability guard (Flags 1 bit 1)
keeps every unaware interpreter untouched; Cosmos already dedups redraws so
a retro machine never re-decompresses on a LOOK. arc_mode 9 (Infocom, upper
third) is the default; 12 (DAAD, upper half) is set with `constant arc_mode
= 12`.

## 2. The target ledger

Fourteen targets. Two facts hold across every one of them, and both were
design bets in B11 that the hardware research has now confirmed:

- The 72px and 96px bands align EXACTLY with each machine's 8-pixel text
  rows. No target has a partial row.
- Every target wants its image data in the machine's NATIVE memory order
  (the Spectrum's interleaved thirds, the CPC's 0x800-stride lines and
  mode-0 bit shuffle, the C64's cell-ordered bitmap, the Amiga's planes,
  the Next's column-major 320 mode). The converter does all layout work at
  build time; the loader on a 1 MHz CPU is a dumb RLE-unpack to screen.

The ledger (band cost is uncompressed, 9-row / 12-row; RLE applies on top):

| Target | Mode | Band (native px) | Color model | Cost 9/12 | Lives in | Terp |
|---|---|---|---|---|---|---|
| Amiga (OCS/ECS) | lowres 5 bitplanes | 320x72/96 | 32 of 4096 (4-bit guns) | 14.4K / 19.2K | chip RAM | Eris 1.0 |
| Atari ST(E) | low res 4 planes | 320x72/96 | 16 of 512 (STE: of 4096) | 11.5K / 15.4K | screen RAM | Eris 1.0 |
| DOS | VGA/MCGA mode 13h | 320x72/96 | 256 of 262144 (6-bit DAC) | 23.0K / 30.7K | VRAM | planned |
| C64 | multicolor bitmap | 160x72/96 (2:1 px) | fixed 16; 3 per 4x8 cell + 1 global | 3.6K / 4.8K | main RAM | planned |
| C128 (C64 mode) | as C64 | as C64 | as C64 | as C64 | as C64 | with C64 |
| C128 (VDC, optional) | 640x200 bitmap+attr | 640x72/96 (2x wide) | fixed 16 RGBI; 2 per 8x8 cell | 6.5K / 8.6K | 64K VDC VRAM | undecided |
| Plus/4 | TED hires bitmap | 320x72/96 | 121 (16 hue x 8 luma); 2 per 8x8 cell | 3.6K / 4.8K | main RAM | planned |
| CPC | Mode 0 | 160x72/96 (2:1 px) | 16 inks of 27; no cells | 5.8K / 7.7K | screen block | Haumea (wip) |
| MSX1 | Screen 2 | 256x72/96 | fixed 15; 2 per 8x1 octet | 4.6K / 6.1K | 16K VRAM (0 CPU RAM) | planned |
| MSX2 | Screen 5 | 256x72/96 | 16 of 512 (3:3:3); free pixels | 9.2K / 12.3K | 128K VRAM (0 CPU RAM) | planned |
| ZX Spectrum +3 | ULA screen | 256x72/96 | fixed 15; 2 per 8x8 cell, shared bright | 2.6K / 3.5K | screen at 0x4000 | planned |
| Atari 8-bit | ANTIC mode E + DLI | 160x72/96 (2:1 px) | 4 per scanline of 128 (per-line palettes) | 3.2K / 4.2K | main RAM | Varuna |
| Apple II | HGR (DHGR variant) | 280x72/96 | 6 artifact colors, 7px groups (DHGR: 16) | 2.9K / 3.8K | 8K hires page | planned |
| ZX Spectrum Next | Layer 2, 320-wide | 320x72/96 | 256 of 512 (RGB333), free pixels | full layer 80K | banked RAM | planned |
| MEGA65 | VIC-IV FCM, H320 | 320x72/96 | 255 of 16M, free pixels | 24.5K / 32.6K | chip RAM | planned |

Reading the ledger, the targets fall into three conversion classes:

- QUANTIZE class (no cell constraints): Amiga, ST, DOS, CPC, MSX2, Next,
  MEGA65. Palette selection and snapping to the machine's gun depth is the
  whole game. These are the easy seven.
- CELL class (attribute hardware, the real work): C64 (3+1 per cell),
  Spectrum +3 and C128 VDC (2 per cell), Plus/4 (2 per cell from 121,
  luma-first), MSX1 (2 per 8x1 octet). Per-cell color-set solving plus
  constraint-aware requantization. This is where the conversion
  intelligence earns its keep.
- SIGNAL class (one machine): Apple II, where color is an NTSC artifact of
  bit patterns and the converter models the signal (the ii-pix approach),
  with 7-pixel palette-bit groups in HGR.

Band width varies (160, 256, 280, 320): the geometry policy in section 4
handles it once, for all targets.

## 3. The format family: .arc files

One format family, one name: an `.arc` image (working name; the extension
per platform is in the naming table below). Per image id, per target, one
file, so a game disk for a machine carries exactly the pictures it shows
and nothing else. The modern `.arcres` (a zip of the master PNGs) remains
the interchange and Actaea format; retro targets get flat files because
retro file systems want flat files.

Design rules, from the ledger:

- A small fixed header: magic, format version, target tag, mode (9/12),
  native width and height, section count. Everything a loader needs to
  sanity-check before touching the screen.
- The payload is SECTIONS, each RLE-compressed separately: bitmap, then
  the per-cell matrices (screen RAM, color RAM, attributes, per-line
  palette tables) as the target needs, then the palette. Sections have
  different statistics; compressing them apart is worth real bytes, and
  loaders point different sections at different memory (the MSX streams
  both straight into VRAM; the C64 splits bitmap, screen, and color RAM).
- Section data is in NATIVE memory order (the rule above). The loader
  never reorders anything.
- Palettes are stored in NATIVE encoding: Amiga $0RGB words, ST 3-bit
  words (an optional STE block with 4-bit values), VGA 6-bit triples,
  MSX2 3:3:3 bytes, Next 9-bit pairs, MEGA65 nibble-swapped bytes. The
  loader writes them to the hardware verbatim.
- ONE shared RLE scheme (PackBits-shaped: literal runs and repeat runs,
  byte-oriented) across all targets, so the decoder is a few dozen bytes
  of 6502/Z80/68k and is written once per CPU, not once per machine.
- Fixed-palette machines (C64, Plus/4, MSX1, Spectrum) carry no palette
  section at all; their palette is the machine.

File naming must survive FAT 8.3, GEMDOS, CBM DOS, AMSDOS, MSX-DOS, and
ProDOS. Proposal: the basename is the decimal id, the extension is the
target tag (`8.C64`, `8.CPC`, `8.ZX3`, `8.MS1`, `8.AP2`, `8.AST`, `8.AMI`,
`8.DOS`, `8.A8`, `8.P4`, `8.NXT`, `8.M65`, `8.VDC`), with per-platform
adjustments where a filesystem demands them (CBM has no extensions proper;
the addendum defines `IMG8 C64`-style names there). Open decision 3.

## 4. arcimg 2.0: the conversion engine

The tool grows from three commands (prep, pack, info) into the pipeline:

    arcimg convert --target c64 masters/ out/     one target
    arcimg convert --all masters/ out/            every target
    arcimg targets                                the ledger, as a command
    arcimg lint --target zx3 hand/8.png           check a hand-painted native

Architecture: one shared front half, per-target back halves.

- THE MASTER (ruled): a band-shaped PNG, 320x72 or 320x96, matching the
  game's arc_mode; the author provides the right shape, exactly what the
  modern `.arcres` already holds. Master RICHNESS varies and the converter
  meets it where it is: the expected common denominator is ST-class art
  (16 colors, what Stefan himself will paint), while Amiga/DOS-class
  richer masters are welcome and convert downward with best effort. From
  a 16-color master the rich targets (DOS, Next, MEGA65) pass through
  near 1:1; nothing is ever upsampled.
- FRONT: load the master PNG, geometry (crop or scale the 320-wide master
  to 256/280/160 wide; center-crop is the default for narrower targets,
  per-image override available; halve horizontally for the wide-pixel
  modes, which is an exact 2:1 average), then into a perceptual space
  (linear RGB/Lab) for all color decisions. Never quantize in gamma sRGB.
- BACK, per class:
  - Quantize class: median-cut to the target's simultaneous-color budget,
    palette snapped to the gun depth BEFORE pixel mapping (4-bit Amiga,
    3-bit ST, 6-bit VGA, 3-bit MSX2/Next channels), then map.
  - Cell class: global/shared colors first (the C64 background, the TED
    globals), then a per-cell color-set solve (choose the cell's 2 or 3
    colors minimizing perceptual error over the cell), then requantize
    the cell's pixels against its own set. Luma-first for the Plus/4
    (dither in luminance, keep hue flat), per-8x1-octet pairs for MSX1,
    bright-constrained pairs for the Spectrum.
  - Signal class: Apple II via NTSC modeling (the ii-pix lineage), with
    the palette-bit group constraint driving a constraint-aware diffuser.
  - Atari 8-bit sits between classes: per-SCANLINE 4-color palettes from
    the 128-color hue/luma space, solved with vertical coherence so the
    palette does not shimmer, emitted as a small table a display-list
    interrupt replays. Cheap at runtime, a large fidelity win.
- DITHER POLICY: ordered (Bayer) by default everywhere. On cell hardware
  error diffusion bleeds across cell boundaries and destabilizes the
  per-cell solve; everywhere it damages RLE ratios (up to 2x). Error
  diffusion is an opt-in flag for the cell-free targets (CPC, MSX2), and
  no dithering at all is the default at 32+ colors (Amiga) and 256 (DOS,
  MEGA65).
- The reference corpus: the Rabenstein masters (320x96, painted, 12-15
  colors). Every back-end's output over the corpus is a golden test, and
  the corpus conversions are the acceptance gate Stefan reviews per
  target. Stefan's hand-painted per-machine Rabenstein art is the quality
  bar the converter is measured against.
- The MASTER SPEC, and an artist guide distilled from the research (value
  structure first, a deliberate palette of at most ~32 colors in 6-10 hue
  families, minimum feature size 2px, stepped shading rather than smooth
  gradients, quiet bottom rows where the text begins, compose so the top
  72px reads alone if the game ships arc_mode 9). One page in the docs;
  it is what makes one master serve fourteen machines.

Pillow is the image backend (the guided-install path from B11 stands);
everything else is stdlib.

## 5. The interpreter contract (the public blueprint)

One core contract, target-independent, published for the family and for
third parties (Vezza):

- Stamp Flags 1 bit 1 at boot (and after restart/restore) if and only if
  pictures can be shown.
- Implement EXT:0x80 `draw_image id mode`: no store, no branch; id 0
  clears the band; an unknown id or a missing asset is ignored silently
  (the game plays on, text-only for that room). mode is 9 or 12 and is
  authoritative for band height: the interpreter sizes the band as
  mode x 8 pixel rows and NEVER measures a picture to lay out the screen.
- The band occupies the top of the screen; the text area, status line
  included, lives below it. Both modes must work.
- An interpreter that does none of this remains correct: the unknown EXT
  opcode is skipped (Standard 14.2), the guard keeps it unreached anyway.
  Eris 1.0 already behaves exactly so (`op_ext: default: break`).

Per-target addenda (one per ledger row) specify: the video mode and the
split technique (raster IRQ on C64/TED, mode-and-ink split on CPC, display
list on Atari, Layer 2 clip on Next, FCM row split on MEGA65, plain bitmap
regions on Spectrum/MSX/Apple/16-bits), the asset lookup (file name pattern
on that platform's disk), the memory strategy (main RAM vs VRAM vs banked),
the decode loop sketch, and how text renders below the band on machines
where the interpreter draws its own font.

Eris is the REFERENCE IMPLEMENTATION of the contract: one new EXT case in
the core behind a `zio_draw_image(id, mode)` seam, two platform renderers
(Amiga planes + copper split palette, ST low-res planes), asset files on
the game disk via the existing disk builders. Eris is also the real-
hardware proving ground.

## 6. Verification: the probe harness

A blueprint is "proven" when its probe is green. Per target:

- A tiny NATIVE probe program (no Z-machine involved): load `8.C64` (etc.)
  from the emulated disk or injected memory, decode, display; once for
  mode 9, once for mode 12. The probe is written from the blueprint alone,
  which is precisely the test the blueprint must pass.
- A scripted emulator run drives it and captures a screenshot; the shot is
  compared against the converter's own rendering of the same file (the
  converter can render any .arc back to PNG for exactly this purpose, and
  that round-trip is also the unit test of the format).
- The bench: FS-UAE or vAmigaTS (Amiga), Hatari (ST), DOSBox-X (DOS),
  VICE x64sc/x128/xplus4 (CBM), Caprice/CPCEC (CPC), openMSX (MSX1/2),
  Fuse or ZEsarUX (+3), atari800 (A8), AppleWin-class (Apple II), CSpect
  or ZEsarUX (Next), Xemu (MEGA65).
- Eris goes further: the full end-to-end (interpreter, real z5, real
  disks, both platforms), verified in emulators by us and on real hardware
  by Stefan. That is the hand-off model from the project method, applied
  to B12.

## 7. Sub-milestones

Each lands with tests and a green done-test before the next (the standing
method). Naming: R for retro.

- R0. THIS DOCUMENT approved: the ledger, the format family, the geometry
  and dither policies, the wave order, the open decisions ruled.
  Done-test: Stefan's approval.
- R1. The format spec (exact header and section layout per target), the
  shared RLE codec (encoder in arcimg, reference decoder in C and in
  6502/Z80 pseudocode in the spec), arcimg's encode/render-back skeleton,
  and the golden corpus scaffold from the Rabenstein masters.
  Done-test: encode + render-back round-trips bit-exact on every target
  format, sizes recorded in the ledger.
- R2. WAVE 1, the quantize 16-bits, and the contract proven end to end:
  Amiga, ST, DOS converters and probes; the Eris reference implementation
  (core EXT case, zio_draw_image, two renderers, disk delivery); the
  first two per-target addenda written from the working code.
  Done-test: the Rabenstein demo z5 with converted art plays with
  pictures in Eris under FS-UAE and Hatari and text-only on Frotz
  unchanged; the DOS probe shows both modes in DOSBox-X; Stefan verifies
  Eris on real hardware.
- R3. WAVE 2, the cell class flagship: C64, ZX Spectrum +3, CPC.
  The per-cell solver framework, the three probes (VICE, Fuse, Caprice),
  the addenda (the CPC one feeds Haumea directly).
  Done-test: corpus conversions approved by Stefan per target; probes
  green both modes.
- R4. WAVE 3: Atari 8-bit (per-line palettes; Varuna gains the band as
  the second interpreter integration), MSX1, MSX2, Plus/4.
  Done-test: probes green; Varuna shows the band in atari800.
- R5. WAVE 4: Apple II (HGR, plus the DHGR variant), Spectrum Next,
  MEGA65; the C128 ruling executed (C64 asset reused in C64 mode; the
  VDC addendum written if ruled in).
  Done-test: probes green both modes on every remaining target.
- R6. Close: the public interpreter-contract document published (the
  Vezza-facing cut), arcimg 2.0 released (amalgam, README, versions),
  docs/00 and PROGRESS synced, the size ledger final.
  Done-test: a fresh reader can implement a target from the blueprints
  alone; B13 (the Rabenstein port) is unblocked.

Wave order rationale: Wave 1 proves the whole pipeline shape end to end on
machines where conversion is easy and an interpreter already exists, so
format or contract mistakes surface before the hard conversion work; Wave
2 is the conversion-intelligence proof on the three most iconic attribute
machines; the rest ride the established framework.

## 8. Ruled decisions (R0, 2026-07-07, Stefan)

1. WAVE ORDER: as proposed. Eris's 16-bit wave first, C64 in wave 2 (the
   target list in the request was unordered by intent; the order here is
   the order of work). The C64 gets the solver framework at full
   strength, not a rushed first cut.
2. DOS VIDEO TARGET: VGA/MCGA mode 13h only; no EGA or CGA variants
   (Infocom's own MCGA-only precedent).
3. FILE NAMING: the `<id>.<TAG>` scheme and the tag table in section 3.
4. THE MASTER'S SHAPE: band-shaped PNGs, 320x72 or 320x96, matching the
   game's arc_mode; the author provides the right shape ("it is not too
   much to ask"). Master richness varies; ST-class 16-color masters are
   the expected common denominator, richer masters convert with best
   effort (section 4).
5. C64 PALETTE DATA: Colodore, "for sure"; Pepto ships as data too.
6. C128: the C64 asset serves C64 mode; the native VDC blueprint IS
   written (wave 4) because C128 users find C64-mode-only disappointing,
   and whether it reaches an interpreter is decided there, not here.
7. ST TEXT COLORS: indices 0 and 15 reserved for the text area by
   contract. R2 verifies this against Eris's existing ST screen layer
   before the addendum is frozen (the contract must match what Eris 1.0
   already does, not fight it); Eris covers both Amiga and ST.
8. THE PUBLIC CONTRACT: this file grows the addenda; R6 cuts the
   standalone interpreter-facing document (docs/09) from it, so Vezza
   never needs to read Arcturus internals.

## 9. Boundaries

- GAME disk packaging stays out of scope (the standing non-goal): each
  interpreter ships its own disk builder, and arcimg only emits the
  per-target files. But PROBE disks are in scope, ruled so at R0: putting
  a converted image onto an emulated disk (or into an emulator's memory)
  and seeing it drawn in the right screen area IS this project's
  verification, and it cannot happen anywhere else. The harness therefore
  builds test disks and directories with the existing command-line
  builders in `~/FictionTools` on the Linux side (the `orb` OrbStack
  machine `debian`): dsktool (MSX), idsk (CPC and Spectrum +3), c1541 and
  cc1541 (CBM), mkatr (Atari 8-bit ATR), adf.py and gemdos.py (Eris's own
  Amiga and ST builders), plus nextraw and friends. Installing missing
  emulators for the bench is in scope too.
- The per-target INTERPRETERS themselves (beyond Eris and Varuna
  integration) are Stefan's builds on the blueprints; B12 delivers the
  blueprints proven by probes, not thirteen interpreters.
- Hand-authored per-machine art remains possible forever (the lint path);
  the converter must never be a ceiling, only a floor that removes eight
  months of pixel work.
