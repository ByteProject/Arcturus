/*

GlkOte windows
==============

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {disableBodyScroll, enableBodyScroll} from 'body-scroll-lock'
import {debounce} from 'lodash-es'

import {Blorb} from '../../blorb/blorb.js'
import {NBSP} from '../../common/constants.js'
import {is_pinch_zoomed} from '../../common/misc.js'
import * as protocol from '../../common/protocol.js'

import {TextInput} from './input.js'
import {create, DOM, type EventFunc, is_iOS} from './shared.js'
import WebGlkOte from './web.js'

export type Window = BufferWindow | GraphicsWindow | GridWindow
type WindowCodes = 'buffer' | 'graphics' | 'grid'

function no_text_selected(): boolean {
    return (window.getSelection() + '') === ''
}

interface WindowConstructorOptions {
    blorb?: Blorb
    dom: DOM,
    id: number,
    manager: Windows,
    metrics: protocol.NormalisedMetrics,
    rock: number,
    styles?: protocol.WindowStyles,
    type: WindowCodes,
}

abstract class WindowBase {
    blorb?: Blorb
    desired = true
    dom: DOM
    frameel: JQuery<HTMLElement>
    id: number
    inputs?: protocol.InputUpdate
    manager: Windows
    metrics: protocol.NormalisedMetrics
    textinput: TextInput
    type: WindowCodes

    constructor(options: WindowConstructorOptions) {
        this.blorb = options.blorb
        this.dom = options.dom
        this.id = options.id
        this.manager = options.manager
        this.metrics = options.metrics
        this.type = options.type

        this.frameel = this.dom.create('div', `window${options.id}`, {
            class: `WindowFrame ${window_types[this.type]} WindowRock_${options.rock}`,
            click: (ev: JQuery.ClickEvent) => this.onclick(ev),
        })
            .appendTo(this.dom.windowport())

        // (this as any as Window) is a silly hack to work around Typescript's abstract class rules
        this.textinput = new TextInput(this as any as Window)
    }

    destroy(remove_frame: boolean) {
        this.textinput.destroy()
        if (remove_frame) {
            this.frameel.remove()
        }
        else {
            this.inputs = undefined
        }
    }

    // Dummy function which is only needed for buffer windows
    measure_height() {}

    protected onclick(ev: JQuery.ClickEvent) {
        if (this.inputs?.type && no_text_selected()) {
            this.textinput.el.trigger('focus')
            return false
        }
    }

    send_text_event(ev: Partial<protocol.CharEvent | protocol.LineEvent>) {
        // Measure the height of the window, which should account for a virtual keyboard
        this.measure_height()
        this.textinput.reset()
        // Clear the input type so we won't accidentally send it again
        this.inputs!.type = undefined
        // We're the last active window
        this.manager.active_window = this as any as Window
        // Set the event's window prop and send it
        ev.window = this.id
        this.manager.send_event(ev)
    }
}

// Apply text run styles, accounting for reverse mode
export function apply_text_run_styles(orig_styles: protocol.CSSProperties, reverse: boolean, el: JQuery<HTMLElement>) {
    // Make a copy of the styles, I'm not sure this is strictly necessary but better to be safe
    const styles = Object.assign({}, orig_styles)
    // Swap colours if reverse mode
    if (reverse) {
        const bg = styles['background-color']
        const fg = styles.color
        if (bg) {
            styles.color = bg
        }
        else {
            delete styles.color
        }
        if (fg) {
            styles['background-color'] = fg
        }
        else {
            delete styles['background-color']
        }
        delete styles.reverse
    }
    el.css(styles)
}

// Split a string into words, with whitespace included after the words it follows
function split_after_spaces(text: string): string[] {
    const res: string[] = ['']
    const whitespace = /\s/
    let prev_whitespace = false
    for (const c of text) {
        const is_whitespace = whitespace.test(c)
        if (!is_whitespace && prev_whitespace) {
            res.unshift('')
        }
        res[0] += c
        prev_whitespace = is_whitespace
    }
    res.reverse()
    return res
}

abstract class TextualWindow extends WindowBase {
    bg: string | null = null
    fg: string | null = null
    last_run_styles?: protocol.CSSProperties
    styles?: protocol.WindowStyles

    constructor(options: WindowConstructorOptions) {
        super(options)

        // We need the `this` object provided by jQuery, so we can't use an arrow function handler like we normally do
        const onlink = (target: HTMLElement) => this.onlink(target)
        this.frameel.on('click', 'a', function() {onlink(this)})

        // Add stylehints
        if (options.styles) {
            this.styles = options.styles
            this.add_stylehints()
        }
    }

    /** Format CSS rules and add to the window */
    add_stylehints() {
        const windowid = `#window${this.id}`
        const styles: protocol.WindowStyles = {}
        if (this.styles) {
            // Copy all the styles
            for (const [selector, original_styles] of Object.entries(this.styles)) {
                const full_selector = `${windowid} ${selector}`.trim()
                const css_styles = styles[full_selector] = Object.assign({}, original_styles)

                // Create a .reverse rule for when text runs are reverse mode
                if (selector) {
                    const bg = css_styles['background-color']
                    const fg = css_styles.color
                    if (bg || fg) {
                        const reverse_styles: protocol.CSSProperties = styles[`${full_selector}.reverse`] = {}
                        if (bg) {
                            reverse_styles.color = bg
                        }
                        if (fg) {
                            reverse_styles['background-color'] = fg
                        }
                    }

                    // Monospace mode - handled in create_text_run
                    delete css_styles.monospace

                    // In reverse mode don't set colour styles
                    if (css_styles.reverse) {
                        delete css_styles['background-color']
                        delete css_styles.color
                    }
                    delete css_styles.reverse

                    // Check if we have any properties left
                    if (Object.keys(css_styles).length === 0) {
                        delete styles[full_selector]
                    }
                }
            }

            // Copy styles for the <input>
            // May not play nice with reverse
            if (styles[`${windowid} .Style_input`]) {
                styles[`${windowid} .LineInput`] = styles[`${windowid} .Style_input`]
            }
        }

        // Set window background colour, for normal and reverse mode
        const normal_styles = styles[`${windowid} .Style_normal`]
        const bg = this.bg || normal_styles?.['background-color']
        const fg = this.fg || normal_styles?.color
        if (bg || fg) {
            if (!styles[windowid]) {
                styles[windowid] = {}
            }
            styles[windowid]['background-color'] = bg || `var(--glkote-${this.type}-bg)`
            styles[`${windowid}.reverse`] = {
                'background-color': fg || `var(--glkote-${this.type}-reverse-bg)`,
            }
        }

        // Finally output the styles
        if (Object.keys(styles).length) {
            this.frameel.children('style').remove()
            this.frameel.prepend(`<style>${Object.entries(styles).map(rule => {
                const [selector, properties] = rule
                return `${selector} {${Object.entries(properties).map(property => {
                    const [name, value] = property
                    return `${name}: ${value}`
                }).join('; ')}}`
            }).join('\n')}</style>`)
        }
    }

    create_text_run(run: protocol.TextRun, split_words?: boolean): JQuery<HTMLElement> {
        const run_style = run.style
        // Is this run or this style monospace mode?
        const monospace_val = run.css_styles?.monospace ?? this.styles?.[`.Style_${run_style}`]?.monospace
        let monospace_class = ''
        // Only add the class if we're changing the default font-family for this style
        if (typeof monospace_val !== 'undefined') {
            if (run_style === 'preformatted') {
                if (!monospace_val) {
                    monospace_class = ' proportional'
                }
            }
            else if (monospace_val) {
                monospace_class = ' monospace'
            }
        }
        // Is this run or this style reverse mode?
        const reverse = run.css_styles?.reverse ?? this.styles?.[`.Style_${run_style}`]?.reverse
        // Proteus: a run-level background (the Z-machine's set_colour
        // reaching us as garglk css_styles) becomes the window's own
        // background, the way Gargoyle repaints its margins; a buffer
        // window's colour also becomes the page background, so the text
        // never sits in glyph-shaped boxes on a mismatched page. In
        // reverse mode the painted background is the run's foreground
        // (the statusline manner), so take whichever will actually show.
        const runbg = reverse ? run.css_styles?.color : run.css_styles?.['background-color']
        if (runbg && runbg !== this.bg) {
            this.bg = runbg
            this.frameel.css('background-color', runbg)
            if (this.type === 'buffer') {
                document.documentElement.style.setProperty('--glkote-page-bg', runbg)
            }
        }
        // Create a template span and apply classes and styles
        const el = create('span', `Style_${run_style}${reverse ? ' reverse' : ''}${monospace_class}`)
        if (run.css_styles) {
            apply_text_run_styles(run.css_styles, !!reverse, el)
        }
        // Split words if instructed to, or if this text run is monospaced
        if (typeof split_words === 'undefined') {
            split_words = !!monospace_val || run_style === 'preformatted'
        }
        const els = split_words
            ? $(split_after_spaces(run.text).map(text => el.clone().text(text)[0]))
            : el.text(run.text)
        // Wrap in a link
        if (run.hyperlink) {
            return $('<a>', {
                data: {
                    glklink: run.hyperlink,
                },
                href: '#',
            })
                .append(els)
        }
        return els
    }

    onlink(target: HTMLElement) {
        const linkval = $(target).data('glklink')
        if (linkval) {
            if (this.inputs?.hyperlink) {
                this.manager.send_event({
                    type: 'hyperlink',
                    value: linkval,
                    window: this.id,
                })
            }
            return false
        }
    }

    /** Refresh styles after a cleared window */
    refresh_styles(bg?: string | null, fg?: string | null) {
        let styles_need_refreshing
        if (typeof bg !== 'undefined' && bg !== this.bg) {
            this.bg = bg
            styles_need_refreshing = 1
        }
        if (typeof fg !== 'undefined' && fg !== this.fg) {
            this.fg = fg
            styles_need_refreshing = 1
        }
        if (styles_need_refreshing) {
            this.add_stylehints()
        }
    }
}

