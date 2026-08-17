; probe.asm - the Apple II DHGR arc_image probe (B12 R5, arc_image/reference/design.md sections 6 and 8)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; Double hi-res on a 128K IIe/IIc/IIgs (the R5 ruling: DHGR only),
; displaying the two embedded .arc images (mode 9, then mode 12 after
; a keypress): the reference Apple II loader for the format. Build
; (ACME, on the orb machine):
;
;   acme -f plain -o probe.bin probe.asm
;
; mk_a2probe.py lays probe.bin onto a bootable 140K .dsk behind a minimal
; boot-sector chain loader; run_probe.py executes the same binary
; headless first, on the strict 6502 core under an Apple II softswitch
; model, and proves both pages' bytes and the switch end-state against
; the pair files before any emulator runs. The emulator verdict is
; AppleWin under wine, and the video mode MUST be composite: the
; conversion targets the NTSC signal (design.md, the signal class), and
; an RGB-card decode shows different colours by construction.
;
; PLAIN 6502 OPCODES; everything Apple about it is a softswitch:
;
;   $C00D 80COL on      $C050 graphics      $C057 hi-res
;   $C052 full screen   $C05E AN3 off = the DHGR gate
;   $C001 80STORE on: PAGE2 ($C055/$C054) then banks the $2000
;         window between the AUX and MAIN hi-res pages, which is the
;         whole memory access story for a DHGR loader
;   $C000/$C010 keyboard and strobe
;
; .arc recap (design.md section 10, all words BIG-endian): 16-byte
; header (magic "ARCI", version, target, mode, section count at +7,
; width at +8, height at +10, id, codec, provenance), then 6-byte
; table entries (type, flags, uncompressed length, compressed length),
; then the ZX0 streams in table order. The AP2 payload:
;   type 1  bitmap   the AUX page: 40 bytes per row, display row
;                    order, 72 or 96 rows
;   type 2  screen   the MAIN page, same shape
; Rows land on the screen through the classic hi-res line-address
; table (the one documented exception to dumb linear unpacking):
; addr(y) = $2000 + (y&7)*$400 + ((y>>3)&7)*$80 + (y>>6)*$28.
;
; The codec is ZX0 (codec 1, the 8-bit default), decoder dzx0_6502
; (the staged bitfire lineage, vendored beside this probe unchanged,
; zero page $F8-$FD): each section decodes to the STAGE buffer, then
; its rows scatter through the line table with PAGE2 selecting the
; page. Memory: the probe with its embedded pairs loads at $6000
; (clear of the hi-res window, the stage, and zero page); STAGE at
; $4000 (3840 bytes at the mode-12 maximum, to $4EFF).

!cpu 6502

src     = $02           ; zp pointer to the .arc
tbl     = $04           ; zp pointer to the current table entry
dst     = $06           ; zp pointer for the row scatter
stg     = $08           ; zp pointer walking the stage
cnt     = $0A           ; sections left
styp    = $0B           ; current section type
rows    = $0C           ; the band's rows (72 or 96)
line    = $0D           ; the row being scattered
scur    = $0E           ; the current compressed stream (2 cells)

STAGE   = $4000

        * = $6000

start:  sei
        ; the screen: 80-column store, graphics, hi-res, full screen,
        ; AN3 off (the DHGR gate); nothing shows yet worth hiding, the
        ; pages are cleared before the first image lands
        sta $c00d               ; 80COL on
        sta $c050               ; graphics
        sta $c057               ; hi-res
        sta $c052               ; full screen
        sta $c05e               ; AN3 off: double hi-res
        sta $c001               ; 80STORE: PAGE2 banks the window
        jsr clear
        ; the review cycle
loop:   lda #<image9
        ldx #>image9
        jsr show
        jsr waitkey
        lda #<image12
        ldx #>image12
        jsr show
        jsr waitkey
        jmp loop

; ---- clear: both pages' full hi-res region to black ----------------------

