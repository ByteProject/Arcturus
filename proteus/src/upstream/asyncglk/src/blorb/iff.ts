/*

Interchange File Format
=======================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {FileView} from '../common/misc.js'

import type {IFFChunk} from './interface.js'

/** An Interchange File Format reader and writer */
export class IFF {
    type = ''
    chunks: IFFChunk[] = []

    parse(data: Uint8Array<ArrayBuffer>) {
        const view = new FileView(data)

        // Check this is actually an IFF file
        if (view.getFourCC(0) !== 'FORM') {
            throw new Error('Not an IFF file')
        }

        // Parse the file
        this.type = view.getFourCC(8)
        let i = 12
        // Adrift 5 Blorbs have an incorrect length, so just use the size of the buffer
        //const length = view.getUint32(4) + 8
        const length = data.length
        while (i < length) {
            const chunk_length = view.getUint32(i + 4)
            if (chunk_length < 0 || (chunk_length + i) > length) {
                throw new Error('IFF chunk out of range')
            }
            this.chunks.push({
                data: view.getUint8Subarray(i + 8, chunk_length),
                length: chunk_length,
                offset_data: i + 8,
                offset_header: i,
                chunktype: view.getFourCC(i),
            })
            i += 8 + chunk_length
            if (i % 2) {
                i++
            }
        }
    }

    write(): Uint8Array {
        // First calculate the required buffer length
        let buffer_length = 12
        for (const chunk of this.chunks) {
            buffer_length += 8 + chunk.data.length
            if (buffer_length % 2) {
                buffer_length++
            }
        }

        // Now make the IFF file and return it
        const view = new FileView(new ArrayBuffer(buffer_length))
        view.setFourCC(0, 'FORM')
        view.setUint32(4, buffer_length - 8)
        view.setFourCC(8, this.type)
        let i = 12
        for (const chunk of this.chunks) {
            view.setFourCC(i, chunk.chunktype)
            view.setUint32(i + 4, chunk.data.length)
            view.setUint8Array(i + 8, chunk.data)
            i += 8 + chunk.data.length
            if (i % 2) {
                i++
            }
        }
        return view.getUint8Subarray()
    }
}