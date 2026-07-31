/*

Blorb interfaces
================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

export interface IFFChunk {
    chunktype: string,
    data: Uint8Array<ArrayBuffer>,
    /** Length of the chunk data */
    length: number,
    /** The offset of the chunk data */
    offset_data: number,
    /** The offset of the chunk header */
    offset_header: number,
}

export interface ImageSize {
    height: number,
    width: number,
}

export interface BlorbChunk {
    /** Whether a data chunk is binary */
    binary?: boolean,
    /** The original Chunk ID FourCC */
    chunktype: string,
    data?: Uint8Array<ArrayBuffer>,
    /** Cached image dimensions */
    imagesize?: ImageSize,
    /** External URL for image */
    url?: string,
}

export interface ImageInfo extends BlorbChunk {
    height?: number,
    /** The resource number */
    image: number,
    width?: number,
}

export interface BlorbDataChunk {
    binary: boolean,
    data: Uint8Array,
}

export interface ResourceMapResource {
    altttext?: string,
    format: string,
    height?: number,
    id: number,
    url: string,
    width?: number,
}