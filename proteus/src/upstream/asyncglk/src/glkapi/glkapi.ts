/*

GlkApi
======

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {cloneDeep} from 'lodash-es'

import {Blorb} from '../blorb/blorb.js'
import type {ImageInfo} from '../blorb/interface.js'
import {DEFAULT_METRICS, PACKAGE_VERSION} from '../common/constants.js'
import {BEBuffer_to_Array, type GlkTypedArray, type GlkTypedArrayConstructor, utf8decoder} from '../common/misc.js'
import * as Protocol from '../common/protocol.js'
import type {BufferWindowImage, FileRef as DialogFileRef, ImageOperation, NormalisedMetrics, SpecialInput, TerminatorCode, WindowStyles} from '../common/protocol.js'
import {CachingDialogWrapper} from '../dialog/common/cache.js'
import type {GlkOte, GlkOteOptions} from '../glkote/common/glkote.js'

import {copy_array, type TimerData} from './common.js'
import * as Const from './constants.js'
import {evtype_Arrange, evtype_CharInput, evtype_Hyperlink, evtype_LineInput, evtype_MouseInput, evtype_None, evtype_Redraw, evtype_Timer, filemode_Read, filemode_ReadWrite, filemode_Write, filemode_WriteAppend, fileusage_SavedGame, fileusage_TypeMask, gestalt_CharInput, gestalt_CharOutput, gestalt_CharOutput_ExactPrint, gestalt_DateTime, gestalt_DrawImage, gestalt_GarglkText, gestalt_Graphics, gestalt_GraphicsCharInput, gestalt_GraphicsTransparency, gestalt_HyperlinkInput, gestalt_Hyperlinks, gestalt_LineInput, gestalt_LineInputEcho, gestalt_LineTerminatorKey, gestalt_LineTerminators, gestalt_MouseInput, gestalt_ResourceStream, gestalt_Timer, gestalt_Unicode, gestalt_UnicodeNorm, gestalt_Version, keycode_Escape, keycode_Func1, keycode_Func12, keycode_Left, keycode_MAXVAL, keycode_Unknown, seekmode_End, stylehint_BackColor, stylehint_Indentation, stylehint_Justification, stylehint_NUMHINTS, stylehint_Oblique, stylehint_ParaIndentation, stylehint_Proportional, stylehint_ReverseColor, stylehint_Size, stylehint_TextColor, stylehint_Weight, style_NUMSTYLES, winmethod_Above, winmethod_Below, winmethod_Border, winmethod_BorderMask, winmethod_DirMask, winmethod_DivisionMask, winmethod_Fixed, winmethod_Left, winmethod_NoBorder, winmethod_Proportional, winmethod_Right, wintype_AllTypes, wintype_Blank, wintype_Graphics, wintype_Pair, wintype_TextBuffer, wintype_TextGrid, zcolor_Current, zcolor_Default} from './constants.js'
import {FileRef} from './filerefs.js'
import * as Interface from './interface.js'
import type {GlkArray, GlkApiOptions, GlkByteArray, GlkSchannel, GlkWordArray, RefBoxArg, RefStructArg, RefStructValue} from './interface.js'
import {DidNotReturn} from './interface.js'
import {CSS_STYLE_PROPERTIES, FILE_MODES, FILE_TYPES, IMAGE_ALIGNMENTS, KEY_NAMES_TO_CODES, MAX_LATIN1, QUESTION_MARK, STYLE_NAMES, TERMINATOR_KEYS, TERMINATOR_KEYS_TO_CODES} from './lib_constants.js'
import {ArrayBackedStream, FileStream, NullStream, type Stream} from './streams.js'
import {BlankWindow, BufferWindow, GraphicsWindow, GridWindow, PairWindow, TextWindow, type Window, type WindowBox} from './windows.js'

export class RefBox implements Interface.RefBox {
    private value: RefStructValue = 0
    get_value() {
        return this.value
    }
    set_value(val: RefStructValue) {
        this.value = val
    }
}

export class RefStruct implements Interface.RefStruct {
    private fields: RefStructValue[] = []
    get_field(index: number): RefStructValue {
        return this.fields[index]
    }
    get_fields(): RefStructValue[] {
        return this.fields
    }
    push_field(val: RefStructValue) {
        this.fields.push(val)
    }
    set_field(index: number, val: RefStructValue) {
        this.fields[index] = val
    }
}

export class AsyncGlk implements Interface.GlkApi {
    private Blorb?: Blorb
    private Dialog: CachingDialogWrapper = null as any as CachingDialogWrapper
    private GiDispa?: Interface.GiDispa
    private GlkOte: GlkOte = null as any as GlkOte
    private VM: Interface.GlkVM = null as any as Interface.GlkVM

    private before_select_hook: GlkApiOptions['before_select_hook']
    private gestalt_hook: GlkApiOptions['glk_gestalt_hook']

    // For assigning disprocks when there is no GiDispa
    private disprock_counter = 1

    private do_autosave = false

    private exited = false

    private first_fref: FileRef | null = null

    private gen = 0

    private metrics: NormalisedMetrics = DEFAULT_METRICS

    private partial_inputs?: Record<number, string>

    private selectref?: RefStruct

    private special?: SpecialInput
    private special_data?: {
        rock: number,
        usage: number,
    }

    private current_stream: Stream | null = null
    private first_stream: Stream | null = null

    private stylehints: {buffer: WindowStyles, grid: WindowStyles} = {
        buffer: {},
        grid: {},
    }

    private support: string[] = []

    private timer: TimerData = {
        interval: 0,
        last_interval: 0,
        started: 0,
    }

    version = PACKAGE_VERSION

    private first_window: Window | null = null
    private root_window: Window | null = null
    private windows_changed = false

    // API functions

    init(options: GlkApiOptions) {
        this.before_select_hook = options.before_select_hook
        this.Blorb = options.Blorb
        if (options.Dialog && !options.Dialog.async) {
            // This synchronous GlkApi doesn't support AsyncDialog
            this.Dialog = new CachingDialogWrapper(options.Dialog)
        }
        else {
            throw new Error('No reference to Dialog')
        }
        this.do_autosave = !!options.do_vm_autosave
        // exit_warning
        // extevent_hook
        this.GiDispa = options.GiDispa
        this.gestalt_hook = options.glk_gestalt_hook
        if (options.GlkOte) {
            this.GlkOte = options.GlkOte
        }
        else {
            throw new Error('No reference to GlkOte')
        }
        if (options.vm) {
            this.VM = options.vm
        }
        else {
            throw new Error('No reference to VM')
        }

        this.before_select_hook?.()
        this.GiDispa?.init({
            io: this,
            vm: this.VM,
        })
        const glkote_options = options as any as GlkOteOptions
        glkote_options.accept = this.accept.bind(this)
        this.GlkOte.init(glkote_options)
    }

    call_may_not_return(id: number): boolean {
        return id === 0x01 || id === 0xC0 || id === 0x62
    }

    fatal_error(msg: string) {
        this.exited = true
        if (!this.GlkOte) {
            console.error('Fatal error: ' + msg)
            return
        }
        this.GlkOte.error(msg)
        this.GlkOte.update({
            type: 'update',
            disable: true,
            gen: this.gen,
        })
    }

    getlibrary(class_name: string) {
        switch (class_name) {
            case 'Blorb':
                return this.Blorb || null
            case 'Dialog':
                return this.Dialog
            case 'GiDispa':
                return this.GiDispa || null
            case 'GlkOte':
                return this.GlkOte
            case 'VM':
                return this.VM
            default:
                return null
        }
    }

    inited() {
        return !!(this.GlkOte && this.VM)
    }

    restore_allstate(_state: any) {
        throw new Error('Autosaves not yet supported')
    }
    save_allstate() {
        throw new Error('Autosaves not yet supported')
    }

    update() {
        const state: Protocol.StateUpdate = {
            gen: this.gen,
            type: 'update',
        }

        if (this.exited) {
            state.disable = true
        }

        // Get the window updates
        const contents: Protocol.ContentUpdate[] = []
        const inputs: Protocol.InputUpdate[] = []
        const sizes: Protocol.WindowUpdate[] = []
        for (let win = this.first_window; win; win = win.next) {
            const update = win.update()
            if (update.content) {
                contents.push(update.content)
            }
            if (update.input) {
                const input_update = update.input
                if (input_update.hyperlink || input_update.mouse || input_update.type) {
                    inputs.push(input_update)
                }
            }
            if (this.windows_changed && update.size) {
                sizes.push(update.size)
            }
        }
        if (contents.length) {
            state.content = contents
        }
        if (inputs.length) {
            state.input = inputs
        }
        if (sizes.length) {
            state.windows = sizes
        }
        this.windows_changed = false

        // TODO: Page BG colour

        // Special input
        if (this.special) {
            state.specialinput = this.special
            delete this.special
        }

        // Timer
        const timer = this.timer
        if (timer.last_interval !== timer.interval) {
            state.timer = timer.interval
            timer.last_interval = timer.interval
        }

        // Autorestore state?

        // Clone the state so that any objects copied into it won't be at risk of modification by GlkOte
        this.GlkOte.update(cloneDeep(state))
        this.before_select_hook?.()
        // TODO
        // if (this.do_autosave) {}
    }

    // References to other things

    Const = Const
    DidNotReturn = DidNotReturn
    RefBox = RefBox
    RefStruct = RefStruct

    // Extra functions

    byte_array_to_string(arr: GlkByteArray) {
        return String.fromCodePoint(...arr)
    }

    glk_put_jstring(val: string, _all_bytes?: boolean) {
        this.glk_put_jstring_stream(this.current_stream!, val)
    }

    glk_put_jstring_stream(str: Stream, val: string, _all_bytes?: boolean) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        str.put_string(val)
    }

    uni_array_to_string(arr: GlkWordArray) {
        return String.fromCodePoint(...arr)
    }

    // The Glk functions

    glk_buffer_canon_decompose_uni(buf: GlkWordArray, initlen: number): number {
        return buffer_transformer(buf, initlen, str => (str as string).normalize('NFD'))
    }

    glk_buffer_canon_normalize_uni(buf: GlkWordArray, initlen: number): number {
        return buffer_transformer(buf, initlen, str => (str as string).normalize('NFC'))
    }

    glk_buffer_to_lower_case_uni(buf: GlkWordArray, initlen: number): number {
        return buffer_transformer(buf, initlen, str => (str as string).toLowerCase())
    }

    glk_buffer_to_title_case_uni(buf: GlkWordArray, initlen: number, lowerrest: number): number {
        return buffer_transformer(buf, initlen, buf => (buf as Uint32Array).reduce((prev, ch, index) => {
            const special_cases: Record<string, string> = {
                ß: 'Ss', Ǆ: 'ǅ', ǅ: 'ǅ', ǆ: 'ǅ', Ǉ: 'ǈ', ǈ: 'ǈ', ǉ: 'ǈ', Ǌ: 'ǋ', ǋ: 'ǋ', ǌ: 'ǋ',
                Ǳ: 'ǲ', ǲ: 'ǲ', ǳ: 'ǲ', և: 'Եւ', ᾲ: 'Ὰͅ', ᾳ: 'ᾼ', ᾴ: 'Άͅ', ᾷ: 'ᾼ͂', ᾼ: 'ᾼ', ῂ: 'Ὴͅ',
                ῃ: 'ῌ', ῄ: 'Ήͅ', ῇ: 'ῌ͂', ῌ: 'ῌ', ῲ: 'Ὼͅ', ῳ: 'ῼ', ῴ: 'Ώͅ', ῷ: 'ῼ͂', ῼ: 'ῼ', ﬀ: 'Ff',
                ﬁ: 'Fi', ﬂ: 'Fl', ﬃ: 'Ffi', ﬄ: 'Ffl', ﬅ: 'St', ﬆ: 'St', ﬓ: 'Մն', ﬔ: 'Մե',
                ﬕ: 'Մի', ﬖ: 'Վն', ﬗ: 'Մխ',
            }
            const slightly_less_special_cases = ['ᾈᾉᾊᾋᾌᾍᾎᾏ', 'ᾘᾙᾚᾛᾜᾝᾞᾟ', 'ᾨᾩᾪᾫᾬᾭᾮᾯ']
            let thischar = String.fromCodePoint(ch)
            if (index === 0) {
                if (special_cases[thischar]) {
                    thischar = special_cases[thischar]
                }
                else if (ch >= 8064 && ch < 8112) {
                    thischar = slightly_less_special_cases[((ch - 8064) / 16) | 0][ch % 8]
                }
                else {
                    thischar = thischar.toUpperCase()
                }
            }
            else if (lowerrest) {
                thischar = thischar.toLowerCase()
            }
            return prev + thischar
        }, ''), true)
    }

    glk_buffer_to_upper_case_uni(buf: GlkWordArray, initlen: number): number {
        return buffer_transformer(buf, initlen, str => (str as string).toUpperCase())
    }

    glk_cancel_char_event(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        delete win.input.type
    }

    glk_cancel_hyperlink_event(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type === 'buffer' || win.type === 'grid') {
            delete win.input.hyperlink
        }
    }

    glk_cancel_line_event(win: Window, ev?: RefStructArg) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.input.type !== 'line') {
            if (ev) {
                set_event(ev)
            }
            return
        }

        this.handle_line_input(win as TextWindow, this.partial_inputs?.[win.disprock] ?? '', ev)
    }

    glk_cancel_mouse_event(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type === 'graphics' || win.type === 'grid') {
            delete win.input.mouse
        }
    }

    glk_char_to_lower(val: number): number {
        if (val >= 0x41 && val <= 0x5A) {
            return val + 0x20
        }
        if (val >= 0xC0 && val <= 0xDE && val !== 0xD7) {
            return val + 0x20
        }
        return val
    }

    glk_char_to_upper(val: number): number {
        if (val >= 0x61 && val <= 0x7A) {
            return val - 0x20
        }
        if (val >= 0xE0 && val <= 0xFE && val !== 0xF7) {
            return val - 0x20
        }
        return val
    }

    glk_current_simple_time(factor: number): number {
        return Math.floor(Date.now() / (factor * 1000))
    }

    glk_current_time(struct: RefStruct) {
        timestamp_to_time_struct(Date.now(), struct)
    }

    glk_date_to_simple_time_local(struct: RefStruct, factor: number): number {
        return Math.floor(date_struct_to_timestamp_local(struct) / (factor * 1000))
    }

    glk_date_to_simple_time_utc(struct: RefStruct, factor: number): number {
        return Math.floor(date_struct_to_timestamp_utc(struct) / (factor * 1000))
    }

    glk_date_to_time_local(datestruct: RefStruct, timestruct: RefStruct) {
        timestamp_to_time_struct(date_struct_to_timestamp_local(datestruct), timestruct)
    }

    glk_date_to_time_utc(datestruct: RefStruct, timestruct: RefStruct) {
        timestamp_to_time_struct(date_struct_to_timestamp_utc(datestruct), timestruct)
    }

    glk_exit(): typeof DidNotReturn {
        this.exited = true
        // What is this for?
        /*if (option_exit_warning) {
            GlkOte.warning(option_exit_warning);
        }*/
        return DidNotReturn
    }

    glk_fileref_create_by_name(usage: number, filename: string, rock: number): FileRef {
        const fixed_filename = this.Dialog.file_clean_fixed_name(filename, usage & fileusage_TypeMask)
        return this.create_fileref(fixed_filename, rock, usage)
    }

    glk_fileref_create_by_prompt(usage: number, fmode: number, rock: number): typeof DidNotReturn {
        const filemode = FILE_MODES[fmode] ?? 'read'
        const filetypenum = usage & fileusage_TypeMask
        const filetype = FILE_TYPES[filetypenum] ?? 'data'

        this.special = {
            filemode,
            filetype,
            type: 'fileref_prompt',
        }
        if (filetypenum === fileusage_SavedGame) {
            this.special.gameid = this.VM.get_signature()
        }
        this.special_data = {
            rock,
            usage,
        }
        return DidNotReturn
    }

    glk_fileref_create_from_fileref(usage: number, oldfref: FileRef, rock: number): FileRef {
        if (!oldfref) {
            throw new Error('Invalid Fileref')
        }
        return this.create_fileref(oldfref.filename, rock, usage)
    }

    glk_fileref_create_temp(usage: number, rock: number): FileRef {
        const filetypename = FILE_TYPES[usage & fileusage_TypeMask]
        const dialog_fref = this.Dialog.file_construct_temp_ref(filetypename)
        return this.create_fileref(dialog_fref.filename, rock, usage, dialog_fref)
    }

    glk_fileref_delete_file(fref: FileRef) {
        if (!fref) {
            throw new Error('Invalid Fileref')
        }
        fref.delete_file()
    }

    glk_fileref_destroy(fref: FileRef) {
        if (!fref) {
            throw new Error('Invalid Fileref')
        }
        this.GiDispa?.class_unregister('fileref', fref)
        const prev = fref.prev
        const next = fref.next
        fref.prev = null
        fref.next = null
        if (prev) {
            prev.next = next
        }
        else {
            this.first_fref = next
        }
        if (next) {
            next.prev = prev
        }
    }

    glk_fileref_does_file_exist(fref: FileRef): boolean {
        if (!fref) {
            throw new Error('Invalid Fileref')
        }
        return fref.exists()
    }

    glk_fileref_get_rock(fref: FileRef): number {
        if (!fref) {
            throw new Error('Invalid Fileref')
        }
        return fref.rock
    }

    glk_fileref_iterate(fref?: FileRef, rockbox?: RefBoxArg): FileRef | null {
        const next_fref = fref ? fref.next : this.first_fref
        if (rockbox) {
            rockbox.set_value(next_fref ? next_fref.rock : 0)
        }
        return next_fref
    }

    glk_gestalt(sel: number, val: number): number {
        return this.glk_gestalt_ext(sel, val, null)
    }

    glk_gestalt_ext(sel: number, val: number, arr: GlkArray | null): number {
        const hook_res = this.gestalt_hook?.(sel, val, arr)
        if (hook_res) {
            return hook_res
        }

        switch (sel) {
            case gestalt_Version:
                return 0x00000705
            case gestalt_CharInput:
                // Known special keys can be returned
                if (val <= keycode_Left && val >= keycode_Func12) {
                    return 1
                }
                // But no other high bit values, non-unicode, or control codes
                if (val >= (0x100000000 - keycode_MAXVAL) || val > 0x10FFFF || (val >= 0 && val < 32) || val >= 127 && val < 160) {
                    return 0
                }
                // Otherwise assume yes
                return 1
            case gestalt_LineInput:
                // Same as above, except no special keys
                if (val > 0x10FFFF || (val >= 0 && val < 32) || val >= 127 && val < 160) {
                    return 0
                }
                return 1
            case gestalt_CharOutput:
                // We'll output anything, but it may not result in something readable
                if (arr) {
                    arr[0] = 1
                }
                return gestalt_CharOutput_ExactPrint
            case gestalt_LineTerminatorKey:
                return +(val === keycode_Escape || (val >= keycode_Func12 && val <= keycode_Func1))
            // These are dependent on what GlkOte tells us it supports
            // TODO: check all of these
            case gestalt_DrawImage:
                return +((val === wintype_Graphics || val === wintype_TextBuffer) && this.support.includes('graphics'))
            case gestalt_GarglkText:
                return +this.support.includes('garglktext')
            case gestalt_Graphics:
            case gestalt_GraphicsCharInput:
            case gestalt_GraphicsTransparency:
                return +this.support.includes('graphics')
            case gestalt_Hyperlinks:
                return +this.support.includes('hyperlinks')
            case gestalt_HyperlinkInput:
                return +((val === wintype_TextBuffer || val === wintype_TextGrid) && this.support.includes('hyperlinks'))
            case gestalt_MouseInput:
                return +((val === wintype_Graphics || val === wintype_TextGrid) && this.support.includes('graphics'))
            case gestalt_Timer:
                return +this.support.includes('timer')
            // These are always supported
            case gestalt_DateTime:
            case gestalt_LineInputEcho:
            case gestalt_LineTerminators:
            case gestalt_ResourceStream:
            case gestalt_Unicode:
            case gestalt_UnicodeNorm:
                return 1
            // Anything else is unsupported
            default:
                return 0
        }
    }

    glk_get_buffer_stream(str: Stream, buf: GlkByteArray): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode !== filemode_Read && str.fmode !== filemode_ReadWrite) {
            throw new Error ('Cannot read from write-only stream')
        }
        if (Array.isArray(buf)) {
            return wrap_for_array(buf, Uint8Array, arr => str.get_buffer(arr))
        }
        else {
            return str.get_buffer(buf)
        }
    }

    glk_get_buffer_stream_uni(str: Stream, buf: GlkWordArray): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode !== filemode_Read && str.fmode !== filemode_ReadWrite) {
            throw new Error ('Cannot read from write-only stream')
        }
        if (Array.isArray(buf)) {
            return wrap_for_array(buf, Uint32Array, arr => str.get_buffer(arr))
        }
        else {
            return str.get_buffer(buf)
        }
    }

    glk_get_char_stream(str: Stream): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode !== filemode_Read && str.fmode !== filemode_ReadWrite) {
            throw new Error ('Cannot read from write-only stream')
        }
        return str.get_char(false)
    }

    glk_get_char_stream_uni(str: Stream): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode !== filemode_Read && str.fmode !== filemode_ReadWrite) {
            throw new Error ('Cannot read from write-only stream')
        }
        return str.get_char(true)
    }

    glk_get_line_stream(str: Stream, buf: GlkByteArray): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode !== filemode_Read && str.fmode !== filemode_ReadWrite) {
            throw new Error ('Cannot read from write-only stream')
        }
        if (Array.isArray(buf)) {
            // Handle the NULL byte by adding and subtracting 1 to the read length
            return wrap_for_array(buf, Uint8Array, arr => str.get_line(arr) + 1) - 1
        }
        else {
            return str.get_line(buf)
        }
    }

    glk_get_line_stream_uni(str: Stream, buf: GlkWordArray): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode !== filemode_Read && str.fmode !== filemode_ReadWrite) {
            throw new Error ('Cannot read from write-only stream')
        }
        if (Array.isArray(buf)) {
            // Handle the NULL byte by adding and subtracting 1 to the read length
            return wrap_for_array(buf, Uint32Array, arr => str.get_line(arr) + 1) - 1
        }
        else {
            return str.get_line(buf)
        }
    }

    glk_image_draw(win: Window, imgid: number, val1: number, val2: number): number {
        const info = this.Blorb?.get_image_info(imgid)
        if (!info) {
            return 0
        }
        this.draw_image(win, info, info.height || 0, val1, val2, info.width || 0)
        return 1
    }

    glk_image_draw_scaled(win: Window, imgid: number, val1: number, val2: number, width: number, height: number): number {
        const info = this.Blorb?.get_image_info(imgid)
        if (!info) {
            return 0
        }
        this.draw_image(win, info, height || 0, val1, val2, width || 0)
        return 1
    }

    glk_image_get_info(imgid: number, width?: RefBoxArg, height?: RefBoxArg): number {
        const info = this.Blorb?.get_image_info(imgid)
        if (height) {
            height.set_value(info?.height || 0)
        }
        if (width) {
            width.set_value(info?.width || 0)
        }
        return info ? 1 : 0
    }

    glk_put_buffer(val: GlkByteArray) {
        this.glk_put_buffer_stream(this.current_stream!, val)
    }

    glk_put_buffer_stream(str: Stream, val: GlkByteArray) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode === filemode_Read) {
            throw new Error('Cannot write to read-only stream')
        }
        str.put_buffer(val, false)
    }

    glk_put_buffer_stream_uni(str: Stream, val: GlkWordArray) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode === filemode_Read) {
            throw new Error('Cannot write to read-only stream')
        }
        str.put_buffer(val, true)
    }

    glk_put_buffer_uni(val: GlkWordArray) {
        this.glk_put_buffer_stream_uni(this.current_stream!, val)
    }

    glk_put_char(val: number) {
        this.glk_put_char_stream(this.current_stream!, val)
    }

    glk_put_char_stream(str: Stream, val: number) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode === filemode_Read) {
            throw new Error('Cannot write to read-only stream')
        }
        str.put_char(val)
    }

    glk_put_char_stream_uni(str: Stream, val: number) {
        this.glk_put_char_stream(str, val)
    }

    glk_put_char_uni(val: number) {
        this.glk_put_char_stream(this.current_stream!, val)
    }

    glk_put_string(val: string) {
        this.glk_put_string_stream(this.current_stream!, val)
    }

    glk_put_string_stream(str: Stream, val: string) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.fmode === filemode_Read) {
            throw new Error('Cannot write to read-only stream')
        }
        str.put_string(val)
    }

    glk_put_string_stream_uni(str: Stream, val: string) {
        this.glk_put_string_stream(str, val)
    }

    glk_put_string_uni(val: string) {
        this.glk_put_string_stream(this.current_stream!, val)
    }

    glk_request_char_event(win: Window) {
        this.request_char_event(win, false)
    }

    glk_request_char_event_uni(win: Window) {
        this.request_char_event(win, true)
    }

    glk_request_hyperlink_event(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type === 'buffer' || win.type === 'grid') {
            win.input.hyperlink = true
        }
    }

    glk_request_line_event(win: Window, buf: GlkByteArray, initlen?: number) {
        this.request_line_event(win, buf, false, initlen)
    }

    glk_request_line_event_uni(win: Window, buf: GlkWordArray, initlen?: number) {
        this.request_line_event(win, buf, true, initlen)
    }

    glk_request_mouse_event(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type === 'graphics' || win.type === 'grid') {
            win.input.mouse = true
        }
    }

    glk_request_timer_events(msecs: number) {
        this.timer.interval = msecs
        this.timer.started = msecs ? Date.now() : 0
    }

    glk_schannel_create(_rock: number): GlkSchannel | null {
        return null
    }

    glk_schannel_create_ext(_rock: number, _volume: number): GlkSchannel | null {
        return null
    }

    glk_schannel_destroy(_schannel: GlkSchannel) {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_get_rock(_schannel: GlkSchannel): number {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_iterate(_schannel?: GlkSchannel, rockbox?: RefBoxArg): GlkSchannel | null {
        if (rockbox) {
            rockbox.set_value(0)
        }
        return null
    }

    glk_schannel_pause(_schannel: GlkSchannel) {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_play(_schannel: GlkSchannel, _sound: number): number {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_play_ext(_schannel: GlkSchannel, _sound: number, _repeats: number, _notify: number): number {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_play_multi(_schannels: GlkSchannel[], _sounds: GlkArray, _notify: number): number {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_set_volume(_schannel: GlkSchannel, _volume: number) {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_set_volume_ext(_schannel: GlkSchannel, _volume: number, __duration: number, notify: number) {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_stop(_schannel: GlkSchannel) {
        throw new Error('Invalid Schannel')
    }

    glk_schannel_unpause(_schannel: GlkSchannel) {
        throw new Error('Invalid Schannel')
    }

    glk_select(ev: RefStruct): typeof DidNotReturn {
        this.selectref = ev
        return DidNotReturn
    }

    glk_select_poll(ev: RefStruct) {
        // As JS is single threaded, the only event we could possibly have had since the last glk_select_poll call is a timer event
        set_event(ev)

        const timer = this.timer
        if (timer.interval) {
            const now = Date.now()
            if (now - timer.started > timer.interval) {
                // Pretend we got a timer event
                timer.last_interval = 0
                timer.started = now
                ev.set_field(0, evtype_Timer)
            }
        }
    }

    glk_set_echo_line_event(win: Window, val: number) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type === 'buffer') {
            win.echo_line_input = !!val
        }
    }

    glk_set_hyperlink(val: number) {
        this.glk_set_hyperlink_stream(this.current_stream!, val)
    }

    glk_set_hyperlink_stream(str: Stream, val: number) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.type === 'window') {
            str.set_hyperlink(val)
        }
    }

    glk_set_style(style: number) {
        this.glk_set_style_stream(this.current_stream!, style)
    }

    glk_set_style_stream(str: Stream, style: number) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.type === 'window') {
            if (style < 0 || style > style_NUMSTYLES) {
                style = 0
            }
            str.set_style(STYLE_NAMES[style])
        }
    }

    glk_set_terminators_line_event(win: Window, keycodes: GlkArray | null) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        const terminators: TerminatorCode[] = []
        if (keycodes) {
            for (const code of keycodes) {
                if (TERMINATOR_KEYS[code]) {
                    terminators.push(TERMINATOR_KEYS[code])
                }
            }
        }
        if (terminators.length) {
            win.input.terminators = terminators
        }
        else {
            delete win.input.terminators
        }
    }

    glk_set_window(win?: Window) {
        this.current_stream = win ? win.str : null
    }

    glk_sound_load_hint(_sound: number, _load: number) {}

    glk_stream_close(str: Stream, result?: RefStructArg) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        str.close(result)
        this.unregister_stream(str)
    }

    glk_stream_get_current(): Stream | null {
        return this.current_stream
    }

    glk_stream_get_position(str: Stream): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        return str.get_position()
    }

    glk_stream_get_rock(str: Stream): number {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        return str.rock
    }

    glk_stream_iterate(str?: Stream, rockbox?: RefBoxArg): Stream | null {
        const next_stream = str ? str.next : this.first_stream
        if (rockbox) {
            rockbox.set_value(next_stream ? next_stream.rock : 0)
        }
        return next_stream
    }

    glk_stream_open_file(fref: FileRef, mode: number, rock: number): Stream | null {
        return this.create_file_stream(fref, mode, rock, false)
    }

    glk_stream_open_file_uni(fref: FileRef, mode: number, rock: number): Stream | null {
        return this.create_file_stream(fref, mode, rock, true)
    }

    glk_stream_open_memory(buf: GlkByteArray | null, mode: number, rock: number): Stream {
        return this.create_memory_stream(buf, mode, rock, Uint8Array)
    }

    glk_stream_open_memory_uni(buf: GlkWordArray | null, mode: number, rock: number): Stream {
        return this.create_memory_stream(buf, mode, rock, Uint32Array)
    }

    glk_stream_open_resource(filenum: number, rock: number): Stream | null {
        return this.create_resource_stream(filenum, rock, false)
    }

    glk_stream_open_resource_uni(filenum: number, rock: number): Stream | null {
        return this.create_resource_stream(filenum, rock, true)
    }

    glk_stream_set_current(str: Stream | null) {
        this.current_stream = str
    }

    glk_stream_set_position(str: Stream, pos: number, seekmode: number) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        str.set_position(seekmode, pos)
    }

    glk_style_distinguish(_win: Window, _style1: number, _style2: number): number {
        return 0
    }

    glk_style_measure(_win: Window, _style: number, _hint: number, result?: RefBoxArg): number {
        if (result) {
            result.set_value(0)
        }
        return 0
    }

    glk_stylehint_clear(wintype: number, style: number, hint: number) {
        const selector = `.Style_${STYLE_NAMES[style]}${hint <= stylehint_Justification ? '_par' : ''}`
        function remove_style(styles: WindowStyles) {
            if (styles[selector]) {
                delete styles[selector][CSS_STYLE_PROPERTIES[hint]]
                if (!Object.keys(styles[selector]).length) {
                    delete styles[selector]
                }
            }
        }

        if (wintype === wintype_AllTypes || wintype === wintype_TextBuffer) {
            remove_style(this.stylehints.buffer)
        }

        if (wintype === wintype_AllTypes || wintype === wintype_TextGrid) {
            remove_style(this.stylehints.grid)
        }
    }

    glk_stylehint_set(wintype: number, style: number, hint: number, value: number) {
        if (style < 0 || style >= style_NUMSTYLES || hint < 0 || hint >= stylehint_NUMHINTS) {
            return
        }
        if (wintype === wintype_AllTypes) {
            this.glk_stylehint_set(wintype_TextBuffer, style, hint, value)
            this.glk_stylehint_set(wintype_TextGrid, style, hint, value)
            return
        }
        if (wintype === wintype_Blank || wintype === wintype_Graphics || wintype === wintype_Pair) {
            return
        }

        const stylehints = wintype === wintype_TextBuffer ? this.stylehints.buffer : this.stylehints.grid
        const selector = `.Style_${STYLE_NAMES[style]}${hint <= stylehint_Justification ? '_par' : ''}`
        const justifications = ['left', 'justify', 'center', 'right']
        const weights = ['lighter', 'normal', 'bold']
        let stylevalue: string | number | undefined

        if (hint === stylehint_Indentation || hint === stylehint_ParaIndentation) {
            stylevalue = value + 'em'
        }
        if (hint === stylehint_Justification) {
            stylevalue = justifications[value]
        }
        if (hint === stylehint_Size) {
            stylevalue = (1 + value * 0.1) + 'em'
        }
        if (hint === stylehint_Weight) {
            stylevalue = weights[value + 1]
        }
        if (hint === stylehint_Oblique) {
            stylevalue = value ? 'italic' : 'normal'
        }
        if (hint === stylehint_Proportional) {
            stylevalue = value ? 0 : 1
        }
        if (hint === stylehint_TextColor || hint === stylehint_BackColor) {
            stylevalue = colour_code_to_css(value)
        }
        if (hint === stylehint_ReverseColor) {
            stylevalue = value
        }

        if (stylevalue === undefined) {
            return
        }

        if (!stylehints[selector]) {
            stylehints[selector] = {}
        }
        stylehints[selector][CSS_STYLE_PROPERTIES[hint]] = stylevalue
    }

    glk_tick() {}

    glk_simple_time_to_date_local(time: number, factor: number, struct: RefStruct) {
        timestamp_to_date_struct_local(time * 1000 * factor, struct)
    }

    glk_simple_time_to_date_utc(time: number, factor: number, struct: RefStruct) {
        timestamp_to_date_struct_utc(time * 1000 * factor, struct)
    }

    glk_time_to_date_local(timestruct: RefStruct, datestruct: RefStruct) {
        timestamp_to_date_struct_local(time_struct_to_timestamp(timestruct), datestruct)
    }

    glk_time_to_date_utc(timestruct: RefStruct, datestruct: RefStruct) {
        timestamp_to_date_struct_utc(time_struct_to_timestamp(timestruct), datestruct)
    }

    glk_window_clear(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.input.type === 'line') {
            throw new Error('Window has pending line input')
        }
        win.clear()
    }

    glk_window_close(win: Window, stats?: RefStructArg) {
        if (!win) {
            throw new Error('Invalid Window')
        }

        win.str.close(stats)

        if (win === this.root_window) {
            // Close the root window, which means all windows
            this.root_window = null
            this.remove_window(win, true)
        }
        else {
            const parent_win = win.parent!
            const sibling_win = parent_win.child1 === win ? parent_win.child2! : parent_win.child1!
            const grandparent_win = parent_win.parent
            if (grandparent_win) {
                if (grandparent_win.child1 === parent_win) {
                    grandparent_win.child1 = sibling_win
                }
                else {
                    grandparent_win.child2 = sibling_win
                }
                sibling_win.parent = grandparent_win
            }
            else {
                this.root_window = sibling_win
                sibling_win.parent = null
            }
            this.remove_window(win, true)
            this.remove_window(parent_win, false)

            this.rearrange_window(sibling_win, parent_win.box)
        }
    }

    glk_window_erase_rect(win: Window, left: number, top: number, width: number, height: number) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type !== 'graphics') {
            throw new Error('Invalid Window: not a graphics window')
        }
        win.draw.push({
            height,
            special: 'fill',
            width,
            x: left,
            y: top,
        })
    }

    glk_window_fill_rect(win: Window, colour: number, left: number, top: number, width: number, height: number) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type !== 'graphics') {
            throw new Error('Invalid Window: not a graphics window')
        }
        win.draw.push({
            color: colour_code_to_css(colour),
            height,
            special: 'fill',
            width,
            x: left,
            y: top,
        })
    }

    glk_window_flow_break(win: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type === 'buffer') {
            win.set_flow_break()
        }
    }

    glk_window_get_arrangement(win: Window, method?: RefBoxArg, size?: RefBoxArg, keywin?: RefBoxArg) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type !== 'pair') {
            throw new Error('Invalid Window: not a pair window')
        }
        if (keywin) {
            keywin?.set_value(win.key)
        }
        if (method) {
            method?.set_value(win.dir | (win.fixed ? winmethod_Fixed : winmethod_Proportional) | (win.border ? winmethod_Border : winmethod_NoBorder))
        }
        if (size) {
            size?.set_value(win.size)
        }
    }

    glk_window_get_echo_stream(win: Window): Stream | null {
        if (!win) {
            throw new Error('Invalid Window')
        }
        return win.echostr
    }

    glk_window_get_parent(win: Window): Window | null {
        if (!win) {
            throw new Error('Invalid Window')
        }
        return win.parent
    }

    glk_window_get_rock(win: Window): number {
        if (!win) {
            throw new Error('Invalid Window')
        }
        return win.rock
    }

    glk_window_get_root(): Window | null {
        return this.root_window
    }

    glk_window_get_sibling(win: Window): Window | null {
        if (!win) {
            throw new Error('Invalid Window')
        }
        const parent = win.parent
        if (!parent) {
            return null
        }
        if (parent.child1 === win) {
            return parent.child2
        }
        else {
            return parent.child1
        }
    }

    glk_window_get_size(win: Window, widthbox?: RefBoxArg, heightbox?: RefBoxArg) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        const metrics = this.metrics
        let height = 0
        let width = 0
        switch (win.type) {
            case 'buffer':
                height = normalise_window_dimension((win.box.bottom - win.box.top - metrics.buffermarginy) / metrics.buffercharheight)
                width = normalise_window_dimension((win.box.right - win.box.left - metrics.buffermarginx) / metrics.buffercharwidth)
                break
            case 'graphics':
            case 'grid':
                height = win.height
                width = win.width
                break
        }
        if (heightbox) {
            heightbox?.set_value(height)
        }
        if (widthbox) {
            widthbox?.set_value(width)
        }
    }

    glk_window_get_stream(win: Window): Stream {
        if (!win) {
            throw new Error('Invalid Window')
        }
        return win.str
    }

    glk_window_get_type(win: Window): number {
        if (!win) {
            throw new Error('Invalid Window')
        }
        return win.typenum
    }

    glk_window_iterate(win?: Window, rockbox?: RefBoxArg): Window | null {
        const next_window = win ? win.next : this.first_window
        if (rockbox) {
            rockbox?.set_value(next_window ? next_window.rock : 0)
        }
        return next_window
    }

    glk_window_move_cursor(win: Window, xpos: number, ypos: number) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type !== 'grid') {
            throw new Error('Invalid Window: not a grid window')
        }
        win.x = Math.max(0, xpos)
        win.y = Math.max(0, ypos)
    }

    glk_window_open(splitwin: Window | null, method: number, size: number, wintype: number, rock: number): Window | null {
        // Check the parameters
        if (!this.root_window) {
            if (splitwin) {
                throw new Error('Invalid splitwin: must be null for first window')
            }
        }
        else {
            if (!splitwin) {
                throw new Error('Invalid splitwin')
            }
            if (splitwin.type === 'pair') {
                throw new Error('Invalid splitwin: must not be a pair window')
            }
            const division = method & winmethod_DivisionMask
            const direction = method & winmethod_DirMask
            if (division !== winmethod_Fixed && division !== winmethod_Proportional) {
                throw new Error('Invalid method: must be fixed or proportional')
            }
            if (division === winmethod_Fixed && splitwin.type === 'blank') {
                throw new Error('Invalid method: blank windows cannot be only be split proportionally')
            }
            if (direction !== winmethod_Above && direction !== winmethod_Below && direction !== winmethod_Left && direction !== winmethod_Right) {
                throw new Error('Invalid method: bad direction')
            }
        }

        // Create the window
        let win: Window
        switch (wintype) {
            case wintype_Blank:
                win = new BlankWindow(rock)
                break
            case wintype_Graphics:
                win = new GraphicsWindow(rock)
                break
            case wintype_TextBuffer:
                win = new BufferWindow(rock, this.stylehints.buffer)
                break
            case wintype_TextGrid:
                win = new GridWindow(rock, this.stylehints.grid)
                break
            default:
                throw new Error('Invalid wintype')
        }
        this.register_window(win)

        // Rearrange the windows for the new window
        if (splitwin) {
            const pairwin = new PairWindow(win, method, size)
            this.register_window(pairwin)
            // Set up the win relations
            pairwin.child1 = splitwin
            pairwin.child2 = win
            const oldparent = splitwin.parent
            splitwin.parent = pairwin
            win.parent = pairwin
            pairwin.parent = oldparent
            if (oldparent) {
                if (oldparent.child1 === splitwin) {
                    oldparent.child1 = pairwin
                }
                else {
                    oldparent.child2 = pairwin
                }
            }
            else {
                this.root_window = pairwin
            }
            this.rearrange_window(pairwin, splitwin.box)
        }
        else {
            this.root_window = win
            this.rearrange_window(win, {
                bottom: this.metrics.height,
                left: 0,
                right: this.metrics.width,
                top: 0,
            })
        }

        return win
    }

    glk_window_set_arrangement(win: Window, method: number, size: number, keywin?: Window) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type !== 'pair') {
            throw new Error('Invalid Window: not a pair window')
        }

        if (keywin) {
            if (keywin.type === 'pair') {
                throw new Error('Invalid keywin: cannot be a pair window')
            }
            let win_parent: Window | null = keywin
            while ((win_parent = win_parent?.parent)) {
                if (win_parent === win) {
                    break
                }
            }
            if (!win_parent) {
                throw new Error('keywin must be a descendent')
            }
        }

        const new_dir = method & winmethod_DirMask
        const new_vertical = new_dir === winmethod_Left || new_dir === winmethod_Right
        if (!keywin) {
            keywin = win.key!
        }
        if (new_vertical && !win.vertical) {
            throw new Error('Invalid method: split must stay horizontal')
        }
        if (!new_vertical && win.vertical) {
            throw new Error('Invalid method: split must stay vertical')
        }
        const new_fixed = (method & winmethod_DivisionMask) === winmethod_Fixed
        if (keywin.type === 'blank' && new_fixed) {
            throw new Error('Invalid method: blank windows cannot be only be split proportionally')
        }

        const new_backward = new_dir === winmethod_Left || new_dir === winmethod_Above
        if (new_backward !== win.backward) {
            // Switch the children
            const temp_win = win.child1
            win.child1 = win.child2
            win.child2 = temp_win
        }

        // Update the window
        win.backward = new_backward
        win.border = (method & winmethod_BorderMask) === winmethod_BorderMask
        win.dir = new_dir
        win.fixed = new_fixed
        win.key = keywin
        win.size = size
        win.vertical = new_vertical

        this.rearrange_window(win, win.box)
    }

    glk_window_set_background_color(win: Window, colour: number) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.type !== 'graphics') {
            throw new Error('Invalid Window: not a graphics window')
        }
        win.draw.push({
            color: colour_code_to_css(colour),
            special: 'setcolor',
        })
    }

    glk_window_set_echo_stream(win: Window, stream: Stream | null) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        win.echostr = stream
    }

    garglk_set_reversevideo(val: number) {
        this.garglk_set_reversevideo_stream(this.current_stream!, val)
    }

    garglk_set_reversevideo_stream(str: Stream, val: number) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.type === 'window') {
            str.set_css('reverse', val ? 1 : undefined)
        }
    }

    garglk_set_zcolors(fg: number, bg: number) {
        this.garglk_set_zcolors_stream(this.current_stream!, fg, bg)
    }

    garglk_set_zcolors_stream(str: Stream, fg: number, bg: number) {
        if (!str) {
            throw new Error('Invalid Stream')
        }
        if (str.type === 'window') {
            if (fg !== zcolor_Current) {
                str.set_css('color', fg === zcolor_Default ? undefined : colour_code_to_css(fg))
            }
            if (bg !== zcolor_Current) {
                str.set_css('background-color', bg === zcolor_Default ? undefined : colour_code_to_css(bg))
            }
        }
    }

    // Private internal functions

    /** Process an input event */
    private accept(ev: Protocol.Event) {
        if (this.exited) {
            return this.GlkOte.log('GlkApi has exited')
        }

        if (ev.gen !== this.gen) {
            return this.GlkOte.log(`Input event has wrong generation number: expected ${this.gen}, received ${ev.gen}`)
        }
        this.gen++

        if (!this.selectref && ev.type !== 'init' && ev.type !== 'specialresponse') {
            return
        }

        this.partial_inputs = ev.partial

        let type = evtype_None
        let win: Window | null = null
        let val1 = 0
        let val2 = 0
        let fref: FileRef | undefined

        if ('window' in ev) {
            for (win = this.first_window; win; win = win.next) {
                if (win.disprock === ev.window) {
                    break
                }
            }
        }

        switch (ev.type) {
            case 'init':
                this.metrics = normalise_metrics(ev.metrics)
                this.support = ev.support
                this.VM.start()
                return
            case 'arrange':
                this.metrics = normalise_metrics(ev.metrics)
                if (this.root_window) {
                    this.rearrange_window(this.root_window, {
                        bottom: this.metrics.height,
                        left: 0,
                        right: this.metrics.width,
                        top: 0,
                    })
                }
                type = evtype_Arrange
                break
            case 'char':
                if (win?.input.type !== 'char') {
                    return
                }
                delete win.input.type
                type = evtype_CharInput
                if (ev.value.length === 1) {
                    val1 = ev.value.codePointAt(0)!
                    if (!(win as TextWindow).uni_input && val1 > MAX_LATIN1) {
                        val1 = QUESTION_MARK
                    }
                }
                else {
                    val1 = KEY_NAMES_TO_CODES[ev.value as Protocol.SpecialKeyCode] ?? keycode_Unknown
                }
                break
            case 'hyperlink':
                if (!win?.input.hyperlink) {
                    return
                }
                delete win.input.hyperlink
                type = evtype_Hyperlink
                val1 = ev.value
                break
            case 'line':
                if (win?.input.type !== 'line') {
                    return
                }
                this.handle_line_input(win as TextWindow, ev.value, this.selectref, ev.terminator)
                this.GiDispa?.prepare_resume(this.selectref!)
                delete this.selectref
                break
            case 'mouse':
                if (!win?.input.mouse) {
                    return
                }
                delete win.input.mouse
                type = evtype_MouseInput
                val1 = ev.x
                val2 = ev.y
                break
            case 'redraw':
                type = evtype_Redraw
                break
            case 'specialresponse': {
                if (ev.response !== 'fileref_prompt') {
                    throw new Error('Unknown type of specialresponse event')
                }
                const dialog_fref = ev.value
                if (typeof dialog_fref === 'string') {
                    throw new Error('AsyncGlk no longer supports bare-string filenames from Dialog')
                }
                if (dialog_fref) {
                    fref = this.create_fileref(dialog_fref.filename, this.special_data!.rock, this.special_data!.usage, dialog_fref)
                }
                break
            }
            case 'timer':
                type = evtype_Timer
                this.timer.started = Date.now()
                break
            default:
                throw new Error(`Event type ${ev.type} not supported by AsyncGlk`)
        }

        if (this.selectref) {
            set_event(this.selectref!, type, win, val1, val2)
            this.GiDispa?.prepare_resume(this.selectref!)
            delete this.selectref
        }
        this.VM.resume(fref)
    }

    private create_fileref(filename: string, rock: number, usage: number, dialog_fref?: DialogFileRef): FileRef {
        if (!dialog_fref) {
            const filetype = usage & fileusage_TypeMask
            const signature = filetype === fileusage_SavedGame ? this.VM.get_signature() : undefined
            dialog_fref = this.Dialog.file_construct_ref(filename, FILE_TYPES[filetype] ?? 'xxx', signature)
        }
        const fref = new FileRef(this.Dialog, filename, dialog_fref, rock, usage)
        fref.next = this.first_fref
        this.first_fref = fref
        if (fref.next) {
            fref.next.prev = fref
        }
        this.GiDispa?.class_register('fileref', fref)
        return fref
    }

    private create_file_stream(fref: FileRef, mode: number, rock: number, unicode: boolean) {
        if (!fref) {
            throw new Error('Invalid Fileref')
        }
        if (mode !== filemode_Write && mode !== filemode_Read && mode !== filemode_ReadWrite && mode !== filemode_WriteAppend) {
            throw new Error('Invalid filemode')
        }
        if (mode === filemode_Read && !fref.exists()) {
            return null
        }

        // Now read in the data
        let data: Uint8Array | null = null
        if (mode !== filemode_Write) {
            data = fref.read()
        }
        if (!data) {
            data = new Uint8Array(0)
            fref.write(data)
        }
        // Create an appropriate stream
        const str = create_stream_from_buffer(data, fref.binary, mode, rock, unicode, fref)

        if (mode === filemode_WriteAppend) {
            str.set_position(seekmode_End, 0)
        }
        this.register_stream(str)
        return str
    }

    private create_memory_stream(buf: GlkArray | null, mode: number, rock: number, typed_array: GlkTypedArrayConstructor) {
        if (mode !== filemode_Read && mode !== filemode_Write && mode !== filemode_ReadWrite) {
            throw new Error('Illegal filemode')
        }
        let str: Stream
        if (buf) {
            const common_cb = () => this.GiDispa?.unretain_array(buf)
            if (Array.isArray(buf)) {
                const new_arr = typed_array.from(buf)
                if (mode === filemode_Read) {
                    str = new ArrayBackedStream(new_arr, mode, rock, common_cb)
                }
                // When opening an Array in a write mode we must copy the values back
                else {
                    str = new ArrayBackedStream(new_arr, mode, rock, () => {
                        copy_array(new_arr, buf, buf.length)
                        common_cb()
                    })
                }
            }
            else {
                str = new ArrayBackedStream(buf, mode, rock, common_cb)
            }
            this.GiDispa?.retain_array(buf)
        }
        else {
            str = new NullStream(mode, rock)
        }
        this.register_stream(str)
        return str
    }

    private create_resource_stream(filenum: number, rock: number, unicode: boolean) {
        if (!this.Blorb) {
            return null
        }
        const chunk = this.Blorb.get_data_chunk(filenum)
        if (!chunk) {
            return null
        }
        const str = create_stream_from_buffer(chunk.data, chunk.binary, filemode_Read, rock, unicode)
        this.register_stream(str)
        return str
    }

    private draw_image(win: Window, imginfo: ImageInfo, height: number, val1: number, val2: number, width: number) {
        const data: Partial<BufferWindowImage & ImageOperation> = {
            // TODO!
            alttext: '',
            height,
            image: imginfo.image,
            special: 'image',
            url: imginfo.url,
            width,
        }
        switch (win.type) {
            case 'buffer':
                data.alignment = IMAGE_ALIGNMENTS[val1] ?? 'inlineup'
                win.put_image(data as BufferWindowImage)
                return 1
            case 'graphics':
                data.x = val1
                data.y = val2
                win.draw.push(data as ImageOperation)
                return 1
        }
        return 0
    }

    private handle_line_input(win: TextWindow, input: string, ev?: RefStructArg, termkey?: TerminatorCode) {
        // The Glk spec is a bit ambiguous here
        // I'm going to echo first
        if (win.request_echo_line_input) {
            win.put_string(input + '\n', 'input')
            if (win.echostr) {
                win.echostr.put_string(input + '\n', 'input')
            }
        }

        // Then trim and convert non-Latin1 characters
        if (input.length > win.line_input_buf!.length) {
            input = input.slice(0, win.line_input_buf!.length)
        }
        if (!win.uni_input) {
            input = input.replace(/[^\x00-\xff]/g, '?')
        }

        const input_buf = Uint32Array.from(input, ch => ch.codePointAt(0)!)
        if (Array.isArray(win.line_input_buf!)) {
            copy_array(input_buf, win.line_input_buf!, input.length)
        }
        else {
            win.line_input_buf?.set(input_buf)
        }

        const terminator = TERMINATOR_KEYS_TO_CODES[termkey as TerminatorCode] ?? 0

        if (ev) {
            set_event(ev, evtype_LineInput, win as Window, input.length, terminator)
        }
        this.GiDispa?.unretain_array(win.line_input_buf!)
        delete win.input.type
        delete win.line_input_buf
    }

    private rearrange_window(win: Window, box: WindowBox) {
        const metrics = this.metrics
        this.windows_changed = true
        win.box = box
        const boxheight = box.bottom - box.top
        const boxwidth = box.right - box.left
        switch (win.type) {
            case 'graphics': {
                win.height = normalise_window_dimension(boxheight - metrics.graphicsmarginy)
                win.width = normalise_window_dimension(boxwidth - metrics.graphicsmarginx)
                break
            }
            case 'grid': {
                const height = normalise_window_dimension((boxheight - metrics.gridmarginy) / metrics.gridcharheight)
                const width = normalise_window_dimension((boxwidth - metrics.gridmarginx) / metrics.gridcharwidth)
                win.update_size(height, width)
                break
            }
            case 'pair': {
                let min, max, splitwidth
                if (win.vertical) {
                    min = box.left
                    max = box.right
                    splitwidth = metrics.inspacingx
                }
                else {
                    min = box.top
                    max = box.bottom
                    splitwidth = metrics.inspacingy
                }
                if (!win.border) {
                    splitwidth = 0
                }
                const diff = max - min

                // Calculate the split size
                let split = 0
                if (win.fixed) {
                    switch (win.key!.type) {
                        case 'buffer':
                            if (win.vertical) {
                                split = win.size ? (win.size * metrics.buffercharwidth + metrics.buffermarginx) : 0
                            }
                            else {
                                split = win.size ? (win.size * metrics.buffercharheight + metrics.buffermarginy) : 0
                            }
                            break
                        case 'graphics':
                            split = win.size ? (win.size + (win.vertical ? metrics.graphicsmarginx : metrics.graphicsmarginy)) : 0
                            break
                        case 'grid':
                            if (win.vertical) {
                                split = win.size ? (win.size * metrics.gridcharwidth + metrics.gridmarginx) : 0
                            }
                            else {
                                split = win.size ? (win.size * metrics.gridcharheight + metrics.gridmarginy) : 0
                            }
                            break
                    }
                    split = Math.ceil(split)
                }
                else {
                    split = Math.floor((diff * win.size) / 100)
                }

                // split is now a number between 0 and diff; now convert it to a number between min and max, and apply upside-down-ness
                if (win.backward) {
                    split = min + split
                }
                else {
                    split = max - split - splitwidth
                }

                // Make sure it really is between min and max
                if (min >= max) {
                    split = min
                }
                else {
                    split = Math.min(Math.max(split, min), max - splitwidth)
                }

                // The two child window boxes can now be constructed
                let box1: WindowBox, box2: WindowBox
                if (win.vertical) {
                    box1 = {
                        bottom: box.bottom,
                        left: box.left,
                        right: split,
                        top: box.top,
                    }
                    box2 = {
                        bottom: box.bottom,
                        left: split + splitwidth,
                        right: box.right,
                        top: box.top,
                    }
                }
                else {
                    box1 = {
                        bottom: split,
                        left: box.left,
                        right: box.right,
                        top: box.top,
                    }
                    box2 = {
                        bottom: box.bottom,
                        left: box.left,
                        right: box.right,
                        top: split + splitwidth,
                    }
                }
                this.rearrange_window(win.child1!, win.backward ? box2 : box1)
                this.rearrange_window(win.child2!, win.backward ? box1 : box2)
                break
            }
        }
    }

    private register_stream(str: Stream) {
        str.next = this.first_stream
        this.first_stream = str
        if (str.next) {
            str.next.prev = str
        }
        this.GiDispa?.class_register('stream', str)
    }

    private register_window(win: Window) {
        this.windows_changed = true
        win.next = this.first_window
        this.first_window = win
        if (win.next) {
            win.next.prev = win
        }
        // A disprock must be assigned because it is used as the protocol ID
        if (this.GiDispa) {
            this.GiDispa?.class_register('window', win)
        }
        else {
            win.disprock = this.disprock_counter++
        }
        win.input.id = win.disprock
        this.register_stream(win.str)
    }

    private remove_window(win: Window, recurse: boolean) {
        this.windows_changed = true

        if (this.GiDispa && 'line_input_buf' in win && win.line_input_buf) {
            this.GiDispa.unretain_array(win.line_input_buf!)
            delete win.line_input_buf
        }

        if (win.type === 'pair') {
            if (recurse) {
                this.remove_window(win.child1!, true)
                this.remove_window(win.child2!, true)
            }
            win.child1 = null
            win.child2 = null
            win.key = null
        }

        this.unregister_stream(win.str)
        win.echostr = null
        win.parent = null

        this.GiDispa?.class_unregister('window', win)
        const prev = win.prev
        const next = win.next
        win.prev = null
        win.next = null
        if (prev) {
            prev.next = next
        }
        else {
            this.first_window = next
        }
        if (next) {
            next.prev = prev
        }
    }

    private request_char_event(win: Window, uni: boolean) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.input.type) {
            throw new Error('Window already has keyboard request')
        }
        if (win.type === 'blank' || win.type === 'pair') {
            throw new Error('Window does not support character input')
        }

        win.input.gen = this.gen
        win.input.type = 'char'
        win.uni_input = uni
    }

    private request_line_event(win: Window, buf: GlkArray, uni: boolean, initlen?: number) {
        if (!win) {
            throw new Error('Invalid Window')
        }
        if (win.input.type) {
            throw new Error('Window already has keyboard request')
        }
        if (win.type !== 'buffer' && win.type !== 'grid') {
            throw new Error('Window does not support line input')
        }

        win.input.gen = this.gen
        if (initlen) {
            win.input.initial = String.fromCodePoint(...buf.slice(0, initlen))
        }
        win.input.type = 'line'
        win.line_input_buf = buf
        if (win.type === 'buffer') {
            win.request_echo_line_input = win.echo_line_input
        }
        win.uni_input = uni
        this.GiDispa?.retain_array(buf)
    }

    private unregister_stream(str: Stream) {
        if (this.current_stream === str) {
            this.current_stream = null
        }
        this.GiDispa?.class_unregister('stream', str)
        const prev = str.prev
        const next = str.next
        str.prev = null
        str.next = null
        if (prev) {
            prev.next = next
        }
        else {
            this.first_stream = next
        }
        if (next) {
            next.prev = prev
        }
    }
}

