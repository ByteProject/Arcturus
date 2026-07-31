/*

The GlkApi interface
====================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {Blorb} from '../blorb/blorb.js'
import type {FileRef} from '../common/protocol.js'
import type {Dialog} from '../dialog/common/interface.js'
import type {GlkOte} from '../glkote/common/glkote.js'

import * as Const from './constants.js'

type TruthyOption = boolean | number

export type GlkArray = Array<number> | Uint8Array | Uint32Array
export type GlkByteArray = Array<number> | Uint8Array
export type GlkWordArray = Array<number> | Uint32Array

// Opaque classes
export type GlkClassName = 'fileref' | 'stream' | 'window'
export interface GlkFref {disprock?: number}
export interface GlkSchannel {disprock?: number}
export interface GlkStream {disprock?: number}
export interface GlkWindow {disprock?: number}
export type GlkObject = GlkFref | GlkSchannel | GlkStream | GlkWindow

export type RefStructValue = GlkWindow | number | null

/** A box to hold a value */
export interface RefBox {
    get_value(): RefStructValue,
    set_value(val: RefStructValue): void,
}
// Existing code may pass a 0 instead of a null, so we need this type alias to remind us we can't use optional chaining
export type RefBoxArg = RefBox | 0

/** A struct for holding multiple values */
export interface RefStruct {
    get_field(index: number): RefStructValue,
    get_fields(): RefStructValue[],
    push_field(val: RefStructValue): void,
    set_field(index: number, val: RefStructValue): void,
}
export type RefStructArg = RefStruct | 0

export const DidNotReturn = {
    dummy: 'Glk call has not yet returned',
}

/** A generic GiDispa interface */
export interface GiDispa {
    check_autosave(): boolean,
    class_obj_from_id(class_name: GlkClassName, disprock: number): GlkObject,
    class_register(class_name: GlkClassName, obj: GlkObject, disprock?: number): void,
    class_unregister(class_name: GlkClassName, obj: GlkObject): void,
    get_retained_array(arr: GlkArray): any,
    init(options: {
        io: GlkApi,
        vm: GlkVM,
    }): void,
    prepare_resume(arg: RefStruct): void,
    retain_array(arr1: GlkArray, useobj?: any): void,
    unretain_array(arr: GlkArray): void,
}

/** A generic VM interface */
export interface GlkVM {
    do_autosave(save: number | any): void,
    get_signature(): string,
    resume(arg?: FileRef): void,
    start(): void,
}

/** Options GlkApi consumes */
export interface GlkApiOptions {
    before_select_hook?: () => void,
    Blorb?: Blorb,
    Dialog: Dialog,
    do_vm_autosave?: TruthyOption,
    exit_warning?: TruthyOption,
    extevent_hook?: (val: any) => void,
    GiDispa?: GiDispa,
    glk_gestalt_hook?: (sel: number, value: number, array: GlkArray | null) => number,
    GlkOte: GlkOte,
    vm: GlkVM,
}

/** The main Glk API */
export interface GlkApi {
    // Class functions
    version: string,
    init(options: GlkApiOptions): void,
    call_may_not_return(id: number): boolean,
    fatal_error(msg: string): void,
    getlibrary(class_name: string): Blorb | Dialog | GiDispa | GlkOte | GlkVM | null,
    inited(): boolean,
    restore_allstate(state: any): void,
    save_allstate(): any,
    update(): void,

    // References to other things
    // TODO: remove in a future semver major update?
    Const: typeof Const,
    DidNotReturn: typeof DidNotReturn,
    RefBox: new () => RefBox,
    RefStruct: new () => RefStruct,

    // Extra functions
    byte_array_to_string(arr: GlkByteArray): string,
    glk_put_jstring(val: string, all_bytes?: boolean): void,
    glk_put_jstring_stream(str: GlkStream, val: string, all_bytes?: boolean): void,
    uni_array_to_string(arr: GlkWordArray): string,

