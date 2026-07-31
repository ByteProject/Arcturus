/*

Caching Dialog wrapper
======================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {debounce} from 'lodash-es'

import {Array_to_BEBuffer, type GlkTypedArray, is_unicode_array, utf8encoder} from '../../common/misc.js'
import type {FileRef} from '../../common/protocol.js'
import {filemode_Read, filemode_Write, seekmode_End, seekmode_Start} from '../../glkapi/constants.js'
import type {AutosaveData, ClassicSyncDialog, ClassicStreamingDialog, DialogOptions} from './interface.js'

/** A file buffer which stores its data in its preferred stream format, only converting back to a Uint8Array when required */
export class FileBuffer {
    private binary: boolean
    private buf: GlkTypedArray
    fref: FileRef
    private uni: boolean

    constructor(buf: GlkTypedArray, binary: boolean, fref: FileRef) {
        this.binary = binary
        this.buf = buf
        this.fref = fref
        this.uni = is_unicode_array(buf)
    }

    convert() {
        if (this.uni) {
            if (this.binary) {
                return Array_to_BEBuffer(this.buf as Uint32Array)
            }
            else {
                const text = String.fromCodePoint(...this.buf)
                return utf8encoder.encode(text)
            }
        }
        else {
            return (this.buf as Uint8Array).slice()
        }
    }
}

/** A Dialog class that wraps another Dialog instance, caching files so that they can be written asyncronously */
export class CachingDialogWrapper implements ClassicSyncDialog {
    'async' = false as const
    private cache: Record<string, FileBuffer> = {}
    classname = 'CachingDialogWrapper'
    private Dialog: ClassicSyncDialog | ClassicStreamingDialog
    streaming = false as const

    constructor(Dialog: ClassicSyncDialog | ClassicStreamingDialog) {
        this.Dialog = Dialog
    }

    init(_options: DialogOptions) {}

    file_ref_exists(fref: FileRef) {
        return !!this.cache[fref.filename] || this.Dialog.file_ref_exists(fref)
    }

    file_read(fref: FileRef) {
        if (this.cache[fref.filename]) {
            // Convert the cached file buffer back into canonical form
            return this.cache[fref.filename].convert()
        }
        if (this.Dialog.streaming) {
            const fstream = this.Dialog.file_fopen(filemode_Read, fref)
            if (!fstream) {
                return null
            }
            fstream.fseek(0, seekmode_End)
            const length = fstream.ftell()
            const buf = new Uint8Array(length)
            fstream.fseek(0, seekmode_Start)
            fstream.fread(buf)
            fstream.fclose()
            return buf
        }
        else {
            return this.Dialog.file_read(fref)
        }
    }

    file_remove_ref(fref: FileRef) {
        if (this.cache[fref.filename]) {
            delete this.cache[fref.filename]
        }
        this.Dialog.file_remove_ref(fref)
    }

    file_write(_fref: FileRef, _content: Uint8Array): boolean {
        throw new Error('CachingDialogWrapper.write_file should be called instead')
    }

    inited() {
        return true
    }

    // Bundle all writes from one JS tick
    private write = debounce(() => {
        for (const filename in this.cache) {
            const filebuf = this.cache[filename]
            if (this.Dialog.streaming) {
                const fstream = this.Dialog.file_fopen(filemode_Write, filebuf.fref)!
                fstream.fwrite(filebuf.convert())
                fstream.fclose()
            }
            else {
                this.Dialog.file_write(filebuf.fref, filebuf.convert())
            }
        }
        this.cache = {}
    }, 0)

    write_file(fref: FileRef, content: FileBuffer) {
        this.cache[fref.filename] = content
        this.write()
        return true
    }

    // And the rest just call the wrapped instance

    autosave_read(signature: string) {
        return this.Dialog.autosave_read(signature)
    }

    autosave_write(signature: string, snapshot: AutosaveData | null) {
        this.Dialog.autosave_write(signature, snapshot)
    }

    file_clean_fixed_name(filename: string, usage: number) {
        return this.Dialog.file_clean_fixed_name(filename, usage)
    }

    file_construct_ref(filename?: string, usage?: string, gameid?: string) {
        return this.Dialog.file_construct_ref(filename, usage, gameid)
    }

    file_construct_temp_ref(usage: string) {
        return this.Dialog.file_construct_temp_ref(usage)
    }

    getlibrary(name: string) {
        return this.Dialog.getlibrary(name)
    }

    open(save: boolean, usage: string | null, gameid: string | null | undefined, callback: (fref: FileRef | null) => void) {
        this.Dialog.open(save, usage, gameid, callback)
    }
}