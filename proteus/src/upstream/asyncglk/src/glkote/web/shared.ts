/*

Web GlkOte shared things
========================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import * as protocol from '../../common/protocol.js'

/** Create an element with specified classes */
export function create(tag: string, className:string): JQuery<HTMLElement> {
    return $(`<${tag}>`, {'class': className})
}

/** Manage the DOM elements used by GlkOte */
export class DOM {
    context_element?: HTMLElement
    errorcontent_id: string
    errorpane_id: string
    gameport_id: string
    loadingpane_id: string
    prefix: string
    windowport_id: string

    constructor(options: {
        context_element?: HTMLElement,
        errorcontent_id: string,
        errorpane_id: string,
        gameport_id: string,
        loadingpane_id: string,
        prefix: string,
        windowport_id: string,
    }) {
        this.context_element = options.context_element
        this.errorcontent_id = options.errorcontent_id
        this.errorpane_id = options.errorpane_id
        this.gameport_id = options.gameport_id
        this.loadingpane_id = options.loadingpane_id
        this.prefix = options.prefix
        this.windowport_id = options.windowport_id
    }

    /** Create an element, adding prefix to the ID */
    create(tag: string, id: string, props?: string | any): JQuery<HTMLElement> {
        props ??= {}
        // Handle class name as props
        if (typeof props === 'string') {
            props = {
                class: props,
            }
        }
        props.id = this.prefix + id
        return $(`<${tag}>`, props)
    }

    gameport(): JQuery<HTMLElement> {
        return $(`#${this.gameport_id}`, this.context_element)
    }

    /** Return a jQuery search for an element ID, using prefix and context_element */
    id(id: string): JQuery<HTMLElement> {
        return $(`#${this.prefix}${id}`, this.context_element)
    }

    windowport(): JQuery<HTMLElement> {
        return $(`#${this.windowport_id}`, this.context_element)
    }
}

export type EventFunc = (event: Partial<protocol.Event>) => void

/** Is any input element focused? */
export function is_input_focused() {
    const activeElement_tagName = document.activeElement?.tagName
    return activeElement_tagName === 'INPUT' || activeElement_tagName === 'TEXTAREA'
}

/** Try to detect iOS */
// From https://stackoverflow.com/a/58065241/2854284
export const is_iOS = /iPad|iPhone|iPod/.test(navigator.platform) || (navigator.platform === 'MacIntel' && (navigator.maxTouchPoints ?? 0) > 1)