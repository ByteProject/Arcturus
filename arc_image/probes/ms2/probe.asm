; probe.asm - the MSX2 arc_image probe (B12 R4, arc_image/reference/design.md sections 6 and 8)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Screen 5 (Graphics 4) on the V9938, displaying the two embedded .arc
; images (mode 9, then mode 12 after a keypress): the reference MSX2
; loader for the format. Build (sjasmplus):
;
;   sjasmplus probe.asm
;
; which SAVEBINs probe.bin ($B400, raw); mk_disk.py wraps it into a
; BSAVE binary on a bootable Disk BASIC .dsk. Runs on any MSX2 with a
; disk drive.
;
; The codec is LZSA2 (codec 2, docs/08 part B), decoded STAGED, the
; 16-bit manner: LZSA2 back-references read the decompressed output,
; and VRAM is port-addressed, so the stream decompresses into a RAM
; staging buffer first and the buffer is then blitted to the VDP data
; port. The decoder is the reference unlzsa2_fast.asm (spke & uniabis,
; vendored beside this probe, verified in test_unlzsa2.py against
; every LZSA2 stream in the repo). The display is BLANKED during
; decode and blit (R#1 bit 6), so VRAM access timing never matters;
; the reveal is one register write.
;
; Memory (Disk BASIC leaves RAM at $8000-$FFFF, and the DISK SYSTEM
; OWNS THE TOP: HIMEM sits near $DE79 on a two-drive MSX2, so nothing
; may LOAD above it; the first build loaded to $E410 and shredded the
; disk work area into a reboot loop): AUTOEXEC.BAS fences BASIC with
; CLEAR 200,&H83FF; the probe loads LOW at $8400 with its embedded
; pairs (ending well under HIMEM); the 12288-byte staging buffer sits
; ABOVE the code at $B600-$E5FF and is written only after the probe
; owns the machine, when the disk system's territory no longer
; matters; the stack sits at $F370.
;
; .arc recap (design.md section 10, all words BIG-endian): 16-byte
; header (magic "ARCI", version, target, mode, section count at +7,
; width at +8, height at +10, id, codec, provenance), then 6-byte
; table entries (type, flags, uncompressed length, compressed length),
; then the LZSA2 streams in table order. The MS2 payload:
;   type 1  bitmap   Screen 5 nibble-packed pixels, 128 bytes per
;                    line, linear: staged, then blitted to VRAM $0000
;   type 5  palette  16 V9938 palette-register pairs (RB, G): staged,
;                    then written through R#16 and the palette port

VDPDATA equ $98
VDPCTRL equ $99
VDPPAL  equ $9A
PPIC    equ $AA                 ; keyboard row select, low nibble
PPIB    equ $A9                 ; keyboard row read
STAGE   equ $B600               ; the 12288-byte staging buffer,
                                ; runtime-only (above the code)

        DEVICE NOSLOT64K

        org $8400

start:  di
        ld sp, $F370            ; our stack, under the system area
        call vdpinit
        ld hl, image9
        call show
        ld hl, image12
        call show
        jp start                ; forever (di and the sp reload are harmless)

show:   push hl
        call blank              ; decode invisibly
        call clrband
        pop hl
        call draw
        ld a, $40               ; display on: the reveal
        ld c, 1
        call vdpreg
        jp waitkey              ; ret through waitkey

; ---- VDP: Screen 5, blanked, cleared, sprites off ------------------------

vdpinit:
        call blank
        ld hl, regtab
        ld b, regcnt
        ld c, 0
.regs:  ld a, (hl)
        inc hl
        ld e, a                 ; value
        ld a, (hl)
        inc hl
        ld c, a                 ; register number
        ld a, e
        call vdpregA
        djnz .regs
        ; clear the whole 192-line bitmap ($0000-$5FFF) once
        ld hl, $0000
        call setwr
        ld de, $6000
.clr:   xor a
        out (VDPDATA), a
        dec de
        ld a, d
        or e
        jr nz, .clr
        ret

; write A to VDP register C
vdpregA:
        push af
        out (VDPCTRL), a
        ld a, c
        or $80
        out (VDPCTRL), a
        pop af
        ret

vdpreg: ; A = value, C = register (tail-call form)
        jp vdpregA

blank:  xor a                   ; R#1 = 0: display off, no interrupts
        ld c, 1
        jp vdpregA

regtab: db $06, 0               ; R#0: M4 (Screen 5 / Graphics 4)
        db $1F, 2               ; R#2: bitmap (name) table at $0000
        db $00, 7               ; R#7: backdrop = palette entry 0
        db $0A, 8               ; R#8: VRAM refresh on, sprites OFF
        db $00, 14              ; R#14: VRAM bank 0
regcnt  equ ($ - regtab) / 2

; clear the band area ($0000-$2FFF) between images
clrband:
        ld hl, $0000
        call setwr
        ld de, $3000
.clr:   xor a
        out (VDPDATA), a
        dec de
        ld a, d
        or e
        jr nz, .clr
        ret

; set the VRAM write address to HL, bank 0 (write mode bit 14).
; R#14 is reprogrammed EVERY time: the V9938 increments R#14 itself
; whenever the address counter crosses a 16K boundary (the init clear
; crosses it once), so a setup that trusts a stale R#14 lands a bank
; up; the first build painted the picture into invisible VRAM $4000.
setwr:  xor a
        out (VDPCTRL), a
        ld a, $80 | 14
        out (VDPCTRL), a
        ld a, l
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
        ld (styp), a
        inc hl
        inc hl
        ld d, (hl)              ; uncompressed length, big-endian
        inc hl
        ld e, (hl)
        ld (slen), de
        ; stage: decompress the stream at (cur) to STAGE
        ld hl, (cur)
        ld de, STAGE
        call DecompressLZSA2
        ld a, (styp)
        cp 1
        jr nz, .notbmp
        call blit               ; bitmap: STAGE -> VRAM $0000, (slen)
        jr .adv
.notbmp:
        cp 5                    ; SEC_PALETTE
        jr nz, .adv
        call setpal             ; palette: STAGE -> palette registers
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

; blit (slen) bytes from STAGE to VRAM $0000 (display is blanked, so
; no access-timing pacing is needed)
blit:   ld hl, $0000
        call setwr
        ld hl, STAGE
        ld de, (slen)
        ld c, VDPDATA
.page:  outi                    ; out (c),(hl); hl++; b--
        dec de
        ld a, d
        or e
        jr nz, .page
        ret

; the staged 32 palette bytes through R#16 and the palette port
setpal: xor a
        ld c, 16
        call vdpregA            ; palette pointer to entry 0
        ld hl, STAGE
        ld b, 32
        ld c, VDPPAL
        otir
        ret

cur:    dw 0
slen:   dw 0
styp:   db 0

        include "unlzsa2_fast.asm"

image9:
        incbin "9.MS2"
image12:
        incbin "12.MS2"

probe_end:

        SAVEBIN "probe.bin", start, probe_end - start
