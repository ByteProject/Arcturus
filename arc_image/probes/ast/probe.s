; probe.s - the Atari ST arc_image probe (B12 R2, docs/08 section 6)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A TOS program for ST low resolution that displays two embedded .arc images
; (mode 9, then mode 12 after a keypress): the reference ST loader for the
; format. Build with Eris's vasm:
;
;   vasmm68k_mot -Ftos -o PROBE.PRG probe.s
;
; and run in Hatari (GEMDOS drive autostart). The RLE decoder is the same
; dozen instructions as everywhere; the ST specifics are Physbase for the
; screen, Setpalette with the file's palette section VERBATIM (the .arc
; carries STF 3-bit hardware words), and the fixed 160-bytes-per-row
; word-interleaved bitmap decoded straight onto the screen from row 0.

        opt     a+,o+

; ---- GEMDOS/XBIOS helpers ----------------------------------------------------

start:
        ; low res, keep the current screen base (Setscreen -1,-1,0)
        clr.w   -(sp)                   ; rez 0 = low
        move.l  #-1,-(sp)               ; physical: keep
        move.l  #-1,-(sp)               ; logical: keep
        move.w  #5,-(sp)                ; Setscreen
        trap    #14
        lea     12(sp),sp

        lea     image9,a5
        bsr     draw
        bsr     waitkey

        bsr     clearscreen
        lea     image12,a5
        bsr     draw
        bsr     waitkey

        clr.w   -(sp)                   ; Pterm0
        trap    #1

waitkey:
        move.w  #8,-(sp)                ; Cnecin: wait one key, no echo
        trap    #1
        addq.l  #2,sp
        rts

clearscreen:
        bsr     physbase
        move.l  a0,a1
        move.w  #32000/4-1,d0
.clr:   clr.l   (a1)+
        dbra    d0,.clr
        rts

physbase:
        move.w  #2,-(sp)                ; XBIOS Physbase
        trap    #14
        addq.l  #2,sp
        move.l  d0,a0
        rts

; ---- draw: a5 -> an embedded .arc ---------------------------------------------
; Header: magic "ARCI", version, target, mode, section count, width, height,
; id, reserved (big-endian, the 68000's native order: no swapping anywhere).
; The AST payload: section 1 = bitmap (the ST's own word interleave, 160
; bytes per row, decoded to the screen from row 0) and section 5 = palette
; (16 STF hardware words, handed to Setpalette verbatim).

draw:
        cmp.l   #"ARCI",(a5)            ; the magic
        bne     .out
        moveq   #0,d7
        move.b  7(a5),d7                ; section count
        lea     16(a5),a3               ; the section table
        move.l  a3,a4
        move.w  d7,d0
        mulu    #6,d0
        add.w   d0,a4                   ; a4 = first section's data
.each:  tst.w   d7
        beq     .out
        move.b  (a3),d0                 ; section type
        cmp.b   #5,d0
        beq     .pal
        cmp.b   #1,d0
        beq     .bmp
.next:  moveq   #0,d0
        move.w  4(a3),d0                ; compressed length
        add.l   d0,a4
        addq.l  #6,a3
        subq.w  #1,d7
        bra     .each

.pal:   ; decode the 32 palette bytes to a buffer, then Setpalette
        lea     palbuf,a1
        move.l  a4,a0
        bsr     unrle
        pea     palbuf
        move.w  #6,-(sp)                ; XBIOS Setpalette
        trap    #14
        addq.l  #6,sp
        bra     .next

.bmp:   ; decode the band straight onto the screen, row 0 down
        move.l  a4,a0
        bsr     physbase                ; a0 clobbered: reorder below
        move.l  a0,a1                   ; a1 = screen
        move.l  a4,a0                   ; a0 = compressed stream
        bsr     unrle
        bra     .next

.out:   rts

; ---- the RLE decoder (docs/08 section 10) --------------------------------------
; in: a0 = compressed stream, a1 = destination.
; control < $80: copy control+1 literals; > $80: repeat next byte 257-control
; times; = $80: end of section.

unrle:
.next:  moveq   #0,d0                   ; the WHOLE register: dbra leaves
        move.b  (a0)+,d0                ; $FFFF in d0.w and move.b keeps it
        cmp.b   #$80,d0
        beq     .end
        blo     .lit
        neg.b   d0                      ; 256 - control
        addq.b  #1,d0                   ; 257 - control (2..128, fits a byte? 128 ok)
        move.b  (a0)+,d1
        subq.w  #1,d0
.run:   move.b  d1,(a1)+
        dbra    d0,.run
        bra     .next
.lit:                                   ; control+1 literal bytes
.cl:    move.b  (a0)+,(a1)+
        dbra    d0,.cl
        bra     .next
.end:   rts

        section bss
palbuf: ds.b    32

        section data
        even
image9:
        incbin  "90.AST"
image12:
        incbin  "100.AST"
