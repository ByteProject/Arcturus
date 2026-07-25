; probe.asm - the Plus/4 (TED) arc_image probe (B12, arc_image/reference/design.md)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A PRG for TED multicolour bitmap mode (160 wide, 2-bit pixels) that
; displays three embedded .arc images (picture 8 in mode 9, then mode
; 12, then picture 12, a keypress apart, cycling), written from the
; blueprint alone: the reference Plus/4 loader for the format.
; Build (ACME):
;
;   acme -f cbm -o probe.prg probe.asm
;
; The codec is ZX0 (codec 1) under the 2048-byte window guarantee, and
; the decompressor is the shared dzx0r_6502.asm ring decoder with its
; default zero-page cells ($08-$12): the probe runs under SEI and never
; returns to BASIC, so the BASIC workspace is ours.
;
; THE P4 PAYLOAD (all sections in native order):
;   type 1  bitmap      cell-ordered mode rows, 3840 bytes (12 cell rows)
;   type 2  screen      per-cell hue pairs   (hueA<<4 | hueB), 480 bytes
;   type 3  color       per-cell luma pairs  (lumA<<4 | lumB), 480 bytes
;   type 7  regs        two global registers, each (hue<<4) | luma:
;                       background (%00) and aux (%11)
;
; TED renders pixel %00 from $FF15, %11 from $FF16, and %01/%10 from the
; cell's nibbles: hue from the colour matrix, luminance from the
; luminance matrix, high nibble for %01 and low for %10 (the codec's
; stated intent; THE PROBE IS THE VERIFICATION). Hardware register
; bytes want (luma<<4)|hue, so the two reg bytes swap nibbles on the
; way in. No interrupts, no per-line work: the A8's whole DLI war does
; not exist on this machine; the picture is a register file and memory.
;
; The band is 96 lines, centred on the 200-line screen: cell rows 6-17,
; bitmap offset $780, matrix offset $F0.

!cpu 6502

; ---- TED registers -------------------------------------------------------------
TED_VERT = $ff06        ; ECM/BMM/enable/rows/vscroll
TED_HORZ = $ff07        ; MCM/columns/hscroll
TED_IMASK = $ff0a       ; interrupt mask
TED_IACK = $ff09        ; interrupt latch (write 1s to ack)
TED_BMBASE = $ff12      ; bits 5-3: bitmap base address bits 15-13
TED_VMBASE = $ff14      ; bits 7-3: matrix base address bits 15-11
TED_BG   = $ff15        ; background register (%00)
TED_AUX  = $ff16        ; first colour register (%11 in MC bitmap)
TED_BORDER = $ff19
KBD_ROWS = $fd30        ; 6529: keyboard row select
KBD_LATCH = $ff08       ; keyboard column latch

; ---- zero page: BASIC workspace, ours under SEI --------------------------------
src     = $d4           ; zp pointer to the .arc
tbl     = $d6           ; zp pointer to the current table entry
cur     = $d8           ; the current compressed stream
pdst    = $da           ; the emit cursor (linear store-and-advance)
cnt     = $dc           ; sections left
; the ring decoder uses its default cells $08-$12 (see dzx0r_6502.asm)

BITMAP  = $6000         ; ABOVE the program: the PRG ends near $2EE6,
LUMMAT  = $5800         ; and a bitmap at $2000 made draw's wipe eat
COLMAT  = $5c00         ; its own embedded images (black screen, green
                        ; border: the runaway decode's emit pointer
                        ; strafing the TED registers)
BANDBM  = BITMAP        ; the band is the TOP of the screen, like
BANDLUM = LUMMAT        ; every target's probe: cell row 0
BANDCOL = COLMAT

; ---- the PRG skeleton ----------------------------------------------------------
        * = $1001
        !byte $0b, $10, $0a, $00, $9e   ; 10 SYS4109
        !text "4109"
        !byte 0, 0, 0

start:  sei
        lda #$00
        sta TED_IMASK           ; no TED interrupts
        lda #$ff
        sta TED_IACK            ; and none pending
        lda #$3b                ; bitmap mode, screen on, 25 rows
        sta TED_VERT
        lda #$18                ; multicolour, 40 columns
        sta TED_HORZ
        lda #$18                ; bitmap at $6000, fetched from RAM
        sta TED_BMBASE
        lda #$58                ; matrices at $5800 (lum) / $5c00 (col)
        sta TED_VMBASE
        lda #$00
        sta TED_BORDER          ; black frame around the band
        lda #<lemit             ; the decoder's emit vector: linear store
        sta zr_emit+1
        lda #>lemit
        sta zr_emit+2

