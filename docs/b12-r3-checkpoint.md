# B12 R3 checkpoint (working note, delete at R3 close)

State 2026-07-08, written before a context compaction; the durable truth
is docs/08 (design record) + docs/09 (implementer book) + this delta.

DONE in R3 so far:
- Wave-2 converters (C64 multicolor solver, ZX 2-per-cell solver, CPC
  mode-0 quantize) with two review rounds from Stefan (the pixel artist):
  luminance-dominant matching, saturation term for ZX pastels, greedy
  error-min cell colors, _protect_extremes for suns/moons, conditional
  night-only ZX pre-curve, dither amp CPC 8 / ZX pair-mix 16/28.
- ZX0 ruled and shipped as the .arc codec (byte 14; RLE stays codec 0):
  pure-Python reference-faithful packer in arcimg (quick window 2176),
  byte-identical vs reference tool; bake-off table in docs/08.
- Training corpus: arc_image/training/ZX Spectrum/ (Stefan's art).

PENDING, in order:
1. Asset regen (ZX0 + trained converters): AMI, ZX3 done; AST/DOS/C64/CPC
   in a background job at checkpoint time. Command lives in the shell
   history; rerunning the per-target loop is idempotent.
2. Probes backport: wave-1 probes (dos/ast/ami) still decode RLE. Write
   ZX0 decompressors (x86 for probe.asm, 68k for probe.s/payload.s,
   modeled on dzx0; the backtrack bit and the dbra trap are documented in
   docs/09 part B), embed regenerated 90/100 assets, rebuild, and Stefan
   re-verifies in DOSBox-X/Hatari/FS-UAE (launch with payload flags only;
   his configs rule the display).
3. Stefan's viewing pass of arc_image/previews (all six targets), the R3
   conversion gate.
4. R3 probes: C64 .prg (ACME on orb debian; VICE for launch, likely needs
   install approval or path from Stefan), ZX +3 and CPC as crafted .sna
   snapshots (sjasmplus at ~/.local/bin/sjasmplus; ZEsarUX covers both,
   ASK STEFAN FOR ITS PATH at first launch, never screenshot, he
   verifies visually).
5. docs/09 chapters C.4 C64, C.5 ZX3, C.6 CPC from working probe code;
   6502 + Z80 ZX0 decoders into part B references.
6. R3 close: docs/08 milestone record, PROGRESS entry, ledger sizes final
   (ZX0 numbers), delete this checkpoint file.

Sizes with ZX0 (docs/08 has the full table): ZX 1.9K, C64 2.8K, CPC 3.7K,
AMI 6.9K, AST 6.6K, DOS 5.7K per picture on the 21-master corpus.
