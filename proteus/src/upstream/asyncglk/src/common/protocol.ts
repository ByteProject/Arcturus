/*

The GlkOte protocol
===================

Copyright (c) 2026 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

/** The GlkOte protocol has two parts:
 * 1. GlkOte sends events to GlkApi/RemGlk
 * 2. GlkApi/RemGlk send content updates to GlkOte
*/

/** GlkOte->GlkApi/RemGlk input events */
export type Event = ArrangeEvent | CharEvent | DebugEvent | ExternalEvent | HyperlinkEvent |
    InitEvent | LineEvent | MouseEvent | RedrawEvent | RefreshEvent | SoundEvent | SpecialEvent |
    TimerEvent | VolumeEvent

interface EventBase {
    /** Event code */
    type: string,
    /** Generation number */
    gen: number,
    /** Partial line input values */
    partial?: Record<number, string>,
}

export interface ArrangeEvent extends EventBase {
    /** Event code */
    type: 'arrange',
    metrics: Metrics,
}

/** Character (single key) event */
export interface CharEvent extends EventBase {
    /** Event code */
    type: 'char',
    /** Character that was received */
    value: SpecialKeyCode | string,
    /** Window ID */
    window: number,
}

export type SpecialKeyCode = 'delete' | 'down' | 'end' | 'escape' | 'func1' | 'func2' | 'func3'
    | 'func4' | 'func5' | 'func6' | 'func7' | 'func8' | 'func9' | 'func10' | 'func11' | 'func12'
    | 'home' | 'left' | 'pagedown' | 'pageup' | 'return' | 'right' | 'tab' | 'up'

export interface DebugEvent extends EventBase {
    /** Event code */
    type: 'debug',
    value: string,
}

export interface ExternalEvent extends EventBase {
    /** Event code */
    type: 'external',
    value: any,
}

export interface HyperlinkEvent extends EventBase {
    /** Event code */
    type: 'hyperlink',
    value: number,
    /** Window ID */
    window: number,
}

/** Initilisation event */
export interface InitEvent extends EventBase {
    /** Event code */
    type: 'init',
    /** Generation number */
    gen: 0,
    metrics: Metrics,
    /** Capabilities list */
    support: string[],
}

/** Line (text) event */
export interface LineEvent extends EventBase {
    /** Event code */
    type: 'line',
    /** Terminator key */
    terminator?: TerminatorCode,
    /** Line input */
    value: string,
    /** Window ID */
    window: number,
}

export interface MouseEvent extends EventBase {
    /** Event code */
    type: 'mouse',
    /** Window ID */
    window: number,
    /** Mouse click X */
    x: number,
    /** Mouse click Y */
    y: number,
}

export interface RedrawEvent extends EventBase {
    /** Event code */
    type: 'redraw',
    /** Window ID */
    window?: number,
}

export interface RefreshEvent extends EventBase {
    /** Event code */
    type: 'refresh',
}

export interface SoundEvent extends EventBase {
    /** Event code */
    type: 'sound',
    /** Sound resource ID which finished playing */
    snd: number,
    /** Notification value */
    notify: number,
}

export interface SpecialEvent extends EventBase {
    /** Event code */
    type: 'specialresponse',
    /** Response type */
    response: 'fileref_prompt',
    /** Event value (file reference from Dialog) */
    value: FileRef | null,
}

export type FileRef = {
    content?: string,
    dirent?: string,
    filename: string,
    gameid?: string,
    usage?: string | null,
}

export interface TimerEvent extends EventBase {
    /** Event code */
    type: 'timer',
}

export interface VolumeEvent extends EventBase {
    /** Event code */
    type: 'volume',
    /** Notification value */
    notify: number,
}

/** Screen and font metrics - all potential options */
export interface Metrics {
    /** Buffer character height */
    buffercharheight?: number,
    /** Buffer character width */
    buffercharwidth?: number,
    /** Buffer window margin */
    buffermargin?: number,
    /** Buffer window margin X */
    buffermarginx?: number,
    /** Buffer window margin Y */
    buffermarginy?: number,
    /** Character height (for both buffer and grid windows) */
    charheight?: number,
    /** Character width (for both buffer and grid windows) */
    charwidth?: number,
    /** Graphics window margin */
    graphicsmargin?: number,
    /** Graphics window margin X */
    graphicsmarginx?: number,
    /** Graphics window margin Y */
    graphicsmarginy?: number,
    /** Grid character height */
    gridcharheight?: number,
    /** Grid character width */
    gridcharwidth?: number,
    /** Grid window margin */
    gridmargin?: number,
    /** Grid window margin X */
    gridmarginx?: number,
    /** Grid window margin Y */
    gridmarginy?: number,
    height: number,
    /** Inspacing */
    inspacing?: number,
    /** Inspacing X */
    inspacingx?: number,
    /** Inspacing Y */
    inspacingy?: number,
    /** Margin for all window types */
    margin?: number,
    /** Margin X for all window types */
    marginx?: number,
    /** Margin Y for all window types */
    marginy?: number,
    /** Outspacing */
    outspacing?: number,
    /** Outspacing X */
    outspacingx?: number,
    /** Outspacing Y */
    outspacingy?: number,
    /** Spacing */
    spacing?: number,
    /** Spacing X */
    spacingx?: number,
    /** Spacing Y */
    spacingy?: number,
    width: number,
}

