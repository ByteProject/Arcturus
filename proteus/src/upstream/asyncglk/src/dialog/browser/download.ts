/*

Download/upload provider
========================

Copyright (c) 2025 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

// The download provider stores its own files just in a map (maybe to be cached in the future), but if files are written next to them, then they need to be done so in another provider

import {gunzipSync} from 'fflate'

import type {DownloadOptions, ProgressCallback} from '../../common/file/interface.js'
import {parse_base64, read_response} from '../../common/file/browser.js'
import {NullProvider} from './common.js'
import type {Provider} from './interface.js'
import {utf8decoder} from '../../common/misc.js'

export class DownloadProvider implements Provider {
    browseable = false
    next = new NullProvider()
    private options: DownloadOptions
    private store: Map<string, Uint8Array<ArrayBuffer>> = new Map()

    constructor(options: DownloadOptions) {
        this.options = options
    }

    async download(url: string, progress_callback?: ProgressCallback): Promise<string> {
        const [final_url, data] = await fetch_storyfile(this.options, url, progress_callback)
        const path = url_to_path(final_url)
        this.store.set(path, data)
        return path
    }

    async upload(filename: string, data: Uint8Array<ArrayBuffer>) {
        const path = '/upload/' + filename
        this.store.set(path, data)
        return path
    }

    async delete(path: string) {
        if (this.store.has(path)) {
            this.store.delete(path)
        }
        else {
            return this.next.delete(path)
        }
    }

    async exists(path: string): Promise<boolean | null> {
        if (this.store.has(path)) {
            return true
        }
        else {
            return this.next.exists(path)
        }
    }

    async read(path: string): Promise<Uint8Array<ArrayBuffer> | null> {
        if (this.store.has(path)) {
            return this.store.get(path)!
        }
        else {
            return this.next.read(path)
        }
        // TODO: try downloading a sibling file
    }

    write(files: Record<string, Uint8Array>) {
        return this.next.write(files)
    }
}

/** Fetch a storyfile, using the proxy if necessary, and handling JSified stories */
async function fetch_storyfile(options: DownloadOptions, url: string, progress_callback?: ProgressCallback): Promise<[string, Uint8Array<ArrayBuffer>]> {
    // Handle a relative URL
    const story_url = new URL(url, document.URL)
    url = story_url + ''
    const story_domain = story_url.hostname
    const same_protocol = story_url.protocol === document.location.protocol
    const same_domain = story_domain === document.location.hostname
    let response: Response

    // Load an embedded storyfile
    if (story_url.protocol === 'embedded:') {
        const node = document.getElementById(story_url.pathname) as HTMLScriptElement
        const data_base64 = node.text
        let data = await parse_base64(data_base64)
        if (node.type.endsWith(';gzip')) {
            data = gunzipSync(data) as Uint8Array<ArrayBuffer>
        }
        return [url, data]
    }

    // Only directly access files same origin files or those from the list of reliable domains
    let direct_access = (same_protocol && same_domain) || story_url.protocol === 'data:'
    const direct_domains = options.direct_domains
    if (!direct_access && direct_domains) {
        for (const domain of direct_domains) {
            if (story_domain.endsWith(domain)) {
                // all direct domains require HTTPS
                story_url.protocol = 'https:'
                direct_access = true
                break
            }
        }
    }

    if (direct_access) {
        try {
            response = await fetch('' + story_url)
            // If we were redirected get the final URL
            url = response.url ?? url
        }
        // We can't specifically detect CORS errors but that's probably what happened
        catch {
            throw new Error('Failed to fetch storyfile (possible CORS error)')
        }
    }

    // Otherwise use the proxy
    else {
        if (options.use_proxy && options.proxy_url) {
            response = await fetch(`${options.proxy_url}?url=${story_url}`)
            // If the proxy was redirected get the final URL
            url = response.headers.get('Final-Url') ?? url
        }
        else {
            throw new Error('Storyfile not in list of direct domains and proxy disabled')
        }
    }

    if (!response.ok) {
        if (response.status === 451) {
            let message = '<p>Storyfile is unavailable for legal reasons'
            if (response.headers.get('Content-type')?.startsWith('text/html')) {
                message += `<p>The server might have <a href='${encodeURI(response.url)}'>more information</a>`
            }
            throw message
        }
        throw new Error(`Could not fetch storyfile, got ${response.status}`)
    }

    // It would be nice to check here if the file was compressed, but we can only read the Content-Encoding header for same domain files

    const data = await read_response(response, progress_callback)

    // Handle JSified stories
    if (url.endsWith('.js')) {
        const text = utf8decoder.decode(data)
        const matched = /processBase64Zcode\(['"]([a-zA-Z0-9+/=]+)['"]\)/.exec(text)
        if (!matched) {
            throw new Error('Abnormal JSified story')
        }

        return [url, await parse_base64(matched[1])]
    }

    return [url, data]
}

function url_to_path(url: string) {
    if (url.startsWith('https:')) {
        return '/download/https/' + url.substring(8)
    }
    else {
        return '/download/http/' + url.substring(7)
    }
}