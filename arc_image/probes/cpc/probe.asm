; probe.asm - the Amstrad CPC arc_image probe (B12 R3, arc_image/reference/design.md section 6)
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
; part B); the decompressor is Einar Saukas & Urusergi's 68-byte standard
; routine, carried verbatim (../dzx0_z80.asm).
;
; The CPC payload (arc_image/reference/design.md section 10):
;   type 1  bitmap    Mode 0 bytes in SUB-BLOCK order: the screen's eight
;                     0x800 blocks each hold every 8th raster line, and
;                     the band's rows land contiguously at each block's
;                     START, so the loader is eight straight copies of
;                     height*10 bytes from the staged stream to
;                     $C000 + s*$800. No other math exists.
;   type 5  palette   16 firmware ink numbers (0..26); the loader maps
;                     them to gate-array hardware colors with the 27-byte
;                     table below and programs pens 0-15.
;   type 7  registers one byte, the border ink (firmware number).
;
; The gate array wants MODE 0 with both ROMs disabled ($8C); the CRTC's
; standard 40x25 screen at $C000 comes preset from the snapshot header.
; Below the band the bytes stay zero: pen 0 everywhere, the interpreter's
; text area.

        DEVICE NOSLOT64K
        org $4000

start:  di
        ld bc, $7F8C            ; gate array: mode 0, ROMs off
        out (c), c
        ld hl, image9
        call draw
        call waitkey
        call cls
        ld hl, image12
        call draw
        call waitkey
        jr $                    ; done; sit still

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
        ld hl, (cur)            ; bitmap: staging, then eight block copies
        ld de, staging
        call dzx0_standard
        call blocks
        jr .adv
.notbmp:
        cp 5
        jr nz, .notpal
        ld hl, (cur)            ; palette: decode 16 firmware inks
        ld de, palbuf
        call dzx0_standard
        call setpens
        jr .adv
.notpal:
        cp 7
        jr nz, .adv
        ld hl, (cur)            ; registers: one byte, the border ink
        ld de, regbuf
        call dzx0_standard
        ld a, (regbuf)
        call hw                 ; firmware -> hardware color
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

; eight copies of rows*10 bytes each: block s of the screen holds every
; 8th raster line, and the band fills each block's start
blocks: ld a, (rows)            ; hl = rows * 10, computed once
        ld l, a
        ld h, 0
        add hl, hl              ; *2
        push hl
        add hl, hl              ; *4
        add hl, hl              ; *8
        pop bc
        add hl, bc              ; *10
        ld (blkn), hl
        ld hl, staging
        ld de, $C000
        ld a, 8
.blk:   push af
        push de
        ld bc, (blkn)
        ldir                    ; one block's band rows (hl walks the stage)
        pop de
        ld a, d                 ; next block: de += $800
        add a, 8
        ld d, a
        pop af
        dec a
        jr nz, .blk
        ret

blkn:   dw 0

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

hwtab:  db $54,$44,$55,$5C,$58,$5D,$4C,$45,$4D
        db $56,$46,$57,$5E,$40,$5F,$4E,$47,$4F
        db $52,$42,$53,$5A,$59,$5B,$4A,$43,$4B

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

        include "../dzx0_z80.asm"

staging:
        ds 7680                 ; the largest band bitmap (96 rows x 80)

image9:
        incbin "90.CPC"
image12:
        incbin "100.CPC"

        SAVEBIN "probe.bin", start, $ - start
