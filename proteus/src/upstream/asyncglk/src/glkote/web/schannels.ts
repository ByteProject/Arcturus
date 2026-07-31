/*

Web GlkOte Sound Channels
=========================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import decode_aiff from '@audio/decode-aiff'
import decode_oggv from '@audio/decode-vorbis'

import {parse_base64} from '../../common/file/browser.js'
import * as protocol from '../../common/protocol.js'
import WebGlkOte from './web.js'

interface AudioData {
    channelData: Float32Array[],
    sampleRate: number,
}

interface AudioPlayer {
    delete(): void
    do_op(op: protocol.SoundChannelOperation): void
}

// From https://github.com/compulim/web-speech-cognitive-services/issues/34
const priming_mp3 = 'SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU3LjU2LjEwMQAAAAAAAAAAAAAA//tAwAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU3LjY0AAAAAAAAAAAAAAAAJAUHAAAAAAAAAYYoRBqpAAAAAAD/+xDEAAPAAAGkAAAAIAAANIAAAARMQU1FMy45OS41VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/7EMQpg8AAAaQAAAAgAAA0gAAABFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV'

export class SoundChannelManager extends Map<number, SoundChannel> {
    private context: AudioContext
    private glkote: WebGlkOte

    constructor(glkote: WebGlkOte) {
        super()
        this.glkote = glkote
        this.context = new AudioContext()

        // Try to prime the audio system so that sounds starting after a timer will work
        this.prime()
    }

    async update(schannels: protocol.SoundChannelUpdate[]) {
        const wanted_schannels = []
        for (const schannel of schannels) {
            const {id, ops} = schannel
            wanted_schannels.push(id)

            // Add new channels
            if (!this.has(id)) {
                this.set(id, new SoundChannel(this.glkote, this.context))
            }

            // Do operations
            if (ops) {
                this.get(id)!.do_ops(ops)
            }
        }

        // Remove unwanted channels
        for (const [id, schannel] of this) {
            if (!wanted_schannels.includes(id)) {
                schannel.delete()
                this.delete(id)
            }
        }
    }

    private async prime() {
        const context = this.context

        const source = this.context.createBufferSource()
        const data = await parse_base64(priming_mp3)
        source.buffer = await context.decodeAudioData(data.buffer)

        source.connect(context.destination)
        source.start()
        setTimeout(() => {
            source.disconnect()
            source.stop()
        }, 10)
    }
}

export class SoundChannel {
    private context: AudioContext
    private gain: GainNode
    private glkote: WebGlkOte
    private paused = false
    private player: AudioPlayer | null = null
    private vol = 1

    constructor(glkote: WebGlkOte, context: AudioContext) {
        this.context = context
        this.glkote = glkote
        this.gain = context.createGain()
        this.gain.connect(context.destination)
    }

    delete() {
        this.player?.delete()
        this.gain.disconnect()
    }

    async do_ops(ops: protocol.SoundChannelOperation[]) {
        for (const op of ops) {
            switch (op.op) {
                case 'pause':
                    this.paused = true
                    break
                case 'play': {
                    if (this.player) {
                        this.player.delete()
                        this.player = null
                    }

                    // Get the data from Blorb
                    const chunk = this.glkote.Blorb!.get_chunk('Snd ', op.snd)
                    if (!chunk) {
                        break
                    }

                    // Load a sound resource specified in a JSON resource map
                    if (chunk.url) {
                        const elem = new Audio(chunk.url)
                        this.player = new AudioElementPlayer(elem, this.paused, this.send_event, this.vol)
                    }
                    else {
                        // Decode
                        // TODO: cache decoded, or try streaming
                        let buffer: AudioBuffer
                        const createBuffer = (data: AudioData) => {
                            const buffer = this.context.createBuffer(data.channelData.length, data.channelData[0].length, data.sampleRate)
                            for (const [i, channel] of data.channelData.entries()) {
                                buffer.getChannelData(i).set(channel)
                            }
                            return buffer
                        }

                        try {
                            buffer = await this.context.decodeAudioData(chunk.data!.slice().buffer)
                        }
                        catch {
                            if (chunk.chunktype === 'AIFF') {
                                const decoded = await decode_aiff(chunk.data!)
                                buffer = createBuffer(decoded)
                            }
                            else if (chunk.chunktype === 'OGGV') {
                                const decoded = await decode_oggv(chunk.data!)
                                buffer = createBuffer(decoded)
                            }
                            else {
                                break
                            }
                        }
                        this.player = new AudioBufferPlayer(buffer, this.context, this.gain, this.paused, this.send_event)
                    }
                    break
                }
                case 'unpause':
                    this.paused = false
                    break
                case 'volume':
                    this.vol = op.vol
                    if (!this.player) {
                        this.gain.gain.value = op.vol
                    }
                    break
            }

            this.player?.do_op(op)

            if (op.op === 'stop') {
                this.player = null
            }
        }
    }

    private send_event = (ev: Partial<protocol.Event>) => {
        this.glkote.send_event(ev)
    }
}

class AudioBufferPlayer implements AudioPlayer {
    private buffer: AudioBuffer
    private context: AudioContext
    private gain: GainNode
    private notify: number = 0
    private paused: boolean
    private paused_time = 0
    private repeats: number = 1
    private send_event: (ev: Partial<protocol.Event>) => void
    private source: AudioBufferSourceNode | null = null
    private snd: number = 0
    private start_time = 0
    private vol_timer = 0

    constructor(buffer: AudioBuffer, context: AudioContext, gain: GainNode, paused: boolean, send_event: (ev: Partial<protocol.Event>) => void) {
        this.buffer = buffer
        this.context = context
        this.gain = gain
        this.paused = paused
        this.send_event = send_event

        // Create a new audio node
        const source = context.createBufferSource()
        this.source = source
        source.addEventListener('ended', this.on_stop)
        source.buffer = this.buffer!
        source.connect(this.gain)
        // Do we need to do source.loop=true for seamless repeats?
    }

    delete() {
        this.stop()
    }

    do_op(op: protocol.SoundChannelOperation) {
        switch (op.op) {
            case 'pause':
                if (!this.paused) {
                    this.paused = true
                    this.paused_time = this.context.currentTime - this.start_time
                    this.stop()
                }
                break
            case 'play':
                this.notify = op.notify || 0
                this.repeats = op.repeats || 1
                this.snd = op.snd
                if (!this.paused) {
                    this.play()
                    this.repeats--
                }
                break
            case 'stop':
                this.stop()
                break
            case 'unpause':
                if (this.paused) {
                    this.play()
                }
                break
            case 'volume': {
                const currentTime = this.context.currentTime
                const gain = this.gain.gain

                // Cancel any current gain changes
                const current_value = gain.value
                gain.cancelScheduledValues(currentTime)
                gain.value = current_value
                if (this.vol_timer) {
                    clearTimeout(this.vol_timer)
                    this.vol_timer = 0
                }

                const notify = () => {
                    this.send_event({
                        type: 'volume',
                        notify: op.notify,
                    })
                }

                if (op.dur) {
                    gain.setValueAtTime(current_value || 0.0001, currentTime)
                    gain.exponentialRampToValueAtTime(op.vol || 0.0001, currentTime + (op.dur) / 1000)
                    if (op.notify) {
                        // Handle Typescript thinking this is the Node version, which doesn't return a number
                        this.vol_timer = setTimeout(notify, op.dur) as any as number
                    }
                }
                else {
                    gain.value = op.vol
                    if (op.notify) {
                        notify()
                    }
                }
                break
            }
        }
    }

    private on_stop = () => {
        this.stop()

        // Repeat
        if (this.repeats > 0) {
            this.play()
            this.repeats--
        }
        else if (this.notify) {
            this.send_event({
                type: 'sound',
                notify: this.notify,
                snd: this.snd,
            })
        }
    }

    private play() {
        // Create a new audio node
        const source = this.context.createBufferSource()
        this.source = source
        source.addEventListener('ended', this.on_stop)
        source.buffer = this.buffer!
        source.connect(this.gain)
        // Do we need to do source.loop=true for seamless repeats?

        // Handle unpausing
        this.paused = false
        this.start_time = this.context.currentTime - this.paused_time
        this.paused_time = 0
        source.start(0, this.paused_time)
    }

    private stop() {
        const source = this.source
        if (source) {
            source.removeEventListener('ended', this.on_stop)
            source.stop()
            source.disconnect()
            this.source = null
        }
    }
}

class AudioElementPlayer implements AudioPlayer {
    private elem: HTMLAudioElement
    private notify: number = 0
    private paused: boolean
    private repeats: number = 1
    private send_event: (ev: Partial<protocol.Event>) => void
    private snd: number = 0
    private vol_timer = 0

    constructor(elem: HTMLAudioElement, paused: boolean, send_event: (ev: Partial<protocol.Event>) => void, vol: number) {
        this.elem = elem
        this.paused = paused
        this.send_event = send_event

        elem.addEventListener('ended', this.on_stop)
        elem.volume = vol
    }

    delete(): void {
        this.elem.pause()
        this.elem.removeEventListener('ended', this.on_stop)
    }

    do_op(op: protocol.SoundChannelOperation): void {
        const elem = this.elem
        switch (op.op) {
            case 'pause':
                elem.pause()
                break
            case 'play':
                this.notify = op.notify || 0
                this.repeats = op.repeats || 1
                this.snd = op.snd
                if (!this.paused) {
                    elem.play()
                    this.repeats--
                }
                break
            case 'stop':
                this.delete()
                break
            case 'unpause':
                elem.play()
                break
            case 'volume': {
                // Cancel any current gain changes
                if (this.vol_timer) {
                    clearTimeout(this.vol_timer)
                    this.vol_timer = 0
                }

                // AudioElements actually throw if you try to set a volume of greater than 1
                let vol = op.vol
                if (vol > 1) {
                    vol = 1
                }

                const notify = () => {
                    this.send_event({
                        type: 'volume',
                        notify: op.notify,
                    })
                }

                if (op.dur) {
                    let steps = Math.ceil(op.dur / 10)
                    const vol_step = (vol - elem.volume) / steps
                    this.vol_timer = setInterval(() => {
                        elem.volume += vol_step
                        steps--
                        if (!steps) {
                            clearInterval(this.vol_timer)
                            this.vol_timer = 0
                            elem.volume = vol
                            if (op.notify) {
                                notify()
                            }
                        }
                    }, 10) as any as number
                }
                else {
                    elem.volume = vol
                    if (op.notify) {
                        notify()
                    }
                }

                break
            }
        }

    }

    private on_stop = () => {
        // Repeat
        if (this.repeats > 0) {
            this.elem.play()
            this.repeats--
        }
        else if (this.notify) {
            this.send_event({
                type: 'sound',
                notify: this.notify,
                snd: this.snd,
            })
        }
    }
}