const inline_alignment_classes: Record<string, string> = {
    inlinecenter: 'ImageInlineCenter',
    inlinedown: 'ImageInlineDown',
    inlineup: 'ImageInlineUp',
    marginleft: 'ImageMarginLeft',
    marginright: 'ImageMarginRight',
}

export class BufferWindow extends TextualWindow {
    type = 'buffer' as const
    /** How much height is available with the keyboard active */
    height_above_keyboard: number
    innerel: JQuery<HTMLElement>
    private is_scrolled_down = true
    lastline?: JQuery<HTMLElement>
    updatescrolltop = 0

    constructor(options: WindowConstructorOptions) {
        super(options)
        this.frameel.attr({
            'aria-live': 'polite',
            role: 'log',
            tabindex: -1,
        })
            .on('scroll', this.onscroll)

        if (is_iOS) {
            disableBodyScroll(this.frameel[0])
        }

        this.innerel = create('div', 'BufferWindowInner')
            .append(this.textinput.el)
            .appendTo(this.frameel)
        this.height_above_keyboard = this.frameel.height()!
    }

    destroy(remove_frame: boolean) {
        if (is_iOS) {
            enableBodyScroll(this.frameel[0])
        }

        super.destroy(remove_frame)
    }

    /** Measure the height of the window that is currently visible (excluding virtual keyboards for example) */
    measure_height() {
        this.height_above_keyboard = this.frameel.height()!
    }