function buffer_transformer(buf: GlkWordArray, initlen: number, func: (str: string | Uint32Array) => string, dont_reduce?: boolean) {
    const utf32_array = Array.isArray(buf) ? buf.slice(0, initlen) as any as Uint32Array : buf.subarray(0, initlen)
    const data = dont_reduce ? utf32_array : utf32_array.reduce((prev, ch) => prev + String.fromCodePoint(ch), '')
    const new_str = func(data)
    const newbuf = Uint32Array.from(new_str, ch => ch.codePointAt(0)!)
    const newlen = newbuf.length
    if (Array.isArray(buf)) {
        copy_array(newbuf, buf, newlen)
    }
    else {
        buf.set(newbuf.subarray(0, Math.min(buf.length, newlen)))
    }
    return newlen
}

function colour_code_to_css(colour: number) {
    // Uppercase colours are required by RegTest
    return '#' + (colour & 0xFFFFFF).toString(16).toUpperCase().padStart(6, '0')
}

function create_stream_from_buffer(buf: Uint8Array, binary: boolean, mode: number, rock: number, unicode: boolean, fref?: FileRef) {
    let data: GlkTypedArray
    if (unicode) {
        if (binary) {
            data = BEBuffer_to_Array(buf)
        }
        else {
            const text = utf8decoder.decode(buf)
            data = Uint32Array.from(text, ch => ch.codePointAt(0)!)
        }
    }
    else {
        data = buf
    }
    if (mode === filemode_Read) {
        return new ArrayBackedStream(data, mode, rock)
    }
    else {
        return new FileStream(fref!, data, mode, rock)
    }
}

