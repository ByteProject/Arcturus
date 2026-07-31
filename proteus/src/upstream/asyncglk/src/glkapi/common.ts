/*

Common GlkApi things
====================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import type {GlkTypedArray} from '../common/misc.js'

export function copy_array(source: GlkTypedArray, target: number[], length: number) {
    const copy_length = Math.min(length, target.length)
    for (let i = 0; i < copy_length; i++) {
        target[i] = source[i]
    }
}

export interface TimerData {
    interval: number
    last_interval: number
    started: number
}