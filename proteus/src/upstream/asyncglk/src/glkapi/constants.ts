/*

GlkApi constants
================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

export const gestalt_Version = 0
export const gestalt_CharInput = 1
export const gestalt_LineInput = 2
export const gestalt_CharOutput = 3
export const gestalt_CharOutput_CannotPrint = 0
export const gestalt_CharOutput_ApproxPrint = 1
export const gestalt_CharOutput_ExactPrint = 2
export const gestalt_MouseInput = 4
export const gestalt_Timer = 5
export const gestalt_Graphics = 6
export const gestalt_DrawImage = 7
export const gestalt_Sound = 8
export const gestalt_SoundVolume = 9
export const gestalt_SoundNotify = 10
export const gestalt_Hyperlinks = 11
export const gestalt_HyperlinkInput = 12
export const gestalt_SoundMusic = 13
export const gestalt_GraphicsTransparency = 14
export const gestalt_Unicode = 15
export const gestalt_UnicodeNorm = 16
export const gestalt_LineInputEcho = 17
export const gestalt_LineTerminators = 18
export const gestalt_LineTerminatorKey = 19
export const gestalt_DateTime = 20
export const gestalt_Sound2 = 21
export const gestalt_ResourceStream = 22
export const gestalt_GraphicsCharInput = 23
export const gestalt_GarglkText = 0x1100

export const keycode_Unknown = 0xffffffff
export const keycode_Left = 0xfffffffe
export const keycode_Right = 0xfffffffd
export const keycode_Up = 0xfffffffc
export const keycode_Down = 0xfffffffb
export const keycode_Return = 0xfffffffa
export const keycode_Delete = 0xfffffff9
export const keycode_Escape = 0xfffffff8
export const keycode_Tab = 0xfffffff7
export const keycode_PageUp = 0xfffffff6
export const keycode_PageDown = 0xfffffff5
export const keycode_Home = 0xfffffff4
export const keycode_End = 0xfffffff3
export const keycode_Func1 = 0xffffffef
export const keycode_Func2 = 0xffffffee
export const keycode_Func3 = 0xffffffed
export const keycode_Func4 = 0xffffffec
export const keycode_Func5 = 0xffffffeb
export const keycode_Func6 = 0xffffffea
export const keycode_Func7 = 0xffffffe9
export const keycode_Func8 = 0xffffffe8
export const keycode_Func9 = 0xffffffe7
export const keycode_Func10 = 0xffffffe6
export const keycode_Func11 = 0xffffffe5
export const keycode_Func12 = 0xffffffe4
// The last keycode is always (0x100000000 - keycode_MAXVAL)
export const keycode_MAXVAL = 28

export const evtype_None = 0
export const evtype_Timer = 1
export const evtype_CharInput = 2
export const evtype_LineInput = 3
export const evtype_MouseInput = 4
export const evtype_Arrange = 5
export const evtype_Redraw = 6
export const evtype_SoundNotify = 7
export const evtype_Hyperlink = 8
export const evtype_VolumeNotify = 9

export const style_Normal = 0
export const style_Emphasized = 1
export const style_Preformatted = 2
export const style_Header = 3
export const style_Subheader = 4
export const style_Alert = 5
export const style_Note = 6
export const style_BlockQuote = 7
export const style_Input = 8
export const style_User1 = 9
export const style_User2 = 10
export const style_NUMSTYLES = 11

export const wintype_AllTypes = 0
export const wintype_Pair = 1
export const wintype_Blank = 2
export const wintype_TextBuffer = 3
export const wintype_TextGrid = 4
export const wintype_Graphics = 5

export const winmethod_Left  = 0x00
export const winmethod_Right = 0x01
export const winmethod_Above = 0x02
export const winmethod_Below = 0x03
export const winmethod_DirMask = 0x0f

export const winmethod_Fixed = 0x10
export const winmethod_Proportional = 0x20
export const winmethod_DivisionMask = 0xf0

export const winmethod_Border = 0x000
export const winmethod_NoBorder = 0x100
export const winmethod_BorderMask = 0x100

export const fileusage_Data = 0x00
export const fileusage_SavedGame = 0x01
export const fileusage_Transcript = 0x02
export const fileusage_InputRecord = 0x03
export const fileusage_TypeMask = 0x0f

export const fileusage_TextMode = 0x100
export const fileusage_BinaryMode = 0x000

export const filemode_Write = 0x01
export const filemode_Read = 0x02
export const filemode_ReadWrite = 0x03
export const filemode_WriteAppend = 0x05
export type FileMode = typeof filemode_Write | typeof filemode_Read | typeof filemode_ReadWrite | typeof filemode_WriteAppend

export const seekmode_Start = 0
export const seekmode_Current = 1
export const seekmode_End = 2

export const stylehint_Indentation = 0
export const stylehint_ParaIndentation = 1
export const stylehint_Justification = 2
export const stylehint_Size = 3
export const stylehint_Weight = 4
export const stylehint_Oblique = 5
export const stylehint_Proportional = 6
export const stylehint_TextColor = 7
export const stylehint_BackColor = 8
export const stylehint_ReverseColor = 9
export const stylehint_NUMHINTS = 10

export const stylehint_just_LeftFlush = 0
export const stylehint_just_LeftRight = 1
export const stylehint_just_Centered = 2
export const stylehint_just_RightFlush = 3

export const imagealign_InlineUp = 1
export const imagealign_InlineDown = 2
export const imagealign_InlineCenter = 3
export const imagealign_MarginLeft = 4
export const imagealign_MarginRight = 5

export const zcolor_Default = -1
export const zcolor_Current = -2