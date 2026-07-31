<script lang="ts">
    import '../../../common/ui/common.css'

    import {is_pinch_zoomed} from '../../../common/misc.js'

    let dialog: HTMLDialogElement
    export let extra_class = ''
    /** Whether or not the dialog should use the full viewport in mobile browsers*/
    export let fullscreen = false
    let promise_resolve: (res: string | boolean) => void
    let title = ''

    export async function open(_title: string): Promise<string | boolean> {
        title = _title
        const promise: Promise<string | boolean> = new Promise((resolve) => promise_resolve = resolve)
        dialog.showModal()
        if (visualViewport) {
            visualViewport.addEventListener('resize', on_visualViewport_resize)
            if (fullscreen) {
                // Try to account for this by setting the dialog to the viewport height
                dialog.style.height = visualViewport.height + 'px'
            }
            dialog.style.top = (visualViewport.height - dialog.offsetHeight) / 2 + 'px'
        }
        return promise
    }

    export function resolve(val: string | boolean) {
        dialog.close()
        if (visualViewport) {
            visualViewport.removeEventListener('resize', on_visualViewport_resize)
            dialog.style.height = ''
        }
        promise_resolve(val)
    }

    function on_close() {
        resolve(false)
    }

    function on_visualViewport_resize() {
        // Don't do anything if the window is pinch zoomed
        if (is_pinch_zoomed()){
            return
        }

        // The iOS virtual keyboard does not change the layout height, but it does change the viewport
        if (fullscreen) {
            // Try to account for this by setting the dialog to the viewport height
            dialog.style.height = visualViewport!.height + 'px'
        }
        // And ensure it's centred vertically
        dialog.style.top = (visualViewport!.height - dialog.offsetHeight) / 2 + 'px'
    }
</script>

<style>
    dialog {
        box-sizing: border-box;
        background: var(--asyncglk-ui-bg);
        border-color: var(--asyncglk-ui-border);
        color: var(--asyncglk-ui-fg);
        font-family: sans-serif;
        max-width: 500px;
        min-width: 300px;
        user-select: none;
    }

    dialog.fullscreen {
        height: 100%;
        width: 100%;
    }

    dialog.manually_positioned {
        margin-top: 0;
    }

    @media screen and (max-width: 767px) {
        dialog.fullscreen {
            border: none !important;
            max-height: none !important;
            max-width: none !important;
        }
    }

    dialog::backdrop {
        background: linear-gradient(rgba(64, 64, 64, 25%), rgba(64, 64, 64, 40%));
    }

    .inner > :global(div) {
        margin: 4px 0;
    }

    .head #title {
        font: bold 20px sans-serif;
        margin: 0;
    }

    .head .close {
        background: none;
        border: none;
        padding: 10px;
        position: absolute;
        right: 10px;
        top: 10px;
    }

    dialog :global(.foot) {
        text-align: right;
    }
</style>

<dialog bind:this={dialog}
    class:fullscreen
    class="asyncglk_ui {extra_class}"
    class:manually_positioned={typeof visualViewport !== 'undefined'}
    on:close={on_close}
>
    <div class="inner">
        <div class="head">
            <div id="title">{title}&nbsp;</div>
            <button class="close" aria-label="Close" on:click={on_close}>✖</button>
        </div>
        <slot></slot>
    </div>
</dialog>