    protected onclick(_: JQuery.ClickEvent) {
        if (this.inputs?.type && no_text_selected()) {
            // Check that we've scrolled to the bottom (if there is actually text in this window)
            if (this.lastline && this.height_above_keyboard) {
                const rect = this.lastline[0].getBoundingClientRect()
                if (rect.bottom < 0 || rect.top > document.documentElement.clientHeight) {
                    return false
                }
            }
            this.textinput.el.trigger('focus')
            return false
        }
    }

    // When the frame element is scrolled, update whether it's scrolled to the bottom
    private onscroll = () => {
        const frameel = this.frameel[0]
        this.is_scrolled_down = frameel.scrollHeight - frameel.scrollTop - frameel.clientHeight < 1
    }

    // Scroll to the bottom, unless `after_metrics_change` is set, in which case only scroll if we *should* be at the bottom (used after updating metrics)
    scroll_to_bottom(after_metrics_change?: boolean) {
        if (!after_metrics_change || this.is_scrolled_down) {
            this.frameel.scrollTop(this.innerel.height()!)
            this.is_scrolled_down = true
        }
    }

    update(data: protocol.BufferWindowContentUpdate) {
        if (data.clear) {
            // Reset the text input before removing the window's buffer lines so that it won't be detached from the document (which would then remove its event handlers)
            this.textinput.reset()
            this.innerel.children('.BufferLine').remove()
            this.is_scrolled_down = true
            this.lastline = undefined
            this.last_run_styles = undefined
            this.refresh_styles(data.bg, data.fg)
        }

        // If the text field is missing, just do nothing
        if (!data.text) {
            return
        }

        // Tell ARIA that we're busy while we're updating the window
        this.frameel.attr('aria-busy', 'true')

        // Get the scrolltop for this update
        this.updatescrolltop = Math.max(0, (this.lastline?.position().top || 0) - 20)

        let line_index = 0
        while (line_index < data.text.length) {
            const line = data.text[line_index++]
            const content = line.content
            let divel: JQuery<HTMLElement> | undefined
            let line_has_style
            if (line.append && this.lastline) {
                divel = this.lastline
                line_has_style = 1
                // If appending to a blank line, fix it up first
                if (divel.hasClass('BlankPara')) {
                    divel.removeClass('BlankPara')
                    divel.children('.BlankLineSpace').remove()
                }
            }
            else {
                divel = create('div', 'BufferLine')
                this.innerel.append(divel)
                this.lastline = divel
                if (!content?.length) {
                    divel.addClass('BlankPara')
                    divel.append(create('span', 'BlankLineSpace').text(NBSP))
                    continue
                }
            }
            if (line.flowbreak) {
                divel.addClass('FlowBreak')
            }

            if (!content?.length) {
                continue
            }
            for (let run_index = 0; run_index < content.length; run_index++) {
                let run: protocol.TextRun
                const instruction = content[run_index]
                if (typeof instruction === 'string') {
                    run = {
                        style: content[run_index++] as string,
                        text: content[run_index] as string,
                    }
                }
                else if ('special' in instruction && instruction.special === 'image') {
                    const image_elem_props: JQuery.PlainObject = {
                        alt: instruction.alttext || `Image ${instruction.image}`,
                        class: inline_alignment_classes[instruction.alignment || 'inlineup'],
                        src: this.blorb && this.blorb.get_image_url(instruction.image!) || instruction.url!,
                        css: {},
                    }
                    // Process the new imagerule constraints
                    if (instruction.widthratio) {
                        image_elem_props.css.width = '' + instruction.widthratio * 100 + '%'
                    }
                    else {
                        if (instruction.winmaxwidth === undefined) {
                            instruction.winmaxwidth = 1
                        }
                        if (instruction.winmaxwidth) {
                            image_elem_props.css['max-width'] = '' + instruction.winmaxwidth * 100 + '%'
                        }
                        image_elem_props.width = instruction.width!
                    }
                    if (instruction.aspectwidth) {
                        image_elem_props.css['aspect-ratio'] = '' + instruction.aspectwidth + '/' + instruction.aspectheight!
                    }
                    else {
                        if (instruction.winmaxwidth && !instruction.widthratio) {
                            image_elem_props.css['aspect-ratio'] = '' + instruction.width + '/' + instruction.height!
                        }
                        else {
                            image_elem_props.height = instruction.height!
                        }
                    }
                    const el = $('<img>', image_elem_props)
                    if (instruction.hyperlink) {
                        $('<a>', {
                            data: {
                                glklink: instruction.hyperlink,
                            },
                            href: '#',
                        })
                            .append(el)
                            .appendTo(divel)
                        continue
                    }
                    divel.append(el)
                    continue
                }
                else {
                    run = instruction as protocol.TextRun
                }
                if (!line_has_style) {
                    line_has_style = 1
                    divel.addClass(`Style_${run.style}_par`)
                }
                divel.append(this.create_text_run(run, line_index === data.text.length ? true : undefined))
                // Store the last text run for setting styles in the input
                this.last_run_styles = run.css_styles
            }
        }

        // Scroll down
        if (!is_pinch_zoomed()) {
            this.frameel.scrollTop(this.updatescrolltop)
        }

        // TODO: Trim log?

        this.frameel.attr('aria-busy', 'false')
    }
}