    // The Glk functions
    glk_buffer_canon_decompose_uni(buf: GlkWordArray, initlen: number): number,
    glk_buffer_canon_normalize_uni(buf: GlkWordArray, initlen: number): number,
    glk_buffer_to_lower_case_uni(buf: GlkWordArray, initlen: number): number,
    glk_buffer_to_title_case_uni(buf: GlkWordArray, initlen: number, lowerrest: number): number,
    glk_buffer_to_upper_case_uni(buf: GlkWordArray, initlen: number): number,
    glk_cancel_char_event(win: GlkWindow): void,
    glk_cancel_hyperlink_event(win: GlkWindow): void,
    glk_cancel_line_event(win: GlkWindow, ev?: RefStructArg): void,
    glk_cancel_mouse_event(win: GlkWindow): void,
    glk_char_to_lower(val: number): number,
    glk_char_to_upper(val: number): number,
    glk_current_simple_time(factor: number): number,
    glk_current_time(struct: RefStruct): void,
    glk_date_to_simple_time_local(struct: RefStruct, factor: number): number,
    glk_date_to_simple_time_utc(struct: RefStruct, factor: number): number,
    glk_date_to_time_local(datestruct: RefStruct, timestruct: RefStruct): void,
    glk_date_to_time_utc(datestruct: RefStruct, timestruct: RefStruct): void,
    glk_exit(): typeof DidNotReturn,
    glk_fileref_create_by_name(usage: number, filename: string, rock: number): GlkFref,
    glk_fileref_create_by_prompt(usage: number, fmode: number, rock: number): typeof DidNotReturn,
    glk_fileref_create_from_fileref(usage: number, oldfref: GlkFref, rock: number): GlkFref,
    glk_fileref_create_temp(usage: number, rock: number): GlkFref,
    glk_fileref_delete_file(fref: GlkFref): void,
    glk_fileref_destroy(fref: GlkFref): void,
    glk_fileref_does_file_exist(fref: GlkFref): boolean,
    glk_fileref_get_rock(fref: GlkFref): number,
    glk_fileref_iterate(fref?: GlkFref, rockbox?: RefBoxArg): GlkFref | null,
    glk_gestalt(sel: number, val: number): number,
    glk_gestalt_ext(sel: number, val: number, arr: GlkArray | null): number,
    glk_get_buffer_stream(str: GlkStream, buf: GlkByteArray): number,
    glk_get_buffer_stream_uni(str: GlkStream, buf: GlkWordArray): number,
    glk_get_char_stream(str: GlkStream): number,
    glk_get_char_stream_uni(str: GlkStream): number,
    glk_get_line_stream(str: GlkStream, buf: GlkByteArray): number,
    glk_get_line_stream_uni(str: GlkStream, buf: GlkWordArray): number,
    glk_image_draw(win: GlkWindow, imgid: number, val1: number, val2: number): number,
    glk_image_draw_scaled(win: GlkWindow, imgid: number, val1: number, val2: number, width: number, height: number): number,
    glk_image_get_info(imgid: number, width?: RefBoxArg, height?: RefBoxArg): number,
    glk_put_buffer(val: GlkByteArray): void,
    glk_put_buffer_stream(str: GlkStream, val: GlkByteArray): void,
    glk_put_buffer_stream_uni(str: GlkStream, val: GlkWordArray): void,
    glk_put_buffer_uni(val: GlkWordArray): void,
    glk_put_char(val: number): void,
    glk_put_char_stream(str: GlkStream, val: number): void,
    glk_put_char_stream_uni(str: GlkStream, val: number): void,
    glk_put_char_uni(val: number): void,
    glk_put_string(val: string): void,
    glk_put_string_stream(str: GlkStream, val: string): void,
    glk_put_string_stream_uni(str: GlkStream, val: string): void,
    glk_put_string_uni(val: string): void,
    glk_request_char_event(win: GlkWindow): void,
    glk_request_char_event_uni(win: GlkWindow): void,
    glk_request_hyperlink_event(win: GlkWindow): void,
    glk_request_line_event(win: GlkWindow, buf: GlkByteArray, initlen?: number): void,
    glk_request_line_event_uni(win: GlkWindow, buf: GlkWordArray, initlen?: number): void,
    glk_request_mouse_event(win: GlkWindow): void,
    glk_request_timer_events(msecs: number): void,
    glk_schannel_create(rock: number): GlkSchannel | null,
    glk_schannel_create_ext(rock: number, volume: number): GlkSchannel | null,
    glk_schannel_destroy(schannel: GlkSchannel): void,
    glk_schannel_get_rock(schannel: GlkSchannel): number,
    glk_schannel_iterate(schannel?: GlkSchannel, rockbox?: RefBoxArg): GlkSchannel | null,
    glk_schannel_pause(schannel: GlkSchannel): void,
    glk_schannel_play(schannel: GlkSchannel, sound: number): number,
    glk_schannel_play_ext(schannel: GlkSchannel, sound: number, repeats: number, notify: number): number,
    glk_schannel_play_multi(schannels: GlkSchannel[], sounds: GlkArray, notify: number): number,
    glk_schannel_set_volume(schannel: GlkSchannel, volume: number): void,
    glk_schannel_set_volume_ext(schannel: GlkSchannel, volume: number, duration: number, notify: number): void,
    glk_schannel_stop(schannel: GlkSchannel): void,
    glk_schannel_unpause(schannel: GlkSchannel): void,
    glk_select(ev: RefStruct): typeof DidNotReturn,
    glk_select_poll(ev: RefStruct): void,
    glk_set_echo_line_event(win: GlkWindow, val: number): void,
    glk_set_hyperlink(val: number): void,
    glk_set_hyperlink_stream(str: GlkStream, val: number): void,
    glk_set_style(style: number): void,
    glk_set_style_stream(str: GlkStream, style: number): void,
    glk_set_terminators_line_event(win: GlkWindow, keycodes: GlkArray): void,
    glk_set_window(win?: GlkWindow): void,
    glk_sound_load_hint(sound: number, load: number): void,
    glk_stream_close(str: GlkStream, result?: RefStructArg): void,
    glk_stream_get_current(): GlkStream | null,
    glk_stream_get_position(str: GlkStream): number,
    glk_stream_get_rock(str: GlkStream): number,
    glk_stream_iterate(str?: GlkStream, rockbox?: RefBoxArg): GlkStream | null,
    glk_stream_open_file(fref: GlkFref, mode: number, rock: number): GlkStream | null,
    glk_stream_open_file_uni(fref: GlkFref, mode: number, rock: number): GlkStream | null,
    glk_stream_open_memory(buf: GlkByteArray | null, mode: number, rock: number): GlkStream,
    glk_stream_open_memory_uni(buf: GlkWordArray | null, mode: number, rock: number): GlkStream,
    glk_stream_open_resource(filenum: number, rock: number): GlkStream | null,
    glk_stream_open_resource_uni(filenum: number, rock: number): GlkStream | null,
    glk_stream_set_current(str: GlkStream | null): void,
    glk_stream_set_position(str: GlkStream, pos: number, seekmode: number): void,
    glk_style_distinguish(win: GlkWindow, style1: number, style2: number): number,
    glk_style_measure(win: GlkWindow, style: number, hint: number, result?: RefBoxArg): number,
    glk_stylehint_clear(wintype: number, style: number, hint: number): void,
    glk_stylehint_set(wintype: number, style: number, hint: number, value: number): void,
    glk_tick(): void,
    glk_simple_time_to_date_local(time: number, factor: number, struct: RefStruct): void,
    glk_simple_time_to_date_utc(time: number, factor: number, struct: RefStruct): void,
    glk_time_to_date_local(timestruct: RefStruct, datestruct: RefStruct): void,
    glk_time_to_date_utc(timestruct: RefStruct, datestruct: RefStruct): void,
    glk_window_clear(win: GlkWindow): void,
    glk_window_close(win: GlkWindow, stats?: RefStructArg): void,
    glk_window_erase_rect(win: GlkWindow, left: number, top: number, width: number, height: number): void,
    glk_window_fill_rect(win: GlkWindow, colour: number, left: number, top: number, width: number, height: number): void,
    glk_window_flow_break(win: GlkWindow): void,
    glk_window_get_arrangement(win: GlkWindow, method?: RefBoxArg, size?: RefBoxArg, keywin?: RefBoxArg): void,
    glk_window_get_echo_stream(win: GlkWindow): GlkStream | null,
    glk_window_get_parent(win: GlkWindow): GlkWindow | null,
    glk_window_get_rock(win: GlkWindow): number,
    glk_window_get_root(): GlkWindow | null,
    glk_window_get_sibling(win: GlkWindow): GlkWindow | null,
    glk_window_get_size(win: GlkWindow, width?: RefBoxArg, height?: RefBoxArg): void,
    glk_window_get_stream(win: GlkWindow): GlkStream,
    glk_window_get_type(win: GlkWindow): number,
    glk_window_iterate(win?: GlkWindow, rockbox?: RefBoxArg): GlkWindow | null,
    glk_window_move_cursor(win: GlkWindow, xpos: number, ypos: number): void,
    glk_window_open(splitwin: GlkWindow | null, method: number, size: number, wintype: number, rock: number): GlkWindow | null,
    glk_window_set_arrangement(win: GlkWindow, method: number, size: number, keywin?: GlkWindow): void,
    glk_window_set_background_color(win: GlkWindow, colour: number): void,
    glk_window_set_echo_stream(win: GlkWindow, stream: GlkStream | null): void,
    garglk_set_reversevideo(val: number): void,
    garglk_set_reversevideo_stream(str: GlkStream, val: number): void,
    garglk_set_zcolors(fg: number, bg: number): void,
    garglk_set_zcolors_stream(str: GlkStream, fg: number, bg: number): void,
}

/** An Async extension of the Glk API */
export interface GlkApiAsync extends GlkApi {
    glk_fileref_create_by_prompt_async(usage: number, fmode: number, rock: number): Promise<GlkFref | null>,
    glk_fileref_does_file_exist_async(fref: GlkFref): Promise<boolean>,
    glk_select_async(ev: RefStruct): Promise<void>,
    glk_stream_open_file_async(fref: GlkFref, mode: number, rock: number): Promise<GlkStream | null>,
    glk_stream_open_file_uni_async(fref: GlkFref, mode: number, rock: number): Promise<GlkStream | null>,
    restore_allstate_async(state: any): Promise<boolean>,
    save_allstate_async(): Promise<any>,
}