/** Normalised screen and font metrics */
export interface NormalisedMetrics {
    /** Buffer character height */
    buffercharheight: number,
    /** Buffer character width */
    buffercharwidth: number,
    /** Buffer window margin X */
    buffermarginx: number,
    /** Buffer window margin Y */
    buffermarginy: number,
    /** Graphics window margin X */
    graphicsmarginx: number,
    /** Graphics window margin Y */
    graphicsmarginy: number,
    /** Grid character height */
    gridcharheight: number,
    /** Grid character width */
    gridcharwidth: number,
    /** Grid window margin X */
    gridmarginx: number,
    /** Grid window margin Y */
    gridmarginy: number,
    height: number,
    /** Inspacing X */
    inspacingx: number,
    /** Inspacing Y */
    inspacingy: number,
    /** Outspacing X */
    outspacingx: number,
    /** Outspacing Y */
    outspacingy: number,
    width: number,
}

/** GlkApi/RemGlk->GlkOte content updates */
export type Update = ErrorUpdate | PassUpdate | RetryUpdate | StateUpdate

export interface ErrorUpdate {
    /** Update type */
    type: 'error',
    /** Error message */
    message: string,
}

export interface PassUpdate {
    /** Update type */
    type: 'pass',
}

export interface RetryUpdate {
    /** Update type */
    type: 'retry',
}

export interface StateUpdate {
    /** Update type */
    type: 'update',
    /** Library specific autorestore data */
    autorestore?: any,
    /** Content data */
    content?: ContentUpdate[],
    /** Debug output */
    debugoutput?: string[],
    /** Glk is now disabled, ie, it has exited. This is *not* used merely to disable the UI for a Dialog modal. */
    disable?: boolean,
    /** Generation number */
    gen: number,
    /** Windows with active input */
    input?: InputUpdate[],
    /** Background colour for the page margin (ie, outside of the gameport) */
    page_margin_bg?: string | null,
    /** Sound channels (new channels, or new operations) */
    schannels?: SoundChannelUpdate[],
    /** Special input */
    specialinput?: SpecialInput,
    timer?: number | null,
    /** Updates to window (new windows, or changes to their arrangements) */
    windows?: WindowUpdate[],
}

// Update structures

/** Content update */
export type ContentUpdate = BufferWindowContentUpdate | GraphicsWindowContentUpdate | GridWindowContentUpdate

export interface TextualWindowUpdate {
    /** Window ID */
    id: number,
    /** Clear the window */
    clear?: boolean,
    /** Background colour after clearing */
    bg?: string | null,
    /** Foreground colour after clearing */
    fg?: string | null,
}

/** Buffer window content update */
export interface BufferWindowContentUpdate extends TextualWindowUpdate {
    /** text data */
    text?: BufferWindowParagraphUpdate[],
}

/** A buffer window paragraph */
export interface BufferWindowParagraphUpdate {
    /** Append to last input */
    append?: boolean,
    /** Line data */
    content?: LineData[],
    /** Paragraph breaks after floating images */
    flowbreak?: boolean,
}

/** Graphics window content update */
export interface GraphicsWindowContentUpdate {
    /** Window ID */
    id: number,
    /** Operations */
    draw: GraphicsWindowOperation[],
}

/** Graphics window operation */
export type GraphicsWindowOperation = FillOperation | ImageOperation | SetcolorOperation

/** Fill operation */
export interface FillOperation {
    /** Operation code */
    special: 'fill',
    /** CSS color */
    color?: string,
    height?: number,
    width?: number,
    /** X coordinate */
    x?: number,
    /** Y coordinate */
    y?: number,
}

/** Image operation */
export interface ImageOperation {
    /** Operation code */
    special: 'image',
    height: number,
    /** Image number (from Blorb or similar) */
    image?: number,
    width: number,
    /** Image URL */
    url?: string,
    /** X position */
    x: number,
    /** Y position */
    y: number,
}

/** Setcolor operation */
export interface SetcolorOperation {
    /** Operation code */
    special: 'setcolor',
    /** CSS color */
    color: string,
}

