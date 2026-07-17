; dzx0r_6502.asm - ZX0 RING decompressor for the 6502/6510 (the arc_image 64K model)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; The 6502 sibling of dzx0r_z80.asm. Unlike the Z80 version (a minimal
; delta on the standard dzx0), this one is a clean transcription of the
; reference ZX0 state machine (zx0_decompress in arcimg, byte-verified;
; the same source as tests/test_dzx0r.py's ring oracle), because the
; bitfire decoder beside it (dzx0_6502.asm) is speed-golfed around a
; readable linear destination and does not re-plumb cleanly. This decoder
; is written for clarity and small size, not cycles: a picture decodes
; once per room entry.
;
; THE CONTRACT (docs/08 part B, the window guarantee, ruled 2026-07-17):
; arcimg packs every codec-1 stream with no match offset beyond 2048
; bytes, so the only history a decoder reads is the last 2048 output
; bytes, kept here in a 2K-aligned ring. Each decoded byte is stored to
; the ring and handed to EMIT, which puts it wherever the platform wants
; (for the C64 probe: a linear store, since every .arc section is already
; in native memory order and contiguous). No staging buffer exists.
;
; ----------------------------------------------------------------------
; WHAT THE INCLUDING PROGRAM SUPPLIES:
;
;   emit        a routine: one decoded byte in A; write it to the next
;               output position and advance your own cursor. May trash
;               A, X, Y. Called once per output byte, in decode order.
;               The decoder reaches it through the vector at zr_emit
;               (a JMP operand the caller patches).
;
;   zx0ring     2048 bytes, 2K-aligned (low 11 address bits zero).
;
;   zero page   $08-$12 (11 cells), free on a C64 while BASIC is dormant.
;
; ENTRY:  X = source lo, A = source hi (the compressed stream, read
;         strictly forward; streamable).
; EXIT :  past the end marker. Trashes A/X/Y and the zp cells.
; SIZE :  about 230 bytes.
; ----------------------------------------------------------------------

zr_src   = $08          ; source pointer (2)
zr_bits  = $0a          ; the bit reservoir, sentinel-armed
zr_noff  = $0b          ; last offset, NEGATIVE 16-bit form (2)
zr_len   = $0d          ; gamma value / run counter (2)
zr_wp    = $0f          ; ring write pointer, absolute (2)
zr_rp    = $11          ; ring read pointer for matches, absolute (2)

RINGMASK = 7            ; high-byte index bits of a 2K ring

dzx0r:  stx zr_src
        sta zr_src+1
        lda #$80        ; reservoir: empty, sentinel armed
        sta zr_bits
        lda #$ff        ; default last offset 1, negative: $ffff
        sta zr_noff
        sta zr_noff+1
        lda #<zx0ring   ; ring write pointer at index 0
        sta zr_wp
        lda #>zx0ring
        sta zr_wp+1

; --- literals -------------------------------------------------------------
.lit    jsr gamma1      ; zr_len = literal run length
.litcp  jsr rdbyte
        jsr put
        jsr declen
        bne .litcp
        jsr getbit      ; after literals: repeat-offset or new-offset match
        bcs .newoff
        jsr gamma1      ; repeat offset: zr_len = match length
        jsr copy
        jsr getbit      ; after a match: literals or a new offset
        bcc .lit

; --- a new offset ---------------------------------------------------------
.newoff lda #$fe        ; offset MSB gamma, seeded $fe (the dzx0 manner)
        sta zr_len
        jsr eflag       ; accumulate into zr_len (lo only; hi is noise)
        inc zr_len
        beq .done       ; MSB gamma hit 256: the end marker
        ; carry is still SET here (the gamma's closing flag bit): inc,
        ; lda, sta and rdbyte leave it alone, exactly like the Z80's path
        lda zr_len
        sta zr_noff+1   ; negative offset, high byte
        jsr rdbyte
        sta zr_noff
        ror zr_noff+1   ; carry(1) -> bit7; the pair shifts right one
        ror zr_noff     ; carry out = the FIRST length bit (the backtrack)
        lda #1
        sta zr_len
        lda #0
        sta zr_len+1
        bcs +           ; first length flag set: gamma complete (value 1)
        jsr edata       ; else continue the gamma, data bit first
+       jsr inclen      ; match length = gamma + 1
        jsr copy
        jsr getbit
        bcc .lit
        bcs .newoff     ; always
.done   rts

; --- copy zr_len bytes from the ring, offset behind the write pointer -----
copy:   lda zr_wp       ; rp = wp + negative_offset (mod 65536), then
        clc             ; re-anchor into the ring: congruence mod 2048
        adc zr_noff     ; keeps the low 11 bits correct through any wrap
        sta zr_rp
        lda zr_wp+1
        adc zr_noff+1
        and #RINGMASK
        ora #>zx0ring
        sta zr_rp+1
.cploop ldy #0
        lda (zr_rp),y   ; history byte from the ring
        jsr put
        inc zr_rp       ; rp++ around the ring
        bne +
        lda zr_rp+1
        clc
        adc #1
        and #RINGMASK
        ora #>zx0ring
        sta zr_rp+1
+       jsr declen
        bne .cploop
        rts

; --- put A: ring[wp] = A, emit, wp++ --------------------------------------
put:    ldy #0
        sta (zr_wp),y   ; shadow into the ring
        jsr zr_emit     ; and out through the platform vector
        inc zr_wp
        bne +
        lda zr_wp+1
        clc
        adc #1
        and #RINGMASK
        ora #>zx0ring
        sta zr_wp+1
+       rts

zr_emit jmp $0000       ; the emit vector: operand patched by the caller

; --- source byte in A (strictly forward) ----------------------------------
rdbyte: ldy #0
        lda (zr_src),y
        inc zr_src
        bne +
        inc zr_src+1
+       rts

; --- one stream bit into the carry (reservoir + sentinel, the dzx0 way) ---
getbit: asl zr_bits
        bne +           ; sentinel still inside: carry is a data bit
        pha
        jsr rdbyte      ; refill: 8 more bits
        rol             ; carry(=1, the popped sentinel) enters bit 0,
        sta zr_bits     ; bit 7 leaves as the bit we return
        pla
+       rts

; --- interlaced Elias gamma into zr_len (flag first, data second) ---------
gamma1: lda #1
        sta zr_len
        lda #0
        sta zr_len+1
eflag:  jsr getbit      ; the flag bit: set = value complete
        bcs +
edata:  jsr getbit      ; the data bit, shifted in
        rol zr_len
        rol zr_len+1
        jmp eflag
+       rts

; --- 16-bit helpers on zr_len ---------------------------------------------
declen: lda zr_len      ; zr_len--, Z flag = reached zero
        bne +
        dec zr_len+1
+       dec zr_len
        lda zr_len
        ora zr_len+1
        rts

inclen: inc zr_len
        bne +
        inc zr_len+1
+       rts
; ---------------------------------------------------------------------------
