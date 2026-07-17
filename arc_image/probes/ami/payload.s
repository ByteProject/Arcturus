; payload.s - the Amiga arc_image probe proper (B12 R2, arc_image/reference/design.md section 6)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Loaded by boot.s to chip RAM at $20000 and entered cold: the reference
; Amiga (OCS) loader for the .arc format. It takes over the display with
; one copper list, decodes the bitmap section (5 bitplanes, ILBM-style
; row-interleave) to a chip buffer that displays IN PLACE via bitplane
; modulos, writes the 32 palette words to COLOR00..31 VERBATIM, and shows
; the embedded mode-9 image, then the mode-12 image after a mouse click.
; No OS calls after entry; a probe owns the machine.
;
; Assemble: vasmm68k_mot -Fbin -o payload.bin payload.s

CUSTOM   = $DFF000
BITMAP   = $30000              ; the decoded band, chip RAM
DIWSTRT  = $08E
DIWSTOP  = $090
DDFSTRT  = $092
DDFSTOP  = $094
BPLCON0  = $100
BPLCON1  = $102
BPL1MOD  = $108
BPL2MOD  = $10A
DMACON   = $096
COLOR00  = $180
COP1LC   = $080
COPJMP1  = $088

        org     $20000

start:
        lea     CUSTOM,a6
        move.w  #$7FFF,DMACON(a6)       ; all DMA off
        ; a stable 320x200 lowres display window
        move.w  #$2C81,DIWSTRT(a6)
        move.w  #$2CC1,DIWSTOP(a6)
        move.w  #$0038,DDFSTRT(a6)
        move.w  #$00D0,DDFSTOP(a6)
        move.w  #$5200,BPLCON0(a6)      ; 5 bitplanes, color on
        move.w  #0,BPLCON1(a6)
        move.w  #160,BPL1MOD(a6)        ; interleave: skip the other 4 rows
        move.w  #160,BPL2MOD(a6)

        lea     image9(pc),a5
        bsr     show
        bsr     waitmouse
        lea     image12(pc),a5
        bsr     show
        bsr     waitmouse
forever:
        bra     forever                 ; the probe ends with the emulator

; ---- show: a5 -> an embedded .arc ---------------------------------------------
; Sections for AMI: 1 = bitmap (5 planes row-interleaved, 200 bytes per
; pixel row) decoded to BITMAP; 5 = palette (32 x $0RGB words) written to
; COLOR00.. verbatim. The copper wait below the band switches to 0 planes,
; so the area under the picture shows COLOR00 flat; its line is patched
; from the header's height so both modes lay out right.

show:
        cmp.l   #"ARCI",(a5)
        bne     .out
        ; patch the copper: end-of-band line = $2C + height
        moveq   #0,d0
        move.b  11(a5),d0               ; height low byte (72 or 96)
        add.b   #$2C,d0
        lea     copwait(pc),a0
        move.b  d0,(a0)
        ; clear the band buffer (both modes share it; 12 rows worth)
        lea     BITMAP,a0
        move.w  #19200/4-1,d0
.clr:   clr.l   (a0)+
        dbra    d0,.clr
        ; walk the sections
        moveq   #0,d7
        move.b  7(a5),d7                ; section count
        lea     16(a5),a3               ; the table
        move.l  a3,a4
        move.w  d7,d0
        mulu    #6,d0
        add.w   d0,a4                   ; a4 = first stream
.each:  tst.w   d7
        beq     .go
        move.b  (a3),d0
        cmp.b   #1,d0
        beq     .bmp
        cmp.b   #5,d0
        beq     .pal
.next:  moveq   #0,d0
        move.w  4(a3),d0                ; compressed length
        add.l   d0,a4
        addq.l  #6,a3
        subq.w  #1,d7
        bra     .each
.bmp:   move.l  a4,a0
        lea     BITMAP,a1
        bsr     lzsa2_depack
        bra     .next
.pal:   move.l  a4,a0
        lea     palbuf(pc),a1
        bsr     lzsa2_depack
        lea     palbuf(pc),a0
        lea     COLOR00(a6),a1
        moveq   #32-1,d0
.pl:    move.w  (a0)+,(a1)+
        dbra    d0,.pl
        bra     .next
.go:    ; point the copper at the list, bitplanes at the buffer, DMA on
        lea     coplist(pc),a0
        move.l  a0,COP1LC(a6)
        move.w  #0,COPJMP1(a6)
        move.w  #$8380,DMACON(a6)       ; SET | DMAEN | BPLEN | COPEN
.out:   rts

waitmouse:
.up:    btst    #6,$BFE001              ; wait for a release first
        beq     .up
.down:  btst    #6,$BFE001              ; then the click
        bne     .down
        rts

; ---- the LZSA2 decoder (codec 2, docs/08 part B) -------------------------------
; the shared 68000 routine (register-only, so it rides the bootblock's
; position-independent world untouched); proven byte-exact under vamos
; before it reached the copper. a0 = raw block, a1 = dest; trashes
; d0-d5/a2, none of which the section walk holds.

        include "../lzsa2_68k.s"

; ---- the copper list -----------------------------------------------------------
; Bitplane pointers: the interleaved buffer displays in place, planes 40
; bytes apart, modulo 160. COLOR00 dark below the band via the 0-plane
; switch at the patched wait line.

        even
coplist:
        dc.w    BPLCON0,$5200                   ; 5 planes ON, restored at
                                                ; the TOP of every frame:
                                                ; the band-bottom switch
                                                ; below turns them off, and
                                                ; a list without this shows
                                                ; the picture for exactly
                                                ; one frame (lesson paid)
        dc.w    $00E0,(BITMAP>>16)&$FFFF        ; BPL1PTH
        dc.w    $00E2,BITMAP&$FFFF              ; BPL1PTL
        dc.w    $00E4,(BITMAP>>16)&$FFFF
        dc.w    $00E6,(BITMAP+40)&$FFFF
        dc.w    $00E8,(BITMAP>>16)&$FFFF
        dc.w    $00EA,(BITMAP+80)&$FFFF
        dc.w    $00EC,(BITMAP>>16)&$FFFF
        dc.w    $00EE,(BITMAP+120)&$FFFF
        dc.w    $00F0,(BITMAP>>16)&$FFFF
        dc.w    $00F2,(BITMAP+160)&$FFFF
copwait:
        dc.b    $8C,$07                         ; WAIT line $2C+height ($8C
        dc.w    $FFFE                           ; patched), any horizontal
        dc.w    BPLCON0,$0200                   ; 0 planes: flat COLOR00
        dc.w    $FFFF,$FFFE                     ; end of list

palbuf: ds.w    32

        even
image9:
        incbin  "9.AMI"
        even                            ; the ST lesson: align every image
image12:
        incbin  "12.AMI"
