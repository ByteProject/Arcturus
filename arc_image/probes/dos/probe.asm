; probe.asm - the DOS arc_image probe (B12 R2, arc_image/reference/design.md section 6)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A 16-bit .COM for VGA/MCGA mode 13h that displays two embedded .arc images
; (mode 9, then mode 12 after a keypress), written from the blueprint alone:
; the reference DOS loader for the format. Build:
;
;   nasm -f bin probe.asm -o PROBE.COM
;
; and run in DOSBOX-X with this directory mounted. The codec is LZSA2
; (codec 2, the 16-bit trio's codec, docs/08 part B); the decompressor is
; Emmanuel Marty's own space-efficient 8088 routine, carried verbatim.
; Everything else is section-table walking.
;
; .arc recap (arc_image/reference/design.md section 10, all words BIG-endian): 16-byte header
; (magic "ARCI", version, target, mode, section count, width, height, id,
; codec, provenance), then 6-byte table entries (type, flags, uncompressed
; length, compressed length), then the LZSA2 raw blocks in table order (one
; per section, each with its own end-of-data marker). The DOS payload:
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
        call lzsa2_decompress
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
        call lzsa2_decompress
.done:  pop dx
        pop ax
        pop bx
        pop cx
        pop di
        pop si
        ret

; ---- the LZSA2 decoder (codec 2, docs/08 part B) -----------------------------
; Emmanuel Marty's space-efficient raw-block decompressor for 8088, from the
; lzsa distribution (zlib license), carried as published: in ds:si = raw
; LZSA2 block, es:di = destination, out ax = decompressed size. Trashes
; bx/cx/dx/bp.

lzsa2_decompress:
   push di                 ; remember decompression offset
   cld                     ; make string operations (lods, movs, stos..) move forward

   xor cx,cx
   mov bx,0100H
   xor bp,bp

.decode_token:
   mov ax,cx               ; clear ah - cx is zero from above or from after rep movsb in .copy_match
   lodsb                   ; read token byte: XYZ|LL|MMMM
   mov dx,ax               ; keep token in dl

   and al,018H             ; isolate literals length in token (LL)
   mov cl,3
   shr al,cl               ; shift literals length into place

   cmp al,03H              ; LITERALS_RUN_LEN_V2?
   jne .got_literals       ; no, we have the full literals count from the token, go copy

   call .get_nibble        ; get extra literals length nibble
   add al,cl               ; add len from token to nibble
   cmp al,012H             ; LITERALS_RUN_LEN_V2 + 15 ?
   jne .got_literals       ; if not, we have the full literals count, go copy

   lodsb                   ; grab extra length byte
   add al,012H             ; overflow?
   jnc .got_literals       ; if not, we have the full literals count, go copy

   lodsw                   ; grab 16-bit extra length

.got_literals:
   xchg cx,ax
   rep movsb               ; copy cx literals from ds:si to es:di

   test dl,0C0h            ; check match offset mode in token (X bit)
   js .rep_match_or_large_offset

   xchg cx,ax              ; clear ah - cx is zero from the rep movsb above
   jne .offset_9_bit

                           ; 5 bit offset
   cmp dl,020H             ; test bit 5
   call .get_nibble_x
   jmp short .dec_offset_top

.offset_9_bit:             ; 9 bit offset
   lodsb                   ; get 8 bit offset from stream in A
   dec ah                  ; set offset bits 15-8 to 1
   test dl,020H            ; test bit Z (offset bit 8)
   je .get_match_length
.dec_offset_top:
   dec ah                  ; clear bit 8 if Z bit is clear
                           ; or set offset bits 15-8 to 1
   jmp short .get_match_length

.rep_match_or_large_offset:
   jpe .rep_match_or_16_bit

                           ; 13 bit offset
   cmp dl,0A0H             ; test bit 5 (knowing that bit 7 is also set)
   xchg ah,al
   call .get_nibble_x
   sub al,2                ; substract 512
   jmp short .get_match_length_1

.rep_match_or_16_bit:
   test dl,020H            ; test bit Z (offset bit 8)
   jne .repeat_match       ; rep-match

                           ; 16 bit offset
   lodsb                   ; get 2-byte match offset

.get_match_length_1:
   xchg ah,al
   lodsb                   ; load match offset bits 0-7

.get_match_length:
   xchg bp,ax              ; bp: offset
.repeat_match:
   xchg ax,dx              ; ax: original token
   and al,07H              ; isolate match length in token (MMM)
   add al,2                ; add MIN_MATCH_SIZE_V2

   cmp al,09H              ; MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2?
   jne .got_matchlen       ; no, we have the full match length from the token, go copy

   call .get_nibble        ; get extra match length nibble
   add al,cl               ; add len from token to nibble
   cmp al,018H             ; MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2 + 15?
   jne .got_matchlen       ; no, we have the full match length from the token, go copy

   lodsb                   ; grab extra length byte
   add al,018H             ; overflow?
   jnc .got_matchlen       ; if not, we have the entire length
   je short .done_decompressing ; detect EOD code

   lodsw                   ; grab 16-bit length

.got_matchlen:
   xchg cx,ax              ; copy match length into cx
   push ds                 ; save ds:si (current pointer to compressed data)
   xchg si,ax
   push es
   pop ds
   lea si,[bp+di]          ; ds:si now points at back reference in output data
   rep movsb               ; copy match
   xchg si,ax              ; restore ds:si
   pop ds
   jmp .decode_token       ; go decode another token

.done_decompressing:
   pop ax                  ; retrieve the original decompression offset
   xchg di,ax              ; compute decompressed size
   sub ax,di
   ret                     ; done

.get_nibble_x:
   cmc                     ; carry set if bit 4 was set
   rcr al,1
   call .get_nibble        ; get nibble for offset bits 0-3
   or al,cl                ; merge nibble
   rol al,1
   xor al,0E1H             ; set offset bits 7-5 to 1
   ret

.get_nibble:
   neg bh                  ; nibble ready?
   jns .has_nibble

   xchg bx,ax
   lodsb                   ; load two nibbles
   xchg bx,ax

.has_nibble:
   mov cl,4                ; swap 4 high and low bits of nibble
   ror bl,cl
   mov cl,0FH
   and cl,bl
   ret

palbuf: times 768 db 0

image9:
        incbin "9.DOS"
image12:
        incbin "12.DOS"
