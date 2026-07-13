# arc_image on retro systems (B12): charter, targets, and roadmap

Status: APPROVED 2026-07-07 (R0 complete; every open decision ruled by
Stefan the same day, rulings folded into section 8). This is the design
record for B12, the way actaea-design.md was for B10; it grows the format
spec and the per-target blueprints as they land.

This file lives with the working set (arc_image/reference/), not under
docs/: docs/ is the author- and implementer-facing shelf, and this is
the engine room. Authors read docs/07-arc-image.md; interpreter authors
read docs/08-arcimage-interpreters.md.

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

Lineage notes (Stefan, 2026-07-08, from the original Rabenstein ports):
MEGA65 uses the same IFF specifications as the Amiga, and the historical
MSX2 and Spectrum Next versions were ported FROM the Amiga graphics (the
Next with reduced width). MSX2 screen-model note for its chapter
(2026-07-10): Screen 5 is a true bitmap, so text renders into it like
DOS (the V9938's block-copy commands accelerate the font); its sixteen
on-screen colors come from ONE global 512-color palette shared by band
and text, so the CPC's per-region reload clause applies, executed more
cleanly through the V9938's line interrupt: art palette above the band
boundary, text palette below, per frame. MSX1 is the different machine
entirely: fixed 15, Screen 2 cell constraints, pattern-based text, no
line interrupt and none needed. So the three remaining quantize-class targets
are small deltas on the wave-1 Amiga recipe: same palette selection,
their own gun snap and layout. They also share the Amiga's disk-room
class, which is why the codec ruling groups them under LZSA2. They sit
in wave 3 not for difficulty but because wave order was ruled
Amiga/ST/DOS first, then the cell class led by the C64; the quantize
stragglers follow the cell work because the cell solvers were the open
research and these three are recipe application.

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
  per-image override available). AMENDED 2026-07-13: on the 8-bit path
  the width halving is NOT an average (averaging manufactures blend
  colors); pairs collapse by agreement, disagreement resolved by global
  frequency. The original perceptual-space clause ("never quantize in
  gamma sRGB") was never implemented, and Pixel Polizei's attested
  results use plain RGB distance on flat input; the clause is retired
  for the flat-base path and stands only as an option for the
  master-to-base ink selection if a future corpus demands it.
- BACK, in two families (AMENDED per Stefan's flat-base ruling,
  2026-07-13, which superseded the original cell-class machinery after
  the A8 rounds proved it wrong at the root):
  - Quantize class (the 16-bit trio, MSX2, Next, MEGA65): median-cut to
    the target's simultaneous-color budget, palette snapped to the gun
    depth BEFORE pixel mapping (4-bit Amiga, 3-bit ST, 6-bit VGA, 3-bit
    MSX2/Next channels), then map. Unchanged: approved in wave 1, and
    conversion there is near-lossless.
  - THE C64, by Pixel Polizei's recipe (Markku Reunanen, WTFPL; source
    kept uncommitted at arc_image/reference/ppolizei/), DIRECT from the
    master: every pixel maps plainly to Colodore (width halving
    collapses pairs by agreement, never an average), the background is
    elected by clashing blocks only, a clashing block keeps its three
    most frequent colors plus background. Then THE SPICE (the dither
    ruling, gate-approved on the beach): flat conversion first, then
    in-cell dither against the master reference, firing ONLY at smooth
    seams where the master sits in the 0.40..0.50 midband between the
    cell's two nearest allowed colors, the strip where flat mapping
    hard-switches sides. Sprinkle at seams, replace color flat
    everywhere else; hinted discs stay solid. A ONE-DAY DETOUR is on
    record and retired: an intermediate "flat base" on the CPC cube
    greyed every soft master color (the 27-cube has no dark purple);
    Polizei converts each machine from the source and so do we.
  - THE C64 CONVERSION IS THE BASE of the whole deriving 8-bit family
    (Stefan's ruling, asked twice), dither included, so nothing is
    ever dithered twice. THE DE-GREY rides every derivation: the C64's
    five-grey ramp is a Colodore idiom its muted palette absorbs, so a
    sibling re-reads each grey C64 pixel through the MASTER's hue
    (chromatic master, chromatic sibling pixel; true neutrals stay
    grey; salient-forced discs exempt, their promotion is deliberately
    anti-master). A hand-authored .C64 (the polish loop) is the source
    of the family when present (no de-grey then; no master to read).
  - The CPC derives by RECOLOR: the C64's pixels verbatim, each
    Colodore color to its nearest cube ink, greys re-read directly in
    CUBE space (Colodore's sixteen collapsed the grey-partnered dither
    weave; the cube's in-between shades keep the shimmer alive), the
    grey-axis ban inside the lookup (a chromatic pixel never lands on
    mid-grey or white; black stays legal, darkness is achromatic),
    sixteen most frequent inks, stragglers to nearest kept.
  - The Atari 8-bit derives by SEGMENT SOLVE: Colodore maps onto GTIA
    through a frozen injective 16-entry table, the C64's 8-line cell
    rhythm is the segment grid, and a dynamic program allocates the
    four per-line registers per segment (the table a display-list
    interrupt replays). The pick carries the DEFENSES, priced inside
    the optimizer so boundaries account for them: the brightest real
    color claims a register when every pick is far darker (the
    swallowed sun), the darkest anchors likewise (the stones' shadow
    mass), a defense's victim is a neutral before a chromatic (one
    grey suffices in four), and the remap metric is symmetric on
    chroma (losing saturation costs, gaining costs too: grey rock
    goes to black, never to sea-blue). Dropped colors remap flat; the
    A8 inherits the C64's dither and adds none (a per-band weave
    collapses where a strand's color lost its register: the band
    limit, accepted at the gate). Per-hue luma refinement stays
    staged. Plus/4 and MSX1 decide their source at their own rounds.
  - Signal class: Apple II via NTSC modeling (the ii-pix lineage), with
    the palette-bit group constraint driving a constraint-aware diffuser
    (wave 4; expected to consume the flat base as well, ruled at its own
    machine round).
