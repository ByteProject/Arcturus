; probe.asm - the Agon Light arc_image probe (arc_image/reference/design.md sections 6 and 8)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A Z80-mode MOS executable for VDP mode 3 (640x240, the fixed 64-color
; RGBA2222 cube), displaying the two embedded .arc images (mode 9, then
; mode 12 on a keypress): the reference Agon loader for the format,
; built for Shawn Sijnstra's Canopus target. Build (sjasmplus):
;
;   sjasmplus probe.asm
;
; then `python3 mk_sd.py` stages the emulated SD card directory; run:
;
;   fab-agon-emulator --sdcard sdcard/
;
; (MOS runs autoexec.txt: load probe.bin / run). Plain Z80 code in the
; eZ80's Z80 mode: MOS enters at the segment's offset 0. MOS API calls
; from Z80 mode go through the .LIS-suffixed RST opcodes (49h prefix),
; the documented convention: a plain RST would land on our own vector
; page, and a jp.lil into the flash handler discards the mixed-mode
; return linkage the handler's long RET expects (the first build
; painted the band as text glyphs that way). INTERRUPTS STAY ENABLED:
; the VDU stream rides MOS's UART driver (MADL is set, so interrupts
; service in ADL mode on their own).
;
; The codec is RLE (codec 0, docs/08 part B), Shawn's ruling for this
; machine, and the display path makes it the purest loader of the whole
; family: THERE IS NO FRAMEBUFFER AND NO STAGING. The decoder's emit is
; RST $10 (the VDU write), so every decoded byte streams down the
; serial link directly into a VDP buffer; the band never exists in eZ80
; RAM at all. Decode working set: the ~20-instruction decoder.
;
; The VDU conversation per image (Buffered Commands API, VDP 2.2.0+):
;   VDU 23,0,&A0,id;2            clear the buffer
;   VDU 23,0,&A0,id;0,len;       write block: len = the section's
;                                uncompressed length, then exactly that
;                                many bytes = the RLE decode stream
;   VDU 23,0,&A0,id;14           consolidate
;   VDU 23,27,&20,id;            select the buffer as bitmap
;   VDU 23,27,&21,w;h;1          bind: width, height, format 1 = RGBA2222
;   VDU 23,27,3,x;y;             draw at 0,0
;
; .arc recap (design.md section 10, all table words BIG-endian; VDU
; parameters LITTLE-endian, so the probe swaps as it speaks): 16-byte
; header (magic "ARCI", section count at +7, width at +8, height at
; +10), 6-byte table entries (type, flags, uncompressed length,
; compressed length), then the RLE streams in table order. The AGN
; payload: one section, bitmap (type 1), raw RGBA2222 rows, top to
; bottom, alpha %11.

BUFID   equ 100                 ; the VDP buffer the band streams into

        DEVICE NOSLOT64K

        org 0

        MACRO MOSAPI            ; RST.LIS 08h: the MOS API from Z80 mode
        db $49, $CF
        ENDM
        MACRO VDU               ; RST.LIS 10h: one byte to the VDP
        db $49, $D7
        ENDM

        jp start                ; entry: MOS jumps to segment offset 0
        ds $40 - $, 0
; ---- the MOS header ------------------------------------------------------
        db "MOS", 0, 0          ; marker, header version 0, Z80 mode

start:  ld a, 22                ; VDU 22, 3: mode 3, 640x240, 64 colors
        VDU
        ld a, 3
        VDU
        ld hl, curoff
        ld b, curofflen
        call puts
loop:   ld hl, image9
        call show
        call waitkey
        ld hl, image12
        call show
        call waitkey
        jr loop

curoff: db 23, 1, 0             ; cursor off
curofflen equ $ - curoff

; ---- show: the .arc at HL ------------------------------------------------

show:   push hl
        pop ix                  ; ix = the .arc base
        ld a, (ix+0)            ; sanity: the magic
        cp 'A'
        ret nz
        ld a, (ix+1)
        cp 'R'
        ret nz
        ld a, 12                ; VDU 12: clear the screen
        VDU
        ; the single bitmap section: stream starts after the table
        ld e, (ix+7)            ; section count (1 for AGN)
        ld d, 0
        ld l, e
        ld h, d
        add hl, hl
        add hl, de
        add hl, hl              ; count * 6
        push ix
        pop de
        add hl, de
        ld de, 16
        add hl, de
        ld (cur), hl            ; the compressed stream
        ; clear the buffer
        ld hl, vclear
        ld b, vclearlen
        call puts
        ; write-block header with the uncompressed length (big-endian
        ; in the table at +2/+3, little-endian on the wire)
        ld hl, vwrite
        ld b, vwritelen
        call puts
        ld a, (ix+19)           ; ulen low (big-endian +2 high, +3 low)
        VDU
        ld a, (ix+18)           ; ulen high
        VDU
        ; the RLE decode, emitted straight down the VDU stream
        ld hl, (cur)
        call unrle
        ; consolidate, select, bind, draw
        ld hl, vtail
        ld b, vtaillen
        call puts
        ld a, (ix+9)            ; width low (big-endian +8/+9)
        VDU
        ld a, (ix+8)            ; width high
        VDU
        ld a, (ix+11)           ; height low
        VDU
        ld a, (ix+10)           ; height high
        VDU
        ld hl, vdraw
        ld b, vdrawlen
        call puts
        ret

vclear: db 23, 0, $A0
        db BUFID, 0             ; bufferId;
        db 2                    ; clear
vclearlen equ $ - vclear

vwrite: db 23, 0, $A0
        db BUFID, 0
        db 0                    ; write block; len; follows, then data
vwritelen equ $ - vwrite

vtail:  db 23, 0, $A0
        db BUFID, 0
        db 14                   ; consolidate
        db 23, 27, $20
        db BUFID, 0             ; select bitmap = buffer
        db 23, 27, $21          ; bind from buffer: w; h; format follow
vtaillen equ $ - vtail

vdraw:  db 1                    ; format 1 = RGBA2222 (ends the bind)
        db 23, 27, 3
        db 0, 0, 0, 0           ; x; y; = 0,0
vdrawlen equ $ - vdraw

; send B bytes at HL down the VDU stream
puts:   ld a, (hl)
        VDU
        inc hl
        djnz puts
        ret

; ---- the RLE decoder (codec 0): emit = VDU (RST.LIS 10h) -----------------
; control byte c: 0x00-0x7F copy c+1 literals; 0x81-0xFF repeat the next
; byte 257-c times (2..128); 0x80 end of section.

unrle:  ld a, (hl)
        inc hl
        cp $80
        ret z                   ; end marker
        jr c, .lit
        ld b, a                 ; run: count = 257 - c, low byte 1 - c
        ld a, 1
        sub b                   ; a = 1 - c = (257 - c) & 0xFF
        ld b, a
        ld a, (hl)
        inc hl
.run:   VDU
        djnz .run
        jr unrle
.lit:   ld b, a
        inc b                   ; c + 1 literals
.copy:  ld a, (hl)
        inc hl
        VDU
        djnz .copy
        jr unrle

; ---- waitkey: the MOS keyboard -------------------------------------------
; mos_getkey (function 0) is documented BLOCKING: it returns only when
; a key is pressed.

waitkey:
        xor a
        MOSAPI
        or a
        jr z, waitkey
        ret

cur:    dw 0

image9:
        incbin "9.AGN"
image12:
        incbin "12.AGN"

probe_end:

        SAVEBIN "probe.bin", 0, probe_end
