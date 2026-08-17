; probe.asm - the Spectrum Next arc_image probe (B12 R5, arc_image/reference/design.md sections 6 and 8)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Layer 2 in the 320x256 mode (Next core 3.0+), displaying the two
; embedded .arc images (mode 9, then mode 12 after a keypress): the
; reference Next loader for the format. Build (sjasmplus):
;
;   sjasmplus --sym=probe.sym probe.asm
;
; which SAVEBINs probe.bin ($C000, raw, code and both pairs inside the
; one 16K bank); mk_nex.py wraps it into a standard .nex (bank 0 only,
; PC $C000), loadable on ZEsarUX (TBBlue), CSpect, or real hardware
; from SD. run_probe.py executes the same binary headless first, on
; Haumea's simz80 core under a TBBlue port model, and proves the layer
; bytes, the palette, and the register writes against the pair files
; before any emulator is asked for its opinion.
;
; PLAIN Z80 ONLY, deliberately: no Z80N opcodes (no `nextreg`, no
; `mul`). Every NextReg access goes through the classic port pair
; ($243B select, $253B data), which real hardware honors identically,
; and which keeps the probe runnable on any Z80 core. The blueprint's
; loader needs nothing faster.
;
; WHY THE NEXT IS THE FRIENDLY ONE. The 320-mode layer is plain banked
; RAM laid out COLUMN-MAJOR (address = x*256 + y), and the .arc bitmap
; section is column-major by design (design.md: native memory order),
; so placing a column is one LDIR and there is no bit-shuffling at
; all. The hardware clip window (NextRegs $18/$1C) frames the band:
; nothing below it is ever painted, the fallback colour ($4A) shows
; instead, and the ULA is switched off entirely ($68 bit 7), so the
; probe owns a black screen without clearing a byte.
;
; Memory (standard post-boot map, the .nex loader's map): code and the
; embedded pairs live in 16K bank 0 at $C000-$FFFF, stack at $DFF0
; (below the bank's upper half, which is briefly remapped during the
; column copy); the staging buffer for a decoded section sits at
; $4000-$B7FF (banks 5 and 2, 30720 bytes at the mode-12 maximum),
; free because the ULA is off and nothing else runs; the palette
; section stages there too, after the bitmap has been placed. The
; column copy maps each 8K page of the
; layer (pages 16.., 16K bank 8 up, set via NextReg $12) into slot 7
; ($E000) with MMU reg $57, then restores page 1 so the next image's
; pair bytes above $E000 are visible again.
;
; The codec is LZSA2 (codec 2, docs/08 part B), decoder unlzsa2_fast
; (spke & uniabis, vendored beside this probe, unchanged), decoding
; into the flat staging buffer; back-references never cross a bank
; seam because staging is contiguous in the CPU map.
;
; .arc recap (design.md section 10, all words BIG-endian): 16-byte
; header (magic "ARCI", version, target, mode, section count at +7,
; width at +8, height at +10, id, codec, provenance), then 6-byte
; table entries (type, flags, uncompressed length, compressed length),
; then the LZSA2 streams in table order. The NXT payload:
;   type 1  bitmap   320xH bytes, column-major (for each x, the
;                    band's H bytes top to bottom): staged, then one
;                    LDIR per column into the layer
;   type 5  palette  256 two-byte entries in NextReg $44 order
;                    (RRRGGGBB, then the ninth bit B0): staged, then
;                    written through $40/$43/$44

TBSEL   equ $243B               ; NextReg select port
TBDAT   equ $253B               ; NextReg data port
L2PORT  equ $123B               ; Layer 2 access/visible port
STAGE   equ $4000               ; decoded-section staging (to $B7FF)

        DEVICE NOSLOT64K

        org $C000

start:  di
        ld sp, $BFF0            ; above staging, below the code
        call nextinit
        ld a, 2                 ; 9.NXT: bank 1 = 8K pages 2 and 3
        call mappair
        call show
        call waitkey
        ld a, 6                 ; 12.NXT: bank 3 = 8K pages 6 and 7
        call mappair
        call show
        call waitkey
        jp start                ; forever, the review cycle

; map a pair's two 8K pages (first page in A) at $0000-$3FFF
mappair:
        ld e, a
        push af
        ld a, $50
        call nreg
        pop af
        inc a
        ld e, a
        ld a, $51
        jp nreg

; show: decode and place the mapped .arc, then reveal.
show:   xor a                   ; Layer 2 invisible while working
        call l2vis
        ld hl, 0                ; the pair sits at the bottom of the map
        call draw
        ld a, (height)          ; clip the layer to the band: Y2 = H-1
        dec a
        ld e, a
        call clipband
        ld a, %00000010         ; Layer 2 visible: the reveal
        jp l2vis

; ---- Next registers ------------------------------------------------------

; write E to NextReg A (the classic port pair; no Z80N)
nreg:   ld bc, TBSEL
        out (c), a
        ld b, $25               ; bc = TBDAT
        out (c), e
        ret

nextinit:
        ld a, $68               ; ULA off: the probe owns the screen
        ld e, $80
        call nreg
        ld a, $4A               ; fallback colour black below the band
        ld e, 0
        call nreg
        ld a, $70               ; Layer 2 resolution: 320x256, 8bpp
        ld e, $10
        call nreg
        ld a, $12               ; the layer's first 16K bank: 8 (the
        ld e, 8                 ; default, stated rather than trusted)
        call nreg
        ld a, $16               ; scroll home
        ld e, 0
        call nreg
        ld a, $17
        ld e, 0
        call nreg
        ld e, 255               ; full-height clip until a band rules
clipband:                       ; E = Y2; X spans the whole 320 width
        ld a, $1C               ; reset the Layer 2 clip write index
        push de
        ld e, $01
        call nreg
        pop de
        ld a, $18               ; X1 = 0 (clip X is in pairs in 320 mode)
        push de
        ld e, 0
        call nreg
        ld e, 159               ; X2 = 159: all 320 pixels
        ld a, $18
        call nreg
        ld e, 0                 ; Y1 = 0
        ld a, $18
        call nreg
        pop de                  ; Y2 = the band's last row
        ld a, $18
        jp nreg

l2vis:  ld bc, L2PORT           ; A = $02 visible, $00 hidden
        out (c), a
        ret

; ---- waitkey: any key on the classic ULA matrix --------------------------

waitkey:
.up:    call anykey
        jr nz, .up
.down:  call anykey
        jr z, .down
        ret

anykey: ld bc, $00FE            ; B=0 selects every half-row at once
        in a, (c)
        cpl
        and $1F
        ret                     ; Z clear if any key is down

; ---- draw: the .arc at HL ------------------------------------------------

draw:   push hl
        pop ix                  ; ix = the .arc base
        ld a, (ix+0)            ; sanity: the magic
        cp 'A'
        ret nz
        ld a, (ix+1)
        cp 'R'
        ret nz
        ld a, (ix+6)            ; mode: 9 is the 72-row band, 12 is 96
        cp 12
        ld a, 96
        jr z, .h
        ld a, 72
.h:     ld (height), a
        ; the data cursor: base + 16 + count*6
        ld e, (ix+7)
        ld d, 0
        ld l, e
        ld h, d
        add hl, hl              ; *2
        add hl, de              ; *3
        add hl, hl              ; *6
        push ix
        pop de
        add hl, de
        ld de, 16
        add hl, de
        ld (cur), hl
        push ix
        pop hl
        ld de, 16
        add hl, de              ; hl = the section table
        ld b, (ix+7)            ; sections to walk
.each:  push bc
        push hl
        ld a, (hl)              ; type
        ld (styp), a
        ; stage: decompress the stream at (cur) to STAGE, then advance
        ; the cursor by the TABLE's compressed length: the decoder's
        ; exit registers are not part of its contract (the first build
        ; trusted HL and handed the palette decoder garbage)
        push hl
        ld hl, (cur)
        ld de, STAGE
        call DecompressLZSA2
        pop hl
        push hl
        inc hl
        inc hl
        inc hl
        inc hl
        ld d, (hl)              ; compressed length, big-endian
        inc hl
        ld e, (hl)
        ld hl, (cur)
        add hl, de
        ld (cur), hl
        pop hl
        ld a, (styp)
        cp 1
        jr nz, .notbmp
        call blit
        jr .next
.notbmp:
        cp 5
        jr nz, .next
        call setpal
.next:  pop hl
        ld de, 6
        add hl, de
        pop bc
        djnz .each
        ret

; ---- blit: staged columns into the layer through slot 7 ------------------
;
; The staged bitmap is 320 columns of H bytes. Layer memory is
; column-major with a 256-byte column stride, 32 columns per 8K page,
; ten pages for the 320. Page P of the layer is MMU page 16+P (16K
; bank 8 up); it is mapped at $E000 (MMU slot 7, NextReg $57), filled
; with its 32 columns, and the next page follows. Page 1 (bank 0
; upper) is restored at the end, so the pair data above $E000 comes
; back before the next image needs it.

blit:   ld hl, STAGE            ; the walking source
        ld a, 16                ; the layer's first 8K page
        ld (page), a
.page:  push hl                 ; map the page at $E000
        ld a, (page)
        ld e, a
        ld a, $57
        call nreg
        pop hl
        ld de, $E000            ; the page's first column
        ld b, 32                ; columns per page
.col:   push bc
        push de
        ld a, (height)          ; BC = the band's column height
        ld c, a
        ld b, 0
        ldir                    ; one column: the whole trick
        pop de
        inc d                   ; next column: stride 256
        pop bc
        djnz .col
        ld a, (page)
        inc a
        ld (page), a
        cp 16+10                ; ten pages = 320 columns
        jr c, .page
        ld a, $57               ; restore slot 7: MMU page 1
        ld e, 1
        jp nreg

; ---- setpal: the staged 512 bytes through $40/$43/$44 --------------------

setpal: ld a, $43               ; palette control: write Layer 2 first
        ld e, %00010000         ; palette, auto-increment on
        call nreg
        ld a, $40               ; start at entry 0
        ld e, 0
        call nreg
        ld hl, STAGE
        ld de, 512
.pal:   ld a, $44               ; two writes per entry, 9-bit
        push de
        ld e, (hl)
        call nreg
        pop de
        inc hl
        dec de
        ld a, d
        or e
        jr nz, .pal
        ret

; ---- state ---------------------------------------------------------------

cur:    dw 0                    ; the stream cursor
styp:   db 0
height: db 0
page:   db 0

        include "unlzsa2_fast.asm"

        SAVEBIN "probe.bin", start, $ - start
