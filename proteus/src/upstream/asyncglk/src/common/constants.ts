/*

Constants
=========

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import * as protocol from './protocol.js'

export const DEFAULT_METRICS: protocol.NormalisedMetrics = {
    buffercharheight: 1,
    buffercharwidth: 1,
    buffermarginx: 0,
    buffermarginy: 0,
    graphicsmarginx: 0,
    graphicsmarginy: 0,
    gridcharheight: 1,
    gridcharwidth: 1,
    gridmarginx: 0,
    gridmarginy: 0,
    height: 50,
    inspacingx: 0,
    inspacingy: 0,
    outspacingx: 0,
    outspacingy: 0,
    width: 80,
}

export const KEY_CODES_TO_NAMES: Record<number, protocol.SpecialKeyCode> = {
    8: 'delete', // Backspace to be precise
    9: 'tab',
    13: 'return',
    27: 'escape',
    33: 'pageup',
    34: 'pagedown',
    35: 'end',
    36: 'home',
    37: 'left',
    38: 'up',
    39: 'right',
    40: 'down',
    112: 'func1',
    113: 'func2',
    114: 'func3',
    115: 'func4',
    116: 'func5',
    117: 'func6',
    118: 'func7',
    119: 'func8',
    120: 'func9',
    121: 'func10',
    122: 'func11',
    123: 'func12',
}

export const KEY_CODE_DOWN = 40
export const KEY_CODE_RETURN = 13
export const KEY_CODE_UP = 38

export const NBSP = '\xa0'
export const THINSPACE = '\u2009'

export const OFFSCREEN_OFFSET = '-10000px'

export const PACKAGE_VERSION = '0.1.0'