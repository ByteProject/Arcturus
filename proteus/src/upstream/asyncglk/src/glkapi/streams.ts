/*

Glk Streams
===========

Copyright (c) 2023 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {type GlkTypedArray, is_unicode_array} from '../common/misc.js'

import {filemode_Write, seekmode_Current, seekmode_End} from './constants.js'
import {FileRef} from './filerefs.js'
import type {GlkArray, GlkStream, RefStructArg} from './interface.js'
import {GLK_NULL, MAX_LATIN1, QUESTION_MARK} from './lib_constants.js'
import type {Window} from './windows.js'

export type Stream = ArrayBackedStream | FileStream | NullStream | WindowStream
type StreamType = 'array' | 'null' | 'window'

abstract class StreamBase implements GlkStream {
    disprock?: number
    fmode: number
    next: Stream | null = null
    prev: Stream | null = null
    rock: number
    abstract type: StreamType
    protected write_count = 0

    constructor(fmode: number, rock: number) {
        this.fmode = fmode
        this.rock = rock
    }

    close(result?: RefStructArg) {
        if (result) {
            result.set_field(0, 0)
            result.set_field(1, this.write_count)
        }
    }

    get_buffer(_buf: GlkTypedArray): number {
        return 0
    }

    get_char(_unicode: boolean): number {
        return -1
    }

    get_line(_buf: GlkTypedArray): number {
        return 0
    }

    get_position(): number {
        return 0
    }

    abstract put_buffer(buf: GlkArray, uni: boolean): void
    abstract put_char(ch: number): void
    abstract put_string(str: string, style?: string): void

    set_position(_mode: number, _pos: number) {}
}

/** A fixed-length TypedArray backed stream */
export class ArrayBackedStream extends StreamBase {
    protected buf: GlkTypedArray
    private close_cb?: () => void
    /** Whether we need to check if we should expand the buffer before writing */
    protected expandable: boolean
    /** The length of the active region of the buffer.
     * This can be shorter than the actual length of the buffer in two situations: a file stream, or a `filemode_Write` memory stream.
     * See https://github.com/iftechfoundation/ifarchive-if-specs/issues/8
     */
    protected len: number
    protected pos = 0
    private read_count = 0
    type = 'array' as const
    protected uni: boolean

    constructor(buf: GlkTypedArray, fmode: number, rock: number, close_cb?: () => void) {
        super(fmode, rock)
        this.buf = buf
        this.close_cb = close_cb
        this.expandable = fmode === filemode_Write
        this.len = fmode === filemode_Write ? 0 : buf.length
        this.uni = is_unicode_array(buf)
    }

    close(result?: RefStructArg) {
        this.close_cb?.()
        this.write()
        if (result) {
            result.set_field(0, this.read_count)
            result.set_field(1, this.write_count)
        }
    }

    protected expand(increase: number) {
        this.len = Math.min(this.pos + increase, this.buf.length)
        if (this.len === this.buf.length) {
            this.expandable = false
        }
    }

    get_buffer(buf: GlkTypedArray): number {
        const read_length = Math.min(buf.length, this.len - this.pos)
        // When a unicode array is read into a latin1 array we must catch non-latin1 characters
        if (!is_unicode_array(buf) && this.uni) {
            for (let i = 0; i < read_length; i++) {
                const ch = this.buf[this.pos + i]
                buf[i] = ch > MAX_LATIN1 ? QUESTION_MARK : ch
            }
        }
        // Otherwise we can copy it whole
        else {
            buf.set(this.buf.subarray(this.pos, this.pos + read_length))
        }
        this.pos += read_length
        this.read_count += read_length
        return read_length
    }

    get_char(unicode: boolean): number {
        if (this.pos < this.len) {
            this.read_count++
            const ch = this.buf[this.pos++]
            return !unicode && ch > MAX_LATIN1 ? QUESTION_MARK : ch
        }
        return -1
    }

    get_line(buf: GlkTypedArray): number {
        const read_length = Math.min(buf.length - 1, this.len - this.pos)
        if (read_length < 0) {
            return 0
        }
        const check_unicode = !is_unicode_array(buf) && this.uni
        let i = 0
        while (i < read_length) {
            const ch = this.buf[this.pos++]
            buf[i++] = check_unicode && ch > MAX_LATIN1 ? QUESTION_MARK : ch
            if (ch === 10) {
                break
            }
        }
        buf[i] = GLK_NULL
        this.read_count += i
        return i
    }

    get_position(): number {
        return this.pos
    }

