/*

Blorb Files and functions
=========================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {unescape} from 'lodash-es'

import {FileView, utf8decoder} from '../common/misc.js'

import {IFF} from './iff.js'
import type {BlorbChunk, BlorbDataChunk, ImageInfo, ImageSize, ResourceMapResource} from './interface.js'

const giblorb_ID_AIFF = 'AIFF'
const giblorb_ID_BINA = 'BINA'
const giblorb_ID_Data = 'Data'
const giblorb_ID_FORM = 'FORM'
const giblorb_ID_JPEG = 'JPEG'
const giblorb_ID_MP3_ = 'MP3 '
const giblorb_ID_OGGV = 'OGGV'
const giblorb_ID_PNG_ = 'PNG '

type BlorbUsage = 'Data' | 'Exec' | 'Pict' | 'Snd '

const resource_to_chunktype: Record<string, string> =  {
    AIFF: giblorb_ID_AIFF,
    JPEG: giblorb_ID_JPEG,
    MP3: giblorb_ID_MP3_,
    'Ogg Vorbis': giblorb_ID_OGGV,
    PNG: giblorb_ID_PNG_,
}

function resource_format_to_usage(resource_format: string): BlorbUsage {
    if (resource_format === 'JPEG' || resource_format === 'PNG') {
        return 'Pict'
    }
    return 'Snd '
}

export class Blorb {
    classname = 'Blorb'
    /** Chunks are indexed with "USE:NUMBER" keys */
    chunks: BlorbChunk[] = []
    private coverimagenum?: number
    //private debugdata?: Uint8Array
    private is_inited = false
    private metadata: Record<string, string> = {}
    private resources: Record<string, BlorbChunk> = {}

    // The original Blorb library requires you to call init(), but I think it's better to pass the data into the constructor
    constructor(data?: Uint8Array<ArrayBuffer>);
    constructor(data?: ResourceMapResource[]);
    constructor(data?: Uint8Array<ArrayBuffer> | ResourceMapResource[]) {
        if (data) {
            this.init(data as any)
        }
    }

    init(data: Uint8Array<ArrayBuffer>): void;
    init(data: ResourceMapResource[]): void;
    init(data: Uint8Array<ArrayBuffer> | ResourceMapResource[]) {
        if (this.is_inited) {
            return
        }
        if (data instanceof Uint8Array) {
            const iff = new IFF()
            iff.parse(data)
            if (iff.type !== 'IFRS') {
                throw new Error('Not a Blorb file')
            }

            // Parse the resource index chunk
            const ridx_chunk = iff.chunks[0]
            if (ridx_chunk.chunktype !== 'RIdx') {
                throw new Error('Malformed blorb: chunk 1 is not RIdx')
            }
            const resources_by_offset: Record<number, string> = {}
            const ridx_view = new FileView(ridx_chunk.data)
            let i = 4
            while (i < ridx_view.byteLength) {
                const usage = ridx_view.getFourCC(i)
                const resource_number = ridx_view.getUint32(i + 4)
                const resource_offset = ridx_view.getUint32(i + 8)
                i += 12
                resources_by_offset[resource_offset] = usage + ':' + resource_number
            }

            // Process the chunks
            for (const iff_chunk of iff.chunks) {
                const chunk: BlorbChunk = {
                    chunktype: iff_chunk.chunktype,
                    data: iff_chunk.data,
                }
                // For FORM chunks we set the chunk type to the internal type and the data to the internal
                if (chunk.chunktype === giblorb_ID_FORM) {
                    const view = new FileView(data)
                    chunk.chunktype = view.getFourCC(iff_chunk.offset_data)
                    chunk.data = view.getUint8Subarray(iff_chunk.offset_header, iff_chunk.length + 8)
                }
                // Check if this chunk is a resource
                const resource_key = resources_by_offset[iff_chunk.offset_header]
                if (resource_key) {
                    this.resources[resource_key] = chunk
                    if (resource_key.startsWith(giblorb_ID_Data)) {
                        if (chunk.chunktype === giblorb_ID_BINA || iff_chunk.chunktype === giblorb_ID_FORM) {
                            chunk.binary = true
                        }
                    }
                }
                // Process other chunks
                switch (iff_chunk.chunktype) {
                    /*case 'Dbug': {
                        // Process the debug chunk
                        this.debugdata = iff_chunk.data
                        break
                    }*/
                    case 'Fspc': {
                        // Process the frontispiece chunk
                        const view = new FileView(iff_chunk.data)
                        this.coverimagenum = view.getUint32(0)
                        break
                    }
                    case 'IFmd': {
                        const xml = utf8decoder.decode(iff_chunk.data)
                        // Normally parsing XML with regexes is super unwise, but the Babel spec places enough restrictions on the metadata XML that this should be safe
                        const bibliographic = /<bibliographic>(.+)<\/bibliographic>/is.exec(xml)
                        const entry_pattern = /<(\w+)>(.+)<\/\1>/gi
                        const linebreak_pattern = /<br\/>/g
                        const whitespace_pattern = /\s+/g
                        if (bibliographic) {
                            let result
                            while ((result = entry_pattern.exec(bibliographic[1]))) {
                                const tag = result[1].toLowerCase()
                                let content = result[2].replace(whitespace_pattern, ' ')
                                if (tag === 'description') {
                                    content = content.replace(linebreak_pattern, '\n')
                                }
                                this.metadata[tag] = unescape(content)
                            }
                        }
                        break
                    }
                    /*case 'RDes': {
                        // Process the resource description chunk
                        const view = new FileView(iff_chunk.data)
                        let i = 4
                        while (i < view.byteLength) {
                            const usage = BLORB_RESOURCE_INDEX_USAGES[view.getFourCC(i)]
                            const resource_number = view.getUint32(i + 4)
                            const text_length = view.getUint32(i + 8)
                            const chunk = this.chunks[`${usage}:${resource_number}`]
                            if (chunk) {
                                chunk.alttext = utf8decoder.decode(view.getUint8Subarray(i + 12, text_length))
                            }
                            i += 12 + text_length
                        }
                        break
                    }*/
                }
                this.chunks.push(chunk)
            }
        }
        // Parse the new Inform 7 resource map
        else if (Array.isArray(data)) {
            for (const resource of data) {
                const chunk: BlorbChunk = {
                    chunktype: resource_to_chunktype[resource.format],
                    url: resource.url,
                }
                if (resource.width) {
                    chunk.imagesize = {
                        height: resource.height!,
                        width: resource.width,
                    }
                }
                this.chunks.push(chunk)
                this.resources[resource_format_to_usage(resource.format) + ':' + resource.id] = chunk
            }
        }
        else {
            throw new Error('Unsupported Blorb.init data format')
        }

        this.is_inited = true
    }

    getlibrary(): null {
        return null
    }

    get_chunk(usage: BlorbUsage, num: number): BlorbChunk | null {
        return this.resources[usage + ':' + num] || null
    }

    get_cover_pict(): number | null {
        return this.coverimagenum ?? null
    }

    get_data_chunk(num: number): BlorbDataChunk | null {
        const chunk = this.resources['Data:' + num]
        if (!chunk?.data) {
            return null
        }
        return {
            binary: chunk.binary!,
            data: chunk.data,
        }
    }

    /*get_debug_info(): Uint8Array | undefined {
        return this.debugdata
    }*/

    /** Return the game file chunk, or null if there isn't one.
     * If type is provided (GLUL or ZCOD) then the game file is checked to ensure it matches
     */
    get_exec_data(gametype?: 'GLUL' | 'ZCOD'): Uint8Array | null {
        const chunk = this.resources['Exec:0']
        if (!chunk?.data || (gametype && chunk.chunktype !== gametype)) {
            return null
        }
        return chunk.data
    }

    get_image_info(num: number): ImageInfo | null {
        const chunk = this.resources['Pict:' + num]
        if (!chunk) {
            return null
        }

        // Try to extract the image sizes
        if (!chunk.imagesize && chunk.data) {
            if (chunk.chunktype === giblorb_ID_JPEG) {
                chunk.imagesize = get_jpeg_dimensions(chunk.data)
            }
            else if (chunk.chunktype === giblorb_ID_PNG_) {
                chunk.imagesize = get_png_dimensions(chunk.data)
            }
        }

        const img: ImageInfo = Object.assign({image: num}, chunk)
        if (img.imagesize) {
            img.height = img.imagesize.height
            img.width = img.imagesize.width
        }
        return img
    }

    get_image_url(num: number): string | null {
        const chunk = this.resources['Pict:' + num]
        if (!chunk) {
            return null
        }

        if (chunk.url) {
            return chunk.url
        }

        if ((chunk.chunktype === giblorb_ID_JPEG || chunk.chunktype === giblorb_ID_PNG_) && chunk.data) {
            chunk.url = URL.createObjectURL(new Blob([chunk.data], {type: `image/${chunk.chunktype === giblorb_ID_JPEG ? 'jpeg' : 'png'}`}))
            return chunk.url
        }

        return null
    }

    get_metadata(field: string): string {
        return this.metadata[field]
    }

    inited(): boolean {
        return this.is_inited
    }
}