export class GraphicsWindow extends WindowBase {
    type = 'graphics' as const
    buffer: JQuery<HTMLCanvasElement>
    canvas: JQuery<HTMLCanvasElement>
    fillcolour = ''
    framequeue: protocol.GraphicsWindowOperation[][] = []
    /** Height in CSS pixels */
    height = 0
    image_cache: Map<number | string, HTMLImageElement> = new Map()
    /** Width in CSS pixels */
    width = 0

    constructor(options: WindowConstructorOptions) {
        super(options)
        // Create the canvas
        this.canvas = this.dom.create('canvas', `win${options.id}_canvas`, {
            data: {
                window: this,
            },
        }) as JQuery<HTMLCanvasElement>
        this.frameel.append(this.canvas)
        this.manager.canvasResizeObserver?.observe(this.canvas[0])

        // And a buffer canvas to reduce flicker
        this.buffer = this.dom.create('canvas', `win${options.id}_buffer`) as JQuery<HTMLCanvasElement>
    }

    // Clear the image cache 5 seconds after the last frame, so that the cache can be useful for animations, but we don't waste memory for images which are only updated each turn
    clear_cache = debounce(() => {
        this.image_cache.clear()
    }, 5000)

    // Decode and cache an image
    decode_image(key: number | string, url: string): Promise<void> {
        const image = new Image()
        image.src = url
        return image.decode()
            .then(() => {
                this.image_cache.set(key, image)
            })
            .catch(() => {})
    }

