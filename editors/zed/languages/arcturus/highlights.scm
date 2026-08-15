; highlights.scm
; part of Arcturus, a programming language and compiler for the Infocom Z-machine.
; Copyright (c) 2026, Stefan Vogt.
; https://github.com/ByteProject/Arcturus
;
; The Zed highlight queries for Arcturus, mirroring the VS Code grammar's
; scopes one to one. The grammar keeps most words as plain identifiers; the
; keyword, attribute, property, and builtin SETS are coloured here, so a new
; library word is one line in this file, never a parser rebuild.

(comment) @comment

(string) @string
(escape_sequence) @string.escape
(number) @number

; ${...} interpolation inside strings: the braces stand out, the content
; reads as embedded code.
(interpolation
  "${" @punctuation.special
  "}" @punctuation.special)
(interpolation (identifier) @variable.special)

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
(words_declaration keyword: _ @property)
(summon "summon" @keyword)
(summon (identifier) @constant)
(summon "granule" @constant)
(player_augmentation "player" @variable.special)
(player_augmentation (identifier) @property)
(when_language "when" @keyword)
(when_language "language" @keyword)
(enhance_redefine "enhance" @keyword)
(enhance_redefine "redefine" @keyword)
(enhance_redefine "verb" @keyword)
(gender) @keyword

; The word-class markers (docs/01 chapter 14): # is the object's trigger,
; > an adjective. The words themselves read as typed vocabulary.
(marker) @punctuation.special
(words_declaration (word_entry (identifier) @string.special))
(words_declaration (word_entry (string) @string.special))

(operator) @operator
(punctuation) @punctuation.delimiter

; Control flow and statement keywords (docs/01 chapters 9 to 13).
((identifier) @keyword
  (#any-of? @keyword
    "if" "else" "while" "for" "each" "switch" "case" "when" "return"
    "stop" "continue" "finish" "death" "alter" "do" "on" "after" "every"
    "append" "insert" "load" "swapping" "checked" "vary" "sequence"
    "mutate" "loop" "let" "change" "now" "move" "add" "remove" "say"
    "show" "zcolor" "par" "to" "from" "award" "you" "reply" "reveal"
    "hide" "grains" "ranks" "ambience" "matrix" "catalog" "game"))

; Word operators.
((identifier) @keyword.operator
  (#any-of? @keyword.operator
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
((identifier) @constant.builtin
  (#any-of? @constant.builtin "true" "false" "nothing"))

; The curated author-facing library services (docs/01, the documented
; surface only), and the grammar slot words of verb lines.
((identifier) @function
  (#any-of? @function
    "teleport" "gain" "convey" "perform" "swap" "worn_count" "list_worn"
    "visible" "reachable" "calculate" "entry" "last" "dice" "position"
    "quote_catalog" "parent_of" "name_contents" "listable_count"
    "press_any_key" "action_id"))

((identifier) @type
  (#any-of? @type
    "thing" "room" "container" "supporter" "door" "character" "held"
    "multi" "scope"))