/** Grid window content update */
export interface GridWindowContentUpdate extends TextualWindowUpdate {
    /** Lines data */
    lines: {
        /** Line data */
        content?: LineData[],
        /** Line number to update */
        line: number,
    }[],
}

/** Line data */
export type LineData = string | BufferWindowImage | TextRun

/** Buffer window image */
export interface BufferWindowImage {
    /** Run code */
    special: 'image',
    /** Image alignment */
    alignment: 'inlinecenter' | 'inlinedown' | 'inlineup' | 'marginleft' | 'marginright' | undefined,
    /** Image alt text */
    alttext?: string,
    aspectheight: number,
    aspectwidth: number,
    height?: number,
    /** Hyperlink value */
    hyperlink?: number,
    /** Image number */
    image?: number,
    /** Image URL */
    url?: string,
    width?: number,
    widthratio?: number,
    winmaxwidth?: number | null,
}

/** Text run */
export interface TextRun {
    /** Additional CSS styles */
    css_styles?: CSSProperties,
    /** Hyperlink value */
    hyperlink?: number,
    /** Run style */
    style: string,
    /** Run content */
    text: string,
}

/** Windows with active input */
export interface InputUpdate {
    /** Generation number, for when the textual input was first requested */
    gen?: number,
    /** Hyperlink requested */
    hyperlink?: boolean,
    /** Window ID */
    id: number,
    /** Preloaded line input */
    initial?: string,
    /** Maximum line input length */
    maxlen?: number,
    /** Mouse input requested */
    mouse?: boolean,
    /** Line input terminators */
    terminators?: TerminatorCode[],
    /** Textual input type */
    type?: 'char' | 'line',
    /** Grid window coordinate X */
    xpos?: number,
    /** Grid window coordinate Y */
    ypos?: number,
}

export type TerminatorCode = 'escape' | 'func1' | 'func2' | 'func3' | 'func4' | 'func5' | 'func6'
    | 'func7' | 'func8' | 'func9' | 'func10' | 'func11' | 'func12'

export interface SoundChannelUpdate {
    /** Sound channel ID */
    id: number,
    /** Sound channel operations */
    ops?: SoundChannelOperation[],
}

export type SoundChannelOperation = PauseOperation | PlayOperation | SetVolumeOperation | StopOperation | UnpauseOperation

export interface PauseOperation {
    op: 'pause',
}

export interface PlayOperation {
    op: 'play',
    /** Notification value */
    notify?: number,
    /** Number of repeats (default: 1) */
    repeats?: number,
    /** Sound resource ID (from a Blorb) */
    snd: number,
}

export interface SetVolumeOperation {
    op: 'volume',
    /** Duration in milliseconds */
    dur?: number,
    /** Notification value */
    notify?: number,
    /** The volume as a number between 0 and 1 */
    vol: number,
}

export interface StopOperation {
    op: 'stop',
}

export interface UnpauseOperation {
    op: 'unpause',
}

export interface SpecialInput {
    /** Special input type */
    type: 'fileref_prompt',
    /** File mode */
    filemode: FileMode,
    /** File type */
    filetype: FileType,
    /** Game ID */
    gameid?: string,
}

export type FileMode = 'read' | 'readwrite' | 'write' | 'writeappend'
export type FileType = 'command' | 'data' | 'save' | 'transcript'

/** Updates to window (new windows, or changes to their arrangements) */
export interface WindowUpdate {
    /** Graphics height (pixels) */
    graphheight?: number,
    /** Graphics width (pixels) */
    graphwidth?: number,
    /** Grid height (chars) */
    gridheight?: number,
    /** Grid width (chars) */
    gridwidth?: number,
    height: number,
    /** Whether the window should be completely hidden, though could potentially still respond to character events */
    hidden?: boolean,
    /** Window ID */
    id: number,
    /** Left position */
    left: number,
    /** Rock value */
    rock: number,
    /** Window styles */
    styles?: WindowStyles,
    /** Top position */
    top: number,
    /** Type */
    type: 'buffer' | 'graphics' | 'grid',
    width: number,
}

/** CSS Properties
 *
 * CSS property names and values, with a few special property:
 * - `monospace`: sets a run to be monospaced, by adding the class `monospace` to the `span`. Should only be used for `span`s, may misbehave if set on a `div`.
 * - `reverse`: enables reverse mode. If you provide colours then do not pre-reverse them.
 *   Ex: `background-color: #FFF, color: #000, reverse: 1` will be displayed as white text on a black background
 */
export type CSSProperties = Record<string, string | number>

/** CSS styles
 * Keys will usually be for Glk styles, ex: `.Style_header_par` or `.Style_user1`
 * But they can be anything else. Use a blank string to target the window itself.
*/
export type WindowStyles = Record<string, CSSProperties>