- DITHER POLICY (amended with the flat base): NONE on the 8-bit path,
  the Polizei manner; an author who wants dither paints it (the polish
  loops). The quantize class keeps the wave-1 policy: ordered (Bayer)
  for gradient masters, scaled to the budget, error diffusion opt-in
  (CPC's flag retired with its converter), nothing at 32+ colors.
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

The interpreters implement the contract INDEPENDENTLY, after B12 is done:
Stefan builds each on the blueprints alone and comes back only if probing
left an issue undiscovered. B12 itself never patches an interpreter; its
proof is the probes (section 6). For the record, the Eris sketch is one
new EXT case in the core behind a `zio_draw_image(id, mode)` seam and two
platform renderers (Amiga planes with a copper palette split, ST low-res
planes), with the asset files delivered by its own disk builders; that
work belongs to Eris, on its own schedule, and real hardware is its
proving ground then.

## 6. Verification: the probe harness

A blueprint is "proven" when its probe is green. Per target:

- A tiny NATIVE probe program (no Z-machine involved): load `8.C64` (etc.)
  from the emulated disk or injected memory, decode, display; once for
  mode 9, once for mode 12. The probe is written from the blueprint alone,
  which is precisely the test the blueprint must pass.
- The emulator is launched with the probe FOR Stefan, and the visual
  verdict is his: no screenshot automation anywhere in the harness (if
  something looks off, Stefan supplies the screenshot). The mechanical
  side of verification is the converter's render-back: arcimg renders any
  .arc back to PNG, and that encode/render round-trip is the unit test of
  the format, run in pytest long before an emulator is opened.
- The bench runs on the macOS side: FS-UAE (Amiga), Hatari (ST),
  DOSBox-X (DOS), VICE x64sc/x128/xplus4 (CBM), ZEsarUX for BOTH the
  Spectrum +3 and the CPC (Stefan's ruling: no Caprice) and for the
  Next, openMSX (MSX1/2), atari800 (A8), AppleWin-class (Apple II),
  Xemu (MEGA65). Several are already installed; each target's probe work
  starts by checking which, rather than installing duplicates.
- Interpreter integration is deliberately NOT part of the harness: the
  probes prove the blueprint, and the interpreters (Eris first) implement
  it independently once B12 is done, returning here only if a probe
  missed something. The end-to-end on real hardware is that later step's
  proof, not this milestone's.

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
- R2 (COMPLETE, 2026-07-08). WAVE 1, the quantize 16-bits: Amiga, ST,
  and DOS converters and probes, and the per-target chapters in docs/08
  written from the working probe code. No interpreter was touched: the
  probes are the proof.
  Done-test PASSED: the corpus (21 masters, bit-exact on AST/DOS,
  snap-only on AMI) and the stresstest pair approved by Stefan, with two
  taste rulings folded in (dither halved, Bayer 8x8); all three probes
  verified by Stefan in both modes (DOSBox-X, Hatari, FS-UAE). Findings
  that became contract: square-pixel presentation on DOS, the text-color
  palette contract on both 68k machines, the Z-machine colours clause,
  and the copper per-frame restore.
- R3. WAVE 2, the cell class flagship: C64, ZX Spectrum +3, CPC.
  COMPLETE 2026-07-10. The per-cell solver framework landed and was
  refined through seven review rounds with Stefan's pixel-artist eye
  and his hand-painted Spectrum art as training data; the conversion
  gate passed 2026-07-08 (C64 and CPC with full approval, converters
  frozen; the Spectrum at the ~90% framing with the scr polish loop).
  The codec era arrived mid-milestone: ZX0 for the 8-bit targets,
  LZSA2 for the 16-bit trio (with arcimg's built-in pure-Python packer
  as the no-binary default), and the wave-1 probes were backported and
  re-verified. All three wave-2 probes are proven and verified by
  Stefan both modes (VICE x64sc for the C64; ZEsarUX for the +3 via
  ZRCP injection and for the CPC likewise, ZEsarUX having no CPC
  snapshot support). Chapters C.4-C.6 carry the blueprints and the
  paid-for lessons: the type-4 attribute number, the stack and
  machine-identity snapshot traps, the 27-cube ink indexing against
  the firmware-numbering trap, CRTC ownership, and the CPC
  split-screen clause that feeds Haumea directly. Per picture on the
  corpus: C64 2.8K, ZX3 2.1K, CPC 3.7K (ZX0); AMI 7.2K, AST 7.0K, DOS
  6.1K (LZSA2).
- R4. WAVE 3: Atari 8-bit (the per-line palette solver), MSX1, MSX2,
  Plus/4.
  Done-test: corpus conversions approved; probes green in atari800,
  openMSX, and xplus4, both modes.
- R5. WAVE 4: Apple II (HGR, plus the DHGR variant), Spectrum Next,
  MEGA65; the C128 ruling executed (C64 asset reused in C64 mode; the
  VDC addendum written if ruled in).
  Done-test: probes green both modes on every remaining target.
- R6. Close: the public interpreter-contract document published (the
  Vezza-facing cut), arcimg 2.0 released (amalgam, README, versions),
  docs/00 and PROGRESS synced, the size ledger final.
  The handover is DOCUMENTS AND CONTENT (Stefan's ruling): docs/08 plus,
  per target, the probe source as reference loader code, the two-mode
  .arc test assets (the beach pair is the standard set), and the arcimg
  standalone for converting art and for rendering any .arc back to PNG
  as ground truth. An implementer, whether a fresh session in an
  interpreter repo or a third party, starts with working pictures on day
  one and never reads Arcturus internals.
  Done-test: a fresh reader can implement a target from the blueprints
  alone; B13 (the Rabenstein port) is unblocked.

Wave order rationale: Wave 1 proves the whole pipeline shape (convert,
encode, disk, probe, addendum) on the machines where conversion is easy,
so format or contract mistakes surface before the hard conversion work;
Wave 2 is the conversion-intelligence proof on the three most iconic
attribute machines; the rest ride the established framework. The
playground for all of it is the repo's `arc_image/` directory (the
Rabenstein working set: the masters under `arc_image/rabenstein/images/`,
per-target conversions landing beside them).

## 8a. Amendments (R4, 2026-07-13, Stefan)

- THE POLIZEI ARCHITECTURE (section 4) supersedes the per-machine
  taste machinery for the whole 8-bit family: each machine direct from
  the master by Polizei's recipes, and the C64 conversion is the base
  of the deriving siblings (A8 first). Blessed after five A8 rounds
  and the re-found truth of the historical workflow: Dylan Barry's CPC
  originals through Pixel Polizei made the ports Stefan rates highest;
  the master stays the only author-facing input. (A same-day detour
  through a CPC-cube intermediate greyed the corpus and is retired;
  the grey-sky mystery traced to that cube's missing dark purple.)
- C64 PALETTE: Colodore REAFFIRMED for conversion and render after a
  one-day Pepto experiment (Pepto holds no teal and no hot pink; the
  Colodore corpus read genuinely well; the real-hardware verdict is
  the probe's). Pepto ships as data, as Polizei carries it.
- PIXEL POLIZEI REFERENCE: the WTFPL source is kept UNCOMMITTED at
  arc_image/reference/ppolizei/ (gitignored), the reference for every
  machine not yet implemented.
- HAND-POLISH INHERITANCE: a hand-authored .C64 is the source of the
  whole 8-bit family's conversions when present (arcimg convert --c64).
- RE-GATE: C64, CPC, and A8 rebuilt on the new architecture await
  Stefan's corpus review; the Spectrum keeps its R3 solver (already
  Polizei-shaped, and geometrically it cannot consume the 160-wide
  base) pending the same review.

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
8. THE PUBLIC CONTRACT: docs/08-arcimage-interpreters.md is the
   implementer's book, live from wave 1 (amended from "cut it at R6" by
   Stefan's ruling to write each chapter while its probe is fresh): part
   A the contract, part B the format with reference decoders, part C one
   chapter per proven target. Vezza and the interpreter sessions read
   docs/08 and the probe sources, never Arcturus internals; R6 only
   finalizes and publishes.

## 9. Boundaries

- GAME disk packaging stays out of scope (the standing non-goal): each
  interpreter ships its own disk builder, and arcimg only emits the
  per-target files. But PROBE disks are in scope, ruled so at R0: putting
  a converted image onto an emulated disk (or into an emulator's memory)
  and seeing it drawn in the right screen area IS this project's
  verification, and it cannot happen anywhere else. Tooling geography:
  `~/FictionTools` on the Linux side (the `orb` OrbStack machine
  `debian`) is the Puny BuildTools REFERENCE repository, the one every
  other BuildTools inherits from; it is at hand for its command-line
  builders (dsktool for MSX, idsk for CPC and Spectrum +3, mkatr for
  Atari 8-bit, adf.py and gemdos.py, Eris's own Amiga and ST builders,
  nextraw and friends) but it is not this project's workbench and is
  never modified from here. Builders it does not cover for our probes
  (the Commodore family among them) are installed on the macOS side
  (VICE brings c1541 alongside its emulators). Installing missing
  emulators for the bench is in scope. Practical note: inside the orb
  shell the Mac filesystem is reachable by absolute path
  (/Users/stefan/Fiction/...), while ~ is the Linux home until exit.
- The per-target INTERPRETERS themselves (beyond Eris and Varuna
  integration) are Stefan's builds on the blueprints; B12 delivers the
  blueprints proven by probes, not thirteen interpreters.
- Hand-authored per-machine art remains possible forever (the lint path);
  the converter must never be a ceiling, only a floor that removes eight
  months of pixel work.

## 10. The .arc container, version 1 (R1)

Everything is BIG-ENDIAN (the Z-machine convention; the family reads
Z-machine files already, and the 68k targets agree).

HEADER, 16 bytes:

    offset  size  field
    0       4     magic "ARCI"
    4       1     container version (1)
    5       1     target id (the table below)
    6       1     mode (9 or 12; the band height in text rows)
    7       1     section count
    8       2     native width in pixels
    10      2     native height in pixels (mode x 8, or the target's
                  equivalent under its own pixel geometry)
    12      2     image id (the arc_image resource slot, a sanity check
                  against the filename)
    14      2     reserved, 0

SECTION TABLE, 6 bytes per section, immediately after the header:

    0       1     section type
    1       1     flags (0 unless a target addendum defines bits)
    2       2     uncompressed length in bytes
    4       2     compressed length in bytes (including the end sentinel)

Section data streams follow, in table order, each RLE-compressed
separately. Section types: 1 bitmap, 2 screen (a per-cell matrix of
color nibbles: the C64 screen RAM, the TED color matrix, the MSX1 color
table), 3 color (a second per-cell matrix: C64 color RAM, TED luminance),
4 attributes (one attribute byte per cell: Spectrum, VDC), 5 palette
(native hardware encoding), 6 linetable (per-scanline register values:
Atari 8-bit), 7 registers (a handful of global hardware values: the C64
background, the TED globals, the CPC border).

THE RLE SCHEME, shared by every target (PackBits-shaped, byte-oriented,
chosen so the decoder is a few dozen bytes on a 6502 or Z80):

    control c = 0x00..0x7F   literal: copy the next c+1 bytes
    control c = 0x81..0xFF   run: repeat the next byte 257-c times (2..128)
    control c = 0x80         end of section

The uncompressed length in the table is authoritative; the 0x80 sentinel
lets a streaming loader run without tracking it. The encoder never emits
a run shorter than 3 (a 2-run is cheaper as literal content).

TARGET TABLE (id, tag, native band geometry at mode 9 / 12, sections in
payload order):

    id  tag  geometry              sections
    1   AMI  320x72 / 320x96       bitmap, palette
    2   AST  320x72 / 320x96       bitmap, palette
    3   DOS  320x72 / 320x96       bitmap, palette
    4   C64  160x72 / 160x96       bitmap, screen, color, registers
    5   P4   320x72 / 320x96       bitmap, screen, color, registers
    6   CPC  160x72 / 160x96       bitmap, palette, registers
    7   MS1  256x72 / 256x96       bitmap, color
    8   MS2  256x72 / 256x96       bitmap, palette
    9   ZX3  256x72 / 256x96       bitmap, attributes
    10  A8   160x72 / 160x96       bitmap, linetable
    11  AP2  280x72 / 280x96       bitmap
    12  NXT  320x72 / 320x96       bitmap, palette
    13  M65  320x72 / 320x96       bitmap, palette
    14  VDC  640x72 / 640x96       bitmap, attributes

PAYLOAD LAYOUTS, per target (native memory order; the loader never
reorders; the full loader detail lives in each wave's addendum):

- AMI: bitmap is 5 bitplanes, row-interleaved ILBM-style (row of plane
  0, row of plane 1, ..., 40 bytes each); palette is 32 words of $0RGB.
- AST: bitmap is the ST's fixed word interleave (per 16-pixel group, 4
  consecutive words hold planes 0..3; 160 bytes per row); palette is 16
  words in STF format (3 bits per gun; an STE palette block may follow
  as a second palette section with flags bit 0 set, 4 bits per gun).
- DOS: bitmap is chunky, one byte per pixel, row-major; palette is 256
  triples of 6-bit DAC values.
- C64: multicolor bitmap in the VIC's cell order (per cell row: 40 cells
  of 8 bytes, each byte four 2-bit pixels); screen is one byte per cell
  (the two per-cell color nibbles), row-major cells; color is one byte
  per cell (color RAM nibble); registers is [background $D021].
- P4: TED hires bitmap in cell order (like the C64 hires layout); screen
  is the color matrix (two hue nibbles per cell), color is the luminance
  matrix (two luma nibbles per cell); registers is [$FF15, $FF16] when
  the image is multicolor, empty for hires.
- CPC: Mode 0 bytes with the hardware pixel-bit shuffle already applied,
  lines in ascending screen-block address order (the eight 0x800
  sub-blocks, band rows only: eight contiguous runs); palette is 16
  hardware ink numbers (0..26); registers is [border ink].
- MS1: bitmap is the Screen 2 pattern table for the band's tiles (8
  bytes per 8x8 tile, tiles in name order); color is the matching color
  table (same shape, one fg/bg byte per pattern byte). The name table is
  implicit (identity); the loader writes it.
- MS2: bitmap is Screen 5 nibble-packed pixels, 128 bytes per line,
  linear; palette is 16 V9938 palette-register pairs.
- ZX3: bitmap is the ULA's interleaved-thirds layout restricted to the
  band's rows, in ascending screen address order; attributes is one byte
  per 8x8 cell, row-major.
- A8: bitmap is ANTIC mode E, 40 bytes per line, linear; linetable is 4
  bytes per band line (COLBK, COLPF0, COLPF1, COLPF2 in GTIA hue<<4|luma
  form), replayed by the display-list interrupt.
- AP2: bitmap is HGR bytes (7 pixels plus the palette bit per byte), 40
  bytes per line, in DISPLAY row order top to bottom; the loader places
  rows via the standard hi-res line-address table (the one documented
  exception to dumb linear unpacking; a DHGR variant lands with wave 4).
- NXT: bitmap is Layer 2 320-mode column-major (for each x, the band's
  bytes top to bottom); palette is 256 two-byte 9-bit entries in
  NextReg 0x44 order.
- M65: bitmap is FCM characters, 64 bytes each, in reading order; the
  screen and color RAM rows are formulaic (consecutive char indices) and
  the loader generates them; palette is 255 nibble-swapped RGB triples
  (index 255 is reserved by the hardware's alpha path).
- VDC: bitmap is 1bpp, 80 bytes per row, linear; attributes is one byte
  per 8x8 cell (fg nibble, bg nibble), row-major, 80 per cell row.

arcimg is the only writer of this format; the loaders are its readers.
arcimg can also RENDER any .arc back to a PNG through the target's
reference palette, which is both the format's unit test (encode, decode,
render, compare) and the preview an author sees without an emulator.

R1 status: implemented in arcimg 1.1.0 (`arcimg targets`, `arcimg render`,
and the codec and layout machinery behind them), with the pack/unpack
round trip proven bit-exact for all fourteen targets in both modes and
the golden corpus in place (tests/test_arcformat.py). Compressed-size
entries join the ledger per wave, when real conversions of the corpus
exist to measure; the render previews of the wave-less targets use
serviceable reference palettes that each wave's addendum freezes against
measured values (TED, GTIA, and the Apple II artifact model are the
marked approximations).

WAVE 1 SIZES (R2; the 21-picture Rabenstein corpus, mode 12, RLE'd):
AMI 217,025 bytes total (10.3K average against 19.2K uncompressed), AST
249,035 (11.9K against 15.4K; the ST word interleave breaks runs, so it
compresses the worst of the three), DOS 313,149 (14.9K against 30.7K).
Conversion fidelity over the corpus: AST and DOS are BIT-EXACT (the
masters sit on the 3-bit and 6-bit gun grids; Stefan painted them in
ST-class color), AMI differs only by the unavoidable 4-bit gun snap
(under 8 per channel, invisible). The ST text contract shipped as ruling
7's guarantee clause rather than the reservation: art takes all 16
entries, sorted darkest-first, entry 0 is the text paper and entry 15
the ink, and the converter re-quantizes to 15 plus white only when the
art carries no readable light color, so a 16-color master loses nothing.
THE CODEC RULING (R3, 2026-07-08): ZX0 replaces RLE as the default .arc
codec (header byte 14; RLE remains codec 0). The bake-off over the
corpus sections, per picture: C64 3602 RLE -> 2779 ZX0, ZX3 2778 ->
1865, CPC 6024 -> 3663, AMI 11013 -> 6796, AST 11830 -> 6596, DOS 14883
-> 5743; Exomizer wins only marginally (and clearly only on DOS, the
machine that least cares), LZSA2 sits between. ZX0's decompressors are
the smallest of the field (~70 bytes of Z80). arcimg carries a pure
Python port of the reference optimizer/compressor, validated
byte-identical against the reference tool in quick mode (the 2176-byte
window, 0-2% off the full window, an order of magnitude faster to pack).

THE CODEC RULING, AMENDED (R3, 2026-07-08, Stefan): the 16-bit big-disk
targets (AMI, AST, DOS, and later MS2, NXT, M65) take LZSA2 as codec 2
instead of ZX0. Measured on the corpus: LZSA2 is ~5% larger than ZX0
(406,004 vs 425,301 bytes over the three targets, roughly 300 bytes per
picture) but packs 75x faster (ZX0's optimal parse in Python took 1486s
for the corpus, the native lzsa tool 20s) and decompresses faster on
68000/8086. Those machines have disk room to spare while a z5 story
caps at 256K; author regeneration time is what actually hurts. The
8-bit cell targets keep ZX0: their pictures share a floppy with the
story, and the tiny decoder matters there. Each target chapter of
docs/08 mandates exactly one codec, so no interpreter ever carries two.
arcimg packs LZSA2 through Emmanuel Marty's lzsa tool when one is
found ($ARCIMG_LZSA first, then PATH), and otherwise through its own
built-in pure-Python greedy packer (ruled 2026-07-09): arcimg never
NEEDS an external binary, matching the BuildTools 4.0 doctrine (Python
only, no Linux dependency, every Trans-Neptunian disk builder
self-contained). The built-in parse is about 8% larger than the tool's
optimal parse on the corpus and runs in seconds; the trade an author
should know: with the tool on PATH the assets pack smaller, but two
machines only produce byte-identical assets when both have the same
lzsa (or neither has one). Every pack, from either packer, is verified
against arcimg's own pure-Python decoder, which is ported from
BlockFormat_LZSA2.md and validated byte-identical on the full corpus;
that decoder is the executable spec for the interpreter side. Also in the amendment, the
regeneration loop itself: `arcimg convert` now converts pictures in a
worker pool and skips outputs that are newer than their master, its
.hint sidecar, and the tool (make-style), so a corpus regen is minutes
and an incremental one is seconds.

THE SALIENT RULING (R3, 2026-07-08): a master may carry an optional
sidecar, `8.png` beside `8.hint`, a one-line JSON file of the form
{"salient": [[cx, cy, r], ...]} naming bright discs (a moon, a sun) in
master pixel coordinates. Converters whose palette cannot hold the disc
apart from its sky promote the disc's bright side to the palette's top
entry, solid, no dither: the C64's white disc against the green night
sky, the Spectrum's white moon (normal white beside a colored sky,
bright white against black trees, so no glowing attribute box forms).
Fully automatic detection was built three ways (threshold blobs, Hough
circles, disc templates) and rejected: on pixel-art masters the clouds
share the moon's colors and the trees occlude its shape, so every
detector either misses the real moon or fires on junk. The author
states the intent once, in seconds, and all fourteen targets benefit;
this is the same author-in-charge philosophy as Pixel Polizei's
check-and-comply loop. Occlusion is handled inside the disc: only the
bright side of the hinted circle is promoted, CONNECTED FROM THE CROWN
(the region reachable from the disc's topmost bright row), so trees in
front of the moon stay trees and bright foreground pixels inside a low
moon's circle (path glints, water) do not mirror a second half-disc
into the ground.

WAVE 2 SIZES (R3, converter stage; the corpus, mode 12, RLE'd):
C64 76,554 bytes total (3.6K average against 4.8K uncompressed), ZX3
65,535 (3.1K against 3.5K), CPC 127,218 (6.1K against 7.7K). The cell
solvers: C64 elects its global background by total remap cost and keeps
each cell's three most frequent colors; the CPC, whose 27-cube has no
muted colors at all, picks its 16 inks directly from the 27 by greedy
error minimization (no cluster middleman to collapse; the earlier
median-cut-then-snap route left a gradient master six inks and a grey
mess) with a chroma-dumping penalty, because by plain distance a dusty
mauve sky IS closest to grey while an artist keeps the hue family and
accepts rose; gradients mix gently (color first, dither as seasoning).

THE SPECTRUM DOCTRINE (R3, 2026-07-08, revised same day on Stefan's
critique with the master references: his own Spectrum Rabenstein in
arc_image/Training, Vanja Utne's Hibernated 1, Rail/Slave's Eight Feet
Under, Shawn G. McClure's Hibernated 2): BRIGHT IS THE CANVAS. Those
pictures live almost entirely in black plus the seven bright colors;
the dark level appears rarely and deliberately, as regional shadowing,
never as a nearest-color accident. The pipeline: downsample every pixel
to its nearest of the fifteen real colors (saturation-aware metric, no
pre-curves), resolve each 8x8 cell to a legal same-bright pair by remap
error with a gentle 19/20 black-pair preference, and render the cell
BRIGHT unless (a) the dark pair actually uses normal white D7, the
Spectrum's only grey, which stonework dissolves without, (b) the cell
is not cloud-white (whites follow their sky), and (c) the dark fit is
decisively better (0.55). A coherence pass then settles stragglers to
their neighborhood's level. Treating dark and bright hues as fifteen
equal citizens was the earlier mistake: dark cells scattered
everywhere, and every boundary between the levels clashed around
rounded shapes. Dark-ish master content renders as black paper with
bright ink, which IS the school; the graveyard statue keeps its grey.
The pivot pair (from studying img2spec at Stefan's pointer) joins the
per-cell candidates: split the cell at its median luminance, average
each side, snap each average to the half's palette; structure catches
what frequency projection misses.

THE SPECTRUM FRAMING (R3, 2026-07-08, Stefan): C64 and CPC conversions
carry full approval and their converters are frozen; the tool speaks of
its conversions with full confidence, EXCEPT that Spectrum results,
depending on the image, may want minor author polish (his estimate:
90% there, and genuinely good conversions already). The polish loop is
first-class: `arcimg scr` writes any ZX3 conversion as a standard
6912-byte .scr, the band on top and a black bar below so editors get
the full 256x192 frame; the author fixes cells in any Spectrum tool
(SevenuP, img2spec); `arcimg unscr` takes the file back, strips the
bar, lints it (FLASH refused, content below the band reported), and
returns it to the portfolio as <id>.ZX3 stamped hand-authored (header
byte 15 = 1), which `arcimg convert` thereafter refuses to overwrite,
force or not; delete the file to reconvert. Loaders ignore byte 15.

The playground carries the outputs (arc_image/ami, ast, dos; previews
beside them), all regenerable with `arcimg convert` and gitignored as
derived artifacts; the masters are the tracked truth.
