<script context="module" lang="ts">
    import type {DirEntry} from '../interface.js'
</script>

<script lang="ts">
    import FileListItem from './FileListItem.svelte'

    export let cur_direntry: DirEntry[] = []
    let file_list: HTMLDivElement
    export let selected_file: DirEntry | undefined

    export function focus_list() {
        const target_path = selected_file?.full_path || cur_direntry[0]?.full_path
        if (target_path) {
            const buttons = file_list.querySelectorAll('button')
            for (const button of buttons) {
                if (button.dataset.fullpath === target_path) {
                    button.focus()
                    break
                }
            }
        }
    }
</script>

<style>
    #filelist {
        border: 2px solid var(--asyncglk-ui-border);
        flex: 1;
        overflow-y: scroll;
        padding: 6px;
    }
</style>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div id="filelist" role="listbox" tabindex="-1"
    bind:this={file_list}
    on:click={focus_list}
>
    {#each cur_direntry as file (file.full_path)}
        <FileListItem
            data={file}
            bind:selected_file
            on:file_delete
            on:file_doubleclicked
            on:file_download
            on:file_rename
        />
    {/each}
</div>