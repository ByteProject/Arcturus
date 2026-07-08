; boot.s - the Amiga probe's bootblock (B12 R2, docs/08 section 6)
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
;
; A classic trackloader bootblock: Kickstart's strap loads these 1024 bytes
; anywhere in RAM and enters at +12 with a1 = the boot floppy's trackdisk
; IORequest and a6 = ExecBase. We reuse that IORequest to CMD_READ the
; payload (sectors 2..) to chip RAM at $20000 and jump to it. The DOS\0
; magic and the checksum longword are stamped by build_adf.py.
;
; Assemble: vasmm68k_mot -Fbin -o boot.bin boot.s

PAYLOAD_ADDR   = $20000
PAYLOAD_OFFSET = 1024          ; the payload starts right after the bootblock

IO_COMMAND = $1C
IO_LENGTH  = $24
IO_DATA    = $28
IO_OFFSET  = $2C
CMD_READ   = 2
LVO_DoIO   = -456

        dc.b    "DOS",0        ; OFS boot signature
        dc.l    0              ; checksum, patched by the builder
        dc.l    880            ; root block, customary

entry:
        ; read the payload: length is patched by the builder at `plen`
        move.w  #CMD_READ,IO_COMMAND(a1)
        move.l  #PAYLOAD_ADDR,IO_DATA(a1)
        move.l  plen(pc),IO_LENGTH(a1)
        move.l  #PAYLOAD_OFFSET,IO_OFFSET(a1)
        jsr     LVO_DoIO(a6)
        jmp     PAYLOAD_ADDR.l

plen:   dc.l    0              ; payload length in bytes, sector-rounded
