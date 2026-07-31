/*

Dialog interfaces for the browser
=================================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import type {ProgressCallback} from '../../common/file/interface.js'
import type {AsyncDialog} from '../common/interface.js'

export interface BrowserDialog extends AsyncDialog {
    download(url: string, progress_callback?: ProgressCallback): Promise<string>
    upload(filename: string, data: Uint8Array<ArrayBuffer>, main_file?: boolean): Promise<string>
}

/** A provider handles part of the filesystem, and can cascade down to another provider for files it doesn't handle */
export interface Provider {
    /** Whether we can browse this provider */
    browseable: boolean
    /** A link to the next provider */
    next: Provider
    /** Delete a file */
    delete(path: string): Promise<void>
    /** Check if a file exists */
    exists(path: string): Promise<boolean | null>
    /** Read a file */
    read(path: string): Promise<Uint8Array<ArrayBuffer> | null>
    /** Write some files */
    write(files: Record<string, Uint8Array>): Promise<void>
}

/** A Provider with a few extra functions for browsing */
export interface BrowseableProvider extends Provider {
    /** Get all file metadata */
    metadata(): Promise<FilesMetadata>
    /** Rename a file or folder */
    rename(dir: boolean, path: string, new_name: string): Promise<void>
}

export interface DirEntry {
    dir: boolean
    full_path: string
    meta?: FileData
    name: string
}

export type FilesMetadata = Record<string, FileData>

export interface FileData {
    atime: number
    etag?: string
    'last-modified'?: string
    mtime: number
    path_prefix?: string
    story_id?: string
}