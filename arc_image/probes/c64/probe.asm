; probe.asm - the C64 arc_image probe (B12 R3, arc_image/reference/design.md section 6)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A .prg for the multicolor bitmap mode that displays two embedded .arc
; images (mode 9, then mode 12 after a keypress), written from the
; blueprint alone: the reference C64 loader for the format. Build (ACME):
;
;   acme -f cbm -o probe.prg probe.asm
;
; and run in VICE (x64sc, autostart). The codec is ZX0 (codec 1, the
; 8-bit cell targets' codec, docs/08 part B); the decompressor is Tobias
; Bindhammer's bitfire routine for the standard v2 stream, carried
; verbatim (dzx0_6502.asm beside this file). Everything else is
; section-table walking.
;
; .arc recap (arc_image/reference/design.md section 10, all words BIG-endian): 16-byte header
; (magic "ARCI", version, target, mode, section count, width, height, id,
; codec, provenance), then 6-byte table entries (type, flags, uncompressed
; length, compressed length), then the ZX0 streams in table order (each
; ends at its own end marker, so the loader never counts output bytes).
; The C64 payload, every section already in native memory order:
;   type 1  bitmap       cell-ordered rows for $2000 (2880 or 3840 bytes)
;   type 2  screen       the video matrix for $0400  (360 or 480)
;   type 3  color        the color RAM nibbles for $D800
;   type 7  registers    one byte: the shared background for $D021
; The band occupies the top 9 or 12 cell rows; everything below stays
; cleared (color 0 on black), where a real interpreter draws its text.
;
; Zero page: the decoder owns $f8-$fc ($f8/$f9 the destination, set by
; the caller). The walk uses $02-$07, free while BASIC is dormant.

!cpu 6510

lz_dst  = $f8           ; the decoder's destination pointer (its zp base)
src     = $02           ; zp pointer to the .arc
tbl     = $04           ; zp pointer to the current table entry
cur     = $06           ; the current compressed stream
cnt     = $57           ; sections left (a spare BASIC work cell)

        * = $0801
        ; 10 SYS 2061
        !byte $0b,$08,$0a,$00,$9e,$32,$30,$36,$31,$00,$00,$00

start:  jsr cls
        lda #<image9
        sta src+0
        lda #>image9
        sta src+1
        jsr draw
        jsr waitkey
        jsr cls
        lda #<image12
        sta src+0
        lda #>image12
        sta src+1
        jsr draw
        jsr waitkey
        lda #$1b                ; back to the text screen
        sta $d011
        lda #$c8
        sta $d016
        lda #$15
        sta $d018
        lda #$0e
        sta $d020
        lda #$06
        sta $d021
        rts

waitkey:
-       jsr $ffe4               ; KERNAL GETIN
        beq -
        rts

; clear the whole canvas (bitmap, matrix, color RAM), black frame, and
; switch the multicolor bitmap on: bank 0, matrix $0400, bitmap $2000
cls:    lda #$00
        sta $d020
        sta $d021
        sta lz_dst+0
        lda #$20                ; wipe $2000-$3fff with the decoder's own
        sta lz_dst+1            ; pointer as the cursor
        ldy #$00
        tya
-       sta (lz_dst),y
        iny
        bne -
        inc lz_dst+1
        ldx lz_dst+1
        cpx #$40
        bne -
-       sta $0400,y             ; matrix and color RAM, page by page
        sta $0500,y
        sta $0600,y
        sta $0700,y
        sta $d800,y
        sta $d900,y
        sta $da00,y
        sta $db00,y
        iny
        bne -
        lda #$3b                ; bitmap mode on
        sta $d011
        lda #$d8                ; multicolor, 40 columns
        sta $d016
        lda #$18                ; matrix $0400, bitmap $2000
        sta $d018
        rts

; ---- draw: the .arc at (src) ---------------------------------------------------

draw:   ldy #0                  ; sanity: the magic "ARCI"
        lda (src),y
        cmp #'A'
        beq +
.fail:  rts
+       iny
        lda (src),y
        cmp #'R'
        bne .fail
        ldy #7                  ; section count
        lda (src),y
        sta cnt
        lda src+0               ; tbl = src + 16
        clc
        adc #16
        sta tbl+0
        lda src+1
        adc #0
        sta tbl+1
        lda cnt                 ; cur = tbl + count*6 (count <= 4)
        asl
        sta cur+0
        asl
        clc
        adc cur+0
        clc
        adc tbl+0
        sta cur+0
        lda tbl+1
        adc #0
        sta cur+1

.each:  lda cnt
        bne +
        rts                     ; all sections walked
+       ldy #0                  ; the entry's type picks the destination
        lda (tbl),y
        cmp #1
        bne +
        ldy #$20                ; bitmap -> $2000
        jsr unpack_page
        jmp .next
+       cmp #2
        bne +
        ldy #$04                ; screen matrix -> $0400
        jsr unpack_page
        jmp .next
+       cmp #3
        bne +
        ldy #$d8                ; color RAM -> $d800
        jsr unpack_page
        jmp .next
+       cmp #7
        bne .next
        lda #<regbuf            ; registers -> staging, then $d021
        sta lz_dst+0
        lda #>regbuf
        sta lz_dst+1
        jsr unpack
        lda regbuf
        sta $d021

.next:  ldy #5                  ; advance the data cursor by clen (BE word)
        lda (tbl),y
        clc
        adc cur+0
        sta cur+0
        dey
        lda (tbl),y
        adc cur+1
        sta cur+1
        lda tbl+0               ; and the table cursor by one 6-byte entry
        clc
        adc #6
        sta tbl+0
        bcc +
        inc tbl+1
+       dec cnt
        jmp .each

; depack the stream at (cur) to page Y (a page-aligned destination)
unpack_page:
        lda #$00
        sta lz_dst+0
        sty lz_dst+1
unpack: ldx cur+0               ; the decoder: src in X/A, dst preloaded
        lda cur+1
                                ; and falls straight into it; its rts
                                ; returns to unpack's caller
!source "dzx0_6502.asm"

regbuf: !byte 0

image9:
        !bin "90.C64"
image12:
        !bin "100.C64"
