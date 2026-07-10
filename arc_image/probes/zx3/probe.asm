; probe.asm - the ZX Spectrum +3 arc_image probe (B12 R3, arc_image/reference/design.md section 6)
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
; (codec 1, docs/08 part B); the decompressor is Einar Saukas & Urusergi's
; 68-byte standard routine, carried verbatim (../dzx0_z80.asm). Everything
; else is section-table walking and the ULA's address interleave.
;
; .arc recap (arc_image/reference/design.md section 10, all words
; BIG-endian): 16-byte header (magic "ARCI", version, target, mode, section
; count at +7, width at +8, height at +10, id, codec, provenance), then
; 6-byte table entries (type, flags, uncompressed length, compressed
; length), then the ZX0 streams in table order (each ends at its own end
; marker). The ZX3 payload:
;   type 1  bitmap      the band's pixel rows in ASCENDING ULA ADDRESS
;                       order (third, line-in-char, char-row): decode to
;                       a staging buffer, then the triple loop below
;                       writes 32-byte rows to $4000 + T*$800 + L*$100
;                       + R*$20. A partial third (the band's tail) spans
;                       only height/8 char-rows, so R is bounded per
;                       third from the header's height, never assumed 8.
;   type 4  attributes  one byte per 8x8 cell, row-major: decode STRAIGHT
;                       to $5800 (contiguous); the rows below the band
;                       stay paper black, where an interpreter's text
;                       goes.

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
        ld hl, (cur)            ; bitmap: staging, then the interleave
        ld de, staging
        call dzx0_standard
        call scatter
        jr .adv
.notbmp:
        cp 4                    ; SEC_ATTR (the Spectrum's attribute file)
        jr nz, .adv
        ld hl, (cur)            ; attributes: straight to the attr file
        ld de, $5800
        call dzx0_standard
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

; ---- scatter: staged rows to the screen ----------------------------------------
; The stream is in (third, line-in-char, char-row) order. Per third: up to
; 64 rows of the band remain; that many /8 is this third's char-row bound.
; Address: high = $40 + third*8 + line, low = charrow*32.

scatter:
        ld hl, staging
        ld a, (rows)
        ld c, a                 ; c = band rows left
        ld a, $40
        ld (base), a
.third: ld a, c
        cp 64
        jr c, .partial
        ld a, 64
.partial:
        ld (t_rows), a          ; rows this third
        rrca                    ; /8 = the char-row bound
        rrca
        rrca
        and $1f
        ld (rmax), a
        ld b, 8                 ; line-in-char 0..7
        ld a, (base)
        ld (line_hi), a
.line:  push bc
        ld a, (rmax)
        ld b, a                 ; char-rows this third
        ld de, (line_hi)        ; d gets junk; set both halves below
        ld a, (line_hi)
        ld d, a
        ld e, 0
.chrow: push bc
        push de
        ld bc, 32
        ldir                    ; one 32-byte row, hl walks the stage
        pop de
        pop bc
        ld a, e
        add a, 32               ; next char-row
        ld e, a
        djnz .chrow
        ld a, (line_hi)
        inc a                   ; next line-in-char
        ld (line_hi), a
        pop bc
        djnz .line
        ld a, (t_rows)          ; this third done; any rows left?
        ld b, a
        ld a, c
        sub b
        ld c, a
        ret z
        ld a, (base)            ; next third
        add a, 8
        ld (base), a
        jr .third

cur:     dw 0
rows:    db 0
base:    db 0
line_hi: db 0
t_rows:  db 0
rmax:    db 0

        include "../dzx0_z80.asm"

staging:
        ds 3072                 ; the largest band bitmap (96 rows x 32)

image9:
        incbin "90.ZX3"
image12:
        incbin "100.ZX3"

        SAVESNA "probe.sna", start
        SAVEBIN "probe.bin", start, $ - start   ; the raw image, for the
                                                ; ZRCP injection route (C.5)
