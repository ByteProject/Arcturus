/*

Metrics and resize handlers
===========================

Copyright (c) 2023 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {throttle} from 'lodash-es'

import {is_pinch_zoomed} from '../../common/misc.js'
import * as protocol from '../../common/protocol.js'

import {create, is_input_focused, is_iOS} from './shared.js'
import WebGlkOte from './web.js'

function get_size(el: JQuery<HTMLElement>): {height: number, width: number} {
    return {
        height: el.outerHeight()!,
        width: el.outerWidth()!,
    }
}

/** Compare two metrics to see if they differ enough to send an arrange event */
function metrics_differ(newmetrics: protocol.NormalisedMetrics, oldmetrics: protocol.NormalisedMetrics): boolean {
    return (oldmetrics.buffercharheight !== newmetrics.buffercharheight ||
        oldmetrics.buffercharwidth !== newmetrics.buffercharwidth ||
        oldmetrics.gridcharheight !== newmetrics.gridcharheight ||
        oldmetrics.gridcharwidth !== newmetrics.gridcharwidth ||
        oldmetrics.height !== newmetrics.height ||
        oldmetrics.width !== newmetrics.width)
}

export default class Metrics {
    /** When we don't know how high the screen is, use a height we've saved before, or, at the very beginning, a rough estimate */
    private height_with_keyboard = (visualViewport?.height || window.innerHeight) / 2
    private loaded: Promise<void>
    private glkote: WebGlkOte
    // Shares the current_metrics and DOM of WebGlkOte
    private metrics: protocol.NormalisedMetrics
    private observer?: ResizeObserver

    constructor(glkote: WebGlkOte) {
        this.glkote = glkote
        this.metrics = glkote.current_metrics

        // AsyncGlk may have started after a DOMContentLoaded event, but Metrics needs the page to be fully loaded so that the CSS and fonts are in use
        // If the page is fast and already loaded by the time we get here (or, apparently, always for file: pages) then just use an auto-resolved promise
        if (document.readyState === 'complete') {
            this.loaded = Promise.resolve()
        }
        else {
            this.loaded = new Promise((resolve: any) => {
                window.addEventListener('load', resolve, {once: true})
            })
        }

        // Use a resize observer on #gameport, or else a resize handler on window
        if (window.ResizeObserver) {
            this.observer = new ResizeObserver(this.on_gameport_resize)
            this.observer.observe(this.glkote.dom.gameport()[0])
        }
        else {
            $(window).on('resize', this.on_gameport_resize)
        }

        // iOS sends repeated visualViewport:resize events, so throttle it
        if (is_iOS) {
            this.on_visualViewport_resize = throttle(this.on_visualViewport_resize, 700)
        }
        if (visualViewport) {
            $(visualViewport).on('resize', this.on_visualViewport_resize)
        }
    }

    destroy() {
        if (this.observer) {
            this.observer.disconnect()
        }
        else {
            $(window).off('resize', this.on_gameport_resize)
        }
        if (visualViewport) {
            $(visualViewport).off('resize', this.on_visualViewport_resize)
        }
    }

