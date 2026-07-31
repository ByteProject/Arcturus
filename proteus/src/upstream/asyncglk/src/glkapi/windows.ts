/*

Glk Windows
===========

Copyright (c) 2023 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {cloneDeep} from 'lodash-es'

import type {BufferWindowImage, ContentUpdate, GraphicsWindowOperation, InputUpdate, TextRun, WindowStyles, WindowUpdate as SizeUpdate} from '../common/protocol.js'

import {winmethod_Above, winmethod_BorderMask, winmethod_DirMask, winmethod_DivisionMask, winmethod_Fixed, winmethod_Left, winmethod_Right, wintype_Blank, wintype_Graphics, wintype_Pair, wintype_TextBuffer, wintype_TextGrid} from './constants.js'
import type {GlkArray, GlkWindow} from './interface.js'
import {type Stream, WindowStream} from './streams.js'

export type Window = BlankWindow | BufferWindow | GraphicsWindow | GridWindow | PairWindow
type WindowTypes = 'blank' | 'buffer' | 'graphics' | 'grid' | 'pair'

export interface WindowBox {
    bottom: number
    left: number
    right: number
    top: number
}

export interface WindowUpdate {
    content: ContentUpdate | null,
    input: InputUpdate | null,
    size: SizeUpdate | null,
}

abstract class WindowBase implements GlkWindow {
    // TODO: Make most of these private?
    box: WindowBox = {
        bottom: 0,
        left: 0,
        right: 0,
        top: 0,
    }
    disprock = 0
    echostr: Stream | null = null
    input: InputUpdate = {
        id: 0,
    }
    next: Window | null = null
    parent: PairWindow | null = null
    prev: Window | null = null
    rock: number
    str: WindowStream
    abstract type: WindowTypes
    abstract typenum: number

    constructor(rock: number) {
        this.rock = rock
        this.str = new WindowStream(this as Window)
    }

    clear() {}
    put_string(_str: string, _style?: string) {}
    set_css(_name: string, _val?: string | number) {}
    set_hyperlink(_val: number) {}
    set_style(_style: string) {}

    update(): WindowUpdate {
        if (this.type === 'blank' || this.type === 'pair') {
            return {
                content: null,
                input: null,
                size: null,
            }
        }

        const input_update: InputUpdate = {
            id: this.input.id,
        }
        copy_prop(this.input, input_update, 'hyperlink')
        copy_prop(this.input, input_update, 'mouse')

        const box = this.box
        const height = box.bottom - box.top
        const width = box.right - box.left
        return {
            content: null,
            input: input_update,
            size: {
                height,
                hidden: height === 0 || width === 0,
                id: this.disprock,
                left: box.left,
                rock: this.rock,
                top: box.top,
                type: this.type,
                width,
            },
        }
    }
}

export class BlankWindow extends WindowBase {
    type = 'blank' as const
    typenum = wintype_Blank
}

export abstract class TextWindow extends WindowBase {
    cleared = true
    line_input_buf?: GlkArray
    request_echo_line_input = true
    stylehints: WindowStyles
    uni_input?: boolean

    constructor(rock: number, stylehints: WindowStyles) {
        super(rock)
        this.stylehints = cloneDeep(stylehints)
    }

    update(): WindowUpdate {
        const update = super.update()

        // TODO: don't resend stylehints when only metrics have changed?
        if (Object.keys(this.stylehints).length) {
            update.size!.styles = this.stylehints
        }

        const input = this.input
        const input_update = update.input!
        if (input.type) {
            copy_prop(input, input_update, 'gen')
            copy_prop(input, input_update, 'type')
            if (input.type === 'line') {
                input_update.maxlen = (this as TextWindow).line_input_buf!.length
                copy_prop(input, input_update, 'initial')
                copy_prop(input, input_update, 'terminators')
            }
        }
        // Clean up the partial output
        delete input.initial

        return update
    }
}

// A modified version of BufferWindowParagraphUpdate that always has content, and the content isn't a string
export interface Paragraph {
    /** Append to last input */
    append?: boolean
    /** Line data */
    content: ParagraphTextRun[]
    /** Paragraph breaks after floating images */
    flowbreak?: boolean
}
type ParagraphTextRun = BufferWindowImage | TextRun

export class BufferWindow extends TextWindow {
    content: Paragraph[]
    echo_line_input = true
    private last_par: Paragraph
    private last_textrun: TextRun = clone_textrun(BASE_TEXTRUN, true)
    type = 'buffer' as const
    typenum = wintype_TextBuffer

    constructor(rock: number, stylehints: WindowStyles) {
        super(rock, stylehints)
        this.last_textrun = clone_textrun(BASE_TEXTRUN, true)
        this.content = [{
            content: [this.last_textrun],
        }]
        this.last_par = this.content[0]
    }

