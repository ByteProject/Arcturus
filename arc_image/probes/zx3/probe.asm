; probe.asm - the ZX Spectrum +3 arc_image probe (B12 R5, arc_image/reference/design.md sections 6 and 8b)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A crafted 128K-family snapshot for the ULA screen that displays two embedded .arc
; images (mode 9, then mode 12 after a keypress), written from the blueprint
; alone: the reference Spectrum loader for the format. Build (sjasmplus):
;
;   sjasmplus probe.asm
;
; which SAVESNAs probe.sna; run in ZEsarUX (any Spectrum model; the +3 is
; the shipping target and uses the same ULA screen). The codec is ZX0
; (codec 1, docs/08 part B) under the 2048-byte window guarantee, and THIS
; PROBE IS THE RING LOADER (R5): decode goes straight to the ULA screen
; through a per-byte emit, back-references come out of a 2K ring in main
; RAM (../dzx0r_z80.asm, machine-verified in tests/test_dzx0r.py), and the
; R3 staging buffer is gone. Decode working set: the ring plus the
; ~110-byte decoder. A machine with RAM to spare may still stage with the
; classic ../dzx0_z80.asm; both read the identical stream.
;
; .arc recap (arc_image/reference/design.md section 10, all words
; BIG-endian): 16-byte header (magic "ARCI", version, target, mode, section
; count at +7, width at +8, height at +10, id, codec, provenance), then
; 6-byte table entries (type, flags, uncompressed length, compressed
; length), then the ZX0 streams in table order (each ends at its own end
; marker). The ZX3 payload:
;   type 1  bitmap      the band's pixel rows in ASCENDING ULA ADDRESS
;                       order (third, line-in-char, char-row). That order
;                       is linear runs with gaps: within one line-in-char
;                       the destination walks rmax*32 contiguous bytes
;                       (rmax = this third's char-row bound, height/8
;                       capped at 8), then hops one $100 page (next line),
;                       and after 8 lines hops to the next $800 third. The
;                       ring loader's screen emit is exactly that: a
;                       write, a countdown, a hop.
;   type 4  attributes  one byte per 8x8 cell, row-major: decoded STRAIGHT
;                       to $5800 (contiguous) through the plain buffer
;                       emit; the rows below the band stay paper black,
;                       where an interpreter's text goes.

        DEVICE ZXSPECTRUM128     ; the 128K snapshot variant: the +3
                                     ; loads it natively, no machine downgrade

        org $8000

start:  di
        ld sp, $7FF0            ; OUR stack, below the code: the snapshot's
                                ; default would sit in the screen we clear
        xor a
        out ($fe), a            ; black border
        call cls
        ld hl, image9
        call draw
        call waitkey
        call cls
        ld hl, image12
        call draw
        call waitkey
        jp start                ; and around again: 9, 12, 9, 12 forever
                                ; (a bare Spectrum has no OS to return to)

cls:    ld hl, $4000            ; pixels and attributes all zero
        ld de, $4001
        ld bc, $1AFF
        ld (hl), 0
        ldir
        ret

waitkey:
.up:    xor a                   ; wait for all keys up, then any key down
        in a, ($fe)
        cpl
        and $1f
        jr nz, .up
.down:  xor a
        in a, ($fe)
        cpl
        and $1f
        jr z, .down
        ret

; ---- draw: the .arc at HL ------------------------------------------------------

draw:   push hl
        pop ix                  ; ix = the .arc base
        ld a, (ix+0)            ; sanity: the magic
        cp 'A'
        ret nz
        ld a, (ix+1)
        cp 'R'
        ret nz
        ld a, (ix+11)           ; height low byte (72 or 96)
        ld (rows), a
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
        cp 1
        jr nz, .notbmp
        call scrinit            ; bitmap: aim emit at the ULA walk
        ld hl, (cur)
        call dzx0r              ; and decode STRAIGHT to the screen
        jr .adv