export function is_blorb(data: Uint8Array<ArrayBuffer>): boolean {
    const view = new FileView(data)
    return view.getFourCC(0) === 'FORM' && view.getFourCC(8) === 'IFRS'
}

function get_jpeg_dimensions(data: Uint8Array<ArrayBuffer>): ImageSize | undefined {
    const view = new FileView(data)
    let i = 0
    while (i < view.byteLength) {
        if (view.getUint8(i) !== 0xFF) {
            return
        }
        while (view.getUint8(i) === 0xFF) {
            i++
        }
        const marker = view.getUint8(i++)
        // Markers with no data
        if (marker === 0x01 || (marker >= 0xD0 && marker <= 0xD9)) {
            continue
        }
        const chunklength = view.getUint16(i)
        if (marker >= 0xC0 && marker <= 0xCF && marker !== 0xC8) {
            if (chunklength < 7) {
                // SOF block is too small
                return
            }
            return {
                height: view.getUint16(i + 3),
                width: view.getUint16(i + 5),
            }
        }
        i += chunklength
    }
}

function get_png_dimensions(data: Uint8Array<ArrayBuffer>): ImageSize | undefined {
    const view = new FileView(data)
    if (view.getFourCC(0) !== '\x89PNG') {
        return
    }

    let i = 8
    while (i < view.byteLength) {
        const chunklength = view.getUint32(i)
        const chunktype = view.getFourCC(i + 4)
        i += 8
        if (chunktype === 'IHDR') {
            return {
                height: view.getInt32(i + 4),
                width: view.getInt32(i),
            }
        }
        // Skip CRC
        i += chunklength + 4
    }
}