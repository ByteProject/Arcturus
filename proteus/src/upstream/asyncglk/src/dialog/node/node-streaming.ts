/*

Streaming Node implementation of Dialog
=======================================

Mostly lifted directly from electrofs.js
Copyright (c) 2016-2020 Andrew Plotkin
Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import fs from 'fs'
import os from 'os'
import path from 'path'

import type {FileRef} from '../../common/protocol.js'
import type {GlkOte} from '../../glkote/common/glkote.js'
import type {AutosaveData, ClassicFileStream, ClassicStreamingDialog, DialogOptions} from '../common/interface.js'

import {
    filemode_Read,
    filemode_ReadWrite,
    filemode_Write,
    filemode_WriteAppend,
    fileusage_Data,
    fileusage_InputRecord,
    fileusage_SavedGame,
    fileusage_Transcript,
    seekmode_Current,
    seekmode_End,
} from '../../glkapi/constants.js'

export default abstract class NodeStreamingDialog implements ClassicStreamingDialog {
    'async' = false as const
    abstract classname: string
    private extfilepath: string
    private GlkOte?: GlkOte
    private is_inited = false
    streaming = true as const
    private userpath: string

    constructor() {
        this.userpath = this.get_user_path()
        this.extfilepath = path.join(this.userpath, 'quixe-files')
    }

    init_async(options: DialogOptions, callback: () => void) {
        if (this.is_inited) {
            callback()
            return
        }

        this.GlkOte = options.GlkOte

        this.is_inited = true
        callback()
    }


    autosave_read(signature: string): AutosaveData | null {
        const gamedirpath = path.join(this.userpath, 'games', signature)
        const pathj = path.join(gamedirpath, 'autosave.json')
        const pathr = path.join(gamedirpath, 'autosave.ram')

        try {
            const str = fs.readFileSync(pathj, {encoding: 'utf8'})
            const snapshot = JSON.parse(str)

            try {
                const buf = fs.readFileSync(pathr, {encoding: null})
                const ram = Array.from(buf.values())
                snapshot.ram = ram
            }
            catch {}

            return snapshot
        }
        catch {
            return null
        }
    }

    autosave_write(signature: string, snapshot: AutosaveData | null) {
        const gamedirpath = path.join(this.userpath, 'games', signature)

        // Make sure the gamedirpath exists.
        let stat = null
        try {
            stat = fs.statSync(gamedirpath)
        }
        catch {}
        if (!stat || !stat.isDirectory()) {
            try {
                fs.mkdirSync(path.join(this.userpath, 'games'))
            }
            catch {}
            try {
                fs.mkdirSync(gamedirpath)
            }
            catch {}
            stat = null
            try {
                stat = fs.statSync(gamedirpath)
            }
            catch {}
            if (!stat || !stat.isDirectory()) {
                // Can't create the directory; give up.
                this.GlkOte!.log('Unable to create gamedirpath: ' + gamedirpath)
                return
            }
        }

        /* We'll save the snapshot in two files: a .ram file (snapshot.ram
           as raw bytes) and a .json file (the rest of snapshot, stringified).
        */

        const pathj = path.join(gamedirpath, 'autosave.json')
        const pathr = path.join(gamedirpath, 'autosave.ram')

        if (!snapshot) {
            try {
                fs.unlinkSync(pathj)
            }
            catch {}
            try {
                fs.unlinkSync(pathr)
            }
            catch {}
            return
        }

        /* Pull snapshot.ram out, if it exists. (It's okay to munge the
           snapshot object,the caller doesn't want it back.) */
        const ram = snapshot.ram
        snapshot.ram = undefined

        const str = JSON.stringify(snapshot)
        fs.writeFileSync(pathj, str, {encoding: 'utf8'})

        if (ram) {
            const buf = Buffer.from(ram)
            fs.writeFileSync(pathr, buf)
        }
    }

    file_clean_fixed_name(filename: string, usage: number): string {
        let res = filename.replace(/["/\\<>:|?*]/g, '')
        const pos = res.indexOf('.')
        if (pos >= 0) {
            res = res.slice(0, pos)
        }
        if (res.length === 0) {
            res = 'null'
        }

        switch (usage) {
            case fileusage_Data:
                return res + '.glkdata'
            case fileusage_SavedGame:
                return res + '.glksave'
            case fileusage_Transcript:
            case fileusage_InputRecord:
                return res + '.txt'
            default:
                return res
        }
    }

    file_construct_ref(filename = '', usage = '', _gameid = ''): FileRef {
        const filepath = path.join(this.extfilepath, filename)
        return {
            filename: filepath,
            usage: usage,
        }
    }

    file_construct_temp_ref(usage: string): FileRef {
        const filename = `_temp_${Date.now()}_${Math.random()}`.replace('.', '')
        const filepath = path.join(this.get_temp_path(), filename)
        return {
            filename: filepath,
            usage: usage,
        }
    }

    file_fopen(fmode: number, fref: FileRef): NodeFileStream | null {
        /* The spec says that Write, ReadWrite, and WriteAppend create the
        file if necessary. However, open(filename, "r+") doesn't create
        a file. So we have to pre-create it in the ReadWrite and
        WriteAppend cases. (We use "a" so as not to truncate.) */

        if (fmode === filemode_ReadWrite || fmode === filemode_WriteAppend) {
            try {
                const tempfd = fs.openSync(fref.filename, 'a')
                fs.closeSync(tempfd)
            }
            catch (ex) {
                this.GlkOte!.log(`fopen: failed to open ${fref.filename}: ${ex}`)
                return null
            }
        }

        /* Another Unix quirk: in r+ mode, you're not supposed to flip from
        reading to writing or vice versa without doing an fseek. We will
        track the most recent operation (as lastop) -- Write, Read, or
        0 if either is legal next. */

        let modestr = 'r'
        switch (fmode) {
            case filemode_Write:
                modestr = 'w'
                break
            case filemode_ReadWrite:
                modestr = 'r+'
                break
            case filemode_WriteAppend:
                /* Can't use "a" here, because then fseek wouldn't work.
                Instead we use "r+" and then fseek to the end. */
                modestr = 'r+'
                break
        }

        let fd: number
        try {
            fd = fs.openSync(fref.filename, modestr!)
        }
        catch (ex) {
            this.GlkOte!.log(`fopen: failed to open ${fref.filename}: ${ex}`)
            return null
        }

        /* This object is analogous to a FILE* in C code. Yes, we're 
        reimplementing fopen() for Node.js. I'm not proud. Or tired. 
        The good news is, the logic winds up identical to that in
        the C libraries.
        */
        const fstream = new NodeFileStream(fd, fref.filename, fmode, this.GlkOte!)

        if (fmode === filemode_WriteAppend) {
            /* We must jump to the end of the file. */
            fstream.fseek(0, seekmode_End)
        }

        return fstream
    }

    file_ref_exists(fref: FileRef): boolean {
        try {
            fs.accessSync(fref.filename, fs.constants.F_OK)
            return true
        }
        catch {
            return false
        }
    }

    file_remove_ref(fref: FileRef) {
        try {
            fs.unlinkSync(fref.filename)
        }
        catch {}
    }

    getlibrary(name: string): GlkOte | null {
        switch (name) {
            case 'GlkOte': return this.GlkOte!
        }
        // Unrecognized library name.
        return null
    }

    protected get_temp_path() {
        return os.tmpdir()
    }

    inited(): boolean {
        return this.is_inited
    }

    protected abstract get_user_path(): string
    abstract open(save: boolean, usage: string | null, gameid: string | null | undefined, callback: (fref: FileRef | null) => void): void
}

// The size of our stream buffering.
const BUFFER_SIZE = 256

export class NodeFileStream implements ClassicFileStream {
    BufferClass = Buffer
    private buffer = Buffer.alloc(BUFFER_SIZE)
    /** How much of the buffer is used */
    private buflen = 0
    /** How much of the buffer has been read out (readmode only) */
    private bufmark = 0
    /** bufuse is filemode_Read or filemode_Write, if the buffer is being used
        for reading or writing. For writing, the buffer starts at mark and
        covers buflen bytes. For reading, the buffer starts at mark amd runs
        buflen bytes, but bufmark bytes have been consumed from it. */
    private bufuse = 0
    fd: number | null
    private filename: string
    //private fmode: number
    private GlkOte: GlkOte
    /** Position in file */
    private mark = 0

    constructor(fd: number, filename: string, _fmode: number, GlkOte: GlkOte) {
        this.fd = fd
        this.filename = filename
        //this.fmode = fmode
        this.GlkOte = GlkOte
    }

    fclose() {
        if (this.fd === null) {
            this.GlkOte.log('file already closed: ' + this.filename)
            return
        }
        // flush any unwritten data
        this.fflush()
        fs.closeSync(this.fd)
        this.bufuse = 0
        this.fd = null
    }

    fflush() {
        if (this.bufuse === filemode_Read) {
            // Do nothing, just advance the mark.
            this.mark += this.bufmark
        }
        else if (this.bufuse === filemode_Write) {
            if (this.buflen) {
                const count = fs.writeSync(this.fd!, this.buffer, 0, this.buflen, this.mark)
                this.mark += count
            }
        }
        this.bufuse = 0
        this.buflen = 0
        this.bufmark = 0
    }

    fread(buf: Uint8Array, len?: number): number {
        if (len === undefined) {
            len = buf.length
        }

        /* got will be our mark in the buf argument. When got reaches
           len, we're done. (Unless we hit EOF first.) */
        let got = 0

        while (true) {
            if (this.bufuse === filemode_Read) {
                if (this.bufmark < this.buflen) {
                    let want = len - got
                    if (want > this.buflen - this.bufmark) {
                        want = this.buflen - this.bufmark
                    }
                    if (want > 0) {
                        buf.set(this.buffer.subarray(this.bufmark, this.bufmark + want), got)
                        this.bufmark += want
                        got += want
                    }
                }
                if (got >= len) {
                    return got
                }

                /* We need more, but we've consumed the entire buffer. Fall
                   through to the next step where we will fflush and keep
                   reading. */
            }

            if (this.bufuse) {
                this.fflush()
            }

            /* ### if len-got >= BUFFER_SIZE, we could read directly and ignore
               our buffer. */
            this.bufuse = filemode_Read
            this.bufmark = 0
            this.buflen = fs.readSync(this.fd!, this.buffer, 0, BUFFER_SIZE, this.mark)
            if (this.buflen === 0) {
                // End of file. Mark the buffer unused, since it's empty.
                this.bufuse = 0
                return got
            }
            // mark stays at the buffer start position
        }
    }

    fseek(pos: number, seekmode: number) {
        /* ### we could seek within the current buffer, which would be
           efficient for small moves. */
        this.fflush()

        let val: number
        if (seekmode === seekmode_Current) {
            val = this.mark + pos
        }
        else if (seekmode === seekmode_End) {
            try {
                const stats = fs.fstatSync(this.fd!)
                val = stats.size + pos
            }
            catch {
                val = this.mark + pos
            }
        }
        else {
            val = pos
        }
        if (val < 0) {
            val = 0
        }
        this.mark = val
    }

    ftell(): number {
        if (this.bufuse === filemode_Read) {
            return this.mark + this.bufmark
        }
        else if (this.bufuse === filemode_Write) {
            return this.mark + this.buflen
        }
        else {
            return this.mark
        }
    }

    fwrite(buf: Uint8Array, len?: number): number {
        if (len === undefined) {
            len = buf.length
        }

        let from = 0

        while (true) {
            if (this.bufuse === filemode_Write) {
                let want = len - from
                if (want > BUFFER_SIZE - this.buflen) {
                    want = BUFFER_SIZE - this.buflen
                }
                if (want > 0) {
                    this.buffer.set(buf.subarray(from, from + want), this.buflen)
                    this.buflen += want
                    from += want
                }
            }
            if (from >= len) {
                return from
            }

            /* We need to write more, but the buffer is full. Fall through
               to the next step where we will fflush and keep writing. */

            if (this.bufuse) {
                this.fflush()
            }

            /* ### if len-from >= BUFFER_SIZE, we could write directly and
               ignore our buffer. */
            
            this.bufuse = filemode_Write
            this.buflen = 0
        }
    }
}