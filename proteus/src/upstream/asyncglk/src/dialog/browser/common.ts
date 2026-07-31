/*

Common implementations
======================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import type {Provider} from './interface.js'
import AlertDialog from './ui/AlertDialog.svelte'

export const ALERT_MODE_ALERT = 0
export const ALERT_MODE_CONFIRM = 1
export const ALERT_MODE_PROMPT = 2
export type AlertMode = typeof ALERT_MODE_ALERT | typeof ALERT_MODE_CONFIRM | typeof ALERT_MODE_PROMPT

export class NullProvider implements Provider {
    browseable = false
    next: Provider = this
    async delete(_path: string) {}
    async exists(_path: string) {
        return null
    }
    async read(_path: string) {
        return null
    }
    async write(_files: Record<string, Uint8Array>) {}
}

export async function show_alert(title: string, message: string) {
    const alert = new AlertDialog({
        target: document.body,
        props: {
            message,
            mode: ALERT_MODE_ALERT,
            title,
        },
    })
    await alert.open()
    alert.$destroy()
}