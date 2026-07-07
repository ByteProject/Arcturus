; probe.asm - the DOS arc_image probe (B12 R2, docs/08 section 6)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A 16-bit .COM for VGA/MCGA mode 13h that displays two embedded .arc images
; (mode 9, then mode 12 after a keypress), written from the blueprint alone:
; the reference DOS loader for the format. Build:
;
;   nasm -f bin probe.asm -o PROBE.COM
;
; and run in DOSBox-X with this directory mounted. The RLE decoder is a
; dozen instructions; everything else is section-table walking.
;
; .arc recap (docs/08 section 10, all words BIG-endian): 16-byte header
; (magic "ARCI", version, target, mode, section count, width, height, id,
; reserved), then 6-byte table entries (type, flags, uncompressed length,
; compressed length), then the RLE streams in table order. The DOS payload:
; section 1 = bitmap, chunky rows for A000:0000; section 5 = palette,
; 256 x 3 bytes of 6-bit DAC values, written to ports 3C8/3C9 VERBATIM.
; The palette pass runs first so the picture never flashes in wrong colors.

        org 100h

start:  mov ax, 0013h           ; mode 13h, 320x200x256, cleared black
        int 10h
        mov si, image9
        call draw
        call waitkey
        mov ax, 0013h           ; clear between the two
        int 10h
        mov si, image12
        call draw
        call waitkey
        mov ax, 0003h           ; back to text
        int 10h
        mov ax, 4C00h
        int 21h

waitkey:
        xor ax, ax
        int 16h
        ret

; ---- draw: si -> an embedded .arc ------------------------------------------

draw:   cmp word [si], "AR"     ; sanity: the magic
        jne .out
        cmp word [si+2], "CI"
        jne .out
        mov al, 5               ; pass 1: the palette section
        call pass
        mov al, 1               ; pass 2: the bitmap section
        call pass
.out:   ret

; pass: run every section of type AL through its handler.
; walk state: bx = table entry, dx = that entry's data offset, cx = count.
pass:   mov cl, [si+7]
        xor ch, ch
        lea bx, [si+16]         ; the section table
        mov dx, bx
        push ax
        mov ax, 6
        push cx
        mul cx                  ; ax = count*6 (dx clobbered by mul: redo)
        pop cx
        lea dx, [si+16]
        add dx, ax              ; dx = first section's data
        pop ax
.each:  cmp [bx], al
        jne .skip
        call handle
.skip:  push ax
        mov ax, [bx+4]          ; compressed length, big-endian
        xchg al, ah
        add dx, ax              ; data cursor to the next stream
        pop ax
        add bx, 6
        loop .each
        ret

; handle one wanted section: AL = 1 bitmap, 5 palette. Source = ds:dx.
handle: push si
        push di
        push cx
        push bx
        push ax
        push dx                 ; the walk's data cursor (the DAC loop uses dx)
        mov si, dx              ; ds:si = the compressed stream
        cmp al, 1
        je .bmp
        ; palette: decode to the buffer, then stream it to the DAC
        push ds
        pop es
        mov di, palbuf
        call unrle
        mov dx, 3C8h
        xor al, al
        out dx, al              ; start at DAC index 0
        inc dx
        mov cx, 768
        mov bx, palbuf
.dac:   mov al, [bx]
        inc bx
        out dx, al
        loop .dac
        jmp .done
.bmp:   mov ax, 0A000h          ; bitmap: decode straight into VRAM row 0
        mov es, ax
        xor di, di
        call unrle
.done:  pop dx
        pop ax
        pop bx
        pop cx
        pop di
        pop si
        ret

; ---- the RLE decoder (docs/08 section 10) -----------------------------------
; in: ds:si = compressed, es:di = destination. control < 80h: copy control+1
; literals; control > 80h: repeat the next byte 257-control times; 80h: end.

unrle:  lodsb
        cmp al, 80h
        je .end
        jb .lit
        mov cl, al              ; 257 - control, in 8-bit arithmetic:
        not cl                  ; 255 - control
        add cl, 2               ; = 257 - control (control >= 81h -> 2..128)
        xor ch, ch
        lodsb
        rep stosb
        jmp unrle
.lit:   mov cl, al
        xor ch, ch
        inc cx                  ; control + 1 literals
        rep movsb
        jmp unrle
.end:   ret

palbuf: times 768 db 0

image9:
        incbin "90.DOS"
image12:
        incbin "100.DOS"
