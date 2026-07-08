# B12 R3 checkpoint (working note, delete at R3 close)

State 2026-07-08, evening; the durable truth is docs/08 (design record)
+ docs/09 (implementer book) + this delta.

DONE in R3 so far:
- Wave-2 converters (C64 multicolor solver, ZX solver, CPC mode-0
  quantize) through THREE review rounds from Stefan (the pixel artist).
  The third round rebuilt the Spectrum on the Polizei doctrine: nearest
  of the 15 real colors first (saturation-aware metric _dist_zx15, NO
  pre-curve), then legal same-bright pairs per cell, gentle 19/20 black
  preference. Judged against his hand-painted Spectrum Rabenstein
  (arc_image/Training/ZX Spectrum/).
- THE SALIENT RULING: optional .hint sidecar per master ({"salient":
  [[cx,cy,r],...]}); converters promote the disc's bright side to the
  palette top (C64 white moon, ZX two-white treatment). Auto-detection
  tried three ways and rejected; docs/08 records why. masters/8.hint is
  the first (the moon of picture 8, the standing complaint, now fixed).
- Codecs: ZX0 (codec 1) for the 8-bit cell targets; LZSA2 (codec 2,
  amendment ruling) for AMI/AST/DOS and later MS2/NXT/M65. lzsa binary
  packs (FictionTools via orb, $ARCIMG_LZSA, or PATH), arcimg's own
  lzsa2_decompress (spec-ported, corpus-verified) checks every pack and
  is the interpreters' executable spec (docs/09 part B).
- Regen loop: cmd_convert converts in a worker pool and skips current
  outputs (master/.hint/tool mtimes, make-style); the FULL six-target
  regen incl. stress now takes ~75 seconds (was ~35 minutes).
- All assets + previews regenerated: AMI 151K / AST 148K / DOS 128K
  (LZSA2) / C64 59K / ZX3 45K / CPC 79K corpus totals; stress pair and
  the mode-9 probe assets 90.* now exist for ALL six targets (90 = top
  72 rows of beach).
- arcimg 1.5.0, standalone rebuilt, README table bumped; suite 715.

THE CONVERSION GATE PASSED (2026-07-08, evening, rounds 4-7): C64 and
CPC carry Stefan's FULL APPROVAL (converters frozen). Spectrum ruled at
~90% with the ship framing: full confidence, except ZX results may want
minor author polish per image; the polish loop is `arcimg scr` /
`arcimg unscr` (band + black bar .scr round-trip, hand-authored flag in
header byte 15 that convert never overwrites). arcimg 1.6.0.

PENDING, in order:
1. Probes backport: wave-1 probes (dos/ast/ami) still decode RLE and
   predate the codec ruling; they need LZSA2 decompressors now (8086
   and 68000, adapt from the lzsa repository's permissively licensed
   asm), embed the regenerated 90/100 assets, rebuild, Stefan
   re-verifies in DOSBox-X/Hatari/FS-UAE (payload flags only; his
   configs rule the display).
2. R3 probes: C64 .prg (ACME on orb debian; VICE for launch, ask
   Stefan for path or install approval), ZX +3 and CPC as .sna
   snapshots (sjasmplus at ~/.local/bin/sjasmplus; ZEsarUX covers
   both, ASK STEFAN FOR ITS PATH at first launch, never screenshot).
   These decode ZX0: Z80 decoder ~70B (official), 6502 ~130B.
3. docs/09 chapters C.4 C64, C.5 ZX3, C.6 CPC from working probe code;
   Z80 + 6502 ZX0 decoder listings into part B.
4. R3 close: docs/08 milestone record, PROGRESS entry, delete this
   checkpoint file.

Per picture: ZX 2.1K, C64 2.8K, CPC 3.7K (ZX0); AMI 7.2K, AST 7.0K,
DOS 6.1K (LZSA2, ~5% over ZX0, 75x faster to pack; ruled worth it).