function date_struct_to_timestamp_local(struct: RefStruct): number {
    const date = new Date(
        struct.get_field(0) as number,
        struct.get_field(1) as number - 1,
        struct.get_field(2) as number,
        struct.get_field(4) as number,
        struct.get_field(5) as number,
        struct.get_field(6) as number,
        struct.get_field(7) as number / 1000,
    )
    return date.getTime()
}

function date_struct_to_timestamp_utc(struct: RefStruct): number {
    const date = new Date(0)
    date.setUTCFullYear(struct.get_field(0) as number)
    date.setUTCMonth(struct.get_field(1) as number - 1)
    date.setUTCDate(struct.get_field(2) as number)
    date.setUTCHours(struct.get_field(4) as number)
    date.setUTCMinutes(struct.get_field(5) as number)
    date.setUTCSeconds(struct.get_field(6) as number)
    date.setUTCMilliseconds(struct.get_field(7) as number / 1000)
    return date.getTime()
}

function normalise_metrics(metrics: Protocol.Metrics) {
    const normalised_metrics: Protocol.NormalisedMetrics = Object.assign({}, DEFAULT_METRICS)
    let val: number | undefined

    val = metrics.charheight
    if (val !== undefined) {
        normalised_metrics.buffercharheight= val
        normalised_metrics.gridcharheight = val
    }
    val = metrics.charwidth
    if (val !== undefined) {
        normalised_metrics.buffercharwidth = val
        normalised_metrics.gridcharwidth = val
    }

    val = metrics.margin
    if (val !== undefined) {
        normalised_metrics.buffermarginx = val
        normalised_metrics.buffermarginy = val
        normalised_metrics.graphicsmarginx = val
        normalised_metrics.graphicsmarginy = val
        normalised_metrics.gridmarginx = val
        normalised_metrics.gridmarginy = val
    }
    val = metrics.buffermargin
    if (val !== undefined) {
        normalised_metrics.buffermarginx = val
        normalised_metrics.buffermarginy = val
    }
    val = metrics.graphicsmargin
    if (val !== undefined) {
        normalised_metrics.graphicsmarginx = val
        normalised_metrics.graphicsmarginy = val
    }
    val = metrics.gridmargin
    if (val !== undefined) {
        normalised_metrics.gridmarginx = val
        normalised_metrics.gridmarginy = val
    }
    val = metrics.marginx
    if (val !== undefined) {
        normalised_metrics.buffermarginx = val
        normalised_metrics.graphicsmarginx = val
        normalised_metrics.gridmarginx = val
    }
    val = metrics.marginy
    if (val !== undefined) {
        normalised_metrics.buffermarginy = val
        normalised_metrics.graphicsmarginy = val
        normalised_metrics.gridmarginy = val
    }

    val = metrics.spacing
    if (val !== undefined) {
        normalised_metrics.inspacingx = val
        normalised_metrics.inspacingy = val
    }
    val = metrics.inspacing
    if (val !== undefined) {
        normalised_metrics.inspacingx = val
        normalised_metrics.inspacingy = val
    }
    val = metrics.spacingx
    if (val !== undefined) {
        normalised_metrics.inspacingx = val
    }
    val = metrics.spacingy
    if (val !== undefined) {
        normalised_metrics.inspacingy = val
    }

    Object.assign(normalised_metrics, metrics)

    if (metrics.outspacing || normalised_metrics.outspacingx || normalised_metrics.outspacingy) {
        throw new Error('AsyncGlk requires that outspacing metrics be 0')
    }

    return normalised_metrics
}

