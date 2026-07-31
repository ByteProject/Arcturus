/*

AsyncGlk exports
================

Copyright (c) 2024 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

export {Blorb, is_blorb} from './blorb/blorb.js'
export {IFF} from './blorb/iff.js'
export type {BlorbChunk, BlorbDataChunk, IFFChunk, ImageInfo, ImageSize} from './blorb/interface.js'

export * as constants from './common/constants.js'
export type {DownloadOptions, ProgressCallback, Resource, TruthyOption} from './common/file/interface.js'
export {FileView, utf8decoder, utf8encoder} from './common/misc.js'
export * as protocol from './common/protocol.js'

export {filetype_to_extension, filters_for_usage} from './dialog/common/common.js'
export type {AsyncDialog, AutosaveData, ClassicFileStream, ClassicStreamingDialog, ClassicSyncDialog, Dialog, DialogDirectories, DialogOptions} from './dialog/common/interface.js'

export type {BrowserDialog, FileData, FilesMetadata} from './dialog/browser/interface.js'

export type {GiDispa, GlkApi, GlkApiAsync, GlkApiOptions, GlkClassName, GlkFref, GlkObject, GlkSchannel, GlkStream, GlkVM, GlkWindow} from './glkapi/interface.js'
export {AsyncGlk, RefBox, RefStruct} from './glkapi/glkapi.js'

export type {GlkOte, GlkOteOptions, TranscriptRecordingData} from './glkote/common/glkote.js'
export {GlkOteBase} from './glkote/common/glkote.js'