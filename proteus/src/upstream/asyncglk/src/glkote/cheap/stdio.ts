/*

Shared cheap-mode stdio
=======================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import MuteStream from 'mute-stream'
import readline from 'readline'

// We dig around in the internals of ReadLine
// TODO: see if we can remove these hacks?
export interface HackableReadline extends readline.ReadLine {
    _line_buffer: any,
    line: string,
}

export interface CheapStdio {
    rl: HackableReadline,
    stdin: NodeJS.ReadStream,
    stdout: MuteStream,
}

// A memoized instance
let instance: CheapStdio

export function get_stdio(): CheapStdio {
    if (instance) {
        return instance
    }

    const stdin = process.stdin
    // Prepare to receive input events
    if (stdin.isTTY) {
        stdin.setRawMode(true)
    }

    const stdout = new MuteStream()
    stdout.pipe(process.stdout)

    const rl = readline.createInterface({
        input: stdin,
        output: stdout,
        prompt: '',
    })
    readline.emitKeypressEvents(stdin)

    instance = {
        rl: rl as HackableReadline,
        stdin: stdin,
        stdout: stdout,
    }
    return instance
}