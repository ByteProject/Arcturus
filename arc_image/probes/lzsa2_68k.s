; lzsa2_68k.s - raw LZSA2 block decompressor for the 68000
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Shared by the ST and Amiga probes (and any 68000 interpreter): the lzsa
; distribution carries no 68000 routine, so this one is written from the
; block format specification in docs/09 part B; arcimg's lzsa2_decompress
; is the executable reference it was checked against, byte for byte, on
; real sections under vamos before it ever touched an emulator.
;
; in:   a0 = raw LZSA2 block (with its end-of-data marker)
;       a1 = destination
; out:  a1 = one past the last written byte
; trashes d0-d5/a2. No stack use beyond the bsr nesting (one level).
;
; Match offsets apply with a sign-extended 16-bit add (adda.w), correct
; while every match distance stays under 32769. That holds by
; construction: no .arc section exceeds 32K uncompressed (the largest is
; the DOS bitmap at 30720 bytes), so a back-reference can never reach
; further. A future format with larger sections would need adda.l and a
; long offset here.
;
; register use: d0 = token, d1 = length/scratch, d2 = match offset
; (negative, word), d3 = buffered low nibble, d4 = nibble-ready flag,
; d5 = scratch.

lzsa2_depack:
        moveq   #0,d4              ; nibble buffer empty
.token: moveq   #0,d0
        move.b  (a0)+,d0           ; token XYZ|LL|MMM

; ---- literals: LL 0-2 direct; 3 extends by nibble, then byte, then word
        move.w  d0,d1
        lsr.w   #3,d1
        and.w   #3,d1
        cmp.w   #3,d1
        bne     .dolits
        bsr     .nib               ; nibble 0-14 adds to 3; 15 extends
        addq.w  #3,d1
        cmp.w   #3+15,d1
        bne     .dolits
        moveq   #0,d1
        move.b  (a0)+,d1
        cmp.b   #239,d1            ; 239: little-endian word, absolute
        beq     .lit16
        add.w   #18,d1             ; 0-237 adds to 18
        bra     .dolits
.lit16: bsr     .le16
.dolits:
        subq.w  #1,d1              ; copy d1 literals (possibly none)
        bmi     .offset
.lcopy: move.b  (a0)+,(a1)+
        dbra    d1,.lcopy

; ---- match offset by XYZ (token bits 7-5), stored negative -------------
.offset:
        move.w  d0,d1
        lsr.w   #5,d1
        cmp.w   #7,d1
        beq     .mlen              ; 111: repeat the previous offset (d2)
        cmp.w   #6,d1
        beq     .o16
        cmp.w   #4,d1
        bcc     .o13               ; 100/101: 13-bit
        cmp.w   #2,d1
        bcc     .o9                ; 010/011: 9-bit

; 00Z, 5-bit: a nibble is offset bits 1-4, NOT Z is bit 0, upper bits 1
        bsr     .nib
        add.w   d1,d1
        bsr     .notz
        or.w    d5,d1
        or.w    #$FFE0,d1
        move.w  d1,d2
        bra     .mlen

.o9:    ; 01Z, 9-bit: a byte is bits 0-7, NOT Z is bit 8, upper bits 1
        bsr     .notz
        lsl.w   #8,d5
        moveq   #0,d1
        move.b  (a0)+,d1
        or.w    d5,d1
        or.w    #$FE00,d1
        move.w  d1,d2
        bra     .mlen

.o13:   ; 10Z, 13-bit: nibble is bits 9-12, NOT Z bit 8, byte bits 0-7,
        ; upper bits 1, then subtract 512
        bsr     .nib
        lsl.w   #8,d1
        add.w   d1,d1              ; nibble << 9 (survives .notz: d5 only)
        bsr     .notz
        lsl.w   #8,d5
        or.w    d1,d5
        moveq   #0,d1
        move.b  (a0)+,d1
        or.w    d5,d1
        or.w    #$E000,d1
        sub.w   #512,d1
        move.w  d1,d2
        bra     .mlen

.o16:   ; 110, 16-bit: byte is bits 8-15, then byte is bits 0-7
        moveq   #0,d5
        move.b  (a0)+,d5
        lsl.w   #8,d5
        move.b  (a0)+,d5
        move.w  d5,d2

; ---- match length: MMM+2 direct for 0-6; 7 extends nibble/byte/word ----
.mlen:  move.w  d0,d1
        and.w   #7,d1
        addq.w  #2,d1
        cmp.w   #9,d1
        bne     .copy
        bsr     .nib               ; 0-14 adds to 9; 15 extends
        addq.w  #8,d1
        addq.w  #1,d1              ; + 9 (addq caps at 8)
        cmp.w   #9+15,d1
        bne     .copy
        moveq   #0,d1
        move.b  (a0)+,d1
        cmp.b   #232,d1            ; the end-of-data marker
        beq     .done
        cmp.b   #233,d1            ; 233: little-endian word, absolute
        beq     .m16
        add.w   #24,d1             ; 0-231 adds to 24
        bra     .copy
.m16:   bsr     .le16

; ---- copy the match: source = destination + negative offset -----------
.copy:  movea.l a1,a2
        adda.w  d2,a2              ; sign-extended: the 32K constraint
        subq.w  #1,d1
.mcopy: move.b  (a2)+,(a1)+
        dbra    d1,.mcopy
        bra     .token

.done:  rts

; NOT Z (token bit 5, inverted) into d5 bit 0
.notz:  move.w  d0,d5
        lsr.w   #5,d5
        not.w   d5
        and.w   #1,d5
        rts

; the next nibble into d1 (0-15): a fresh byte serves its high half first,
; the buffered low half second
.nib:   tst.b   d4
        beq     .fresh
        moveq   #0,d4
        moveq   #0,d1
        move.b  d3,d1
        rts
.fresh: moveq   #0,d1
        move.b  (a0)+,d1
        move.b  d1,d3
        and.b   #$0F,d3
        moveq   #1,d4
        lsr.w   #4,d1
        rts

; a little-endian 16-bit value into d1 (the absolute length escapes)
.le16:  moveq   #0,d1
        move.b  (a0)+,d1
        moveq   #0,d5
        move.b  (a0)+,d5
        lsl.w   #8,d5
        or.w    d5,d1
        rts