    async measure() {
        // Ensure #gameport exists
        const dom = this.glkote.dom
        const gameport = dom.gameport()
        if (!gameport.length) {
            throw new Error(`Cannot find gameport element #${dom.gameport_id}`)
        }

        // Old versions of GlkOte used a pre-existing #layouttestpane, remove it if it exists
        dom.id('layouttestpane').remove()

        // Create a layout test pane
        const layout_test_pane = dom.create('div', 'layout_test_pane')
        layout_test_pane.text('This should not be visible')

        // Create the test windows
        const line = $('<div>')
        create('span', 'Style_normal').text('12345678').appendTo(line)

        const bufwin = create('div', 'WindowFrame BufferWindow')
        const bufinnerwin = create('div', 'BufferWindowInner').appendTo(bufwin)
        const bufline1 = line.clone().addClass('BufferLine').appendTo(bufinnerwin)
        const bufline2 = line.clone().addClass('BufferLine').appendTo(bufinnerwin)
        create('span', 'InvisibleCursor').appendTo(bufline2)
        const bufspan = bufline1.children('span')
        layout_test_pane.append(bufwin)

        const graphwin = create('div', 'WindowFrame GraphicsWindow')
        const graphcanvas = $('<canvas>', {
            height: 32,
            width: 64,
        }).appendTo(graphwin)
        layout_test_pane.append(graphwin)

        const gridwin = create('div', 'WindowFrame GridWindow')
        const gridline1 = line.clone().addClass('GridLine').appendTo(gridwin)
        const gridline2 = line.clone().addClass('GridLine').appendTo(gridwin)
        const gridspan = gridline1.children('span')
        layout_test_pane.append(gridwin)

        gameport.append(layout_test_pane)

        // Wait first for the load event for the CSS to be loaded
        await this.loaded
        // And then for the actual font(s) to be loaded
        const font_family = getComputedStyle(gridwin[0]).getPropertyValue('--glkote-grid-mono-family').split(',')[0].replace(/"/g, '')
        await document.fonts.load(`14px ${font_family}`)

        // Measure the gameport height/width, excluding border and padding
        this.metrics.height = gameport.height()!
        this.metrics.width = gameport.width()!

        // Measure the buffer window
        const bufwinsize = get_size(bufwin)
        const bufspansize = get_size(bufspan)
        const bufline1size = get_size(bufline1)
        const bufline2size = get_size(bufline2)
        // A minimum of 1, but not necessarily an integer
        this.metrics.buffercharheight = Math.max(1, bufline2.position().top - bufline1.position().top)
        this.metrics.buffercharwidth = Math.max(1, bufspan.width()! / 8)
        this.metrics.buffermarginx = bufwinsize.width - bufspansize.width
        this.metrics.buffermarginy = bufwinsize.height - (bufline1size.height + bufline2size.height)

        // Measure the graphics window
        const graphicswinsize = get_size(graphwin)
        const canvassize = get_size(graphcanvas)
        this.metrics.graphicsmarginx = graphicswinsize.width - canvassize.width
        this.metrics.graphicsmarginy = graphicswinsize.height - canvassize.height

        // Measure the grid window
        const gridwinsize = get_size(gridwin)
        const gridspansize = get_size(gridspan)
        const gridline1size = get_size(gridline1)
        const gridline2size = get_size(gridline2)
        // A minimum of 1, but not necessarily an integer
        this.metrics.gridcharheight = Math.max(1, gridline2.position().top - gridline1.position().top)
        this.metrics.gridcharwidth = Math.max(1, gridspan.width()! / 8)
        this.metrics.gridmarginx = gridwinsize.width - gridspansize.width
        this.metrics.gridmarginy = gridwinsize.height - (gridline1size.height + gridline2size.height)

        // Clean up
        layout_test_pane.remove()
    }

    on_gameport_resize = throttle(async () => {
        // Delay again if not yet inited or disabled
        if (this.glkote.disabled || !this.glkote.inited()) {
            this.on_gameport_resize()
            return
        }
        const oldmetrics = Object.assign({}, this.metrics)
        await this.measure()
        if (metrics_differ(this.metrics, oldmetrics)) {
            this.glkote.send_event({type: 'arrange'})
        }
    }, 200, {leading: false})

    on_visualViewport_resize = () => {
        // If the keyboard is active, then store the height for later
        const height = visualViewport!.height
        if (is_input_focused()) {
            this.height_with_keyboard = height
        }

        // The iOS virtual keyboard does not change the gameport height, but it does change the viewport
        // Try to account for this by setting the gameport to the viewport height
        this.set_gameport_height(height)
    }

    /** Update the gameport height and then send new metrics */
    set_gameport_height(height: number) {
        // Don't do anything if the window is pinch zoomed
        if (is_pinch_zoomed()){
            return
        }

        if (!height) {
            height = this.height_with_keyboard
        }

        // We set the outer height to account for any padding or margin
        this.glkote.dom.gameport().outerHeight(height, true)

        // Safari might have scrolled weirdly, so try to put it right
        window.scrollTo(0, 0)

        // Measure and send the new metrics
        this.on_gameport_resize()
    }
}