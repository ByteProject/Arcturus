#!/usr/bin/env node
/*

Parchment single-file converter
===============================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/parchment

*/

import fs from 'fs/promises'
import path from 'path'
import {fileURLToPath} from 'url'

import minimist from 'minimist'

import {identify_blorb_storyfile_format} from '../common/formats.js'
import {Blorb} from '../upstream/asyncglk/src/index-common.js'

import {process_index_html, type SingleFileOptions} from './index-processing.js'

interface BasicFormat {
    extensions: RegExp
    engine?: string
}

interface Options extends SingleFileOptions {
    terps: string[]
}


const rootpath = path.join(path.dirname(fileURLToPath(import.meta.url)), '..')
const webpath = path.join(rootpath, 'dist/web')

// Presets and options
const base_options: Options = {
    // Proteus: no build date in the page title
    date: 0,
    font: 1,
    gzip: 1,
    single_file: 1,
    terps: [],
}
// Proteus: one preset, one engine.
const presets: Record<string, Options> = {
    dist: {
        terps: ['zvm'],
    },
}

// this is a stripped-down version of src/common/formats.js, so we don't have to import the world
const formats: Record<string, BasicFormat> = {
    blorb: {
        extensions: /\.(blb|blorb)/i,
    },
    zcode: {
        extensions: /\.(zblorb|zlb|z3|z4|z5|z8)/i,
        engine: 'zvm',
    },
}

const argv = minimist(process.argv.slice(2))
const outdir = (argv.out as string) || path.join(webpath, '../single-file')
const preset = (argv.preset as string) || 'dist'
const story_file_path: string | undefined = argv.story_file

if (!presets[preset]) {
    throw new Error(`Unknown preset: ${preset}`)
}
const options = Object.assign({}, base_options, presets[preset])

if (story_file_path) {
    try {
        options.story = {
            data: await fs.readFile(story_file_path) as Uint8Array<ArrayBuffer>,
            filename: path.basename(story_file_path),
        }
    }
    catch (cause: any) {
        throw new Error(`Couldn't read story_file_path ${story_file_path}`, {cause})
    }

    let format = Object.keys(formats).find(format => formats[format].extensions.test(story_file_path))
    if (!format) {
        throw new Error(`Unknown storyfile format ${story_file_path}`)
    }
    if (format === 'blorb') {
        const blorb = new Blorb(options.story.data)
        format = identify_blorb_storyfile_format(blorb).id
    }
    options.story.format = format
    options.terps = [formats[format!].engine!]
}

// Load files
const common_files = [
    'jquery.min.js',
    'ie.js',
    'waiting.gif',
    'web.css',
    'web.js',
    '../fonts/iosevka/iosevka-extended.woff2',
    '../../index.html',
]
const interpreter_files: Record<string, string[]> = {
    bocfel: ['bocfel.wasm', 'bocfel.js'],
    git: ['git.wasm', 'git.js'],
    glulxe: ['glulxe.wasm', 'glulxe.js'],
    hugo: ['hugo.wasm', 'hugo.js'],
    quixe: ['quixe.js'],
    scare: ['scare.wasm', 'scare.js'],
    tads: ['tads.wasm', 'tads.js'],
    zvm: ['zvm.js'],
}

// Get all the files, flattened and deduplicated
const filenames = [...new Set(common_files.concat(options.terps.map(terp => interpreter_files[terp]).flat()))]
const files: Map<string, Uint8Array<ArrayBuffer>> = new Map()
for (const file of filenames) {
    files.set(path.basename(file), await fs.readFile(path.join(webpath, file)) as Uint8Array<ArrayBuffer>)
}

const indexhtml = await process_index_html(options, files)

await fs.mkdir(outdir, {recursive: true})
const outpath = path.join(outdir, 'proteus.html')

// Write it out. Proteus: the html IS the artifact; upstream's zip step
// is gone with its name.
console.log('Creating', outpath)
await fs.writeFile(outpath, indexhtml)
