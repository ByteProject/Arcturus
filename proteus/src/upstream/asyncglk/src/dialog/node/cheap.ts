/*

Cheap console implementation of Dialog
======================================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

import MuteStream from 'mute-stream'
import os from 'os'

import type {FileRef} from '../../common/protocol.js'

import {filters_for_usage} from '../common/common.js'
import type {ClassicStreamingDialog} from '../common/interface.js'
import NodeStreamingDialog from './node-streaming.js'
import {get_stdio, type HackableReadline} from '../../glkote/cheap/stdio.js'

export class CheapStreamingDialog extends NodeStreamingDialog implements ClassicStreamingDialog {
    classname = 'CleapDialog'
    private rl: HackableReadline
    private stdout: MuteStream

    constructor() {
        super()

        const cheap_stdio = get_stdio()
        this.rl = cheap_stdio.rl
        this.stdout = cheap_stdio.stdout
    }

    get_user_path() {
        return os.homedir()
    }

    open(_save: boolean, usage: string | null, _gameid: string | null | undefined, callback: (fref: FileRef | null) => void) {
        this.stdout.write('\n')
        this.rl.question('Please enter a file name (without an extension): ', (path) => {
            if (!path) {
                callback(null)
            }
            else {
                callback({
                    filename: path + '.' + filters_for_usage(usage)[0]?.extensions[0],
                    usage: usage,
                })
            }
        })
    }
}