cycle:  lda #<image9            ; picture 8 in mode 9, then mode 12,
        sta src+0               ; then picture 12, a keypress apart:
        lda #>image9            ; the standard probe programme
        sta src+1
        jsr draw
        jsr waitkey
        lda #<image12
        sta src+0
        lda #>image12
        sta src+1
        jsr draw
        jsr waitkey
        lda #<imagep12
        sta src+0
        lda #>imagep12
        sta src+1
        jsr draw
        jsr waitkey
        jmp cycle               ; a probe holds its pictures; reset ends it

; ---- any key, by the metal: rows low, strobe the latch, read ------------------
waitkey:
-       jsr scan                ; wait for all keys up first
        cmp #$ff
        bne -
-       jsr scan                ; then for a press
        cmp #$ff
        beq -
        rts
scan:   lda #$00
        sta KBD_ROWS
        sta KBD_LATCH           ; any write strobes the latch
        lda KBD_LATCH           ; $ff = nothing held
        rts

; ---- draw: clear the canvas, walk the .arc at (src) ----------------------------
draw:   lda #>BITMAP            ; wipe the full bitmap: $6000-$7FFF
        ldx #$20                ; (32 pages), so the off-band rows are
        jsr wipe                ; %00 = background... which is black
        lda #>LUMMAT            ; only if the matrices are black too:
        ldx #$08                ; both 1K attribute pages to zero
        jsr wipe                ; (hue 0 = TED black, luma 0)
        lda #$00                ; and the registers dark while drawing
        sta TED_BG
        sta TED_AUX

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
        jmp regs                ; all sections walked: light the globals
+       ldy #0                  ; the entry's type picks the destination
        lda (tbl),y
        cmp #1
        bne +
        lda #<BANDBM            ; bitmap -> the centred band
        sta pdst+0
        lda #>BANDBM
        sta pdst+1
        jsr unpack
        jmp .next
+       cmp #2
        bne +
        lda #<BANDCOL           ; screen (hue pairs) -> colour matrix
        sta pdst+0
        lda #>BANDCOL
        sta pdst+1
        jsr unpack
        jmp .next
+       cmp #3
        bne +
        lda #<BANDLUM           ; color (luma pairs) -> luminance matrix
        sta pdst+0
        lda #>BANDLUM
        sta pdst+1
        jsr unpack
        jmp .next
+       cmp #7
        bne .next
        lda #<regbuf            ; the two globals, applied after the walk
        sta pdst+0
        lda #>regbuf
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
        lda tbl+1
        adc #0
        sta tbl+1
        dec cnt
        jmp .each

; the .arc reg byte is (hue<<4)|luma; TED wants (luma<<4)|hue
regs:   lda regbuf
        jsr tedreg
        sta TED_BG
        lda regbuf+1
        jsr tedreg
        sta TED_AUX
        rts
tedreg: pha
        and #$0f                ; luma to the high nibble
        asl
        asl
        asl
        asl
        sta regtmp
        pla
        lsr                     ; hue to the low nibble
        lsr
        lsr
        lsr
        ora regtmp
        rts

wipe:   sta pdst+1              ; A = first page, X = page count
        lda #$00
        sta pdst+0
        tay
-       sta (pdst),y
        iny
        bne -
        inc pdst+1
        dex
        bne -
        rts

unpack: ldx cur+0               ; the ring decoder: src in X/A, output
        lda cur+1               ; through the emit vector
        jmp dzx0r               ; its rts returns to unpack's caller

; the one emit the P4 needs: every section is contiguous native memory
lemit:  ldy #0
        sta (pdst),y
        inc pdst+0
        bne +
        inc pdst+1
+       rts

regbuf: !byte 0, 0
regtmp: !byte 0

; ---- the shared ring decoder ---------------------------------------------------
zx0ring = $0800         ; the 2K window ring, 2K-aligned: the cassette
                        ; and input buffers, ours under SEI
        !source "../c64/dzx0r_6502.asm"

; ---- the pictures, whole .arc files --------------------------------------------
image9:
        !bin "9.P4"             ; picture 8, mode 9
image12:
        !bin "12.P4"            ; picture 8, mode 12
imagep12:
        !bin "pic12.P4"         ; picture 12, mode 12
