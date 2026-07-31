/*

File processing functions
=========================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

export type ProgressCallback = (bytes: number) => void

export type TruthyOption = boolean | number

export interface DownloadOptions {
    /** Domains to access directly: should always have both Access-Control-Allow-Origin and compression headers */
    direct_domains?: string[],
    /** If files have to be loaded via <script> then the function name to use */
    jsonp?: string,
    /** Path to resources */
    lib_path?: string,
    /** URL of Proxy */
    proxy_url?: string,
    /** Whether to load embedded resources in single file mode */
    single_file?: TruthyOption,
    /** Use the file proxy; if disabled may mean that some files can't be loaded */
    // We could just say to exclude proxy_url instead?
    use_proxy?: boolean | number,
}

export interface Resource<T> {
    base64?: TruthyOption,
    data: T | string,
    gzip?: TruthyOption,
}