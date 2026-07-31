export {}

// Declare Uint8Array.fromBase64 because Typescript 5.9 doesn't know about it
declare global {
    interface Uint8ArrayConstructor {
        fromBase64: (str: string) => Uint8Array<ArrayBuffer>
    }
}