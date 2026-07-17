; dzx0r_z80.asm - ZX0 ring decompressor for the Z80 (the arc_image 64K model)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; The ring counterpart of dzx0_z80.asm, built as the SMALLEST POSSIBLE DELTA
; on Einar Saukas & Urusergi's standard decoder (BSD 3-Clause): the bit
; reservoir, the interlaced Elias gamma routine, the negative-offset
; bookkeeping, and the end-marker detection are carried verbatim, because
; they are the parts a rewrite gets wrong. Only the two LDIR copy paths are
; re-plumbed, and DE changes meaning from "linear destination" to "ring
; write pointer".
;
; WHY: the standard decoder copies matches out of its own OUTPUT
; (add hl,de / ldir), so the output must be readable and fully resident.
; On the 64K profiles (a CPC 464 with a disc drive, the ruled aim) there is
; no room for a staging band beside the compressed data and a running
; Z-machine, and on write-only video (a port-addressed board, a serial VDP)
; there is nothing to read back at all. arc_image therefore guarantees
; (docs/08 part B, ruled 2026-07-17) that no codec-1 stream carries a match
; offset beyond 2048 bytes; this decoder keeps exactly those 2048 bytes of
; history in a ring and pushes every decoded byte out through EMIT instead
; of assembling the image anywhere.
;
; THE RING TRICK: the ring is 2048 bytes at a 2K-aligned address, so the low
; 11 bits of any pointer ARE the ring index. Offsets stay negative exactly
; as in the standard decoder, `add hl,de` still computes WP-offset, and one
; AND/OR on H re-anchors the result into the ring: arithmetic mod 65536 is
; congruent mod 2048, so the low bits are always already correct.
;
; ----------------------------------------------------------------------
; THE PLATFORM CONTRACT (what the including program supplies):
;
;   emit        one decoded byte in A: write it to the next screen (or
;               buffer) position and advance your own cursor. Must preserve
;               BC, DE, HL; may trash AF. Called once per output byte, in
;               decode order (arcimg already lays sections out in native
;               screen order, docs/08 part C).
;
;   zx0ring     2048 bytes, 2K-aligned (low 11 address bits zero).
;               The decoder's only working memory besides the stack.
;
; ENTRY:  HL = compressed source (read strictly forward; streamable).
; EXIT :  past the end marker, stack balanced; the image is fully emitted.
; USES :  AF, BC, DE, HL.
; SIZE :  about 110 bytes.
; ----------------------------------------------------------------------

; the re-anchor constants: low 3 bits of H are ring index bits, the rest
; is the (2K-aligned) ring base page
RIDX    equ     $07                     ; high-byte index mask (2048 = 8 pages)

dzx0r:
        ld      de, zx0ring             ; DE = ring write pointer (index 0)
        ld      bc, $ffff               ; preserve default offset 1 (negative)
        push    bc
        inc     bc
        ld      a, $80                  ; empty reservoir, sentinel armed
dzx0r_literals:
        call    dzx0r_elias             ; BC = literal length
        push    af                      ; reservoir sleeps across the copy
.lit:   ld      a, (hl)                 ; literal byte from the source
        inc     hl
        ld      (de), a                 ; shadow into the ring
        call    emit                    ; and out to the screen
        call    dzx0r_next_de           ; WP++ (ring wrap)
        dec     bc
        ld      a, b
        or      c
        jr      nz, .lit
        pop     af                      ; reservoir wakes
        add     a, a                    ; match: last offset or new offset?
        jr      c, dzx0r_new_offset
        call    dzx0r_elias             ; BC = match length
dzx0r_copy:
        ex      (sp), hl                ; HL = -offset, TOS = source
        push    hl                      ; preserve -offset
        push    af                      ; reservoir sleeps BEFORE the anchor
                                        ; math below borrows A
        add     hl, de                  ; HL = WP - offset (mod 65536)
        ld      a, h                    ; re-anchor into the ring: the low
        and     RIDX                    ; 11 bits are already correct
        or      high zx0ring
        ld      h, a                    ; HL = ring read pointer
.cpy:   ld      a, (hl)                 ; history byte from the ring
        ld      (de), a                 ; shadow the new byte
        call    emit                    ; and out to the screen
        call    dzx0r_next_hl           ; RP++ (ring wrap)
        call    dzx0r_next_de           ; WP++ (ring wrap)
        dec     bc
        ld      a, b
        or      c
        jr      nz, .cpy
        pop     af
        pop     hl                      ; restore -offset
        ex      (sp), hl                ; HL = source, TOS = -offset
        add     a, a                    ; literals or new offset next?
        jr      nc, dzx0r_literals
dzx0r_new_offset:
        pop     bc                      ; discard last offset
        ld      c, $fe                  ; prepare negative offset MSB
        call    dzx0r_elias_loop        ; obtain offset MSB
        inc     c
        ret     z                       ; end marker: done, stack balanced
        ld      b, c
        ld      c, (hl)                 ; offset LSB
        inc     hl
        rr      b                       ; last offset bit -> first length bit
        rr      c
        push    bc                      ; preserve new -offset
        ld      bc, 1                   ; length base
        call    nc, dzx0r_elias_backtrack
        inc     bc
        jr      dzx0r_copy

; --- ring stepping: advance and re-anchor (the 2K wrap) --------------------
; each trashes A only
dzx0r_next_de:
        inc     de
        ld      a, d
        and     RIDX
        or      high zx0ring
        ld      d, a
        ret
dzx0r_next_hl:
        inc     hl
        ld      a, h
        and     RIDX
        or      high zx0ring
        ld      h, a
        ret

; --- interlaced Elias gamma, verbatim from dzx0_standard -------------------
dzx0r_elias:
        inc     c
dzx0r_elias_loop:
        add     a, a
        jr      nz, dzx0r_elias_skip
        ld      a, (hl)                 ; refill: 8 more bits
        inc     hl
        rla
dzx0r_elias_skip:
        ret     c
dzx0r_elias_backtrack:
        add     a, a
        rl      c
        rl      b
        jr      dzx0r_elias_loop
; ---------------------------------------------------------------------------
