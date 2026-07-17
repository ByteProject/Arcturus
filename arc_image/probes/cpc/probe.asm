; probe.asm - the Amstrad CPC arc_image probe (B12 R5, arc_image/reference/design.md sections 6 and 8b)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A crafted snapshot for Mode 0 that displays two embedded .arc images
; (mode 9, then mode 12 after a keypress), written from the blueprint
; alone: the reference CPC loader for the format. Build:
;
;   sjasmplus probe.asm          (assembles probe.bin)
;   python3 build_sna.py         (wraps it into probe.sna, a v1 snapshot)
;
; and run in ZEsarUX (CPC 464/6128). The codec is ZX0 (codec 1, docs/08
; part B) under the 2048-byte window guarantee, and THIS PROBE IS THE RING
; LOADER (R5, 2026-07-17): decode goes straight to the screen through a
; per-byte emit, back-references come out of a 2K ring in main RAM, and
; the old 7680-byte staging band is gone. The decode working set is the
; ring plus the ~110-byte decoder (../dzx0r_z80.asm, machine-verified
; against the corpus in tests/test_dzx0r.py); that is the 64K posture the
; CPC 464 aim demands, since a real interpreter also holds the Z-machine
; and the story. A machine with RAM to spare may still stage with the
; classic ../dzx0_z80.asm; both read the identical stream.
;
; The CPC payload (arc_image/reference/design.md section 10):
;   type 1  bitmap    Mode 0 bytes in SUB-BLOCK order: the screen's eight
;                     0x800 blocks each hold every 8th raster line, and
;                     the band's rows land contiguously at each block's
;                     START. The ring loader emits linearly into block 0
;                     until rows*10 bytes have landed, hops to the next
;                     block base ($C000 + s*$800), and so on: the emit is
;                     a write, a counter, and a hop. No other math exists.
;   type 5  palette   16 ink indices in the 27-cube, r*9+g*3+b with
;                     levels 0..2; the loader maps them to gate-array
;                     hardware colors with the 27-byte table below and
;                     programs pens 0-15.
;   type 7  registers one byte, the border ink (firmware number).
;
; The gate array wants MODE 0 with both ROMs disabled ($8C); the CRTC's
; standard 40x25 screen at $C000 comes preset from the snapshot header.
; Below the band the bytes stay zero: pen 0 everywhere, the interpreter's
; text area.

        DEVICE NOSLOT64K
        org $4000

start:  di
        ld sp, $3FF0            ; our stack, below the code
        ld bc, $7F8C            ; gate array: mode 0, ROMs off
        out (c), c
        call crtc               ; OWN the screen geometry: an injected or
                                ; firmware-scrolled CRTC has a nonzero
                                ; display offset, and the picture wraps
        call cls
        ld hl, image9
        call draw
        call waitkey
        call cls
        ld hl, image12
        call draw
        call waitkey
        jp start                ; and around again: 9, 12, 9, 12 forever

; the standard 40x25 screen at $C000: R1/R2/R6/R7 geometry, R12/R13
; display start (this is what firmware scrolling moves), R9 char height
crtc:   ld hl, crtctab
        xor a
.reg:   ld b, $BC               ; CRTC register select
        out (c), a
        ld b, $BD               ; CRTC register data
        ld d, (hl)
        inc hl
        out (c), d
        inc a
        cp 14
        jr nz, .reg
        ret

crtctab:
        db 63, 40, 46, $8E, 38, 0, 25, 30, 0, 7, 0, 0, $30, 0

cls:    ld hl, $C000            ; the whole 16K screen to zero (pen 0)
        ld de, $C001
        ld bc, $3FFF
        ld (hl), 0
        ldir
        ret

; ---- draw: the .arc at HL ------------------------------------------------------

draw:   push hl
        pop ix
        ld a, (ix+0)
        cp 'A'
        ret nz
        ld a, (ix+1)
        cp 'R'
        ret nz
        ld a, (ix+11)           ; height low byte (72 or 96)
        ld (rows), a
        ld e, (ix+7)            ; data cursor = base + 16 + count*6
        ld d, 0
        ld l, e
        ld h, d
        add hl, hl
        add hl, de
        add hl, hl
        push ix
        pop de
        add hl, de
        ld de, 16
        add hl, de
        ld (cur), hl
        push ix
        pop hl
        ld de, 16
        add hl, de
        ld b, (ix+7)
.each:  push bc
        push hl
        ld a, (hl)
        cp 1
        jr nz, .notbmp
        call scrinit            ; bitmap: aim emit at the screen sub-blocks
        ld hl, (cur)
        call dzx0r              ; and decode STRAIGHT to the screen
        jr .adv
.notbmp:
        cp 5
        jr nz, .notpal
        ld hl, palbuf           ; palette: aim emit at the 16-byte buffer
        call bufinit
        ld hl, (cur)
        call dzx0r
        call setpens
        jr .adv
