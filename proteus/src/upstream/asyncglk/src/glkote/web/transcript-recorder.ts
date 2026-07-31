/*

GlkOte transcript recording handler
===================================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import * as protocol from '../../common/protocol.js'
import type {GlkOteOptions, TranscriptRecordingData} from '../common/glkote.js'

import Windows from './windows.js'

export default class TranscriptRecorder {
    enabled = false
    handler: (state: TranscriptRecordingData) => void = state => this.web_handler(state)
    event?: Partial<protocol.Event>
    label = ''
    session = Date.now() + Math.ceil(Math.random() * 10000).toString(16)
    timestamp?: number
    url = ''
    private windows: Windows

    constructor(options: GlkOteOptions, windows: Windows) {
        this.windows = windows
        if (options.recording_handler) {
            this.enabled = true
            this.handler = options.recording_handler
            this.url = '(custom handler)'
        }
        if (options.recording_url) {
            this.enabled = true
            this.url = options.recording_url
        }
        this.label = options.recording_label ?? ''
        if (this.enabled) {
            console.log(`Transcript recording active: session ${this.session} "${this.label}", destination ${this.url}`)
        }
    }

    // Store the event for later
    record_event(ev: Partial<protocol.Event>) {
        this.event = ev
        this.timestamp = Date.now()
    }

    // Record an event-output pair
    record_update(state: protocol.StateUpdate) {
        if (!state.content) {
            return
        }

        // Check the event type
        const event = this.event!
        const eventtype = event.type
        let input = ''
        if (eventtype === 'char' || eventtype === 'line') {
            input = (event as protocol.CharEvent | protocol.LineEvent).value
        }
        else if (!(!eventtype || eventtype === 'external' || eventtype === 'init' || eventtype === 'specialresponse')) {
            return
        }

        // Collect the buffer window outputs
        let output = ''
        for (const update of state.content) {
            const win = this.windows.get(update.id)
            if (!win || win.type !== 'buffer') {
                continue
            }
            const textdata = (update as protocol.BufferWindowContentUpdate).text || []
            for (const data of textdata) {
                if (!data.append) {
                    output += '\n'
                }
                const content = data.content
                if (!content?.length) {
                    continue
                }
                for (let run_index = 0; run_index < content.length; run_index++) {
                    const instruction = content[run_index]
                    if (typeof instruction === 'string') {
                        output += content[++run_index]
                    }
                    else if ('text' in instruction) {
                        output += instruction.text
                    }
                }
            }
        }

        this.handler({
            format: 'simple',
            input,
            label: this.label,
            output,
            outtimestamp: Date.now(),
            sessionId: this.session,
            timestamp: this.timestamp!,
        })
    }

    async web_handler(state: TranscriptRecordingData) {
        try {
            const response = await fetch(this.url, {
                body: JSON.stringify(state),
                headers: {
                    'Content-Type': 'application/json',
                },
                method: 'POST',
            })

            if (!response.ok) {
                throw new Error(`Could not submit transcript update, got ${response.status}`)
            }
        }
        catch (err: any) {
            this.enabled = false
            console.log(`Transcript recording failed; disabling. Error: ${err as Error}`)
        }
    }
}