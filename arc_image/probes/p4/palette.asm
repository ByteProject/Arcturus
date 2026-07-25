; palette.asm - the TED palette staircase (B12, the P4 calibration probe)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Displays the full TED gamut as a swatch grid: 16 hue columns (0-15,
; two cells wide) by 8 luma rows (three cell-rows tall), in multicolour
; bitmap mode with every pixel set to code %01, so each swatch's colour
; comes purely from its cell's attribute nibbles. One screenshot of
; this screen IS the measured TED palette: arcimg's _ted_color is
; preview-grade by its own comment, and this display retires it with
; emulator truth (the GTIA wheel playbook, applied to TED).
; Build (ACME): acme -f cbm -o palette.prg palette.asm

!cpu 6502

TED_VERT = $ff06
TED_HORZ = $ff07
TED_IMASK = $ff0a
TED_IACK = $ff09
TED_BMBASE = $ff12
TED_VMBASE = $ff14
TED_BG   = $ff15
TED_AUX  = $ff16
TED_BORDER = $ff19

ptr     = $d4

BITMAP  = $6000
LUMMAT  = $5800
COLMAT  = $5c00

        * = $1001
        !byte $0b, $10, $0a, $00, $9e   ; 10 SYS4109
        !text "4109"
        !byte 0, 0, 0

start:  sei
        lda #$00
        sta TED_IMASK
        lda #$ff
        sta TED_IACK
        lda #$3b                ; bitmap mode, screen on
        sta TED_VERT
        lda #$18                ; multicolour, 40 columns
        sta TED_HORZ
        lda #$18                ; bitmap at $6000, RAM
        sta TED_BMBASE
        lda #$58                ; matrices at $5800/$5c00
        sta TED_VMBASE
        lda #$00
        sta TED_BORDER
        sta TED_BG
        sta TED_AUX

        lda #>BITMAP            ; every pixel code %01: the swatch
        sta ptr+1               ; colour is the cell's A nibbles
        lda #<BITMAP
        sta ptr+0
        ldx #$20                ; 32 pages
        lda #$55
        ldy #0
-       sta (ptr),y
        iny
        bne -
        inc ptr+1
        dex
        bne -

; the matrices: cell (cx, cy), cx 0-39, cy 0-24
;   cx < 32:  hue = cx/2   else black column
;   cy < 24:  luma = cy/3  else black row
; colour matrix byte = hue<<4 | hue; luminance byte = luma<<4 | luma
        ldx #0                  ; cell index low; walk 1000 cells via
        lda #0                  ; row/col counters in zp
row     = $d6
col     = $d7
cell_lo = $d8
cell_hi = $d9
        sta row
        sta cell_lo
        sta cell_hi
.rows:  lda #0
        sta col
.cols:  lda row                 ; luma = row/3 (rows 0-23), else 0
        cmp #24
        bcs .black
        lda col
        cmp #32
        bcs .black
        lsr                     ; hue = col/2
        sta ptr                 ; hue in ptr (scratch)
        asl
        asl
        asl
        asl
        ora ptr                 ; hue<<4 | hue
        pha
        lda row                 ; luma = row/3: subtract 3s
        ldy #$ff
-       iny
        sec
        sbc #3
        bcs -
        tya                     ; luma in A
        sta ptr
        asl
        asl
        asl
        asl
        ora ptr                 ; luma<<4 | luma
        tay
        pla
        jmp .store
.black: lda #0
        tay
.store: pha                     ; A = colour byte, Y = luminance byte
        lda cell_lo
        sta ptr+0
        lda cell_hi
        clc
        adc #>COLMAT
        sta ptr+1
        pla
        ldx #0
        sta (ptr,x)
        lda cell_hi
        clc
        adc #>LUMMAT
        sta ptr+1
        tya
        sta (ptr,x)
        inc cell_lo
        bne +
        inc cell_hi
+       inc col
        lda col
        cmp #40
        bne .cols
        inc row
        lda row
        cmp #25
        bne .rows

-       jmp -                   ; hold the staircase; reset ends it