    put_buffer(buf: GlkArray, uni: boolean) {
        const buf_length = buf.length
        this.write_count += buf_length
        if (this.pos + buf_length > this.len && this.expandable) {
            this.expand(buf_length)
        }
        const write_length = Math.min(buf_length, this.len - this.pos)
        if (write_length === 0) {
            return
        }
        // When writing a unicode array into a latin1 array we must catch non-latin1 characters
        if (uni && !this.uni) {
            for (let i = 0; i < write_length; i++) {
                const ch = buf[i]
                this.buf[this.pos + i] = ch > MAX_LATIN1 ? QUESTION_MARK : ch
            }
        }
        // Otherwise we can copy it whole
        else {
            if (Array.isArray(buf)) {
                buf = (uni ? Uint32Array : Uint8Array).from(buf)
            }
            this.buf.set(buf.subarray(0, write_length), this.pos)
        }
        this.pos += write_length
        this.write()
    }

    put_char(ch: number) {
        this.write_count++
        if (this.pos === this.len && this.expandable) {
            this.expand(1)
        }
        if (this.pos < this.len) {
            this.buf[this.pos++] = (!this.uni && ch > MAX_LATIN1) ? QUESTION_MARK : ch
            this.write()
        }
    }

    put_string(str: string) {
        this.put_buffer(Uint32Array.from(str, ch => ch.codePointAt(0)!), true)
    }

    set_position(mode: number, pos: number) {
        if (mode === seekmode_Current) {
            this.pos += pos
        }
        else if (mode === seekmode_End) {
            this.pos = this.len + pos
        }
        // Default to start if the mode is invalid
        else {
            this.pos = pos
        }
        if (this.pos < 0) {
            this.pos = 0
        }
        if (this.pos > this.len) {
            this.pos = this.len
        }
    }

    protected write() {}
}

/** FileStreams are based on array backed streams, but can grow in length */
export class FileStream extends ArrayBackedStream {
    private fref: FileRef

    constructor(fref: FileRef, buf: GlkTypedArray, fmode: number, rock: number) {
        super(buf, fmode, rock)
        this.expandable = true
        this.fref = fref
    }

    protected expand(increase: number) {
        const end_pos = this.pos + increase
        this.len = end_pos
        let maxlen = this.buf.length
        if (end_pos > maxlen) {
            // Always expand by at least 100
            maxlen += Math.max(end_pos - maxlen, 100)
            const old_buf = this.buf
            this.buf = new (this.uni ? Uint32Array : Uint8Array)(maxlen)
            this.buf.set(old_buf)
        }
    }

    protected write() {
        this.fref.write(this.buf.subarray(0, this.len))
    }
}

/** A null stream */
export class NullStream extends StreamBase {
    type = 'null' as const

    put_buffer(buf: GlkArray, _uni: boolean) {
        this.write_count += buf.length
    }

    put_char(_ch: number) {
        this.write_count++
    }

    put_string(str: string, _style?: string) {
        this.write_count += [...str].length
    }
}

/** Window streams operate a little bit differently */
export class WindowStream extends StreamBase {
    type = 'window' as const
    private win: Window

    constructor(win: Window) {
        super(filemode_Write, 0)
        this.win = win
    }

    put_buffer(buf: GlkArray, uni: boolean) {
        if (this.win.input.type === 'line') {
            throw new Error('Window has pending line request')
        }
        this.write_count += buf.length
        this.win.put_string(String.fromCodePoint(...buf))
        this.win.echostr?.put_buffer(buf, uni)
    }

    put_char(ch: number) {
        if (this.win.input.type === 'line') {
            throw new Error('Window has pending line request')
        }
        this.write_count++
        this.win.put_string(String.fromCodePoint(ch))
        this.win.echostr?.put_char(ch)
    }

    put_string(str: string, style?: string) {
        if (this.win.input.type === 'line') {
            throw new Error('Window has pending line request')
        }
        this.write_count += [...str].length
        this.win.put_string(str, style)
        this.win.echostr?.put_string(str, style)
    }

    set_css(name: string, val?: string | number) {
        this.win.set_css(name, val)
        if (this.win.echostr?.type === 'window') {
            this.win.echostr.set_css(name, val)
        }
    }

    set_hyperlink(val: number) {
        this.win.set_hyperlink(val)
        if (this.win.echostr?.type === 'window') {
            this.win.echostr.set_hyperlink(val)
        }
    }

    set_style(style: string) {
        this.win.set_style(style)
        if (this.win.echostr?.type === 'window') {
            this.win.echostr.set_style(style)
        }
    }
}