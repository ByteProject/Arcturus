; probe.asm - the MEGA65 arc_image probe (B12 R5, arc_image/reference/design.md sections 6 and 8)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; VIC-IV full-colour characters at H320, displaying the two embedded
; .arc images (mode 9, then mode 12 after a keypress): the reference
; MEGA65 loader for the format. Build (ACME, on the orb machine):
;
;   acme -f cbm -o probe.prg probe.asm
;
; and run in Xemu (xmega65 -prg probe.prg) or from SD on the metal.
; run_probe.py executes the same binary headless first, on a strict
; 6502 core under a VIC-IV register model, and proves the character
; data, the screen matrix, the palette pages, and the register
; discipline against the pair files before any emulator runs.
;
; PLAIN 6510 OPCODES, deliberately: no 45GS02 extensions, no DMAgic.
; The MEGA65's own CPU runs this unchanged, and it keeps the probe
; provable on the ordinary 6502 core the repo already trusts (the
; C64 probe's manner). Everything MEGA65 about it is memory-mapped.
;
; WHY THE MEGA65 IS FREE OF TRICKS. Full-colour mode makes each 8x8
; character 64 chunky palette bytes, and the .arc bitmap section IS
; the character set, in reading order: the whole band decompresses
; straight to the charset base, no shuffling, no planes, no fixups.
; The screen matrix is formulaic (chars 0, 1, 2, ... left to right,
; top to bottom, 16-bit numbers) and the loader generates it once.
; The palette section is stored nibble-swapped exactly as the
; VIC-III/IV palette registers want their bytes, so the upload is a
; copy. Palette index 255 is never used by pixels (the format
; reserves it for the hardware's alpha path), which hands the loader
; a free entry: it is set to black and used for border and backdrop.
;
; THE HOTREG DISCIPLINE (the one MEGA65 trap worth naming): writing
; any legacy VIC-II register while hot registers are enabled makes
; the VIC-IV recalculate its layout from the legacy view, clobbering
; the precise registers. So the order is fixed: knock, legacy writes
; first (border, backdrop, H640 off), then HOTREG OFF, and only then
; the precise registers (pointers, line step, character count).
;
; .arc recap (design.md section 10, all words BIG-endian): 16-byte
; header (magic "ARCI", version, target, mode, section count at +7,
; width at +8, height at +10, id, codec, provenance), then 6-byte
; table entries (type, flags, uncompressed length, compressed
; length), then the LZSA2 streams in table order. The M65 payload:
;   type 1  bitmap   the full-colour character set: 64 bytes per 8x8
;                    char, reading order; 23040 bytes in mode 9,
;                    30720 in mode 12, decoded straight to CHARS
;   type 5  palette  255 RGB triples, nibble-swapped (the register
;                    file's own encoding), scattered to $D100/2/300
;
; The codec is LZSA2 (codec 2, docs/08 part B), decoder
; decompress_fast_v2 (Emmanuel Marty & Peter Ferrie, vendored beside
; this probe as unlzsa2_6502.asm), self-modifying: the source and
; destination are stored into its instruction stream, and NIBCOUNT
; lives at zero page $FC.
;
; Memory: the mode-12 charset (30720 bytes) plus both embedded pairs
; (15265) plus screen, palette, and code exceed what fits above the
; BASIC load address, so BOOT RELOCATES: the .prg loads at $2001
; (stub, boot copier, the resident code blob, both pairs), the boot
; copies the resident code to CODE ($0500) and the pairs high, just
; under the I/O hole (IMG9 at $9300, IMG12 at $AD00; the copies are
; page-granular, and IMG12's 35 pages end exactly at $CFFF),
; then runs from the copy. The charset then decodes to CHARS ($1800,
; through $8FFF in mode 12, freely overwriting the spent load image),
; the screen matrix lives at SCREEN ($8F00, 480 16-bit char numbers),
; the palette stages at PALBUF ($0200), and colour RAM's first 960
; pairs are zeroed through the $D800 window with CRAM2K giving the
; second K. Build-time !if guards fail the assembly loudly if a
; regenerated pair outgrows its region.

!cpu 6510

src     = $02           ; zp pointer to the .arc
tbl     = $04           ; zp pointer to the current table entry
pal     = $06           ; zp pointer for the palette scatter
cnt     = $08           ; sections left
styp    = $09           ; current section type
rows    = $0A           ; the band's character rows (9 or 12)
mch     = $0B           ; matrix: the running char number
mcell   = $0D           ; matrix: the running cell index
mlim    = $0F           ; matrix: cells inside the band (rows*40)

BLANKCH = $9280         ; 64 bytes of $FF: the all-black char (palette
                        ; entry 255), named by every cell past the band
BLANKNO = BLANKCH / 64

CHARS   = $1640
SCREEN  = $8E40
PALBUF  = $0200
CODE    = $0500
IMG9    = $9300
IMG12   = $AD00

        * = $2001
        ; 10 SYS 8205 (BASIC 65's stub, the C64 stub's shape at $2001)
        !byte $0b,$20,$0a,$00,$9e,$38,$32,$30,$35,$00,$00,$00

; ---- boot: relocate, then run from the copy ------------------------------
;
; Three straight copies with no overlap (every destination is above
; the whole load image): the resident blob to CODE, the pairs to
; their high homes. Then the load region is spent, and the charset
; may decode over it.

boot:   sei
        lda #<blob
        sta $02
        lda #>blob
        sta $03
        lda #<CODE
        sta $04
        lda #>CODE
        sta $05
        ldx #>(blobend-blob+$FF)
        jsr copy
        lda #<pair9
        sta $02
        lda #>pair9
        sta $03
        lda #<IMG9
        sta $04
        lda #>IMG9
        sta $05
        ldx #>(pair9end-pair9+$FF)
        jsr copy
        lda #<pair12
        sta $02
        lda #>pair12
        sta $03
        lda #<IMG12
        sta $04
        lda #>IMG12
        sta $05
        ldx #>(pair12end-pair12+$FF)
        jsr copy
        jmp start

copy:   ldy #0                  ; X whole pages, forward
cpg:    lda ($02),y
        sta ($04),y
        iny
        bne cpg
        inc $03
        inc $05
        dex
        bne cpg
        rts

blob:
!pseudopc CODE {

start:  sei
        ; the knock: VIC-IV / MEGA65 I/O personality
        lda #$45
        sta $d02f
        lda #$54
        sta $d02f
        ; BLANK FIRST, the legacy way (DEN off), border and backdrop
        ; to the BOOT palette's black: nothing of the setup below is
        ; ever seen, and no frame shows the boot screen reinterpreted
        ; (the flash of the first builds). The reveal colours come at
        ; the reveal, when palette entry 255 is ours and black.
        lda $d011
        and #$ef
        sta $d011
        lda #0
        sta $d020
        sta $d021
        ; the C65 ROM overlays OFF (bits 3/4/5/7: ROM at $8000, $A000,
        ; $C000, $E000): the pairs live high, and under a ROM shadow
        ; their bytes would read back as BASIC (the first Xemu run's
        ; black second image: image 12's tail sat under ROMC)
        lda $d030
        and #%01000111
        sta $d030
        ; LEGACY writes first, while hot registers still listen:
        ; H640 and V400 off (H320, 200-line view)
        lda $d031
        and #$77
        sta $d031
        ; hot registers OFF: the precise registers now stay put
        lda $d05d
        and #$7f
        sta $d05d
        ; nothing visible while we work
        lda #0
        sta $d07b               ; DISPROWS 0
        ; 16-bit characters, full-colour for both char ranges, and
        ; VFAST: the decode runs at full speed, not the C65's 3.5MHz
        lda #$47
        sta $d054               ; VFAST | CHR16 | FCLRLO | FCLRHI
        ; a text row is 40 chars of 2 bytes, and it DISPLAYS 40: the
        ; ROM boots an 80-column screen, and CHRCOUNT survives the
        ; hotreg recalcs (the first Xemu run interleaved every other
        ; row: 80 matrix entries consumed per line against a 40-wide
        ; matrix)
        lda #80
        sta $d058               ; LINESTEP low
        lda #0
        sta $d059
        lda #40
        sta $d05e               ; CHRCOUNT: display width in chars
        ; the precise pointers: screen at SCREEN, charset at CHARS
        lda #<SCREEN
        sta $d060
        lda #>SCREEN
        sta $d061
        lda #0
        sta $d062
        sta $d063
        lda #<CHARS
        sta $d068
        lda #>CHARS
        sta $d069
        lda #0
        sta $d06a
        ; the colour RAM base to 0: the ROM boot leaves COLPTR aimed
        ; at its own 80-column screen's colour data, whose stale
        ; attribute bytes garbled exactly the band's top rows (the
        ; rows under the boot banner) while the CPU window zeroed
        ; offset 0 all along
        sta $d064
        sta $d065
        ; palette entry 255 = black: border, backdrop, and the blank
        ; char below all ride it
        sta $d1ff
        sta $d2ff
        sta $d3ff
        ; the all-black char: 64 bytes of $FF in the gap between the
        ; screen matrix and IMG9
        lda #$ff
        ldx #63
blc:    sta BLANKCH,x
        dex
        bpl blc
        jsr colram
        ; the review cycle
loop:   lda #<IMG9
        ldx #>IMG9
        jsr show
        jsr waitkey
        lda #<IMG12
        ldx #>IMG12
        jsr show
        jsr waitkey
        jmp loop

; ---- the screen matrix: 16-bit char numbers, formulaic -------------------
;
; In full-colour mode a char number times 64 is an ABSOLUTE chip-RAM
; address (CHARPTR plays no part), so the matrix counts from CHARS/64
; upward: the band's cells name the charset in reading order (the
; first Xemu run counted from 0 and displayed zero page and stack as
; art, the whole picture 92 characters late). The matrix is built PER
; IMAGE: cells inside the band (rows*40) run sequentially, and every
; cell after them, thirteen rows' worth, names the all-black char, so
; the partial fourteenth row the 200-line window exposes below the
; band shows black, never stale entries (the garbage strip of the
; first builds).

CHBASE = CHARS / 64

matrix: lda #<SCREEN
        sta pal
        lda #>SCREEN
        sta pal+1
        lda #<CHBASE            ; the running char number
        sta mch
        lda #>CHBASE
        sta mch+1
        lda #0                  ; the running cell
        sta mcell
        sta mcell+1
        ; the band's cell count: rows*40 (360 or 520-40=480)
        ldx #<360
        ldy #>360
        lda rows
        cmp #12
        bne m9
        ldx #<480
        ldy #>480
m9:     stx mlim
        sty mlim+1
        ldy #0
mrow:   ; inside the band? (mcell < mlim)
        lda mcell
        cmp mlim
        lda mcell+1
        sbc mlim+1
        bcs mblank
        lda mch                 ; sequential char
        sta (pal),y
        iny
        lda mch+1
        sta (pal),y
        iny
        jmp mstep
mblank: lda #<BLANKNO           ; the all-black char
        sta (pal),y
        iny
        lda #>BLANKNO
        sta (pal),y
        iny
mstep:  cpy #0
        bne mnowrap
        inc pal+1
mnowrap:
        inc mch
        bne mc2
        inc mch+1
mc2:    inc mcell
        bne mc3
        inc mcell+1
mc3:    lda mcell
        cmp #<520               ; thirteen rows written in all
        bne mrow
        lda mcell+1
        cmp #>520
        bne mrow
        rts

; ---- colour RAM: one enhanced DMA fill (the canonical MEGA65 way) --------
;
; The $D800 CPU window proved unreliable for colour RAM in MEGA65
; mode: on the metal it left the boot screen's stale attributes in
; place, and the VIC read them as full-colour cell attributes, which
; garbled exactly the rows under the old boot text. Filling colour
; RAM at $FF80000 by DMAgic is the platform's own idiom for this,
; and the ONE deliberate exception to the plain-6510 doctrine.

colram: lda #0
        sta $d702               ; list bank 0 (clears the MB register)
        lda #>dmalist
        sta $d701
        lda #<dmalist
        sta $d705               ; low byte, and the enhanced trigger
        rts

dmalist:
        !byte $81, $ff          ; option: destination megabyte $FF
        !byte $0a               ; option: F018A list format
        !byte $00               ; end of options
        !byte $03               ; FILL
        !byte <1920, >1920      ; count: the band's 960 pairs
        !byte $00, $00, $00     ; source: the fill value, zero
        !byte $00, $00, $08     ; destination $FF80000 (with the MB)
        !byte $00, $00          ; modulo

; ---- show: the .arc at A/X (lo/hi) ---------------------------------------

show:   sta src
        stx src+1
        lda #0
        sta $d07b               ; hide while decoding
        ldy #0                  ; sanity: the magic
        lda (src),y
        cmp #'A'
        bne sbail
        iny
        lda (src),y
        cmp #'R'
        beq sok
sbail:  rts
sok:
        ldy #6                  ; mode: 9 is 9 char rows, 12 is 12
        lda (src),y
        cmp #12
        beq s12
        lda #9
        !byte $2c               ; BIT abs: skip the next two bytes
s12:    lda #12
        sta rows
        ; the data cursor: src + 16 + count*6 (count is 2)
        jsr matrix              ; the matrix knows the band's rows
        ldy #7
        lda (src),y
        sta cnt
        asl                     ; *2
        clc
        adc cnt                 ; *3
        asl                     ; *6
        adc #16
        adc src                 ; the first stream (fits one page here:
        sta scur1+1             ; header and table are 28 bytes)
        lda src+1
        adc #0
        sta scur2+1
        ; the table cursor
        lda src
        clc
        adc #16
        sta tbl
        lda src+1
        adc #0
        sta tbl+1
walk:   ldy #0                  ; type
        lda (tbl),y
        sta styp
        ; wire the decoder: source = the stream cursor (self-modified
        ; OPERANDS, named, never offset arithmetic: the first build
        ; wrote the high byte over the next instruction's opcode)
scur1:  lda #0                  ; low
        sta LZSA_SRC_LO
scur2:  lda #0                  ; high
        sta LZSA_SRC_HI
        ; destination by type
        lda styp
        cmp #1
        bne notbmp
        lda #<CHARS
        sta LZSA_DST_LO
        lda #>CHARS
        sta LZSA_DST_HI
        jmp godec
notbmp: lda #<PALBUF
        sta LZSA_DST_LO
        lda #>PALBUF
        sta LZSA_DST_HI
godec:  jsr DECOMPRESS_LZSA2_FAST
        lda styp
        cmp #5
        bne next
        jsr setpal
next:   ; advance the stream cursor by the table's compressed length
        ; (big-endian at +4/+5); the decoder's registers are not a
        ; contract (the Next probe's lesson, kept)
        ldy #5
        lda (tbl),y
        clc
        adc scur1+1
        sta scur1+1
        dey
        lda (tbl),y
        adc scur2+1
        sta scur2+1
        ; next table entry
        lda tbl
        clc
        adc #6
        sta tbl
        bcc twrap
        inc tbl+1
twrap:  dec cnt
        bne walk
        lda rows                ; the reveal: the band's rows,
        sta $d07b               ; our black on the border and the
        lda #$ff                ; backdrop, and the display on
        sta $d020
        sta $d021
        lda $d011
        ora #$10
        sta $d011
srts:   rts

; ---- setpal: PALBUF's 255 triples into the three register pages ----------

setpal: lda #<PALBUF
        sta pal
        lda #>PALBUF
        sta pal+1
        ldx #0                  ; the entry
pl:     ldy #0
        lda (pal),y
        sta $d100,x
        iny
        lda (pal),y
        sta $d200,x
        iny
        lda (pal),y
        sta $d300,x
        ; pal += 3
        lda pal
        clc
        adc #3
        sta pal
        bcc pnext
        inc pal+1
pnext:  inx
        cpx #255
        bne pl
        rts

; ---- waitkey: the MEGA65 hardware typing buffer --------------------------

waitkey:
        lda $d610
        beq waitkey
        sta $d610               ; consume it
        rts

        !src "unlzsa2_6502.asm"

}
blobend:

pair9:  !bin "9.M65"
pair9end:
pair12: !bin "12.M65"
pair12end:

; the regions' capacity, enforced at build time
!if ((pair9end-pair9+$FF) & $FF00) > (IMG12-IMG9) { !error "9.M65 outgrew its region" }
; page-granular copy: the ROUNDED size must stay under the I/O hole
!if ((pair12end-pair12+$FF) & $FF00) > ($D000-IMG12) { !error "12.M65 outgrew its region" }
!if (blobend-blob) > (CHARS-CODE) { !error "the resident blob outgrew CODE" }
