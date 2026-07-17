; probe.asm - the TRS-80 Model 4 arc_image probe (B12 R5, arc_image/reference/design.md sections 6 and 8b)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A /CMD program for the Model 4 hi-res board that displays two embedded
; .arc images (mode 9, then mode 12 after a keypress), written from the
; blueprint alone: the reference TRSM4 loader for the format. Build:
;
;   sjasmplus probe.asm            (assembles probe.bin)
;   python3 build_cmd.py probe.bin probe.cmd 3000
;
; and run in trs80gp: trs80gp -m4 -gt -vs probe.cmd
;
; THIS IS THE MACHINE THE RING MODEL WAS BUILT FOR: the hi-res board's
; memory is port-addressed and cannot be usefully read back, so the ring
; decoder (../dzx0r_z80.asm, machine-verified in tests/test_dzx0r.py) is
; not an option here but the ONLY model. The emit is a port write; the 2K
; ring in main RAM is the entire decode working set. No layout hazards
; exist on this target: the graphics live behind ports, not in the
; address space, so code, ring, and embedded images sit wherever they
; like.
;
; The board (Shawn Sijnstra's spec, 2026-07-17): port 128 ($80) X byte
; column 0-79, port 129 ($81) Y row 0-239, port 130 ($82) data (bit 7 the
; leftmost pixel), configured so every data write auto-increments X with
; NO wrap to Y: the emit writes a row's 80 bytes and re-addresses per
; row. Port 131 ($83) is the board's option register; real interpreters
; autodetect and configure the two card models (Shawn's wrappers), and
; the single CTRL byte below is this probe's one hardware assumption:
; graphics display on plus X auto-increment on data write. If the screen
; stays dark on real iron or another emulator, this equate is the knob.
;
; The .arc (docs/08 part C.7): ONE section, the bitmap, 80 bytes a row,
; top to bottom. The keypress wait uses the DOS @KEY service so the probe
; runs politely under LS-DOS 6 / TRSDOS 6 (interrupts stay enabled; the
; decoder does not care).

CTRL    equ     $83             ; port $83, calibrated against trs80gp's
                                ; Tandy board by VRAM readback 2026-07-17:
                                ; bit 7 selects the X axis for the write
                                ; clock (auto-inc X per data write; clear
                                ; = the clock drives Y, the first build's
                                ; shear), bit 2 = X decrement, bit 1 =
                                ; WAIT (without it a write colliding with
                                ; the video fetch window is DROPPED: one
                                ; byte vanished deterministically at row
                                ; 0 col 14 until this bit went in), bit 0
                                ; enable. Shawn's wrappers own the real-
                                ; hardware autodetect of the two cards.

        DEVICE NOSLOT64K
        org $3000

start:  ld a, CTRL
        out ($83), a            ; the board on, in the write discipline
        call gcls
        ld hl, image9
        call draw
        call waitkey
        call gcls
        ld hl, image12
        call draw
        call waitkey
        xor a
        out ($83), a            ; graphics off, back to the text screen
        ld a, 22                ; @EXIT: return to LS-DOS
        rst 40
        jr $                    ; (not reached)

waitkey:
        ld a, 1                 ; @KEY: wait for one keystroke
        rst 40
        ret

; clear the graphics RAM: 240 rows of 80 zero bytes through the ports
gcls:   ld c, 0                 ; row
.row:   ld a, c
        out ($81), a            ; y
        xor a
        out ($80), a            ; x = 0
        ld b, 80
.col:   xor a
        out ($82), a            ; data, X auto-increments
        djnz .col
        inc c
        ld a, c
        cp 240
        jr nz, .row
        ret

; ---- draw: the .arc at HL ------------------------------------------------------

draw:   push hl
        pop ix
        ld a, (ix+0)            ; sanity: the magic
        cp 'A'
        ret nz
        ld a, (ix+1)
        cp 'R'
        ret nz
        ld a, (ix+11)           ; height low byte (72 or 96)
        ld (rows), a
        ; the one data stream: base + 16 + count*6 (count is 1 here, but
        ; walk it honestly like every probe)
        ld e, (ix+7)
        ld d, 0
        ld l, e
        ld h, d
        add hl, hl              ; *2
        add hl, de              ; *3
        add hl, hl              ; *6
        push ix
        pop de
        add hl, de
        ld de, 16
        add hl, de              ; hl = the compressed bitmap stream
        call scrinit            ; aim emit at the board
        di                      ; the DOS timer ISR can collide with an
                                ; in-flight board write (one byte dropped
                                ; deterministically at row 0 col 14 until
                                ; this went in); the decode needs no
                                ; interrupts, @KEY gets them back
        call dzx0r              ; decode straight out the ports
        ei
        ret

; ---- the emit vector: dzx0r calls `emit` ---------------------------------

emit:   jp emit_scr             ; one emit on this machine; kept a vector
                                ; for symmetry with the other probes

; ---- screen emit: a port write, a column counter, a row re-address -------
; The board auto-increments X per data write (no Y wrap), so the emit
; only counts 80 columns and re-addresses at each row start.
; Preserves BC/DE/HL (the dzx0r contract).

scrinit:
        xor a
        ld (row), a
        out ($81), a            ; y = 0
        out ($80), a            ; x = 0
        ld a, 80
        ld (colsleft), a
        ret

emit_scr:
        out ($82), a            ; the byte lands on the board, X steps
        ld a, (colsleft)
        dec a
        ld (colsleft), a
        ret nz
        ld a, (row)             ; row done: re-address the next one
        inc a
        ld (row), a
        out ($81), a            ; y = next row
        xor a
        out ($80), a            ; x = 0
        ld a, 80
        ld (colsleft), a
        ret

rows:     db 0
row:      db 0
colsleft: db 0

        include "../dzx0r_z80.asm"

        align 2048
zx0ring:
        ds 2048
        ASSERT (zx0ring & $7FF) == 0

image9:
        incbin "9.TRSM4"
image12:
        incbin "12.TRSM4"

        SAVEBIN "probe.bin", start, $ - start
