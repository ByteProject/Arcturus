/*

Cheap console GlkOte implementation
===================================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import MuteStream from 'mute-stream'
import * as readline from 'readline'
import * as TTY from 'tty'

import {get_stdio, type HackableReadline} from './stdio.js'
import * as GlkOte from '../common/glkote.js'
import * as protocol from '../../common/protocol.js'

// Ansi escapes
// From https://github.com/sindresorhus/ansi-escapes/blob/main/index.js
const isTerminalApp = process.env.TERM_PROGRAM === 'Apple_Terminal'
const ESC = '\u001B['
const cursorRestorePosition = isTerminalApp ? '\u001B8' : ESC + 'u'
const cursorSavePosition = isTerminalApp ? '\u001B7' : ESC + 's'
const eraseEndLine = ESC + 'K'
const scrollDown = ESC + 'T'

const KEY_REPLACEMENTS: Record<string, string> = {
    '\x7F': 'delete',
    '\t': 'tab',
}

export default class CheapGlkOte extends GlkOte.GlkOteBase implements GlkOte.GlkOte {
    private current_input_type: 'char' | 'line' | null = null
    private handle_char_input_callback: (str: string, key: readline.Key) => void = (str: string, key: readline.Key) => this.handle_char_input(str, key)
    private handle_line_input_callback: (line: string) => void = (line: string) => this.handle_line_input(line)
    private rl: HackableReadline
    private stdin: TTY.ReadStream
    private stdout: MuteStream
    private window: protocol.WindowUpdate | null = null

    constructor() {
        super()

        const cheap_stdio = get_stdio()
        this.rl = cheap_stdio.rl
        this.stdin = cheap_stdio.stdin
        this.stdout = cheap_stdio.stdout
    }

    async init(options: GlkOte.GlkOteOptions) {
        if (!options) {
            throw new Error('no options provided')
        }

        // TODO: handle output from all buffer windows
        // Wrap glk_window_open so that only one window can be opened
        if (options.Glk) {
            const old_glk_window_open = options.Glk.glk_window_open.bind(options.Glk)
            options.Glk.glk_window_open = function(splitwin: any, method: any, size: any, wintype: any, rock: any) {
                if (splitwin) {
                    return null
                }
                return old_glk_window_open(splitwin, method, size, wintype, rock)
            }
        }

        this.rl.resume()

        if (process.stdout.isTTY) {
            this.current_metrics.height = process.stdout.rows
            this.current_metrics.width = process.stdout.columns
        }

        // Note that this must be called last as it will result in VM.start() being called
        super.init(options)
    }

    private attach_handlers() {
        if (this.current_input_type === 'char') {
            this.stdout.mute()
            this.stdin.on('keypress', this.handle_char_input_callback!)
        }
        if (this.current_input_type === 'line') {
            this.rl.on('line', this.handle_line_input_callback!)
        }
    }

    protected cancel_inputs(windows: protocol.InputUpdate[]) {
        if (windows.length === 0) {
            this.current_input_type = null
            this.detach_handlers()
        }
    }

    private detach_handlers() {
        this.stdin.removeListener('keypress', this.handle_char_input_callback!)
        this.rl.removeListener('line', this.handle_line_input_callback!)
        this.stdout.unmute()
    }

    protected disable(disable: boolean) {
        this.disabled = disable
        if (disable) {
            this.detach_handlers()
        }
        else {
            this.attach_handlers()
        }
    }

    protected exit() {
        this.detach_handlers()
        this.rl.close()
        this.stdout.write('\n')
        super.exit()
    }

    private handle_char_input(str: string, key: readline.Key) {
        if (this.current_input_type === 'char') {
            this.current_input_type = null
            this.detach_handlers()

            // Make sure this char isn't being remembered for the next line input
            this.rl._line_buffer = null
            this.rl.line = ''

            // Process special keys
            const res = KEY_REPLACEMENTS[str] || str || key.name!.replace(/f(\d+)/, 'func$1')
            this.send_event({
                type: 'char',
                window: this.window!.id,
                value: res,
            })
        }
    }

    private handle_line_input(line: string) {
        if (this.current_input_type === 'line') {
            if (this.stdout.isTTY) {
                this.stdout.write(scrollDown + cursorRestorePosition + eraseEndLine)
            }
            this.current_input_type = null
            this.detach_handlers()
            this.send_event({
                type: 'line',
                window: this.window!.id,
                value: line,
            })
        }
    }

    save_allstate(): any {
        throw new Error('save_allstate not yet implemented')
    }

    protected update_content(content: protocol.ContentUpdate[]) {
        const window_content = content.filter(content => content.id === this.window!.id)[0] as protocol.BufferWindowContentUpdate | undefined
        for (const line of window_content?.text || []) {
            if (!line.append) {
                this.stdout.write('\n')
            }
            const content = line.content
            if (content) {
                for (let i = 0; i < content.length; i++) {
                    const run = content[i]
                    if (typeof run === 'string') {
                        i++
                        this.stdout.write(content[i])
                    }
                    else if ('text' in run) {
                        this.stdout.write(run.text)
                    }
                }
            }
        }
    }

    protected update_inputs(windows: protocol.InputUpdate[]) {
        if (windows.length) {
            if (windows[0].type === 'char') {
                this.current_input_type = 'char'
            }

            if (windows[0].type === 'line') {
                if (this.stdout.isTTY) {
                    this.stdout.write(cursorSavePosition)
                }
                this.current_input_type = 'line'
            }
            this.attach_handlers()
        }
    }

    protected update_windows(windows: protocol.WindowUpdate[]) {
        for (const win of windows) {
            if (win.type === 'buffer') {
                this.window = win
            }
        }
    }
}