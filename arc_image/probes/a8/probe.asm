; probe.asm - the Atari 8-bit arc_image probe (B12 R4, arc_image/reference/design.md)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; An .xex for ANTIC mode E (160 wide, 2-bit pixels) that displays two
; embedded .arc images (mode 9, then mode 12 after a keypress), written
; from the blueprint alone: the reference A8 loader for the format.
; Build (ACME):
;
;   acme -f plain -o probe.xex probe.asm
;
; and run in atari800 with BASIC off (the probe owns RAM from $3000 up).
; The codec is ZX0 (codec 1) under the 2048-byte window guarantee, and
; the decompressor is the shared dzx0r_6502.asm ring decoder
; (machine-verified against the corpus), with its zero-page cells moved
; into the FP scratch area: the C64 defaults ($08-$12) are OS cells here
; (DOSVEC, POKMSK), and a probe that clobbers the interrupt mask while
; running display-list interrupts would be lying to itself.
;
; THE A8 PAYLOAD (both sections in native order):
;   type 1  bitmap      linear mode-E rows, 40 bytes each (2880 or 3840)
;   type 6  line table  4 GTIA register bytes per scan line (288 or 384);
;                       the values repeat within each 8-line segment, so
;                       the probe compacts them to one palette per
;                       segment and replays them with a DLI chain:
;                       pixel %00 = COLBK, %01 = COLPF0, %10 = COLPF1,
;                       %11 = COLPF2, exactly the table's byte order.
; Segment 0 loads through the OS shadows (the VBLANK handler restores
; them every frame); a deferred VBI resets the chain cursor, and the
; DLI on the last line of each segment loads the next segment's four
; registers. A 72-line image simply leaves segments 9-11 black: the
; bitmap is cleared and the compacted table is zeroed before every draw.

!cpu 6502

; ---- OS equates ----------------------------------------------------------------
WSYNC   = $d40a
NMIEN   = $d40e
COLBK   = $d01a
COLPF0  = $d016
COLPF1  = $d017
COLPF2  = $d018
VDSLST  = $0200
SDLSTL  = $0230
COLOR0  = $02c4         ; shadow: PF0
COLOR1  = $02c5         ; shadow: PF1
COLOR2  = $02c6         ; shadow: PF2
COLOR4  = $02c8         ; shadow: BAK
CH      = $02fc
SETVBV  = $e45c
XITBV   = $e462

; ---- zero page: FP scratch, free while no floating point runs ------------------
src     = $d4           ; zp pointer to the .arc
tbl     = $d6           ; zp pointer to the current table entry
cur     = $d8           ; the current compressed stream
pdst    = $da           ; the emit cursor (linear store-and-advance)
cnt     = $dc           ; sections left
segidx  = $dd           ; the DLI chain's segment cursor

zr_src  = $e0           ; the ring decoder's cells (see dzx0r_6502.asm)
zr_bits = $e2
zr_noff = $e3
zr_len  = $e5
zr_wp   = $e7

BMP     = $9000         ; 3840 bytes of mode-E rows, one 4K block

; ---- the XEX skeleton ----------------------------------------------------------
        * = $2ffa               ; six header bytes ahead of the load
        !word $ffff
        !word load_start
        !word load_end - 1

load_start:

start:  lda #<lemit             ; the decoder's emit vector: linear store
        sta zr_emit+1
        lda #>lemit
        sta zr_emit+2
        lda #0
        sta segidx
        lda #<dli
        sta VDSLST
        lda #>dli
        sta VDSLST+1
        ldy #<vbi               ; deferred VBI: resets the DLI cursor
        ldx #>vbi
        lda #7
        jsr SETVBV
        lda #<dlist             ; our display list, via the OS shadow
        sta SDLSTL
        lda #>dlist
        sta SDLSTL+1
        lda #$c0                ; VBI + DLI
        sta NMIEN

        lda #<image9
        sta src+0
        lda #>image9
        sta src+1
        jsr draw
        jsr waitkey
        lda #<image12
        sta src+0
        lda #>image12
        sta src+1
        jsr draw
        jsr waitkey
-       jmp -                   ; a probe holds its picture; reset ends it

waitkey:
        lda #$ff
        sta CH