    destroy(remove_frame: boolean) {
        this.manager.canvasResizeObserver?.unobserve(this.canvas[0])
        super.destroy(remove_frame)
    }

    onclick(ev: JQuery.ClickEvent) {
        if (this.inputs?.mouse && ev.button === 0) {
            this.inputs.mouse = false
            this.manager.send_event({
                type: 'mouse',
                window: this.id,
                x: Math.floor(ev.offsetX - this.metrics.graphicsmarginx / 2),
                y: Math.floor(ev.offsetY - this.metrics.graphicsmarginy / 2),
            })
            return false
        }
        return super.onclick(ev)
    }

    set_dimensions(height: number, width: number) {
        // First set the things which use CSS pixels
        this.canvas.css({height, width})
        this.height = height
        this.width = width
        // Then the canvas dimensions using devicePixelRatio
        const dPR = devicePixelRatio
        height = height * dPR
        width = width * dPR
        this.buffer.attr({height, width})
        this.canvas.attr({height, width})
        // The resize observer will handle setting true pixel sizes if supported
    }

    // This function is async because images must be loaded asynchrounously, and each operation painted in sequence, but the rest of GlkOte doesn't need to await it
    async update() {
        const buffercontext = this.buffer[0].getContext('2d')!

        // If we're slow loading images then more than one frame may have arrived, so go through the queue now
        for (let i = 0; i < this.framequeue.length; i++) {
            const frame = this.framequeue[i]

            // Stop if the window is collapsed
            if (!this.height || !this.width) {
                break
            }
            // There shouldn't be any empty frames, but check just in case
            if (!frame.length) {
                continue
            }

            // Preload images
            const loading_images = []
            for (const op of frame) {
                if (op.special === 'image') {
                    const key = op.url || op.image!
                    if (this.image_cache.has(key)) {
                        continue
                    }
                    const url = op.url || this.blorb && this.blorb.get_image_url(op.image!)
                    if (url) {
                        loading_images.push(this.decode_image(key, url))
                    }
                }
            }
            await Promise.all(loading_images)

            const dPR = devicePixelRatio
            for (const op of frame) {
                switch (op.special) {
                    case 'fill':
                        buffercontext.fillStyle = op.color || this.fillcolour
                        if (Number.isFinite(op.x)) {
                            buffercontext.fillRect(op.x! * dPR, op.y! * dPR, op.width! * dPR, op.height! * dPR)
                        }
                        else {
                            buffercontext.fillRect(0, 0, parseInt(this.buffer.attr('width')!), parseInt(this.buffer.attr('height')!))
                        }
                        break
                    case 'image': {
                        const image = this.image_cache.get(op.url || op.image!)
                        if (image) {
                            buffercontext.drawImage(image, op.x * dPR, op.y * dPR, op.width * dPR, op.height * dPR)
                        }
                        break
                    }
                    case 'setcolor':
                        this.fillcolour = op.color
                        break
                }
            }
        }
        // Now that all operations/frames are finished, draw the buffer to the main canvas (as long as it hasn't been collapsed)
        if (this.height && this.width) {
            this.canvas[0].getContext('2d')!.drawImage(this.buffer[0], 0, 0)
        }

        // Empty the queue
        this.framequeue.length = 0
        // And queue the cache to be cleared, if more frames don't arrive soon
        this.clear_cache()
    }
}

