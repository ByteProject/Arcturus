/*

Glk FileRefs
============

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import type {GlkTypedArray} from '../common/misc.js'
import type {FileRef as DialogFileRef} from '../common/protocol.js'
import {CachingDialogWrapper, FileBuffer} from '../dialog/common/cache.js'

import {fileusage_TextMode} from './constants.js'
import type {GlkFref} from './interface.js'

export class FileRef implements GlkFref {
    binary: boolean
    private Dialog: CachingDialogWrapper
    disprock?: number
    filename: string
    next: FileRef | null = null
    prev: FileRef | null = null
    private dfref: DialogFileRef
    rock: number

    constructor(Dialog: CachingDialogWrapper, filename: string, dialog_fref: DialogFileRef, rock: number, usage: number) {
        this.binary = !(usage & fileusage_TextMode)
        this.Dialog = Dialog
        this.filename = filename
        this.dfref = dialog_fref
        this.rock = rock
    }

    delete_file() {
        this.Dialog.file_remove_ref(this.dfref)
    }

    exists(): boolean {
        return this.Dialog.file_ref_exists(this.dfref)
    }

    read(): Uint8Array | null {
        return this.Dialog.file_read(this.dfref)
    }

    write(buf: GlkTypedArray) {
        const filebuf = new FileBuffer(buf, this.binary, this.dfref)
        this.Dialog.write_file(this.dfref, filebuf)
    }
}