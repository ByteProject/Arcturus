; probe.asm - the MSX1 arc_image probe (B12 R4, arc_image/reference/design.md sections 6 and 8)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Screen 2 (Graphics II) on the TMS9918A, displaying the two embedded .arc
; images (mode 9, then mode 12 after a keypress): the reference MSX1 loader
; for the format. Build (sjasmplus):
;
;   sjasmplus probe.asm
;
; which SAVEBINs probe.bin ($9000, raw); tools in this directory wrap it
; into a BSAVE binary on a bootable Disk BASIC .dsk (AUTOEXEC.BAS does
; CLEAR and BLOAD"PROBE.BIN",R). Runs on any MSX1 with a disk drive; the
; openMSX bench machine is Stefan's Sony HitBit.
;
; The codec is ZX0 (codec 1, docs/08 part B) under the 2048-byte window
; guarantee, decoded by THE SAME ring decoder as the Spectrum and CPC
; probes (../dzx0r_z80.asm, machine-verified in tests/test_dzx0r.py).
; MSX1 is the friendliest emit of the family: BOTH sections stream to the
; VDP data port, which auto-increments its own address, so the emit is
; two instructions and there is no walk state at all. The decode pace
; through the ring (every byte passes emit) also satisfies the TMS9918A's
; VRAM access spacing without explicit delays.
;
; .arc recap (design.md section 10, all words BIG-endian): 16-byte header
; (magic "ARCI", version, target, mode, section count at +7, width at +8,
; height at +10, id, codec, provenance), then 6-byte table entries (type,
; flags, uncompressed length, compressed length), then the ZX0 streams in
; table order. The MS1 payload (both in name order, 8 bytes per tile):
;   type 1  bitmap   the Screen 2 pattern table for the band's tiles,
;                    streamed to VRAM $0000
;   type 3  color    the matching color table (fg/bg nibbles per pattern
;                    byte), streamed to VRAM $2000
; The name table is IMPLICIT (identity): this loader writes 0..255 three
; times at $1800 once at startup; the band's tiles fill from the top and
; the cleared pattern/color tables keep everything below the band black.

VDPDATA equ $98
VDPCTRL equ $99
PPIC    equ $AA                 ; keyboard row select, low nibble
PPIB    equ $A9                 ; keyboard row read

        DEVICE NOSLOT64K

        org $9000

start:  di
        ld sp, $8FF0            ; our stack, just below the code (the
                                ; CLEAR in AUTOEXEC keeps BASIC out)
        call vdpinit
        ld hl, image9
        call draw
        call waitkey
        call cls
        ld hl, image12
        call draw
        call waitkey
        call cls
        jp start                ; around again: 9, 12, 9, 12 forever
                                ; (di and the sp reload are harmless)

; ---- VDP: Screen 2, tables cleared, identity name table ------------------

vdpinit:
        ld hl, regtab
        ld b, 8
        ld c, 0                 ; register number
.regs:  ld a, (hl)
        out (VDPCTRL), a
        ld a, c
        or $80
        out (VDPCTRL), a
        inc hl
        inc c
        djnz .regs
        call cls
        ld hl, $1800            ; the identity name table, three thirds
        call setwr
        ld c, 3
.third: ld b, 0                 ; 256 entries
        xor a
.name:  out (VDPDATA), a
        inc a
        djnz .name
        dec c
        jr nz, .third
        ld hl, $1B00            ; sprite attribute table: Y=208 ends it
        call setwr
        ld a, 208
        out (VDPDATA), a
        ret

regtab: db $02                  ; R0: M3 (Screen 2)
        db $C0                  ; R1: 16K, display on, no interrupts
        db $06                  ; R2: name table $1800
        db $FF                  ; R3: color table $2000, full
        db $03                  ; R4: pattern table $0000, full
        db $36                  ; R5: sprite attributes $1B00
        db $07                  ; R6: sprite patterns $3800
        db $01                  ; R7: backdrop black

; clear the pattern and color tables (all-zero pattern on color 0 shows
; the black backdrop): the screen below the band, and between images
cls:    ld hl, $0000
        call fill6k
        ld hl, $2000
fill6k: call setwr
        ld bc, 6144
.fill:  xor a
        out (VDPDATA), a
        dec bc
        ld a, b
        or c
        jr nz, .fill
        ret

; set the VRAM write address to HL (write mode: bit 14 of the address)
setwr:  ld a, l
        out (VDPCTRL), a
        ld a, h
        and $3F
        or $40
        out (VDPCTRL), a
        ret

; ---- waitkey: the PPI matrix, any key on rows 0..10 ----------------------

waitkey:
.up:    call anykey
        jr nz, .up
.down:  call anykey
        jr z, .down
        ret

anykey: ld d, 0                 ; accumulated pressed bits
        ld e, 0                 ; row
.row:   in a, (PPIC)
        and $F0
        or e
        out (PPIC), a
        in a, (PPIB)
        cpl
        or d
        ld d, a
        inc e
        ld a, e
        cp 11
        jr c, .row
        ld a, d
        or a                    ; Z clear if any key is down
        ret

; ---- draw: the .arc at HL ------------------------------------------------

draw:   push hl
        pop ix                  ; ix = the .arc base
        ld a, (ix+0)            ; sanity: the magic
        cp 'A'
        ret nz
        ld a, (ix+1)
        cp 'R'
        ret nz
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
        jr nz, .notpat
        ld hl, $0000            ; bitmap: the pattern table
        jr .go
.notpat:
        cp 3                    ; SEC_COLOR
        jr nz, .adv
        ld hl, $2000            ; color: the color table
.go:    call setwr
        ld hl, (cur)
        call dzx0r              ; decode STRAIGHT into the VDP
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

; ---- the emit vector: dzx0r calls `emit`, the VDP does the walking -------
; (BC/DE/HL preserved trivially: nothing is touched)

emit:   out (VDPDATA), a
        ret

cur:    dw 0

        include "../dzx0r_z80.asm"

        align 2048
zx0ring:
        ds 2048
        ASSERT (zx0ring & $7FF) == 0

image9:
        incbin "9.MS1"
image12:
        incbin "12.MS1"

probe_end:

        SAVEBIN "probe.bin", start, probe_end - start