class GridWindow extends TextualWindow {
    type = 'grid' as const
    height = 0
    lines: JQuery<HTMLElement>[] = []
    width = 0

    constructor(options: WindowConstructorOptions) {
        super(options)
        this.frameel.attr({
            'aria-atomic': 'true',
            'aria-live': 'off',
            role: 'status',
        })
    }

    onclick(ev: JQuery.ClickEvent) {
        if (this.inputs?.mouse && ev.button === 0 && no_text_selected()) {
            this.inputs.mouse = false
            this.manager.send_event({
                type: 'mouse',
                window: this.id,
                x: Math.floor((ev.offsetX - this.metrics.gridmarginx / 2) / this.metrics.gridcharwidth),
                y: Math.floor((ev.offsetY - this.metrics.gridmarginy / 2) / this.metrics.gridcharheight),
            })
            return false
        }
        return super.onclick(ev)
    }

    update(data: protocol.GridWindowContentUpdate) {
        if (data.clear) {
            this.last_run_styles = undefined
            this.refresh_styles(data.bg, data.fg)
        }

        // Tell ARIA that we're busy while we're updating the window
        this.frameel.attr('aria-busy', 'true')

        for (const line of data.lines) {
            const lineel = this.lines[line.line]
            if (!lineel.length) {
                throw new Error(`Got content for nonexistent line ${line.line} of window ${this.id}`)
            }

            const content = line.content
            if (!content || !content.length) {
                lineel.text(NBSP)
            }
            else {
                lineel.empty()
                for (let i = 0; i < content.length; i++) {
                    let run: protocol.TextRun
                    if (typeof content[i] === 'string') {
                        run = {
                            style: content[i++] as string,
                            text: content[i] as string,
                        }
                    }
                    else {
                        run = content[i] as protocol.TextRun
                    }
                    lineel.append(this.create_text_run(run, false))
                    // Store the last text run for setting styles in the input
                    this.last_run_styles = run.css_styles
                }
            }
        }

        // Apply the class of 'reverse' to the window if all the text in it is reversed
        this.frameel.toggleClass('reverse', $(`#window${this.id} span:not(.reverse)`).length === 0)

        // If there are more than 4 lines, set aria-live to polite
            .attr({
                'aria-busy': 'false',
                'aria-live': this.lines.length > 3 ? 'polite' : 'off',
            })
    }
}

const window_classes: Record<string, new (opt: WindowConstructorOptions) => Window> = {
    buffer: BufferWindow,
    graphics: GraphicsWindow,
    grid: GridWindow,
}

