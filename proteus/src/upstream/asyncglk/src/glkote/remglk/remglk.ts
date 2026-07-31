/*

RemGlk mode GlkOte implementation
===================================

Copyright (c) 2023 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import * as TTY from 'tty'

import * as Constants from '../../common/constants.js'
import * as GlkOte from '../common/glkote.js'
import * as protocol from '../../common/protocol.js'

export default class RemGlk extends GlkOte.GlkOteBase implements GlkOte.GlkOte {
    private stdin: TTY.ReadStream
    private stdout: TTY.WriteStream

    constructor() {
        super()

        this.stdin = process.stdin
        this.stdout = process.stdout

        // Pause stdin because with `init` being an async function the data event handler won't be attached in time to catch the init event
        this.stdin.pause()
        if (this.stdin.isTTY) {
            this.stdin.setRawMode(true)
        }
    }

    async init(options: GlkOte.GlkOteOptions) {
        if (!options) {
            throw new Error('no options provided')
        }
        if (!options.accept) {
            throw new Error('an accept function was not given to GlkOte')
        }

        this.options = options
        this.accept_func = options.accept

        let buffer = ''

        this.stdin.on('data', chunk => {
            buffer += chunk.toString().trim()
            if (buffer.endsWith('}')) {
                let event: protocol.Event | undefined
                try {
                    event = JSON.parse(buffer)
                }
                catch {}
                if (event) {
                    buffer = ''
                    if (event.type === 'init') {
                        // Fill out the metrics
                        event.metrics = Object.assign({}, Constants.DEFAULT_METRICS, event.metrics)
                    }
                    if (event.type === 'specialresponse' && typeof event.value === 'string') {
                        event.value = {filename: event.value}
                    }
                    this.accept_func(event)
                }
            }
        })
        this.stdin.resume()

        this.is_inited = true
    }

    log(_msg: string) {}

    update(data: protocol.Update) {
        this.stdout.write(`${JSON.stringify(data)}\n\n`)
        if (data.type === 'update' && data.disable) {
            process.exit()
        }
    }

    cancel_inputs(windows: protocol.InputUpdate[]) {
        throw new Error('cancel_inputs method should not be called in RemGlk mode')
    }

    disable(disable: boolean) {
        throw new Error('disable method should not be called in RemGlk mode')
    }

    handle_specialinput(data: protocol.SpecialInput) {
        throw new Error('handle_specialinput method should not be called in RemGlk mode')
    }

    save_allstate() {
        throw new Error('save_allstate method should not be called in RemGlk mode')
    }

    update_content(content: protocol.ContentUpdate[]) {
        throw new Error('update_content method should not be called in RemGlk mode')
    }

    update_inputs(windows: protocol.InputUpdate[]) {
        throw new Error('update_inputs method should not be called in RemGlk mode')
    }

    update_windows(windows: protocol.WindowUpdate[]) {
        throw new Error('update_windows method should not be called in RemGlk mode')
    }
}