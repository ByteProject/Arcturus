// grammar.js
// part of Arcturus, a programming language and compiler for the Infocom Z-machine.
// Copyright (c) 2026, Stefan Vogt.
// https://github.com/ByteProject/Arcturus
//
// The Tree-sitter grammar for .storyarc source, built for HIGHLIGHTING, not
// for full parsing: Arcturus structures itself by indentation, which a
// highlighter does not need. Declaration heads (thing, room, block, words
// with its markers, summon, verb) are structural rules so their names can be
// coloured and outlined; every other word is a plain identifier, and the
// keyword, attribute, property, and builtin SETS are coloured in the Zed
// queries (highlights.scm) with #any-of? predicates, mirroring the VS Code
// grammar one to one. This shape never errors on half-typed source, and a
// new attribute is one query line, not a parser rebuild.

/* eslint-disable arrow-parens */

function sepBy1(sep, rule) {
  return seq(rule, repeat(seq(sep, rule)));
}

module.exports = grammar({
  name: 'arcturus',

  extras: $ => [/[ \t\r\n]/, $.comment],

  word: $ => $.identifier,

  rules: {
    source_file: $ => repeat($._item),

    _item: $ => choice(
      $.object_declaration,
      $.block_declaration,
      $.topic_declaration,
      $.value_declaration,
      $.verb_declaration,
      $.vocabulary_declaration,
      $.words_declaration,
      $.summon,
      $.player_augmentation,
      $.when_language,
      $.enhance_redefine,
      $.gender,
      $.string,
      $.number,
      $.interpolation,
      $.identifier,
      $.operator,
      $.punctuation,
    ),

    // thing lantern / room hallway / kind lamp: the name is optional so a
    // stray keyword mid-line ("if noun is thing") stays error-free.
    object_declaration: $ => prec.right(seq(
      field('keyword', choice('thing', 'room', 'kind')),
      optional(field('name', $.identifier)),
    )),

    block_declaration: $ => prec.right(seq(
      field('keyword', 'block'),
      optional(field('name', $.identifier)),
      // The parameter list is loose on purpose: `alter block` on one line
      // followed by a call on the next must not error, so anything up to
      // the closing paren is admitted.
      optional(seq(
        token.immediate('('),
        repeat(choice($.identifier, $.string, $.number, ',')),
        ')',
      )),
    )),

    topic_declaration: $ => prec.right(seq(
      field('keyword', choice('topic', 'subject')),
      optional(field('name', $.identifier)),
    )),

    value_declaration: $ => prec.right(seq(
      field('keyword', choice('global', 'constant', 'flag', 'counter')),
      optional(field('name', $.identifier)),
    )),

    verb_declaration: $ => prec.right(seq(
      field('keyword', 'verb'),
      sepBy1(',', $.string),
      optional($.verb_mode),
    )),

    verb_mode: $ => 'meta',

    // The language-layer word declarations: their words are strings.
    vocabulary_declaration: $ => prec.right(seq(
      field('keyword', choice(
        'direction', 'particle', 'pronoun', 'chain', 'noise', 'fold',
        'all', 'language',
      )),
      repeat(choice($.identifier, $.string, ',')),
    )),

    // words #chest, box, trunk, >wooden, >heavy: the class markers (docs/01
    // chapter 14). # is the trigger, > an adjective; both stay vocabulary.
    words_declaration: $ => prec.right(seq(
      field('keyword', choice('words', 'plural', 'spans')),
      sepBy1(',', $.word_entry),
    )),

    word_entry: $ => seq(
      optional($.marker),
      choice($.identifier, $.string),
    ),

    marker: $ => token(prec(2, /[#>]/)),

    // summon.statusline / summon whistle.granule / summon "path".
    summon: $ => prec.right(seq(
      'summon',
      optional(choice(
        seq(token.immediate('.'), $.identifier),
        seq($.identifier, token.immediate('.'), 'granule'),
        $.string,
      )),
    )),

    // player.words mich, dich / player.name "..." (docs/01 chapter 4); a
    // bare `player` mid-line stays a plain reference.
    player_augmentation: $ => prec.right(seq(
      'player',
      optional(seq(token.immediate('.'), $.identifier)),
    )),

    // when language "german" (docs/01 chapter 22); a bare `when` is the
    // ordinary handler guard and stays error-free.
    when_language: $ => prec.right(1, seq(
      'when',
      optional(seq('language', $.string)),
    )),

    enhance_redefine: $ => seq(choice('enhance', 'redefine'), 'verb'),

    // The bare German gender line in an object body (docs/01 chapter 21).
    gender: $ => prec(-1, choice('der', 'die', 'das')),

    // Strings carry escapes and ${...} interpolation (docs/01 chapter 15).
    string: $ => seq(
      '"',
      repeat(choice(
        $.escape_sequence,
        $.interpolation,
        token.immediate(prec(1, /[^"\\$]+|\$/)),
      )),
      '"',
    ),

    escape_sequence: $ => token.immediate(/\\["\\$n]/),

    interpolation: $ => seq(
      '${',
      repeat(choice($.identifier, $.number, $.string, $.operator, $.punctuation)),
      '}',
    ),

    comment: $ => token(seq('//', /.*/)),

    number: $ => /-?[0-9]+/,

    identifier: $ => /[A-Za-z\u00c0-\u017f_][A-Za-z0-9\u00c0-\u017f_]*/,

    operator: $ => choice('++', '--', '<=', '>=', '<', '>', '+', '-', '*', '/', '='),

    punctuation: $ => choice(',', '.', '(', ')', ':'),
  },
});
