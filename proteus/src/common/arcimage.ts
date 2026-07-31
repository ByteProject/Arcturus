/*

Proteus arc_image band
======================

The picture band of the arc_image extension (docs/08 in the Arcturus
repository): a picture across the top of the screen, above the text
area. The Blorb carries the master PNGs as Pict resources and declares
itself with an ARCI chunk; the game draws by id through EXT:0x80, which
the patched ZVM forwards here. Id 0 clears the band. An id that cannot
be resolved is ignored silently and play continues.

The band lives OUTSIDE the gameport and pushes it down through the
--arc-band-height variable: GlkOte's own ResizeObserver on the gameport
then re-measures and lays the windows out in the remaining space, so
the input line stays on screen however tall the picture is.

Copyright (c) 2026 Stefan Vogt (part of the Arcturus project)
MIT licenced

*/

import type {Blorb} from '../upstream/asyncglk/src/index-browser.js'

export type ArcImageDraw = (id: number, mode: number) => void

/** When the Blorb declares arc_image pictures (the ARCI chunk), build
 * the band above the gameport and return the draw handler the engine
 * forwards EXT:0x80 to. Returns undefined otherwise, in which case the
 * capability bit is left alone and the game never draws. */
export function setup_arc_image(blorb?: Blorb): ArcImageDraw | undefined {
    if (!blorb) {
        return undefined
    }
    const arci = blorb.chunks.find(chunk => chunk.chunktype === 'ARCI')
    if (!arci) {
        return undefined
    }

    const gameport = document.getElementById('gameport')
    if (!gameport || !gameport.parentElement) {
        return undefined
    }
    const band = document.createElement('div')
    band.id = 'arc-image-band'
    band.style.display = 'none'
    const img = document.createElement('img')
    img.alt = ''
    band.appendChild(img)
    gameport.parentElement.insertBefore(band, gameport)

    // The flex layout (parchment.css) reflows the gameport whenever the
    // band changes, and GlkOte re-measures on its own. The one thing
    // GlkOte's relayout does not promise is the buffer window's scroll
    // position, so pin the transcript back to the prompt after each band
    // change: once when the band size settles, once after the relayout.
    const scroll_to_prompt = () => {
        for (const el of document.querySelectorAll('.BufferWindow')) {
            el.scrollTop = el.scrollHeight
        }
    }
    const settle = () => {
        requestAnimationFrame(scroll_to_prompt)
        setTimeout(scroll_to_prompt, 120)
        setTimeout(scroll_to_prompt, 400)
    }
    img.addEventListener('load', settle)
    if (window.ResizeObserver) {
        new ResizeObserver(settle).observe(band)
    }

    return (id: number, _mode: number) => {
        if (id === 0) {
            band.style.display = 'none'
            img.removeAttribute('src')
            settle()
            return
        }
        const url = blorb.get_image_url(id)
        if (url) {
            img.src = url
            band.style.display = ''
            settle()
        }
    }
}