    clear() {
        this.cleared = true
        this.clear_content()
    }

    clear_content() {
        this.last_textrun = clone_textrun(this.last_textrun, false)
        this.content = [{
            append: true,
            content: [this.last_textrun],
        }]
        this.last_par = this.content[0]
    }

    private clone_textrun(clone_styles: boolean, force?: boolean) {
        if (force || this.last_textrun.text !== '') {
            this.last_textrun = clone_textrun(this.last_textrun, clone_styles)
            this.last_par.content!.push(this.last_textrun)
        }
    }

    put_image(img: BufferWindowImage) {
        img.hyperlink = this.last_textrun.hyperlink
        this.last_par.content!.push(img)
        this.clone_textrun(false, true)
    }

    put_string(str: string, style?: string) {
        const old_style = this.last_textrun.style
        if (style) {
            this.set_style(style)
        }
        for (const [i, line] of str.split('\n').entries()) {
            if (i !== 0) {
                this.last_textrun = clone_textrun(this.last_textrun, false)
                this.last_par = {content: [this.last_textrun]}
                this.content.push(this.last_par)
            }
            this.last_textrun.text += line
        }
        if (style) {
            this.set_style(old_style)
        }
    }

    set_css(name: string, val?: string | number) {
        if (this.last_textrun.css_styles![name] !== val) {
            this.clone_textrun(true)
            if (val === undefined) {
                delete this.last_textrun.css_styles![name]
            }
            else {
                this.last_textrun.css_styles![name] = val
            }
        }
    }

    set_flow_break() {
        this.last_par.flowbreak = true
    }

    set_hyperlink(val?: number) {
        if (val === 0) {
            val = undefined
        }
        if (val !== this.last_textrun.hyperlink) {
            this.clone_textrun(false)
            if (val) {
                this.last_textrun.hyperlink = val
            }
            else {
                delete this.last_textrun.hyperlink
            }
        }
    }

    set_style(style: string) {
        if (style !== this.last_textrun.style) {
            this.clone_textrun(false)
            this.last_textrun.style = style
        }
    }

    update(): WindowUpdate {
        const update = super.update()

        // Clone the textrun now because the css_style could get deleted in cleanup_paragraph_styles
        this.last_textrun = clone_textrun(this.last_textrun, false)

        // Exclude empty text runs
        const paragraphs = this.content
        for (const par of paragraphs) {
            par.content = cleanup_paragraph_styles(par.content.filter((text) => 'special' in text || text.text))
        }
        // Only send an update if there is new content or the window has been cleared
        if (this.cleared || paragraphs.length > 1 || paragraphs[0].content.length) {
            update.content = {
                id: this.disprock,
                // Send an empty object for a blank line
                text: paragraphs.map(par => par.append || par.flowbreak || par.content.length ? par : {}),
            }
            if (this.cleared) {
                update.content.clear = true
                this.cleared = false
                // TODO: fg bg
            }
        }
        this.clear_content()

        return update
    }
}

export class GraphicsWindow extends WindowBase {
    draw: GraphicsWindowOperation[] = []
    height = 0
    type = 'graphics' as const
    typenum = wintype_Graphics
    uni_input?: boolean
    width = 0

    clear() {
        this.draw = this.draw.filter(op => op.special === 'setcolor').slice(-1)
        this.draw.push({special: 'fill'})
    }

    update(): WindowUpdate {
        const update = super.update()

        if (this.draw.length) {
            update.content = {
                draw: this.draw,
                id: this.disprock,
            }
            this.draw = []
        }

        update.size!.graphheight = this.height
        update.size!.graphwidth = this.width

        return update
    }
}

interface GridLine {
    content: TextRun[]
    changed: boolean
}

export class GridWindow extends TextWindow {
    private current_styles = clone_textrun(BASE_TEXTRUN, true)
    height = 0
    lines: GridLine[] = []
    type = 'grid' as const
    typenum = wintype_TextGrid
    width = 0
    x = 0
    y = 0

    clear() {
        this.cleared = true
        const height = this.height
        this.update_size(0, this.width)
        this.update_size(height, this.width)
        this.x = this.y = 0
    }

    fit_cursor() {
        if (this.x >= this.width) {
            this.x = 0
            this.y++
        }
        if (this.y >= this.height) {
            return true
        }
    }

    put_string(str: string, style?: string) {
        const old_style = this.current_styles.style
        if (style) {
            this.set_style(style)
        }
        for (const ch of str) {
            if (this.fit_cursor()) {
                break
            }
            if (ch === '\n') {
                this.x = 0
                this.y++
                continue
            }
            const line = this.lines[this.y]
            line.changed = true
            line.content[this.x++] = clone_textrun(this.current_styles, false, ch)
        }
        if (style) {
            this.set_style(old_style)
        }
    }