const window_types: Record<string, string> = {
    buffer: 'BufferWindow',
    graphics: 'GraphicsWindow',
    grid: 'GridWindow',
}

export default class Windows extends Map<number, Window> {
    active_window?: Window
    blorb?: Blorb // Note will be set after this is constructed, in WebGlkOte.init
    canvasResizeObserver?: ResizeObserver // Will only be created if the browser's ResizeObserver supports devicePixelContentBoxSize
    private dom: DOM
    glkote: WebGlkOte
    history: string[] = []
    private metrics: protocol.NormalisedMetrics
    send_event: EventFunc

    constructor(glkote: WebGlkOte) {
        super()
        this.dom = glkote.dom
        this.glkote = glkote
        this.metrics = glkote.current_metrics
        if (window.ResizeObserver) {
            // We can use a ResizeObserver to get true pixel dimensions for canvases, but it's not supported in all browsers, so test
            const testRO = new ResizeObserver((entries) => {
                if (typeof entries?.[0].devicePixelContentBoxSize?.[0].blockSize !== 'undefined') {
                    this.canvasResizeObserver = new ResizeObserver((entries: ResizeObserverEntry[]) => this.oncanvasresize(entries))
                }
                testRO.disconnect()
            })
            testRO.observe(document.body)
        }
        this.send_event = ev => glkote.send_event(ev)

        $(document).on('keydown', this.onkeydown)
        this.dom.gameport().on('click', () => this.onclick())
    }

    // Clean up after a GlkOte.exit() call, but don't empty the HTML
    destroy() {
        for (const win of this.values()) {
            win.destroy(false)
            this.delete(win.id)
        }
        $(document).off('keydown', this.onkeydown)
    }

    cancel_inputs(windows: protocol.InputUpdate[]) {
        const newinputs: Record<number, protocol.InputUpdate> = {}
        for (const window of windows) {
            newinputs[window.id] = window
        }

        for (const win of this.values()) {
            const update = newinputs[win.id]
            if (!update && win.inputs) {
                if (win.textinput.el.is(':focus')) {
                    this.active_window = win
                }
                win.textinput.el.prop('disabled', true)
                delete win.inputs
            }
        }
    }

    // Use a resize observer to set true pixel sizes on graphics windows
    private oncanvasresize(entries: ResizeObserverEntry[]) {
        for (const entry of entries) {
            const box = entry.devicePixelContentBoxSize![0]
            const height = box.blockSize
            const width = box.inlineSize
            const win: GraphicsWindow = $(entry.target).data('window')
            win.buffer.attr({height, width})
            win.canvas.attr({height, width})
        }
        this.send_event({type: 'redraw'})
    }

    // If the gameport receives a click event, then find one window with active text input to focus
    private onclick() {
        if (!this.glkote.disabled && no_text_selected()) {
            for (const window of this.values()) {
                if (window.inputs?.type) {
                    window.frameel.trigger('click')
                    break
                }
            }
        }
    }

    // On document.keypress events, redirect to a window
    private onkeydown = (ev: JQuery.KeyDownEvent) => {
        // Don't fire on inputs
        if (!this.glkote.disabled && ev.target.nodeName !== 'INPUT' && ev.target.nodeName !== 'TEXTAREA') {
            // Look first for a window with active text input, but as a fallback any buffer window
            const windows = [...this.values()]
            const window = windows.filter(win => win.inputs?.type)[0] || windows.filter(win => win.type === 'buffer')[0]
            if (window) {
                window.frameel.trigger('click')
                // After focusing, the keypress event will fire, but not the keydown, meaning that function keys won't be recognised
                // So manually trigger the keydown event in the input (as long as it is actually focused)
                if (window.textinput.el.is(':focus')) {
                    window.textinput.el.trigger(ev)
                }
                // Otherwise focus the window so that nav keys will work
                else if (window.type === 'buffer') {
                    window.frameel.trigger('focus')
                    // If the key is a regular letter key then scroll down
                    if (ev.which >= 65 && ev.which <= 90) {
                        const new_scrollTop = window.frameel.scrollTop()! + window.frameel.height()! * 0.9
                        window.frameel.animate({scrollTop: new_scrollTop}, 100)
                    }
                }
            }
        }
    }

