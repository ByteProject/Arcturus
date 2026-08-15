; highlights.scm
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
; https://github.com/ByteProject/Arcturus
;
; The Zed highlight queries for Arcturus, a full port of the VS Code
; grammar's scoping. ORDER MATTERS: in Zed the later pattern wins, so the
; generic identifier SETS come first and the structural, position-aware
; captures come last, overriding them where context knows better (a word
; inside a words list is vocabulary, whatever else it spells).

; ---- calls first, so statement keywords can override them ----------------

; A call: quote(5, 29), action_id("go"). Known statement words with parens
; (show, say) are recoloured by the keyword set BELOW, matching VS Code.
(call name: (identifier) @function)

; ---- generic word sets (the VS Code lists, one to one) -------------------

; Control flow, statements, and declaration-adjacent keywords.
((identifier) @keyword
  (#any-of? @keyword
    "if" "else" "while" "for" "each" "switch" "case" "when" "return"
    "stop" "continue" "finish" "death" "alter" "do" "on" "after" "every"
    "append" "insert" "load" "swapping" "checked" "vary" "sequence"
    "mutate" "loop" "let" "change" "now" "move" "add" "remove" "say"
    "show" "zcolor" "par" "to" "from" "award" "you" "reply" "reveal"
    "hide" "grains" "ranks" "ambience" "matrix" "catalog" "game" "list"
    "start"
    "is" "not" "and" "or" "holds" "in" "within" "of" "mod"))

; Standard Cosmos boolean attributes (docs/01 chapter 5).
((identifier) @attribute
  (#any-of? @attribute
    "fixed" "scenery" "hidden" "concealed" "wearable" "worn" "lit"
    "edible" "named" "switchable" "binary" "active" "glow" "openable"
    "open" "lockable" "locked" "visited" "clear" "seen" "moved" "animate"
    "an" "feminine" "neutral" "pluribus" "beyond" "scored" "component"
    "shiftable" "restless"))

; Standard value properties, game metadata, and topic modifiers.
((identifier) @property
  (#any-of? @property
    "name" "desc" "intro" "appearance" "capacity" "unseal_with" "article"
    "indefinite" "tag" "arc_image" "title" "headline" "author" "copyright"
    "release" "serial" "UUID" "scoring" "banner" "once" "idle" "about"
    "order" "at" "percent" "points" "meta" "timers"))

; Builtin references (docs/01 chapter 2).
((identifier) @variable.special
  (#any-of? @variable.special
    "self" "player" "here" "noun" "second" "turns" "score" "max_score"
    "way" "grain" "refused" "ambience_rate" "action" "verb_trigger"
    "meta_turn"))

; Language constants.
((identifier) @constant
  (#any-of? @constant "true" "false" "nothing"))

; The curated author-facing library services (the documented surface).
((identifier) @function
  (#any-of? @function
    "teleport" "gain" "convey" "perform" "swap" "worn_count" "list_worn"
    "visible" "reachable" "calculate" "entry" "last" "dice" "position"
    "quote_catalog" "parent_of" "name_contents" "listable_count"
    "press_any_key" "action_id" "clear_screen" "screen_width"
    "screen_height" "print_banner" "status_bar" "confirm_quit" "do_quit"
    "do_restart" "do_save" "do_restore" "list_contents" "reveal_contents"
    "content_listable" "quote_line" "quote_done"))

; Standard kinds and grammar-line slots.
((identifier) @type
  (#any-of? @type
    "thing" "room" "container" "supporter" "door" "character" "held"
    "multi" "scope"))

; The colour words of the zcolor family (support constants in VS Code).
((identifier) @constant
  (#any-of? @constant
    "default" "black" "red" "green" "yellow" "blue" "magenta" "cyan"
    "white"))

; The compass, so exits read at a glance (east tuer).
((identifier) @constant
  (#any-of? @constant
    "north" "south" "east" "west" "northeast" "northwest" "southeast"
    "southwest" "up" "down" "out"))

; ---- tokens --------------------------------------------------------------

(comment) @comment
(number) @number
(uuid) @constant
(operator) @operator
(punctuation) @punctuation.delimiter

; ---- structural captures (position beats spelling) -----------------------

; A dotted chain: say.yellow.par, obj.article, here.(way). The head keeps
; its own set colour; the tail reads as modifiers.
(dotted_name tail: (identifier) @property)

; Declaration heads and their names.
(object_declaration keyword: _ @keyword)
(object_declaration name: (identifier) @type)
(block_declaration keyword: _ @keyword)
(block_declaration name: (identifier) @function)
(topic_declaration keyword: _ @keyword)
(topic_declaration name: (identifier) @function)
(value_declaration keyword: _ @keyword)
(value_declaration name: (identifier) @variable)
(verb_declaration keyword: _ @keyword)
(verb_mode) @keyword
(vocabulary_declaration keyword: _ @keyword)
(data_declaration keyword: _ @keyword)
(data_declaration name: (identifier) @type)
(words_declaration keyword: _ @property)
(summon "summon" @keyword)
(summon (identifier) @attribute)
(summon "granule" @attribute)
(player_augmentation "player" @variable.special)
(player_augmentation (identifier) @property)
(when_language "when" @keyword)
(when_language "language" @keyword)
(enhance_redefine "enhance" @keyword)
(enhance_redefine "redefine" @keyword)
(enhance_redefine "verb" @keyword)
(gender) @keyword

; The word-class markers and the vocabulary they mark (docs/01 chapter 14):
; # is the object's trigger, > an adjective; the words themselves read as
; typed vocabulary, whatever else they spell elsewhere.
(marker) @punctuation.special
(words_declaration (word_entry (identifier) @string.special))
(words_declaration (word_entry (string) @string.special))

; ---- strings last, so nothing bleeds into them ---------------------------

(string) @string
(escape_sequence) @string.escape

; ${...} interpolation: the braces stand out; the article or copula with
; its case tag reads as a keyword (${the:acc noun}), the case tag as its
; modifier, and the interpolated names keep their set colours.
(interpolation
  "${" @punctuation.special
  "}" @punctuation.special)
((interpolation (identifier) @keyword)
  (#any-of? @keyword "the" "The" "a" "an" "A" "An" "is" "Is"))
((interpolation (punctuation) @_colon . (identifier) @property)
  (#eq? @_colon ":"))