clear:  sta $c055               ; the AUX page first
        jsr clr1
        sta $c054               ; then MAIN
clr1:   lda #$20
        sta dst+1
        lda #0
        sta dst
        tay
.pg:    lda #0
.by:    sta (dst),y
        iny
        bne .by
        inc dst+1
        lda dst+1
        cmp #$40
        bne .pg
        rts

; ---- waitkey: the keyboard register --------------------------------------

waitkey:
        lda $c000
        bpl waitkey
        sta $c010               ; strobe: consume it
        rts

; ---- show: the .arc at A/X (lo/hi) ---------------------------------------

show:   sta src
        stx src+1
        ldy #0                  ; sanity: the magic
        lda (src),y
        cmp #'A'
        bne sbail
        iny
        lda (src),y
        cmp #'R'
        beq sok
sbail:  rts
sok:    ldy #11                 ; height low byte (72 or 96; BE word)
        lda (src),y
        sta rows
        ; the table cursor, and the first stream: src + 16 + count*6
        lda src
        clc
        adc #16
        sta tbl
        lda src+1
        adc #0
        sta tbl+1
        ldy #7
        lda (src),y
        sta cnt
        asl                     ; *2
        clc
        adc cnt                 ; *3
        asl                     ; *6
        adc #16
        clc
        adc src
        sta scur
        lda src+1
        adc #0
        sta scur+1
walk:   ldy #0                  ; type
        lda (tbl),y
        sta styp
        ; decode the stream at (scur) to STAGE
        lda #<STAGE
        sta .lz_dst
        lda #>STAGE
        sta .lz_dst+1
        ldx scur
        lda scur+1
        jsr .depacker_start
        ; scatter the staged rows through the line table; type 1 is
        ; the AUX page, type 2 MAIN
        lda styp
        cmp #2
        beq domain
        sta $c055               ; PAGE2: the window shows AUX
        jsr scatter
        jmp next
domain: sta $c054               ; the window shows MAIN
        jsr scatter
next:   ; advance the stream cursor by the table's compressed length
        ; (big-endian at +4/+5); a decoder's exit registers are not a
        ; contract (the Next probe's lesson, kept)
        ldy #5
        lda (tbl),y
        clc
        adc scur
        sta scur
        dey
        lda (tbl),y
        adc scur+1
        sta scur+1
        ; next table entry
        lda tbl
        clc
        adc #6
        sta tbl
        bcc twrap
        inc tbl+1
twrap:  dec cnt
        bne walk
        rts

; ---- scatter: STAGE's rows to the hi-res line addresses ------------------

scatter:
        lda #<STAGE
        sta stg
        lda #>STAGE
        sta stg+1
        lda #0
        sta line
.row:   ldx line                ; the line table: assembled, not computed
        lda linelo,x
        sta dst
        lda linehi,x
        sta dst+1
        ldy #39                 ; move one 40-byte row
.mv:    lda (stg),y
        sta (dst),y
        dey
        bpl .mv
        lda stg                 ; stage cursor forward one row
        clc
        adc #40
        sta stg
        bcc .nc
        inc stg+1
.nc:    inc line
        lda line
        cmp rows
        bne .row
        rts

; the classic hi-res line-address table, computed by the assembler:
; addr(y) = $2000 + (y&7)*$400 + ((y>>3)&7)*$80 + (y>>6)*$28
linelo: !for y, 0, 95 { !byte <($2000 + (y & 7) * $400 + ((y >> 3) & 7) * $80 + (y >> 6) * $28) }
linehi: !for y, 0, 95 { !byte >($2000 + (y & 7) * $400 + ((y >> 3) & 7) * $80 + (y >> 6) * $28) }

; ---- the decoder's seam --------------------------------------------------
; dzx0_6502.asm: entry X = source lo, A = source hi, lz_dst set;
; its zero page lives at $F8-$FD (see the vendored file).

        !src "dzx0_6502.asm"

image9: !bin "9.AP2"
image12:
        !bin "12.AP2"
