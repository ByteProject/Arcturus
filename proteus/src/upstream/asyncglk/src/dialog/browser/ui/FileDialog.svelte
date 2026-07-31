<script context="module" lang="ts">
    import type {Filter} from '../browser.js'
    import type {DirEntry, FilesMetadata} from '../interface.js'

    export interface PromptOptions {
        filter?: Filter
        metadata: FilesMetadata
        save: boolean
        submit_label: string,
        title: string
    }
</script>

<script lang="ts">
    import path from 'path-browserify-esm'

    import {DialogController} from '../browser.js'
    import {type AlertMode, ALERT_MODE_CONFIRM, ALERT_MODE_PROMPT} from '../common.js'

    import AlertDialog from './AlertDialog.svelte'
    import BaseDialog from './BaseDialog.svelte'
    import DirTree from './DirTree.svelte'
    import FileList from './FileList.svelte'

    let base_dialog: BaseDialog
    export let controller: DialogController
    export let cur_dir: string = '/usr'
    let cur_direntry: DirEntry[] = []
    let cur_filter: string = ''
    let file_list: FileList
    let filename_input: HTMLTextAreaElement
    let filter: Filter | undefined
    export let metadata: FilesMetadata = {}
    let saving: boolean
    let selected_file: DirEntry | undefined
    let submit_label = ''
    let upload_files: HTMLInputElement

    // Regex from https://stackoverflow.com/a/23522755/2854284
    const is_safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent)

    $: selected_file = (cur_dir, undefined)
    $: cur_direntry = filter_files(cur_dir, cur_filter, metadata)

    $: {
        if (saving && filename_input && selected_file && !selected_file.dir) {
            filename_input.value = selected_file.name
        }
    }

    export function prompt(opts: PromptOptions): Promise<string | null> {
        metadata = opts.metadata
        if (opts.filter?.extensions.join() !== filter?.extensions.join()) {
            if (cur_filter !== '*') {
                cur_filter = opts.filter?.extensions.join() ?? '*'
            }
            filter = opts.filter
            if (!filter) {
                cur_filter = '*'
            }
        }
        cur_direntry = filter_files(cur_dir, cur_filter, metadata)
        saving = opts.save
        submit_label = opts.submit_label
        selected_file = undefined
        const promise = base_dialog.open(opts.title)
        if (saving) {
            selected_file = undefined
            if (filename_input) {
                filename_input.focus()
                filename_input.value = ''
            }
        }
        else {
            selected_file = cur_direntry[0]
            file_list.focus_list()
        }
        return promise.then(res => {
            return typeof res === 'string' ? res : null
        })
    }

    // Filter the metadata down to the current directory
    function filter_files(cur_dir: string, filter: string, metadata: FilesMetadata): DirEntry[] {
        const files: Record<string, DirEntry> = {}
        const working = cur_dir + '/'
        const working_length = working.length
        for (const [full_path, meta] of Object.entries(metadata)) {
            if (full_path.startsWith(working)) {
                const subset_file_path = full_path.substring(working_length)
                const parsed_path = path.parse(subset_file_path)
                if (parsed_path.dir) {
                    if (!parsed_path.dir.includes('/') && !files[parsed_path.dir]) {
                        files[parsed_path.dir] = {
                            dir: true,
                            full_path: working + parsed_path.dir,
                            name: parsed_path.dir,
                        }
                    }
                }
                else {
                    files[parsed_path.base] = {
                        dir: false,
                        full_path,
                        meta,
                        name: parsed_path.base,
                    }
                }
            }
        }
        const files_list = Object.values(files).filter(file => {
            if (file.name.endsWith('.dir')) {
                return false
            }
            if (file.dir || filter === '*') {
                return true
            }
            const filters = filter.split(',')
            for (const ext of filters) {
                if (file.name.endsWith(ext)) {
                    return true
                }
            }
            return false
        }).sort((a, b) => {
            if (a.dir !== b.dir) {
                return +b.dir - +a.dir
            }
            return a.name.localeCompare(b.name)
        })
        return files_list
    }

    async function open_alert_dialog(mode: AlertMode, title: string, message: string, initial?: string): Promise<string | boolean> {
        const dialog = new AlertDialog({
            target: document.body,
            props: {
                initial,
                message,
                mode,
                title,
            },
        })
        const result = await dialog.open()
        await dialog.$destroy()
        return result
    }

    async function check_overwrite(filename: string) {
        // TODO: also check with default extension
        for (const entry of cur_direntry) {
            if (filename === entry.name) {
                return !!(await open_alert_dialog(ALERT_MODE_CONFIRM, 'Overwrite file', `Are you sure you want to overwrite ${filename}?`))
            }
        }
        return true
    }

    function on_add_file() {
        upload_files.click()
    }

    function on_close() {
        base_dialog.resolve(false)
    }

    function on_create_input(node: HTMLTextAreaElement) {
        filename_input = node
        filename_input.focus()
        filename_input.value = ''
    }

    async function on_file_delete(ev: CustomEvent) {
        const file: DirEntry = ev.detail
        if (await open_alert_dialog(ALERT_MODE_CONFIRM, 'Delete file', `Are you sure you want to delete ${file.dir ? 'the folder ' : ''}${file.name}?`)) {
            controller.delete(file)
        }
    }

    function on_file_doubleclicked(ev: CustomEvent) {
        const file: DirEntry = ev.detail
        if (file.dir) {
            cur_dir = file.full_path
        }
        else {
            if (saving) {
                filename_input.value = file.name
            }
            on_submit()
        }
    }

    function on_file_download(ev: CustomEvent) {
        const file: DirEntry = ev.detail
        controller.download(file)
    }

    async function on_file_rename(ev: CustomEvent) {
        const file: DirEntry = ev.detail
        const file_type = file.dir ? 'folder' : 'file'
        const new_file_name = await open_alert_dialog(ALERT_MODE_PROMPT, `Rename ${file_type}`, `Enter new ${file_type} name`, file.name) as string | undefined
        if (new_file_name) {
            if (await check_overwrite(new_file_name)) {
                controller.rename(file, new_file_name)
            }
        }
    }

    function on_input_keydown(ev: KeyboardEvent) {
        if (ev.code === 'Enter') {
            on_submit()
            ev.preventDefault()
        }
    }

    async function on_new_folder() {
        const new_folder_name = await open_alert_dialog(ALERT_MODE_PROMPT, 'New folder', 'Enter new folder name')
        if (new_folder_name) {
            const path = cur_dir + '/' + new_folder_name
            controller.new_folder(path)
        }
    }

    async function on_submit() {
        if (saving) {
            const filename = filename_input.value.trim()
            if (await check_overwrite(filename)) {
                base_dialog.resolve(filename ? cur_dir + '/' + filename : false)
            }
        }
        else {
            base_dialog.resolve(selected_file?.full_path ?? false)
        }
    }

    async function on_upload_files() {
        if (upload_files.files) {
            const files: Record<string, File> = {}
            let have_files = false
            for (const file of upload_files.files) {
                if (await check_overwrite(file.name)) {
                    files[cur_dir + '/' + file.name] = file
                    have_files = true
                }
            }
            if (have_files) {
                controller.upload(files)
            }
        }
        upload_files.value = ''
    }
