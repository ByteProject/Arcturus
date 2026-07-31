/*

Web GlkOte implementation
=========================

Copyright (c) 2023 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import * as GlkOte from '../common/glkote.js'
import * as protocol from '../../common/protocol.js'

import Metrics from './metrics.js'
import {SoundChannelManager} from './schannels.js'
import {DOM, is_iOS} from './shared.js'
import TranscriptRecorder from './transcript-recorder.js'
import Windows, {GraphicsWindow} from './windows.js'

interface AutosaveState {
    graphics_bg?: Array<[number, string]>,
    history?: Array<string>,
    transcript_recorder_session?: string,
}

/** A GlkOte implementation for the web
 * 
 * WebGlkOte requires the following HTML divs to be present (though the id names can be varied through the options):
 * 
 * ```
 *     <div id="gameport">
 *         <div id="windowport"></div>
 *         <div id="loadingpane">Loading...</div>
 *         <div id="errorpane" style="display:none;"><div id="errorcontent"></div></div>
 *     </div>
 * ```
 */
export default class WebGlkOte extends GlkOte.GlkOteBase implements GlkOte.GlkOte {
    dom: DOM = new DOM({
        context_element: undefined,
        errorcontent_id: 'errorcontent',
        errorpane_id: 'errorpane',
        gameport_id: 'gameport',
        loadingpane_id: 'loadingpane',
        prefix: '',
        windowport_id: 'windowport',
    })
    metrics_calculator: Metrics
    private schannels?: SoundChannelManager
    private showing_error = false
    private showing_loading = true
    private transcript_recorder?: TranscriptRecorder
    private windows: Windows

    constructor() {
        super()

        this.metrics_calculator = new Metrics(this)
        this.windows = new Windows(this)
    }

    async init(options: GlkOte.GlkOteOptions) {
        try {
            if (!options) {
                throw new Error('no options provided')
            }

            if (typeof jQuery === 'undefined') {
                throw new Error('jQuery is not loaded')
            }

            // Set DOM IDs
            if (options.dom_prefix) {
                this.dom.prefix = options.dom_prefix
            }
            if (options.errorcontent) {
                this.dom.errorcontent_id = options.errorcontent
            }
            if (options.errorpane) {
                this.dom.errorpane_id = options.errorpane
            }
            if (options.gameport) {
                this.dom.gameport_id = options.gameport
            }
            if (options.loadingpane) {
                this.dom.loadingpane_id = options.loadingpane
            }
            if (options.windowport) {
                this.dom.windowport_id = options.windowport
            }

            if (options.Blorb) {
                this.windows.blorb = options.Blorb
            }

            // The windowport is required to already exist
            const windowport = this.dom.windowport()
            if (!windowport.length) {
                throw new Error(`Cannot find windowport element #${this.dom.windowport_id}`)
            }
            windowport.empty()

            // Augment the viewport meta tag
            // Rather than requiring all users to update their HTML we will add new properties here
            // The properties we want are initial-scale, minimum-scale, width, and the new interactive-widget
            // See https://developer.chrome.com/blog/viewport-resize-behavior
            let viewport_meta_tag_content = 'initial-scale=1,interactive-widget=resizes-content,minimum-scale=1,width=device-width'

            // Prevent iOS from zooming in when focusing input, but allow Android to still pinch zoom
            // As they handle the maximum-scale viewport meta option differently, we will conditionally add it only in iOS
            // Idea from https://stackoverflow.com/a/62750441/2854284
            if (is_iOS) {
                viewport_meta_tag_content += ',maximum-scale=1'
            }

            (document.head.querySelector('meta[name="viewport"]')! as HTMLMetaElement).content = viewport_meta_tag_content

            await this.metrics_calculator.measure()

            // Set up transcript recording
            if (options.recording_url || options.recording_handler) {
                if (options.recording_format && options.recording_format !== 'simple') {
                    console.warn('GlkOte: only the "simple" recording_format is supported')
                }
                else {
                    // Check if the user has opted out
                    const query_feedback = (new URLSearchParams(document.location.search)).get('feedback')
                    const cookie_name = options.recording_cookie || 'transcript_recording_opt_out'
                    if ((query_feedback && query_feedback !== '1') || document.cookie.includes(`${cookie_name}=1`)) {
                        console.log('User has opted out of transcript recording.')
                    }
                    else {
                        this.transcript_recorder = new TranscriptRecorder(options, this.windows)
                    }
                }
            }

            // Set up sound channels now to try to avoid the autoplaying-without-user input problem
            if (typeof AudioContext !== 'undefined') {
                this.schannels = new SoundChannelManager(this)
            }

            // Note that this must be called last as it will result in VM.start() being called
            return super.init(options)
        }
        catch (err) {
            this.error(err as Error)
        }
    }

    protected autorestore(data: AutosaveState) {
        // erkyrath/glkote history is an object rather than an array
        if (Array.isArray(data.history)) {
            this.windows.history = data.history
        }

        for (const win of this.windows.values()) {
            // Scroll all buffer windows
            if (win.type === 'buffer') {
                win.scroll_to_bottom()
            }
        }

        if (data.graphics_bg) {
            for (const [winid, colour] of data.graphics_bg) {
                (this.windows.get(winid) as GraphicsWindow).fillcolour = colour
            }
        }

        if (data.transcript_recorder_session && this.transcript_recorder) {
            this.transcript_recorder.session = data.transcript_recorder_session
            console.log(`Resuming autosaved transcript recording session: ${data.transcript_recorder_session}`)
        }

        // Always send a rearrange event after autorestoring
        setTimeout(() => this.send_event({type: 'arrange'}), 0)
    }