    set_css(name: string, val?: string | number) {
        if (this.current_styles.css_styles![name] !== val) {
            this.current_styles = clone_textrun(this.current_styles, true)
            if (val === undefined) {
                delete this.current_styles.css_styles![name]
            }
            else {
                this.current_styles.css_styles![name] = val
            }
        }
    }

    set_hyperlink(val: number) {
        if (val) {
            this.current_styles.hyperlink = val
        }
        else {
            delete this.current_styles.hyperlink
        }
    }

    set_style(style: string) {
        this.current_styles.style = style
    }

    update_size(height: number, width: number) {
        const oldheight = this.height
        const oldwidth = this.width
        this.height = height
        this.width = width

        // Resize the lines array if necessary
        const blank_space = clone_textrun(BASE_TEXTRUN, true, ' ')
        if (oldheight > height) {
            this.lines.length = height
        }
        else if (height > oldheight) {
            for (let i = oldheight; i < height; i++) {
                const new_line: TextRun[] = []
                for (let c = 0; c < width; c++) {
                    new_line.push(clone_textrun(blank_space, false, ' '))
                }
                this.lines[i] = {
                    changed: true,
                    content: new_line,
                }
            }
        }
        // Fix the width of old rows
        const rows_to_fix = Math.min(height, oldheight)
        if (rows_to_fix && width !== oldwidth) {
            for (let i = 0; i < rows_to_fix; i++) {
                const line = this.lines[i]
                if (width < oldwidth) {
                    line.changed = true
                    line.content.length = width
                }
                else {
                    line.changed = true
                    for (let c = oldwidth; c < width; c++) {
                        line.content.push(clone_textrun(blank_space, false, ' '))
                    }
                }
            }
        }
    }

    update(): WindowUpdate {
        const update = super.update()

        if (this.lines.find(line => line.changed)) {
            update.content = {
                id: this.disprock,
                lines: this.lines.flatMap((line, index) => {
                    if (!line.changed) {
                        return []
                    }
                    line.changed = false
                    return {
                        content: cleanup_paragraph_styles(line.content.reduce((acc: TextRun[], cur) => {
                            if (!acc.length) {
                                return [clone_textrun(cur, false, cur.text)]
                            }

                            // Combine adjacent characters when they have the same textrun properties
                            const last = acc[acc.length - 1]
                            if (cur.css_styles === last.css_styles && cur.hyperlink === last.hyperlink && cur.style === last.style) {
                                last.text += cur.text
                            }
                            else {
                                acc.push(clone_textrun(cur, false, cur.text))
                            }
                            return acc
                        }, [])) as TextRun[],
                        line: index,
                    }
                }),
            }
            if (this.cleared) {
                update.content.clear = true
                this.cleared = false
                // TODO: fg bg
            }
        }

        if (this.input.type) {
            const input_update = update.input!
            if (this.fit_cursor()) {
                input_update.xpos = this.width - 1
                input_update.ypos = this.height - 1
            }
            else {
                input_update.xpos = this.x
                input_update.ypos = this.y
            }
        }

        update.size!.gridheight = this.height
        update.size!.gridwidth = this.width

        return update
    }
}

export class PairWindow extends WindowBase {
    backward: boolean
    child1: Window | null = null
    child2: Window | null = null
    border: boolean
    dir: number
    fixed: boolean
    key: Window | null
    size: number
    type = 'pair' as const
    typenum = wintype_Pair
    vertical: boolean

    constructor(keywin: Window, method: number, size: number) {
        super(0)
        this.border = (method & winmethod_BorderMask) === winmethod_BorderMask
        this.dir = method & winmethod_DirMask
        this.fixed = (method & winmethod_DivisionMask) === winmethod_Fixed
        this.key = keywin
        this.size = size
        this.backward = this.dir === winmethod_Left || this.dir === winmethod_Above
        this.vertical = this.dir === winmethod_Left || this.dir === winmethod_Right
    }
}

const BASE_TEXTRUN: TextRun = {
    css_styles: {},
    style: 'normal',
    text: '',
}

/** Remove css_styles from a paragraph when empty */
function cleanup_paragraph_styles(par: ParagraphTextRun[]) {
    return par.map(tr => {
        if (!('special' in tr)) {
            if (!Object.keys(tr.css_styles!).length) {
                delete tr.css_styles
            }
        }
        return tr
    })
}

/** Clone a text run */
function clone_textrun(tr: TextRun, clone_styles: boolean, new_text = '') {
    return Object.assign({}, tr, {
        css_styles: clone_styles ? Object.assign({}, tr.css_styles) : tr.css_styles,
        text: new_text,
    })
}

/** Copy a property from one InputUpdate to another */
function copy_prop(from: InputUpdate, to: InputUpdate, prop: keyof InputUpdate) {
    if (from[prop]) {
        (to[prop] as any) = from[prop]
    }
}