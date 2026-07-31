/*

Format specifications
=====================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/parchment

*/

import {Blorb} from '../upstream/asyncglk/src/index-common.js'

import type {ParchmentOptions, StoryOptions} from './interface.js'

export interface Engine {
    id: string
    load: string[]
    start: (story: StoryOptions, options: ParchmentOptions, requires: any) => void
}

export interface Format {
    blorbable?: boolean
    engines?: Engine[]
    extensions: RegExp
    id: string
}

// Proteus: Z-machine only. Every other format (and the emglken engines
// that ran them) is trimmed out of this fork; ZVM is the one engine.
export const formats: Format[] = [
    {
        id: 'blorb',
        extensions: /\.(blb|blorb)/i,
    },

    {
        id: 'zcode',
        blorbable: true,
        extensions: /\.(zblorb|zlb|z3|z4|z5|z8)/i,
        engines: [
            {
                id: 'zvm',
                load: ['zvm.js'],
                // Proteus: ZVM against the modern launcher interface. The
                // story arrives as a Dialog path (the old engine got raw
                // bytes in requires), and the Glk instance is an AsyncGlk
                // the launcher installs on the options.
                start: async (story: StoryOptions, options, requires) =>
                {
                    const [zvm] = requires

                    const data = (await options.Dialog.read(story.path!))!
                    const vm = new zvm.ZVM()
                    const vm_options = Object.assign({}, options, {
                        vm,
                        // The Glk's file side speaks the classic Dialog;
                        // story loading above used the async one.
                        Dialog: options.classic_dialog ?? options.Dialog,
                        GiDispa: new zvm.ZVMDispatch(),
                    })

                    vm.prepare(data, vm_options)
                    vm_options.Glk!.init(vm_options)
                },
            },
        ],
    },
]

/** Match a format by format ID or file extension */
export function find_format(format?: string | null, path?: string) {
    for (const formatspec of formats) {
        if (formatspec.id === format || (path && formatspec.extensions.test(path))) {
            return formatspec
        }
    }
    throw new Error('Unknown storyfile format')
}

/** Search within a Blorb to find what format is inside
 * Must be passed a Blorb instance */
export function identify_blorb_storyfile_format(blorb: Blorb) {
    const blorb_chunks: Record<string, string> = {
        GLUL: 'glulx',
        ZCOD: 'zcode',
    }
    const chunktype = blorb.get_chunk('Exec', 0)?.chunktype
    if (chunktype && blorb_chunks[chunktype]) {
        return find_format(blorb_chunks[chunktype])
    }
    throw new Error('Unknown storyfile format in Blorb')
}