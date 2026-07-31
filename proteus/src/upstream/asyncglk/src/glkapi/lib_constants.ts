/*

GlkApi constants
================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import type {BufferWindowImage, FileMode, FileType, SpecialKeyCode, TerminatorCode} from '../common/protocol.js'

import {keycode_Delete, keycode_Down, keycode_End, keycode_Escape, keycode_Func1, keycode_Func2, keycode_Func3, keycode_Func4,  keycode_Func5, keycode_Func6, keycode_Func7, keycode_Func8, keycode_Func9, keycode_Func10, keycode_Func11, keycode_Func12, keycode_Home, keycode_Left, keycode_PageDown, keycode_PageUp, keycode_Return, keycode_Right, keycode_Tab, keycode_Up} from './constants.js'

export const GLK_NULL = 0
export const MAX_LATIN1 = 0xFF
export const QUESTION_MARK = 63

export const CSS_STYLE_PROPERTIES = ['margin-left', 'text-indent', 'text-align', 'font-size', 'font-weight', 'font-style', 'monospace', 'color', 'background-color', 'reverse']

export const FILE_MODES: Record<number, FileMode> = {
    1: 'write',
    2: 'read',
    3: 'readwrite',
    5: 'writeappend',
}

export const FILE_TYPES: Record<number, FileType> = {
    0: 'data',
    1: 'save',
    2: 'transcript',
    3: 'command',
}

export const IMAGE_ALIGNMENTS: Record<number, BufferWindowImage['alignment']> = {
    1: 'inlineup',
    2: 'inlinedown',
    3: 'inlinecenter',
    4: 'marginleft',
    5: 'marginright',
}

export const KEY_NAMES_TO_CODES: Record<SpecialKeyCode, number> = {
    delete: keycode_Delete,
    down: keycode_Down,
    end: keycode_End,
    escape: keycode_Escape,
    func1: keycode_Func1,
    func2: keycode_Func2,
    func3: keycode_Func3,
    func4: keycode_Func4,
    func5: keycode_Func5,
    func6: keycode_Func6,
    func7: keycode_Func7,
    func8: keycode_Func8,
    func9: keycode_Func9,
    func10: keycode_Func10,
    func11: keycode_Func11,
    func12: keycode_Func12,
    home: keycode_Home,
    left: keycode_Left,
    pagedown: keycode_PageDown,
    pageup: keycode_PageUp,
    return: keycode_Return,
    right: keycode_Right,
    tab: keycode_Tab,
    up: keycode_Up,
}

export const STYLE_NAMES: Record<number, string> = {
    0: 'normal',
    1: 'emphasized',
    2: 'preformatted',
    3: 'header',
    4: 'subheader',
    5: 'alert',
    6: 'note',
    7: 'blockquote',
    8: 'input',
    9: 'user1',
    10: 'user2',
}

export const TERMINATOR_KEYS: Record<number, TerminatorCode> = {
    0xfffffff8: 'escape',
    0xffffffef: 'func1',
    0xffffffee: 'func2',
    0xffffffed: 'func3',
    0xffffffec: 'func4',
    0xffffffeb: 'func5',
    0xffffffea: 'func6',
    0xffffffe9: 'func7',
    0xffffffe8: 'func8',
    0xffffffe7: 'func9',
    0xffffffe6: 'func10',
    0xffffffe5: 'func11',
    0xffffffe4: 'func12',
}

export const TERMINATOR_KEYS_TO_CODES: Partial<Record<SpecialKeyCode, number>> = {
    escape: keycode_Escape,
    func1: keycode_Func1,
    func2: keycode_Func2,
    func3: keycode_Func3,
    func4: keycode_Func4,
    func5: keycode_Func5,
    func6: keycode_Func6,
    func7: keycode_Func7,
    func8: keycode_Func8,
    func9: keycode_Func9,
    func10: keycode_Func10,
    func11: keycode_Func11,
    func12: keycode_Func12,
}