</script>

<style>
    /* TODO: consider changing to an ID rather than a class, however that would need a regtest-html update */
    :global(dialog.asyncglk_file_dialog) {
        max-height: 500px !important;
        max-width: 700px !important;
    }

    :global(dialog.asyncglk_file_dialog .inner) {
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
    }

    #actions {
        float: right;
        text-align: right;
    }

    .filename {
        display: flex;
    }

    #filename_input {
        flex-grow: 1;
        margin-left: 6px;
        resize: none;
    }

    #filter {
        float: left;
    }

    #dialog_filter {
        min-width: 100px;
    }

    #storage_warning {
        font-size: 80%;
        margin: 0;
        text-align: center;
    }

    #add_file {
        display: none;
    }
</style>

<BaseDialog
    bind:this={base_dialog}
    extra_class="asyncglk_file_dialog {!saving ? 'selecting' : ''}"
    fullscreen
>
    <div>
        <div id="actions">
            <button on:click={on_add_file}>Add file</button>
            <button on:click={on_new_folder}>New Folder</button>
        </div>
        <DirTree bind:cur_dir/>
    </div>
    <FileList
        bind:cur_direntry
        bind:selected_file
        bind:this={file_list}
        on:file_delete={on_file_delete}
        on:file_doubleclicked={on_file_doubleclicked}
        on:file_download={on_file_download}
        on:file_rename={on_file_rename}
    />
    {#if saving}
        <div class="filename">
            <label for="filename_input">File name:</label>
            <textarea id="filename_input" autocapitalize="off" rows="1" on:keydown={on_input_keydown} use:on_create_input></textarea>
        </div>
    {/if}
    <div class="foot uirow">
        <div id="filter">
            {#if filter}
                <label for="dialog_filter">File type:</label>
                <select id="dialog_filter" bind:value={cur_filter}>
                    {#if filter.label}
                        <option value="{filter.extensions.join()}">{filter.label}</option>
                    {:else}
                        <option value="{filter.extensions.join()}">{filter.extensions[0]} file</option>
                    {/if}
                    <option value="*">All files</option>
                </select>
            {/if}
        </div>
        <div>
            <button class="close" on:click={on_close}>Cancel</button>
            <button class="submit" on:click={on_submit}>{submit_label}</button>
        </div>
    </div>
    {#if saving}
        <div id="storage_warning">
            {#if is_safari}
                Warning: Files saved in this browser will be lost if you don't visit again within a week.
            {:else}
                Note: Files saved in this browser may be lost by clearing cookies, or depending on your browser settings.
            {/if}
        </div>
    {/if}
    <input bind:this={upload_files} id="add_file" type="file" multiple on:change={on_upload_files}>
</BaseDialog>