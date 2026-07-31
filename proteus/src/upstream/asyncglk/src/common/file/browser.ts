/*

File processing functions for the browser
=========================================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {gunzipSync} from 'fflate'

import type {DownloadOptions, ProgressCallback, Resource} from './interface.js'

/** Fetch a resource */
let jsonp_queue: JSONPQueue
const resource_map: Map<string, any> = new Map()
export async function fetch_resource<T>(options: DownloadOptions, path: string, progress_callback?: ProgressCallback): Promise<T> {
    if (!jsonp_queue && options.jsonp) {
        jsonp_queue = new JSONPQueue(options)
    }

    // Check the cache
    const cached = resource_map.get(path)
    if (cached) {
        return cached
    }

    const response = fetch_resource_inner<T>(options, path, progress_callback)
    // Fill the cache with the promise, and then when the resource has been obtained, update the cache
    resource_map.set(path, response)
    response.then((resource: any) => {
        resource_map.set(path, resource)
    })
    return response
}

/** Actually fetch a resource */
async function fetch_resource_inner<T>(options: DownloadOptions, path: string, progress_callback?: ProgressCallback): Promise<T> {
    // Handle embedded resources
    const node = document.getElementById(path) as HTMLScriptElement | null
    if (node) {
        const data = node.text
        if (path.endsWith('.js')) {
            return import(`data:text/javascript,${encodeURIComponent(data)}`)
        }
        if (!path.endsWith('.wasm')) {
            throw new Error(`Can't load ${path} in single file mode`)
        }
        const node_types = node.type.split(';')
        return process_resource<T>({
            base64: 1,
            data,
            gzip: node_types.includes('gzip'),
        })
    }

    // Handle when lib_path is a proper URL (such as import.meta.url), as well as the old style path fragment
    const lib_path = options.lib_path ?? import.meta.url
    let url: URL | string
    try {
        url = new URL(path, lib_path)
    }
    catch {
        url = lib_path + path
    }

    if (options.jsonp) {
        return jsonp_queue.request(url + '')
    }

    if (path.endsWith('.js')) {
        return import(url + '')
    }

    // Something else, like a .wasm
    const response = await fetch(url)
    return read_response(response, progress_callback) as Promise<T>
}

/** Parse Base 64 into a Uint8Array */
export async function parse_base64(data: string) {
    if (Uint8Array.fromBase64) {
        return Uint8Array.fromBase64(data)
    }

    // Firefox has a data URL limit of 32MB, so we have to chunk large data
    const chunk_length = 30_000_000
    if (data.length < chunk_length) {
        return parse_base64_with_data_url(data)
    }
    const chunks: Uint8Array<ArrayBuffer>[] = []
    let i = 0
    while (i < data.length) {
        chunks.push(await parse_base64_with_data_url(data.substring(i, i += chunk_length)))
    }
    const blob = new Blob(chunks)
    return new Uint8Array(await blob.arrayBuffer())
}

async function parse_base64_with_data_url(data: string) {
    // Parse base64 using a trick from https://stackoverflow.com/a/54123275/2854284
    const response = await fetch(`data:application/octet-stream;base64,${data}`)
    if (!response.ok) {
        throw new Error(`Could not parse base64: ${response.status}`)
    }
    return new Uint8Array(await response.arrayBuffer())
}

/** Decode and decompress a resource if required */
export async function process_resource<T>(resource: Resource<T>): Promise<T> {
    if (resource.base64) {
        let data = await parse_base64(resource.data as string)
        if (resource.gzip) {
            data = gunzipSync(data) as Uint8Array<ArrayBuffer>
        }
        return data as T
    }
    return resource.data as T
}

/** Read a response, with optional progress notifications */
export async function read_response(response: Response, progress_callback?: ProgressCallback) {
    if (!response.ok) {
        throw new Error(`Could not fetch ${response.url}, got ${response.status}`)
    }

    if (!progress_callback) {
        return new Uint8Array(await response.arrayBuffer())
    }

    // Read the response, calling the callback with each chunk
    const chunks: Array<[number, Uint8Array]> = []
    let length = 0
    const reader = response.body!.getReader()
    for (;;) {
        const {done, value} = await reader.read()
        if (done) {
            break
        }
        chunks.push([length, value])
        progress_callback(value.length)
        length += value.length
    }

    // Join the chunks together
    const result = new Uint8Array(length)
    for (const [offset, chunk] of chunks) {
        result.set(chunk, offset)
    }
    return result
}

/** Read an uploaded file and return it as a Uint8Array */
export function read_uploaded_file(file: File): Promise<Uint8Array<ArrayBuffer>> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onerror = () => reject(reader.error)
        reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer))
        reader.readAsArrayBuffer(file)
    })
}

interface QueueRequest<T> {
    path: string,
    resolve: (value: T) => void,
}
/** A helper class to handle requesting JSONP resources one at a time */
class JSONPQueue {
    private options: DownloadOptions
    private pending = false
    private queue: QueueRequest<any>[] = []

    constructor(options: DownloadOptions) {
        this.options = options
    }

    private async next<T>() {
        if (this.pending) {
            return
        }

        const next = this.queue.pop()
        if (!next) {
            return
        }

        this.pending = true

        const script_elem = document.createElement('script')
        script_elem.src = next.path

        ;(window as any)[this.options.jsonp!] = async (resource: Resource<T>) => {
            const data = await process_resource(resource)
            next.resolve(data)
            this.pending = false
            script_elem.remove()
            delete (window as any)[this.options.jsonp!]
            this.next()
        }

        document.head.appendChild(script_elem)
    }

    async request<T>(path: string): Promise<T> {
        return new Promise((resolve) => {
            this.queue.push({path, resolve})
            this.next<T>()
        })
    }
}