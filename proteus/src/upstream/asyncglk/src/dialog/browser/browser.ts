/*

Browser Dialog
==============

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import {saveAs as filesave_saveAs} from 'file-saver'
import path from 'path-browserify-esm'

import {read_uploaded_file} from '../../common/file/browser.js'
import type {DownloadOptions, ProgressCallback} from '../../common/file/interface.js'
import type {DialogDirectories, DialogOptions} from '../common/interface.js'
import {show_alert} from './common.js'
import {DownloadProvider} from './download.js'
import type {BrowseableProvider, BrowserDialog, DirEntry, FilesMetadata, Provider} from './interface.js'
import {WebStorageProvider} from './storage.js'
import FileDialog from './ui/FileDialog.svelte'

export class ProviderBasedBrowserDialog implements BrowserDialog {
    'async' = true as const
    private controller?: DialogController
    private dirs: DialogDirectories = {
        storyfile: '',
        system_cwd: '/',
        temp: '/tmp',
        working: '/usr',
    }
    private downloader: DownloadProvider | undefined
    private providers: (Provider | BrowseableProvider)[] = []

    async init(options: DialogOptions & DownloadOptions): Promise<void> {
        this.downloader = new DownloadProvider(options)
        try {
            this.providers = [
                this.downloader,
                new WebStorageProvider('/tmp', sessionStorage, this.dirs),
                new WebStorageProvider('/', localStorage, this.dirs, true),
            ]
        }
        catch {
            this.providers = [
                this.downloader,
            ]
        }

        for (const [i, provider] of this.providers.entries()) {
            const next = this.providers[i + 1]
            if (next) {
                provider.next = next
            }
            // Set up the Svelte UI
            if (provider.browseable) {
                this.controller = new DialogController(provider as BrowseableProvider)
            }
        }
    }

    async download(url: string, progress_callback?: ProgressCallback): Promise<string> {
        const file_path = await this.downloader!.download(url, progress_callback)
        this.setup(file_path)
        return file_path
    }

    get_dirs(): DialogDirectories {
        return this.dirs
    }

    async prompt(extension: string, save: boolean): Promise<string | null> {
        if (this.controller) {
            return this.controller.prompt(extension, save)
        }
        else {
            await show_alert(`Cannot ${save ? 'save' : 'open'}`, 'LocalStorage is not currently supported in this browser. You should be able to enable it in your browser settings; it may be under a setting about cookies.')
            return null
        }
    }

    set_storyfile_dir(path: string): Partial<DialogDirectories> {
        return {
            storyfile: path,
        }
    }

    async upload(filename: string, data: Uint8Array<ArrayBuffer>, main_file = true) {
        const file_path = await this.downloader!.upload(filename, data)
        if (main_file) {
            this.setup(file_path)
        }
        return file_path
    }

    async delete(path: string) {
        await this.providers[0].delete(path)
    }

    async exists(path: string): Promise<boolean> {
        return !!(await this.providers[0].exists(path))
    }

    async read(path: string): Promise<Uint8Array<ArrayBuffer> | null> {
        return this.providers[0].read(path)
    }

    async write(files: Record<string, Uint8Array>) {
        await this.providers[0].write(files)
    }

    private setup(file_path: string) {
        const parsed_path = path.parse(file_path)
        this.dirs.storyfile = parsed_path.dir
        this.dirs.working = '/usr/' + parsed_path.name.toLowerCase().trim()
        this.controller?.update_working(this.dirs.working)
    }
}

/** Controller for FileDialog */
export class DialogController {
    private dialog: FileDialog
    private metadata: FilesMetadata = {}
    private provider: BrowseableProvider

    constructor(provider: BrowseableProvider) {
        this.dialog = new FileDialog({
            target: document.body,
            props: {
                controller: this,
            },
        })
        this.provider = provider
    }

    async prompt(extension: string, save: boolean): Promise<string | null> {
        const action = save ? 'Save' : 'Open'
        const filter = extension_to_filter(extension)
        this.metadata = await this.provider.metadata()
        return this.dialog.prompt({
            filter,
            metadata: this.metadata,
            save,
            submit_label: action,
            title: `${action} a ${filter?.title}`,
        })
    }

    async delete(file: DirEntry) {
        if (file.dir) {
            const dir_path = file.full_path + '/'
            for (const path of Object.keys(this.metadata)) {
                if (path.startsWith(dir_path)) {
                    delete this.metadata[path]
                    await this.provider.delete(path)
                }
            }
        }
        else {
            await this.provider.delete(file.full_path)
            delete this.metadata[file.full_path]
        }
        await this.update()
    }

    async download(file: DirEntry) {
        const data = (await this.provider.read(file.full_path))!
        filesave_saveAs(new Blob([data]), file.name)
    }

    async new_folder(path: string) {
        // Consider making this a function of the provider, to better support providers which can store actual empty folders
        const now = Date.now()
        const dir_path = path + '/.dir'
        await this.provider.write({[dir_path]: new Uint8Array(0)})
        this.metadata[dir_path] = {
            atime: now,
            mtime: now,
        }
        this.dialog.$set({
            cur_dir: path,
            metadata: this.metadata,
        })
    }

    async rename(file: DirEntry, new_file_name: string) {
        const parsed_path = path.parse(file.full_path)
        const new_path = parsed_path.dir + '/' + new_file_name
        await this.provider.rename(file.dir, file.full_path, new_path)
        await this.update(true)
    }

    async update(refresh: boolean = false) {
        if (refresh) {
            this.metadata = await this.provider.metadata()
        }
        this.dialog.$set({metadata: this.metadata})
    }

    update_working(path: string) {
        this.dialog.$set({cur_dir: path})
    }

    async upload(files: Record<string, File>) {
        const now = Date.now()
        const read_files: Record<string, Uint8Array> = {}
        for (const [path, data] of Object.entries(files)) {
            read_files[path] = await read_uploaded_file(data)
            this.metadata[path] = {
                atime: now,
                mtime: now,
            }
        }
        await this.provider.write(read_files)
        await this.update()
    }
}

export interface Filter {
    extensions: string[]
    label?: string
}

function extension_to_filter(extension: string): (Filter & {title: string}) | undefined {
    switch (extension) {
        case '.glkdata':
            return {
                extensions: ['.glkdata'],
                label: 'Data file',
                title: 'data file',
            }
        case '.glksave':
            return {
                extensions: ['.glksave', '.sav'],
                label: 'Save file',
                title: 'savefile',
            }
        case '.txt':
            return {
                extensions: ['.txt'],
                label: 'Transcript or log',
                title: 'log',
            }
    }
}