    update(windows: protocol.WindowUpdate[]) {
        // Mark all windows as non-desired
        for (const win of this.values()) {
            win.desired = false
        }

        // Go through each window in this update
        for (const update of windows) {
            const id = update.id
            const type = update.type

            // Is there an existing window?
            let win = this.get(id)

            // Create it if not
            if (!win) {
                win = new (window_classes[type])({
                    blorb: this.blorb,
                    dom: this.dom,
                    id,
                    manager: this,
                    metrics: this.metrics,
                    rock: update.rock,
                    styles: update.styles,
                    type,
                })
                this.set(id, win)
            }
            else {
                if (win.type !== type) {
                    throw new Error(`Window ${id} was created with type ${win.type}, but now is described as type ${type}`)
                }
            }
            win.desired = true

            // Ensure graphics windows are the right size
            if (win.type === 'graphics') {
                if (win.height !== update.graphheight || win.width !== update.graphwidth) {
                    win.set_dimensions(update.graphheight!, update.graphwidth!)
                }
            }

            // Ensure grid windows have the right number of lines
            if (win.type === 'grid') {
                if (update.gridheight! > win.height) {
                    for (let i = win.height; i < update.gridheight!; i++) {
                        const line = this.dom.create('div', `win${win.id}_ln${i}`, 'GridLine')
                        line.append(NBSP)
                        win.frameel.append(line)
                        win.lines[i] = line
                    }
                }
                if (update.gridheight! < win.height) {
                    for (let i = update.gridheight!; i < win.height; i++) {
                        this.dom.id(`win${win.id}_ln${i}`).remove()
                    }
                }
                win.height = update.gridheight!
                win.lines.length = win.height
                win.width = update.gridwidth!
            }

            // Update the position of the window
            win.frameel.css({
                height: update.height,
                left: update.left,
                top: update.top,
                width: update.width,
            })
                .toggleClass('hidden', !!update.hidden)
            if (win.type === 'buffer') {
                win.scroll_to_bottom(true)
            }
        }

        const windowstoclose: Window[] = []
        for (const win of this.values()) {
            if (!win.desired) {
                windowstoclose.push(win)
            }
        }
        for (const win of windowstoclose) {
            win.destroy(true)
            this.delete(win.id)
        }
    }

    update_content(content: protocol.ContentUpdate[]) {
        for (const update of content) {
            const win = this.get(update.id)
            if (!win) {
                throw new Error(`Got content update for window ${update.id}, which does not exist`)
            }
            // TODO: check for pending line input

            switch (win.type) {
                case 'buffer': win.update(update as protocol.BufferWindowContentUpdate); break
                case 'graphics':
                    // Queue this frame, but only run the update function if this is the only frame
                    win.framequeue.push((update as protocol.GraphicsWindowContentUpdate).draw)
                    if (win.framequeue.length === 1) {
                        win.update()
                    }
                    break
                case 'grid': win.update(update as protocol.GridWindowContentUpdate); break
            }
        }
    }

    update_inputs(windows: protocol.InputUpdate[]) {
        for (const update of windows) {
            const win = this.get(update.id)
            if (!win) {
                throw new Error(`Got input update for window ${update.id}, which does not exist`)
            }

            const oldgen = win.inputs?.gen
            win.inputs = update
            if (update.type){
                if (update.gen !== oldgen) {
                    win.textinput.update()
                }
            }
        }

        // Refocus an <input>
        // On Android this forces the window to be scrolled down to the bottom, so only refocus if the virtual keyboard doesn't make the window too small for the full update text to be seen
        if (this.active_window) {
            // Refocus the same window if it hasn't been deleted and still wants input
            if (this.has(this.active_window.id) && this.active_window.inputs?.type) {
                this.active_window.textinput.refocus()
            }
            // Look for any window with text input
            else {
                [...this.values()].filter(win => win.inputs?.type)[0]?.textinput.refocus()
            }
        }
    }
}