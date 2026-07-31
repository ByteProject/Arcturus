<script lang="ts">
    import {type AlertMode, ALERT_MODE_ALERT, ALERT_MODE_PROMPT} from '../common.js'
    import BaseDialog from './BaseDialog.svelte'

    let base_dialog: BaseDialog
    export let initial: string | undefined = undefined
    export let message: string
    export let mode: AlertMode
    export let title: string
    let val_input: HTMLTextAreaElement

    export function open(): Promise<string | boolean> {
        const promise = base_dialog.open(title)
        if (val_input) {
            val_input.value = initial || ''
            val_input.focus()
        }
        return promise
    }

    function on_cancel() {
        base_dialog.resolve(false)
    }

    function on_create_input(node: HTMLTextAreaElement) {
        val_input = node
        val_input.focus()
        val_input.value = initial || ''
    }

    function on_input_keydown(ev: KeyboardEvent) {
        if (ev.code === 'Enter') {
            on_submit()
            ev.preventDefault()
        }
    }

    function on_submit() {
        if (mode === ALERT_MODE_PROMPT) {
            const val = val_input.value.trim()
            base_dialog.resolve(val || false)
        }
        else {
            base_dialog.resolve(true)
        }
    }
</script>

<style>
    #val_input {
        box-sizing: border-box;
        resize: none;
        width: 100%;
    }
</style>

<BaseDialog bind:this={base_dialog}>
    <p>{message}</p>
    <div>
        {#if mode === ALERT_MODE_PROMPT}
            <textarea id="val_input" autocapitalize="off" rows="1" on:keydown={on_input_keydown} use:on_create_input></textarea>
        {/if}
    </div>
    <div class="foot uirow">
        <div>
            {#if mode !== ALERT_MODE_ALERT}
                <button class="close" on:click={on_cancel}>Cancel</button>
            {/if}
            <!-- svelte-ignore a11y-autofocus -->
            <button class="submit" on:click={on_submit} autofocus>Ok</button>
        </div>
    </div>
</BaseDialog>