.notbmp:
        cp 4                    ; SEC_ATTR (the Spectrum's attribute file)
        jr nz, .adv
        ld hl, $5800            ; attributes: straight to the attr file
        call bufinit
        ld hl, (cur)
        call dzx0r
.adv:   pop hl
        push hl
        inc hl                  ; +4: compressed length, big-endian
        inc hl
        inc hl
        inc hl
        ld d, (hl)
        inc hl
        ld e, (hl)
        ld hl, (cur)
        add hl, de
        ld (cur), hl
        pop hl
        ld de, 6
        add hl, de
        pop bc
        djnz .each
        ret

; ---- the emit vector: dzx0r calls `emit`, the probe redirects it ---------

emit:   jp 0                    ; operand patched by scrinit/bufinit

; ---- screen emit: the ULA walk as write + countdown + hop ----------------
;
; State per third: rmax32 = (min(rowsleft,64)/8)*32, the contiguous run one
; line-in-char contributes; 8 lines per third, each starting one $100 page
; up; thirds start $800 apart. Preserves BC/DE/HL (the dzx0r contract).

scrinit:
        ld a, (rows)
        ld (rowsleft), a
        ld a, $40               ; first third's page
        ld (thirdhi), a
        call thirdinit
        ld hl, emit_scr
        ld (emit+1), hl
        ret

; set up the CURRENT third from rowsleft/thirdhi: consumes its rows
thirdinit:
        ld a, (rowsleft)
        cp 64
        jr c, .partial
        ld a, 64
.partial:
        ld b, a                 ; b = rows this third
        ld a, (rowsleft)
        sub b
        ld (rowsleft), a
        ld a, b                 ; run length = rows/8*32 = rows*4,
        add a, a                ; a WORD: a full third's 64 rows give 256
        add a, a
        ld l, a
        ld h, 0
        or a
        jr nz, .small
        inc h                   ; 256: h:l = $0100
.small: ld (runlen), hl
        ld (runleft), hl
        ld a, 8
        ld (linesleft), a
        ld a, (thirdhi)
        ld (linehi), a
        ld h, a
        ld l, 0
        ld (scrptr), hl
        ret

emit_scr:
        push hl
        ld hl, (scrptr)
        ld (hl), a              ; the byte lands on the ULA screen
        inc hl
        ld (scrptr), hl
        ld hl, (runleft)        ; count down this line's run
        dec hl
        ld (runleft), hl
        ld a, h
        or l
        jr nz, .done
        ld a, (linesleft)       ; line-run done: next line-in-char?
        dec a
        ld (linesleft), a
        jr z, .third
        ld a, (linehi)          ; next $100 page, run restarts at low 0
        inc a
        ld (linehi), a
        ld h, a
        ld l, 0
        ld (scrptr), hl
        ld hl, (runlen)
        ld (runleft), hl
        jr .done
.third: ld a, (rowsleft)        ; third done: another one?
        or a
        jr z, .done             ; band complete (no byte follows)
        ld a, (thirdhi)
        add a, 8
        ld (thirdhi), a
        push bc
        ld b, a                 ; thirdinit trashes B
        call thirdinit
        pop bc
.done:  pop hl
        ret

; ---- buffer emit: plain store-and-advance (attributes) -------------------

bufinit:                        ; HL = destination
        ld (bufptr), hl
        ld hl, emit_buf
        ld (emit+1), hl
        ret

emit_buf:
        push hl
        ld hl, (bufptr)
        ld (hl), a
        inc hl
        ld (bufptr), hl
        pop hl
        ret

cur:      dw 0
rows:     db 0
rowsleft: db 0
thirdhi:  db 0
linehi:   db 0
linesleft: db 0
runlen:   dw 0
runleft:  dw 0
scrptr:   dw 0
bufptr:   dw 0

        include "../dzx0r_z80.asm"

        align 2048
zx0ring:
        ds 2048
        ASSERT (zx0ring & $7FF) == 0

image9:
        incbin "90.ZX3"
image12:
        incbin "100.ZX3"

        SAVESNA "probe.sna", start
        SAVEBIN "probe.bin", start, $ - start   ; the raw image, for the
                                                ; ZRCP injection route (C.5)