    protected cancel_inputs(windows: protocol.InputUpdate[]) {
        this.windows.cancel_inputs(windows)
    }

    protected capabilities(): string[] {
        const capabilities = [
            'garglktext',
            'graphics',
            'graphicsext',
            'graphicswin',
            'hyperlinks',
            'timer',
        ]
        if (typeof AudioContext !== 'undefined') {
            capabilities.push('sounds')
        }
        return capabilities
    }

    protected disable(disable: boolean) {
        for (const win of this.windows.values()) {
            win.textinput.el.prop('disabled', disable || !win.inputs?.type)
        }
        this.disabled = disable
    }

    private embellish_error() {
        if (typeof $ === 'undefined') {
            return
        }

        const errorpane = $(`#${this.dom.errorpane_id}`)

        // Add close button
        if (!errorpane.find('#errorclose').length) {
            $('<button>', {
                'aria-label': 'Close',
                click: () => {
                    errorpane.hide()
                    return false
                },
                id: 'errorclose',
                text: '✖',
                type: 'button',
            })
                .appendTo(errorpane)
        }

        // If autorestoring, add a link to restart after clearing the autosave
        // TODO: fix for AsyncDialog
        if (this.autorestoring && !this.Dialog?.async && this.Dialog?.autosave_clear) {
            const link = $('<a>', {
                click: async () => {
                    if (!this.Dialog!.async) {
                        await this.Dialog!.autosave_clear!()
                    }
                    location.reload()
                },
                text: 'Clear autosave and restart',
            })
            $('<div>')
                .append(link)
                .appendTo(errorpane)
        }
    }

    error(error: Error | string) {
        error ??= '???'
        let msg: string
        if (typeof error === 'string') {
            msg = error
            error = new Error(error)
        }
        else {
            msg = error.toString()
        }

        // Don't use jQuery, because this is called if jQuery isn't present
        const errorcontent = document.getElementById(this.dom.errorcontent_id)
        if (!errorcontent) {
            throw new Error(msg)
        }
        errorcontent.innerHTML = msg

        const errorpane = document.getElementById(this.dom.errorpane_id)!
        if (errorpane.className === 'WarningPane') {
            errorpane.className = ''
        }

        this.embellish_error()

        errorpane.style.display = ''
        this.showing_error = true
        this.hide_loading()
        console.error(error)
    }

    protected exit() {
        // Try to clean up and remove any event handlers
        this.metrics_calculator.destroy()
        this.windows.destroy()
    }

    getdomcontext(): HTMLElement | undefined {
        return this.dom.context_element
    }

    getdomid(name: string): string {
        switch (name) {
            case 'errorcontent': return this.dom.errorcontent_id
            case 'errorpane': return this.dom.errorpane_id
            case 'gameport': return this.dom.gameport_id
            case 'loadingpane': return this.dom.loadingpane_id
            case 'windowport': return this.dom.windowport_id
            default: return name
        }
    }

    private hide_loading() {
        if (!this.showing_loading) {
            return
        }
        this.showing_loading = false

        // Don't use jQuery because this could be called from error()
        const loadingpane = document.getElementById(this.dom.loadingpane_id)
        if (loadingpane) {
            loadingpane.style.display = 'none'
        }
    }

    save_allstate(): AutosaveState {
        const graphics_bg: Array<[number, string]> = []
        for (const win of this.windows.values()) {
            if (win.type === 'graphics') {
                graphics_bg.push([win.id, win.fillcolour])
            }
        }

        return {
            graphics_bg,
            history: this.windows.history,
            transcript_recorder_session: this.transcript_recorder?.session,
        }
    }

    // Send partial line input values
    send_event(ev: Partial<protocol.Event>) {
        if (ev.type !== 'init' && ev.type !== 'refresh' && ev.type !== 'specialresponse') {
            for (const win of this.windows.values()) {
                if (win.inputs?.type) {
                    const val = win.textinput.el.val() as string
                    if (val) {
                        if (!ev.partial) {
                            ev.partial = {}
                        }
                        ev.partial[win.id] = val
                    }
                }
            }
        }
        if (this.transcript_recorder?.enabled) {
            this.transcript_recorder.record_event(ev)
        }
        super.send_event(ev)
    }

    setdomcontext(val: HTMLElement) {
        this.dom.context_element = val
    }

    protected set_page_bg(colour: string | null) {
        $('body').css('background-color', colour || '')
    }

    update(data: protocol.Update) {
        if (this.showing_loading) {
            this.hide_loading()
        }
        super.update(data)
        if (this.transcript_recorder?.enabled && data.type === 'update' && !data.autorestore) {
            this.transcript_recorder.record_update(data)
        }
    }

    protected update_content(content: protocol.ContentUpdate[]) {
        this.windows.update_content(content)
    }

    protected update_inputs(windows: protocol.InputUpdate[]) {
        this.windows.update_inputs(windows)
    }

    protected update_schannels(schannels: protocol.SoundChannelUpdate[]) {
        this.schannels?.update(schannels)
    }

    protected update_windows(windows: protocol.WindowUpdate[]) {
        this.windows.update(windows)
    }

    warning(msg: any) {
        // Don't show warnings if an error is already being shown
        if (this.showing_error) {
            return
        }

        const errorpane = $(`#${this.dom.errorpane_id}`)

        // Hide a warning
        if (!msg) {
            errorpane.hide()
            return
        }

        const errorcontent = document.getElementById(this.dom.errorcontent_id)
        if (!errorcontent) {
            console.warn(msg)
            return
        }
        errorcontent.innerHTML = msg

        this.embellish_error()

        errorpane.addClass('WarningPane')
        errorpane.show()
        this.hide_loading()
    }
}