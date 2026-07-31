/*

Cheap implementation of AsyncDialog
===================================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import fs from 'fs'
import fs_async from 'fs/promises'
import MuteStream from 'mute-stream'
import os from 'os'
import path from 'path'

import type {AsyncDialog, DialogOptions} from '../common/interface.js'
import {get_stdio, type HackableReadline} from '../../glkote/cheap/stdio.js'

export class CheapAsyncDialog implements AsyncDialog {
    'async' = true as const
    private rl: HackableReadline
    private stdout: MuteStream

    constructor() {
        const cheap_stdio = get_stdio()
        this.rl = cheap_stdio.rl
        this.stdout = cheap_stdio.stdout
    }

    async init(_options: DialogOptions) {
        // Anything to do here?
    }

    async delete(path: string) {
        try {
            fs.unlinkSync(path_posix_to_native(path))
        }
        catch {}
    }

    async exists(path: string) {
        try {
            await fs_async.access(path_posix_to_native(path), fs.constants.F_OK)
            return true
        }
        catch {
            return false
        }
    }

    get_dirs() {
        const cwd = path_native_to_posix(process.cwd())
        return {
            storyfile: cwd,
            system_cwd: cwd,
            temp: path_native_to_posix(os.tmpdir()),
            working: cwd,
        }
    }

    prompt(extension: string, _save: boolean): Promise<string | null> {
        this.stdout.write('\n')
        return new Promise(resolve => {
            this.rl.question('Please enter a file name (without an extension): ', path => {
                resolve(path ? `${path}${extension}` : null)
            })
        })
    }

    read(path: string): Promise<Uint8Array<ArrayBuffer> | null> {
        return fs_async.readFile(path_posix_to_native(path))
            .catch(() => null)
    }

    set_storyfile_dir(path: string) {
        return {
            storyfile: path,
            working: path,
        }
    }

    async write(files: Record<string, Uint8Array>) {
        for (const [path, data] of Object.entries(files)) {
            fs.writeFileSync(path_posix_to_native(path), data, {flush: true})
        }
    }
}

/** Convert a native path to a POSIX path */
export function path_native_to_posix(native_path: string): string {
    if (process.platform === 'win32') {
        let new_path = native_path.replaceAll(path.sep, path.posix.sep)
        if (/^\w:/.test(new_path)) {
            new_path = path.posix.sep + new_path
        }
        return new_path
    }
    else {
        return native_path
    }
}

/** Convert a POSIX path to a native path */
export function path_posix_to_native(posix_path: string): string {
    if (process.platform === 'win32') {
        let new_path = posix_path.replaceAll(path.posix.sep, path.sep)
        if (new_path.startsWith('\\')) {
            new_path = new_path.substring(1)
        }
        return new_path
    }
    else {
        return posix_path
    }
}