-       lda CH
        cmp #$ff
        beq -
        lda #$ff
        sta CH
        rts

; ---- draw: clear the canvas, walk the .arc at (src) ----------------------------

draw:   lda #0                  ; wipe the bitmap: BMP..BMP+$0EFF
        sta pdst+0
        lda #>BMP
        sta pdst+1
        ldy #0
        tya
-       sta (pdst),y
        iny
        bne -
        inc pdst+1
        ldx pdst+1
        cpx #(>BMP) + $0f       ; parenthesized: acme's > binds LOW, and
        bne -                   ; the unbracketed form wiped all of RAM
                                ; through POKEY (Stefan heard it: minutes
                                ; of "disk stress" was the runaway loop
                                ; strafing $D2xx)
        ldx #47                 ; zero the compacted segment table
        lda #0
-       sta segtab,x
        dex
        bpl -

        ldy #0                  ; sanity: the magic "ARCI"
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
        jmp shadows             ; all sections walked: arm segment 0
+       ldy #0                  ; the entry's type picks the destination
        lda (tbl),y
        cmp #1
        bne +
        lda #<BMP               ; bitmap -> the mode-E canvas
        sta pdst+0
        lda #>BMP
        sta pdst+1
        jsr unpack
        jmp .next
+       cmp #6
        bne .next
        lda #<linetab           ; line table -> its buffer
        sta pdst+0
        lda #>linetab
        sta pdst+1
        jsr unpack

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

unpack: ldx cur+0               ; the ring decoder: src in X/A, output
        lda cur+1               ; through the emit vector
        jmp dzx0r               ; its rts returns to unpack's caller

; the one emit the A8 needs: both sections are contiguous native memory
lemit:  ldy #0
        sta (pdst),y
        inc pdst+0
        bne +
        inc pdst+1
+       rts

; compact the per-line table (4 bytes per line) into one palette per
; 8-line segment (the first line of each; the values repeat within a
; segment), then arm segment 0 through the OS shadows.
shadows:
        lda #<linetab
        sta pdst+0
        lda #>linetab
        sta pdst+1
        ldx #0                  ; segtab cursor 0..47
.seg:   ldy #0
-       lda (pdst),y
        sta segtab,x
        inx
        iny
        cpy #4
        bne -
        lda pdst+0              ; the next segment's first line: +32
        clc
        adc #32
        sta pdst+0
        bcc +
        inc pdst+1
+       cpx #48
        bne .seg
        lda segtab+0            ; segment 0 through the shadows
        sta COLOR4
        lda segtab+1
        sta COLOR0
        lda segtab+2
        sta COLOR1
        lda segtab+3
        sta COLOR2
        rts

; ---- interrupts -----------------------------------------------------------------
; deferred VBI: the chain cursor rests at segment 0 every frame
vbi:    lda #0
        sta segidx
        jmp XITBV

; DLI, on the last line of segment s: load segment s+1's four registers
dli:    pha
        txa
        pha
        inc segidx
        lda segidx
        cmp #12
        bcs +                   ; safety: never index past the table
        asl
        asl
        tax
        lda segtab+0,x
        sta WSYNC
        sta COLBK
        lda segtab+1,x
        sta COLPF0
        lda segtab+2,x
        sta COLPF1
        lda segtab+3,x
        sta COLPF2
+       pla
        tax
        pla
        rti

; ---- the display list: 96 mode-E lines, DLI on each segment's last line --------
; segment 0: the LMS line + 6 plain + 1 DLI line; segments 1-10: 7 plain
; + 1 DLI line; segment 11: 8 plain (no DLI below the band).
dlist:  !byte $70, $70, $70     ; 24 blank lines
        !byte $4e               ; mode E + LMS
        !word BMP
        !fill 6, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 7, $0e
        !byte $8e
        !fill 8, $0e
        !byte $41               ; JVB
        !word dlist

!source "../c64/dzx0r_6502.asm"

        !align 2047, 0
zx0ring: !fill 2048, 0
linetab: !fill 384, 0
segtab:  !fill 48, 0

image9:
        !bin "9.A8"
image12:
        !bin "12.A8"
load_end:

; ---- autostart -----------------------------------------------------------------
        !word $02e0
        !word $02e1
        !word start
