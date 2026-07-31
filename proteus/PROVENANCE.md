# Proteus: provenance

Proteus is the Arcturus web interpreter: a trimmed, Z-machine-only fork
of Parchment with arc_image support, living inside the Arcturus
repository (no separate fork repo; Stefan's ruling, 2026-07-31). The
name follows the Solar System naming of the other interpreters.

Upstream sources, all MIT licensed, vendored at these commits:

- parchment 44a5596363249f52409cce365a7af9cda2df24d3
  https://github.com/curiousdannii/parchment
- asyncglk 9a805307c80bddc7e23bb99f27d5b861ff11582e
  https://github.com/curiousdannii/asyncglk
- ifvms.js 8b8804495b28bac0f54029011bdb90bc7c5d5f69
  https://github.com/curiousdannii/ifvms.js

Trimmed from upstream: the iplayif.com app, the Inform 7 packaging,
Glulx/TADS/Hugo/SCARE/AGT engines (emglken), quixe, glkote, test
suites, and all fonts except iosevka-extended.woff2 (the one the
single-file build inlines). src/common/zvm.js is restored from
parchment history (commit 977a6c9, where ZVM was still wired in).

Licenses: see LICENSE files under src/upstream/*, and upstream
copyright headers throughout. Do not remove them.