function normalise_window_dimension(val: number) {
    return Math.max(0, Math.floor(val))
}

function set_event(ev: Interface.RefStruct, type: number = evtype_None, win: Window | null = null, val1 = 0, val2 = 0) {
    ev.set_field(0, type)
    ev.set_field(1, win)
    ev.set_field(2, val1)
    ev.set_field(3, val2)
}

function timestamp_to_date_struct_local(timestamp: number, struct: RefStruct) {
    const date = new Date(timestamp)
    struct.set_field(0, date.getFullYear())
    struct.set_field(1, date.getMonth() + 1)
    struct.set_field(2, date.getDate())
    struct.set_field(3, date.getDay())
    struct.set_field(4, date.getHours())
    struct.set_field(5, date.getMinutes())
    struct.set_field(6, date.getSeconds())
    struct.set_field(7, date.getMilliseconds() * 1000)
}

function timestamp_to_date_struct_utc(timestamp: number, struct: RefStruct) {
    const date = new Date(timestamp)
    struct.set_field(0, date.getUTCFullYear())
    struct.set_field(1, date.getUTCMonth() + 1)
    struct.set_field(2, date.getUTCDate())
    struct.set_field(3, date.getUTCDay())
    struct.set_field(4, date.getUTCHours())
    struct.set_field(5, date.getUTCMinutes())
    struct.set_field(6, date.getUTCSeconds())
    struct.set_field(7, date.getUTCMilliseconds() * 1000)
}

function timestamp_to_time_struct(timestamp: number, struct: RefStruct) {
    struct.set_field(0, Math.floor(timestamp / 4294967296000))
    struct.set_field(1, Math.floor(timestamp / 1000) >>> 0)
    let microsecs = Math.floor((timestamp % 1000) * 1000)
    if (microsecs < 0) {
        microsecs += 1000000
    }
    struct.set_field(2, microsecs)
}

function time_struct_to_timestamp(struct: RefStruct): number {
    return (struct.get_field(0) as number) * 4294967296000 +
        (struct.get_field(1) as number) * 1000 +
        (struct.get_field(2) as number) / 1000
}

/** Handle legacy non-typed arrays in functions which need to write to the array */
function wrap_for_array(arr: number[], typed_array: GlkTypedArrayConstructor, func: (arr: GlkTypedArray) => number): number {
    const new_arr = new typed_array(arr.length)
    const res = func(new_arr)
    copy_array(new_arr, arr, res)
    return res
}