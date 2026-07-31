/*

Miscellaneous common things
===========================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

export type GlkTypedArray = Uint8Array | Uint32Array
export type GlkTypedArrayConstructor = Uint8ArrayConstructor | Uint32ArrayConstructor

/** A DataView with support for getting and setting arrays and four character codes */
export class FileView extends DataView<ArrayBuffer> {
    constructor(array: Uint8Array<ArrayBuffer>);
    constructor(buffer: ArrayBuffer, byteOffset?: number, byteLength?: number);
    constructor(data: Uint8Array<ArrayBuffer> | ArrayBuffer, byteOffset?: number, byteLength?: number) {
        if (data instanceof Uint8Array) {
            super(data.buffer, data.byteOffset, data.byteLength)
        }
        else {
            super(data, byteOffset, byteLength)
        }
    }

    getFourCC(index: number) {
        return String.fromCharCode(this.getUint8(index), this.getUint8(index + 1), this.getUint8(index + 2), this.getUint8(index + 3))
    }

    getUint8Subarray(index?: number, length?: number): Uint8Array<ArrayBuffer> {
        return new Uint8Array(this.buffer, this.byteOffset + (index || 0), length)
    }

    setFourCC(index: number, text: string) {
        this.setUint8(index, text.charCodeAt(0) )
        this.setUint8(index + 1, text.charCodeAt(1))
        this.setUint8(index + 2, text.charCodeAt(2))
        this.setUint8(index + 3, text.charCodeAt(3))
    }

    setUint8Array(index: number, data: Uint8Array) {
        const subarray = this.getUint8Subarray(index, data.length)
        subarray.set(data)
    }
}

/** Write a Uint32Array as a big-endian Uint8Array */
export function Array_to_BEBuffer(arr: Uint32Array) {
    const buf = new Uint8Array(arr.length * 4)
    const dv = new DataView(buf.buffer)
    for (let i = 0; i < arr.length; i++) {
        dv.setUint32(i * 4, arr[i])
    }
    return buf
}

/** Read a big-endian Uint8Array into a Uint32Array */
export function BEBuffer_to_Array(buf: Uint8Array) {
    const dv = new DataView(buf.buffer, buf.byteOffset, buf.length)
    const arr = new Uint32Array(buf.length / 4)
    for (let i = 0; i < buf.length; i += 4) {
        arr[i / 4] = dv.getUint32(i)
    }
    return arr
}

/** If we can determine that the browser is currently pinch zoomed */
export function is_pinch_zoomed() {
    if (visualViewport) {
        return (visualViewport.scale - 1) > 0.001
    }
    return false
}

export function is_unicode_array(arr: GlkTypedArray) {
    return arr.BYTES_PER_ELEMENT === 4
}

export const utf8decoder = new TextDecoder()
export const utf8encoder = new TextEncoder()