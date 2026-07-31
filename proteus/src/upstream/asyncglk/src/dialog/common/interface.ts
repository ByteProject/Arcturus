/*

Dialog interfaces
=================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import type {FileRef} from '../../common/protocol.js'
import type {GlkOte} from '../../glkote/common/glkote.js'

export type Dialog = AsyncDialog | ClassicSyncDialog | ClassicStreamingDialog

export type AutosaveData = {
    ram?: Array<number> | Uint8Array,
}

export interface DialogOptions {
    dom_prefix?: string,
    GlkOte: GlkOte,
}

export interface AsyncDialog {
    async: true
    /** Delete a file */
    delete(path: string): Promise<void>
    /** Check if a file exists */
    exists(path: string): Promise<boolean>
    /** Get directories */
    get_dirs(): DialogDirectories
    /** Initialise the library */
    init(options: DialogOptions): Promise<void>
    /** Prompt the user for a filename */
    // TODO: support multiple extensions
    prompt(extension: string, save: boolean): Promise<string | null>
    /** Read a file */
    read(path: string): Promise<Uint8Array<ArrayBuffer> | null>
    /** Set storyfile directory and return directories */
    set_storyfile_dir(path: string): Partial<DialogDirectories>
    /** Write some files */
    write(files: Record<string, Uint8Array>): Promise<void>
}

export interface DialogDirectories {
    /** The storyfile directory, used by `garglk_add_resource_from_file` */
    storyfile: string
    /** The system current working directory, used by `glkunix_stream_open_pathname` */
    system_cwd: string
    /** Temp folder */
    temp: string
    /** The Glk "current directory", used by `glk_fileref_create_by_name`/`glk_fileref_create_by_prompt` */
    working: string
}

interface ClassicDialogBase {
    async: false
    /** Clear an autosave */
    autosave_clear?(): Promise<void>,
    /** Read an autosave */
    autosave_read(signature: string): AutosaveData | null,
    /** Save or delete an autosave */
    autosave_write(signature: string, snapshot: AutosaveData | null): void,
    /** Name of this Dialog instance */
    classname: string,
    /** Clean a filename into one that can be used */
    file_clean_fixed_name(filename: string, usage: number): string,
    /** Construct a file ref */
    file_construct_ref(filename?: string, usage?: string, gameid?: string): FileRef,
    /** Construct a file ref for a temporary file */
    file_construct_temp_ref(usage: string): FileRef,
    /** Does the file for a file ref actually exist? */
    file_ref_exists(fref: FileRef): boolean,
    /** Delete a file */
    file_remove_ref(fref: FileRef): void,
    /** Returns libraries this instance has been given */
    getlibrary(name: string): GlkOte | null;
    /** Has this Dialog instance been init()ed? */
    inited(): boolean,
    /** Open a file choosing dialog */
    open(save: boolean, usage: string | null, gameid: string | null | undefined, callback: (fref: FileRef | null) => void): void,
    /** Whether or not this Dialog instance uses the streaming API */
    streaming: boolean,
}

/** Synchronous Dialog library for browsers */
export interface ClassicSyncDialog extends ClassicDialogBase {
    /** Read a file */
    file_read(fref: FileRef): Uint8Array | null,
    /** Write a file */
    file_write(fref: FileRef, content: Uint8Array | '', raw_string?: boolean): boolean,
    /** Initialise the library */
    init(options?: DialogOptions): void,
    streaming: false,
}

/** Streaming Dialog library for Node/Electron */
export interface ClassicStreamingDialog extends ClassicDialogBase {
    /** Open a file */
    file_fopen(fmode: number, fref: FileRef): ClassicFileStream | null,
    /** Initialise the library */
    init_async(options: DialogOptions, callback: () => void): void,
    streaming: true,
}

/** A file stream */
export interface ClassicFileStream {
    /** A reference to a buffer class - except that browsers may load this interface and they don't have Buffer, so just say `any` for now */
    BufferClass: any,
    /** Close this stream */
    fclose(): void,
    /** Flush the stream */
    fflush(): void,
    /** Read bytes from a file
     *
     * Up to buf.length bytes are read into the given buffer. If the len
     * argument is given, up to len bytes are read; the buffer must be at least
     * len bytes long. Returns the number of bytes read, or 0 if end-of-file. */
    fread(buf: Uint8Array, len?: number): number,
    /** Seek to position */
    fseek(pos: number, seekmode: number): void
    /** Get the current stream position */
    ftell(): number,
    /** Write bytes to a file
     *
     * buf.length bytes are written to the stream. If the len argument is
     * given, that many bytes are written; the buffer must be at least len
     * bytes long. Return the number of bytes written. */
    fwrite(buf: Uint8Array, len?: number): number,
}