.notpal:
        cp 7
        jr nz, .adv
        ld hl, regbuf           ; registers: one byte, the border ink
        call bufinit
        ld hl, (cur)
        call dzx0r
        ld a, (regbuf)
        call hw                 ; cube index -> hardware color
        ld bc, $7F10            ; select the border
        out (c), c
        ld b, $7F
        or $40                  ; color-write command bits
        out (c), a
.adv:   pop hl
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
        ld de, 6
        add hl, de
        pop bc
        djnz .each
        ret

; ---- the emit vector: dzx0r calls `emit`, the probe redirects it ---------

emit:   jp 0                    ; operand patched by scrinit/bufinit

; ---- screen emit: linear within a sub-block, hop every rows*10 bytes ------

; block s of the screen holds every 8th raster line, and the band's rows
; fill each block's start: emit walks block 0 for rows*10 bytes, hops to
; $C000 + s*$800, and repeats. Preserves BC/DE/HL (the dzx0r contract).
scrinit:
        ld a, (rows)            ; blkn = rows * 10, computed once
        ld l, a
        ld h, 0
        add hl, hl              ; *2
        push hl
        add hl, hl              ; *4
        add hl, hl              ; *8
        pop bc
        add hl, bc              ; *10
        ld (blkn), hl
        ld (blkcnt), hl
        ld hl, $C000
        ld (scrptr), hl
        ld (blkbase), hl
        ld hl, emit_scr
        ld (emit+1), hl
        ret

emit_scr:
        push hl
        ld hl, (scrptr)
        ld (hl), a              ; the byte lands on the screen
        inc hl
        ld (scrptr), hl
        ld hl, (blkcnt)         ; count down this block's share
        dec hl
        ld (blkcnt), hl
        ld a, h
        or l
        jr nz, .done
        ld hl, (blkbase)        ; block done: hop to the next $800 base
        ld a, h
        add a, 8
        ld h, a
        ld (blkbase), hl
        ld (scrptr), hl
        ld hl, (blkn)
        ld (blkcnt), hl
.done:  pop hl
        ret

; ---- buffer emit: plain store-and-advance (palette, registers) -----------

bufinit:                        ; HL = destination buffer
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

; program pens 0-15 from the decoded firmware inks
setpens:
        ld hl, palbuf
        xor a                   ; pen number
.pen:   push af
        ld bc, $7F00
        ld c, a
        out (c), c              ; select the pen (bits 7-6 low = pen select)
        ld a, (hl)
        inc hl
        call hw
        or $40
        ld b, $7F
        out (c), a              ; its color
        pop af
        inc a
        cp 16
        jr nz, .pen
        ret

; firmware ink number (0..26) to gate-array hardware color
hw:     push hl
        ld hl, hwtab
        add a, l
        ld l, a
        jr nc, .nc
        inc h
.nc:    ld a, (hl)
        pop hl
        ret

; the .arc ink index is r*9+g*3+b with levels 0..2 (the 27-cube in RGB
; order, arc_image/reference/design.md section 10), NOT the firmware's
; ink numbering: this table is indexed by that cube.
hwtab:  db $54,$44,$55,$56,$46,$57,$52,$42,$53
        db $5C,$58,$5D,$5E,$40,$5F,$5A,$59,$5B
        db $4C,$45,$4D,$4E,$47,$4F,$4A,$43,$4B

; wait for a key: select AY register 14 through the PPI, then strobe the
; ten keyboard rows; any held key pulls a bit low
waitkey:
.up:    call anykey
        jr c, .up               ; wait for all keys released
.down:  call anykey
        jr nc, .down            ; then for any key down
        ret

anykey: ; carry set when some key is down
        ld bc, $F782            ; PPI control: port A output
        out (c), c
        ld bc, $F40E            ; port A = AY register 14
        out (c), c
        ld bc, $F6C0            ; AY: latch the address
        out (c), c
        ld bc, $F600
        out (c), c
        ld bc, $F792            ; PPI control: port A input
        out (c), c
        ld e, 0                 ; accumulated (inverted) key bits
        ld a, $40               ; rows $40..$49
.row:   ld b, $F6
        out (c), a
        ld b, $F4
        ld d, a
        in a, (c)
        cpl
        or e
        ld e, a
        ld a, d
        inc a
        cp $4A
        jr nz, .row
        ld bc, $F782            ; port A back to output
        out (c), c
        ld a, e
        or a
        scf
        ret nz
        ccf
        ret

cur:    dw 0
rows:   db 0
palbuf: ds 16
regbuf: db 0
scrptr: dw 0
blkbase: dw 0
blkcnt: dw 0
blkn:   dw 0
bufptr: dw 0

        include "../dzx0r_z80.asm"

; the 2K history ring (the whole decode working set; the staging band of
; the R3 probe is gone). 2K-aligned so the low 11 address bits are the
; ring index; the ASSERT keeps a careless edit from breaking that.
        align 2048
zx0ring:
        ds 2048
        ASSERT (zx0ring & $7FF) == 0

image9:
        incbin "90.CPC"
image12:
        incbin "100.CPC"

        SAVEBIN "probe.bin", start, $ - start
