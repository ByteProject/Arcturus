<script lang="ts">
    export let cur_dir: string
    let dir_tree: string[]

    $: dir_tree = cur_dir.substring(1).split('/')

    function on_click(ev: MouseEvent) {
        const target = ev.target as HTMLButtonElement
        cur_dir = target.dataset.path!
    }
</script>

<style>
    #dirtree {
        display: flex;
        flex-wrap: wrap;
        line-height: 28px;
    }

    button {
        padding: 0;
    }

    span.slash {
        padding: 0 5px;
    }
</style>

<div id="dirtree">
    {#each dir_tree as dir, i (dir)}
        {#if i !== 0}
            <span class="slash">&nbsp;/&nbsp;</span>
        {/if}
        {#if dir_tree[i + 1]}
            <span><button
                class="flat"
                data-path={'/' + dir_tree.slice(0, i + 1).join('/')}
                on:click={on_click}
            >{dir === 'usr' ? 'My files' : dir}</button></span>
        {:else}
            <span>{dir === 'usr' ? 'My files' : dir}</span>
        {/if}
    {/each}
</div>