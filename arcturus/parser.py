# parser.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The Arcturus parser.

Recursive descent over the token stream from the lexer, producing the AST in
ast.py. Declarations and statements are parsed top-down; expressions use
precedence-climbing. The grammar followed is docs/01 appendix B, with the
runtime constructs (grains attach, scheduling) from docs/02.

The parser records structure only. The is-as-property-test versus
is-as-equality decision, scope, the property/attribute storage choice, and
dead-code elimination are semantic concerns handled in later milestones.
"""

from __future__ import annotations

import re

from . import ast
from . import tokens as T
from .errors import ArcError
from .lexer import RawInterp, tokenize
from .prelude import _ZCOLOURS

# Articles recognized at the start of an interpolation (docs/01 section 16).
_ARTICLES = frozenset({"a", "an", "the", "A", "An", "The"})

# A leading article, an optional :case tag, and the expression that follows. The
# article alternatives are ordered longest-first so "an" wins over "a". The tag
# (:acc, :dat, and so on) is only read by a case-inflected language layer; English
# and Spanish ignore it. A real expression must follow, so ${the} alone is left as
# a plain variable read, matching the earlier behaviour.
_ARTICLE_CASE_RE = re.compile(
    r"^\s*(An|The|an|the|A|a)(?::([A-Za-z]+))?\s+(\S.*)$",
    re.DOTALL,
)

_META_KEYS = frozenset(
    {"title", "headline", "author", "release", "serial", "UUID", "start"}
)

_GRAMMAR_SLOTS = frozenset({"held", "multi", "text", "direction"})


class Parser:
    def __init__(self, toks: list[T.Token], filename: str = "<source>") -> None:
        self.toks = toks
        self.filename = filename
        self.i = 0

    # -- token cursor ------------------------------------------------------

    @property
    def cur(self) -> T.Token:
        return self.toks[self.i]

    def _at(self, offset: int = 0) -> T.Token:
        j = self.i + offset
        if j >= len(self.toks):
            return self.toks[-1]
        return self.toks[j]

    def advance(self) -> T.Token:
        tok = self.toks[self.i]
        if self.i < len(self.toks) - 1:
            self.i += 1
        return tok

    def check(self, kind: str) -> bool:
        return self.cur.kind == kind

    def check_kw(self, word: str) -> bool:
        return self.cur.is_kw(word)

    def check_op(self, sym: str) -> bool:
        return self.cur.is_op(sym)

    def accept_kw(self, word: str) -> bool:
        if self.cur.is_kw(word):
            self.advance()
            return True
        return False

    # -- errors ------------------------------------------------------------

    def _error(self, message: str, tok: T.Token | None = None) -> ArcError:
        tok = tok or self.cur
        return ArcError(message, tok.line, tok.column, self.filename)

    @staticmethod
    def _describe(tok: T.Token) -> str:
        if tok.kind == T.EOF:
            return "end of file"
        if tok.kind == T.NEWLINE:
            return "end of line"
        if tok.kind in (T.INDENT, T.DEDENT):
            return "a change in indentation"
        if tok.kind in (T.KW, T.OP):
            return f"'{tok.value}'"
        return repr(tok.value)

    def expect(self, kind: str, what: str | None = None) -> T.Token:
        if self.cur.kind == kind:
            return self.advance()
        raise self._error(f"expected {what or kind}, got {self._describe(self.cur)}")

    def expect_kw(self, word: str) -> T.Token:
        if self.cur.is_kw(word):
            return self.advance()
        raise self._error(f"expected '{word}', got {self._describe(self.cur)}")

    def expect_op(self, sym: str) -> T.Token:
        if self.cur.is_op(sym):
            return self.advance()
        raise self._error(f"expected '{sym}', got {self._describe(self.cur)}")

    def expect_name(self, what: str = "a name") -> T.Token:
        if self.cur.kind == T.NAME:
            return self.advance()
        raise self._error(f"expected {what}, got {self._describe(self.cur)}")

    def _kind_name(self, what: str) -> str:
        """A kind reference: an ordinary identifier or one of the builtin kinds
        `thing` and `room`, which are keywords (docs/01 section 5)."""
        if self.cur.kind == T.NAME:
            return self.advance().value
        if self.cur.kind == T.KW and self.cur.value in ("thing", "room"):
            return self.advance().value
        raise self._error(f"expected {what}, got {self._describe(self.cur)}")

    def _object_ref_name(self, what: str) -> str:
        """A name that refers to an object: an ordinary identifier or one of the
        builtin object keywords (player, here, self, noun, second)."""
        if self.cur.kind == T.NAME:
            return self.advance().value
        if self.cur.kind == T.KW and self.cur.value in (
            "player",
            "here",
            "self",
            "noun",
            "second",
        ):
            return self.advance().value
        raise self._error(f"expected {what}, got {self._describe(self.cur)}")

    def expect_newline(self) -> None:
        self.expect(T.NEWLINE, "end of line")

    # -- entry -------------------------------------------------------------

    def parse(self) -> ast.Program:
        decls: list[ast.Decl] = []
        while not self.check(T.EOF):
            if self.check(T.NEWLINE):
                self.advance()
                continue
            decls.append(self.parse_toplevel())
        return ast.Program(decls)

    def parse_toplevel(self) -> ast.Decl:
        t = self.cur
        if t.is_kw("game"):
            return self.parse_game()
        if t.is_kw("summon"):
            return self.parse_summon()
        if t.is_kw("kind"):
            return self.parse_kind()
        if t.is_kw("room") or t.is_kw("thing"):
            return self.parse_object()
        if t.is_kw("verb"):
            return self.parse_verb()
        if t.is_kw("global"):
            return self.parse_global()
        if t.is_kw("constant"):
            return self.parse_constant()
        if t.is_kw("block"):
            return self.parse_block_decl()
        if t.is_kw("on"):
            return self.parse_handler()
        if t.kind == T.NAME and t.value == "direction":
            return self.parse_direction()
        if t.kind == T.NAME and t.value == "particle":
            return self.parse_particle()
        if t.kind == T.NAME and t.value == "pronoun":
            return self.parse_pronoun()
        if t.kind == T.NAME and t.value == "chain":
            return self.parse_chain()
        if t.kind == T.NAME and t.value == "all" and self._at(1).kind == T.STRING:
            return self.parse_all()
        if t.kind == T.NAME and t.value == "noise" and self._at(1).kind == T.STRING:
            return self.parse_noise()
        if t.value == "player" and t.kind in (T.NAME, T.KW):
            nxt = self._at(1)
            if nxt.kind == T.OP and nxt.value == ".":
                # player.words Olivia, Lund / player.desc "..." / player.desc
                # block: augment the seeded player object (docs/01 section 5a).
                line = t.line
                self.advance()
                self.advance()
                return ast.PlayerDecl(self.parse_property(), line)
        if t.kind == T.NAME and t.value == "language":
            return self.parse_language_decl()
        if t.kind == T.NAME:
            return self.parse_grains_attach()
        raise self._error(
            f"expected a top-level declaration, got {self._describe(t)}"
        )

    # -- indented bodies ---------------------------------------------------

    def parse_stmt_block(self) -> list[ast.Stmt]:
        """An indented block of statements (handler, control flow, computed
        property, block routine)."""
        self.expect(T.INDENT, "an indented block")
        stmts: list[ast.Stmt] = []
        while not self.check(T.DEDENT):
            if self.check(T.EOF):
                raise self._error("unexpected end of file inside an indented block")
            if self.check(T.NEWLINE):
                self.advance()
                continue
            stmts.append(self.parse_statement())
        self.expect(T.DEDENT)
        return stmts

    def parse_members(self) -> list[ast.Member]:
        self.expect(T.INDENT, "an indented body")
        members: list[ast.Member] = []
        while not self.check(T.DEDENT):
            if self.check(T.EOF):
                raise self._error("unexpected end of file inside an object body")
            if self.check(T.NEWLINE):
                self.advance()
                continue
            members.append(self.parse_member())
        self.expect(T.DEDENT)
        return members

    # -- game block --------------------------------------------------------

    def parse_game(self) -> ast.GameBlock:
        line = self.cur.line
        self.expect_kw("game")
        self.expect_newline()
        self.expect(T.INDENT, "the game metadata block")
        meta: list[ast.MetaLine] = []
        while not self.check(T.DEDENT):
            if self.check(T.NEWLINE):
                self.advance()
                continue
            meta.append(self.parse_meta_line())
        self.expect(T.DEDENT)
        return ast.GameBlock(meta, line)

    def parse_meta_line(self) -> ast.MetaLine:
        tok = self.cur
        # `banner false`: stop the automatic banner at start; the game prints it
        # later (or never) with print_banner(). Not a reserved word, so it is
        # accepted here as a plain name.
        if tok.kind == T.NAME and tok.value == "banner":
            self.advance()
            if not (self.cur.kind == T.KW and self.cur.value == "false"):
                raise self._error(
                    "banner takes only false (the banner is on by default)"
                )
            self.advance()
            self.expect_newline()
            return ast.MetaLine("banner", False, tok.line)
        if tok.kind != T.KW or tok.value not in _META_KEYS:
            raise self._error(
                f"expected a game metadata key (title, headline, author, "
                f"release, serial, UUID, start), got {self._describe(tok)}"
            )
        key = tok.value
        self.advance()
        if key in ("title", "headline", "author", "serial"):
            value: object = self._plain_text(self.expect(T.STRING, "a string"))
        elif key == "release":
            value = self.expect(T.NUMBER, "a number").value
        elif key == "UUID":
            value = self.expect(T.UUID, "a UUID").value
        else:  # start
            value = self.expect_name("a room name").value
        self.expect_newline()
        return ast.MetaLine(key, value, tok.line)

    # -- summon ------------------------------------------------------------

    def parse_summon(self) -> ast.Summon:
        line = self.cur.line
        self.expect_kw("summon")
        # summon.statusline - the dotted feature form (the bundled copy, always).
        if self.check_op("."):
            self.advance()
            feature = self.expect_name("a feature name").value
            arg = None
            if self.check(T.STRING):
                arg = self._plain_text(self.advance())
            self.expect_newline()
            return ast.Summon(feature, form="feature", arg=arg, line=line)
        # summon "x.granule" - the quoted path form (an explicit file).
        if self.check(T.STRING):
            target = self._plain_text(self.advance())
            self.expect_newline()
            return ast.Summon(target, form="path", line=line)
        # summon statusline.granule - the bareword filename form. Reassemble the
        # dotted name (statusline + . + granule) the lexer split into tokens.
        if self.check(T.NAME):
            parts = [self.advance().value]
            while self.check_op("."):
                self.advance()
                parts.append(self.expect_name("a granule filename").value)
            self.expect_newline()
            return ast.Summon(".".join(parts), form="name", line=line)
        raise self._error(
            "expected a feature name, a granule filename, or a quoted path after "
            "'summon'"
        )

    # -- object and kind ---------------------------------------------------

    def parse_object(self) -> ast.ObjectDecl:
        line = self.cur.line
        category = self.advance().value  # room or thing
        name = self.expect_name("an object name").value
        parent = None
        location = None
        if self.accept_kw("of"):
            parent = self._kind_name("a kind name")
        spans: list[str] = []
        if self.accept_kw("in"):
            location = self._object_ref_name("a location name")
            # `in hall, livingroom` or `in hall and livingroom`: the extra rooms
            # are spanned (the object lives in the first and is in scope in all).
            while self.check_op(",") or self.check_kw("and"):
                self.advance()
                spans.append(self._object_ref_name("a room name"))
        self.expect_newline()
        members = self.parse_members()
        # A `spans a, b, c` member folds into the same spans list (and is not a
        # real property): pull it out of the members here.
        kept: list[ast.Member] = []
        for m in members:
            if isinstance(m, ast.PropertyDecl) and m.name == "spans":
                if m.form != ast.PROP_VALUE or not m.values:
                    raise self._error("`spans` needs one or more room names", m.line)
                for v in m.values:
                    if not isinstance(v, ast.Name):
                        raise self._error("`spans` takes room names", m.line)
                    spans.append(v.ident)
            else:
                kept.append(m)
        # A spanning object with no `in` lives in the first room it spans (its
        # tree home); it is in scope in all of them either way.
        if location is None and spans:
            location = spans[0]
        return ast.ObjectDecl(category, name, parent, location, kept, line, spans)

    def parse_kind(self) -> ast.KindDecl:
        line = self.cur.line
        self.expect_kw("kind")
        name = self.expect_name("a kind name").value
        parent = None
        if self.accept_kw("of"):
            parent = self._kind_name("a parent kind name")
        self.expect_newline()
        members = self.parse_members()
        return ast.KindDecl(name, parent, members, line)

    def parse_member(self) -> ast.Member:
        if self.check_kw("on"):
            return self.parse_handler()
        if self.check_kw("grains"):
            return self.parse_grains_block()
        if self.check_kw("topic"):
            return self.parse_topic()
        if self.check(T.NAME) and self.cur.value == "ambience":
            return self.parse_ambience()
        if self.check(T.NAME):
            return self.parse_property()
        raise self._error(
            "expected a property, an 'on' handler, a 'grains' block, or a "
            f"'topic', got {self._describe(self.cur)}"
        )

    def _vocab_word(self) -> ast.Name:
        t = self.cur
        if t.kind in (T.NAME, T.KW):
            self.advance()
            return ast.Name(t.value, t.line)
        raise self._error(f"a vocabulary word, got {self._describe(t)}")

    def parse_topic(self) -> ast.TopicDecl:
        line = self.cur.line
        self.expect_kw("topic")
        subject = self.expect_name("a topic id").value
        label = self.parse_expr()  # the menu label string
        words: list[str] = []
        when = None
        once = False
        hidden = False
        # Modifiers in any order until the end of the header line.
        while not self.check(T.NEWLINE):
            if self.check_kw("when"):
                self.advance()
                when = self.parse_expr()
            elif self.check(T.NAME) and self.cur.value == "words":
                self.advance()
                words.append(self.expect_name("a topic match word").value)
                while self.check_op(","):
                    self.advance()
                    words.append(self.expect_name("a topic match word").value)
            elif self.check(T.NAME) and self.cur.value == "once":
                self.advance()
                once = True
            elif self.check(T.NAME) and self.cur.value == "hidden":
                self.advance()
                hidden = True
            else:
                raise self._error(
                    "expected 'words', 'when', 'once', or 'hidden' in the topic "
                    f"header, got {self._describe(self.cur)}"
                )
        self.expect_newline()
        body = self.parse_stmt_block()
        return ast.TopicDecl(subject, label, words, when, once, hidden, body, line)

    def parse_property(self) -> ast.PropertyDecl:
        tok = self.expect_name("a property name")
        name = tok.value
        if name in ("words", "plural"):
            # Vocabulary, not expressions: any word is admissible, including
            # the language's reserved ones (words self, you), since the player
            # types them without knowing our keywords. `plural` is the group
            # vocabulary the plurals granule matches (docs/05).
            values = [self._vocab_word()]
            while self.check_op(","):
                self.advance()
                values.append(self._vocab_word())
            self.expect_newline()
            return ast.PropertyDecl(name, ast.PROP_VALUE, values=values, line=tok.line)
        if self.check(T.NEWLINE):
            self.advance()
            return ast.PropertyDecl(name, ast.PROP_BOOL, line=tok.line)
        if self.check_kw("list"):
            self.advance()
            cap = self.expect(T.NUMBER, "a list capacity").value
            self.expect_newline()
            return ast.PropertyDecl(name, ast.PROP_LIST, capacity=cap, line=tok.line)
        if self.check_kw("block"):
            self.advance()
            self.expect_newline()
            body = self.parse_stmt_block()
            return ast.PropertyDecl(name, ast.PROP_BLOCK, body=body, line=tok.line)
        values = [self.parse_expr()]
        while self.check_op(","):
            self.advance()
            values.append(self.parse_expr())
        self.expect_newline()
        return ast.PropertyDecl(name, ast.PROP_VALUE, values=values, line=tok.line)

    # -- handlers ----------------------------------------------------------

    def parse_handler(self) -> ast.Handler:
        line = self.cur.line
        self.expect_kw("on")
        after = self.accept_kw("after")
        # One handler may answer several verbs, separated by commas
        # (on attack, push, pull). Operand alternatives still use `or`.
        events = [self._parse_event_name()]
        while self.check_op(","):
            self.advance()
            events.append(self._parse_event_name())
        pattern = self._parse_pattern()
        when = None
        if self.accept_kw("when"):
            when = self.parse_expr()
        self.expect_newline()
        body = self.parse_stmt_block()
        return ast.Handler(events, after, pattern, when, body, line)

    def _parse_event_name(self) -> str:
        # Most event names are ordinary identifiers; `start` is also a core
        # keyword (the game metadata key), so accept it here too.
        if self.check(T.NAME):
            return self.advance().value
        if self.check_kw("start"):
            return self.advance().value
        raise self._error(
            f"expected an event name after 'on', got {self._describe(self.cur)}"
        )

    def _parse_pattern(self) -> list[ast.PatternItem]:
        items: list[ast.PatternItem] = []
        while not (self.check(T.NEWLINE) or self.check_kw("when")):
            names = [self._parse_operand_name()]
            while self.accept_kw("or"):
                names.append(self._parse_operand_name())
            items.append(ast.Operand(names))
            if not (self.check(T.NEWLINE) or self.check_kw("when")):
                # A literal preposition word joining operands (in, on, with).
                word = self.advance().value
                items.append(ast.Prep(word))
        return items

    def _parse_operand_name(self) -> str:
        if self.check(T.NAME):
            return self.advance().value
        # The matched-object keywords and the builtin kinds may appear as
        # handler operands (on take noun; on put thing in chest).
        if self.cur.kind == T.KW and self.cur.value in (
            "noun",
            "second",
            "thing",
            "room",
        ):
            return self.advance().value
        raise self._error(
            "expected an object, kind, or direction name in the handler "
            f"header, got {self._describe(self.cur)}"
        )

    # -- grains ------------------------------------------------------------

    def parse_ambience(self) -> ast.AmbienceBlock:
        # `ambience [about N turns | every N turns] [in order] [once]
        #  [when <cond>]` then an indented list of lines: a string, or
        #  `do <block>`, each optionally guarded with a trailing `when`.
        #  The when-modifier reads to the end of the header line, so it
        #  comes last (like a topic's).
        line = self.cur.line
        self.advance()  # the leading `ambience`
        mode = "about"
        rate = None
        once = False
        when = None
        while not self.check(T.NEWLINE):
            if self.check(T.NAME) and self.cur.value == "about":
                self.advance()
                rate = self.expect(T.NUMBER, "a turn count after 'about'").value
                self._expect_turns()
            elif self.check_kw("every"):
                self.advance()
                mode = "every"
                rate = self.expect(T.NUMBER, "a turn count after 'every'").value
                self._expect_turns()
            elif self.check_kw("in") or (self.check(T.NAME) and self.cur.value == "in"):
                self.advance()
                if not (self.check(T.NAME) and self.cur.value == "order"):
                    raise self._error("'order' after 'in' in an ambience header")
                self.advance()
                mode = "order"
            elif self.check(T.NAME) and self.cur.value == "once":
                self.advance()
                once = True
            elif self.check_kw("when"):
                self.advance()
                when = self.parse_expr()
            else:
                raise self._error(
                    "expected 'about N turns', 'every N turns', 'in order', "
                    f"'once', or 'when' in the ambience header, got {self._describe(self.cur)}"
                )
        self.expect_newline()
        self.expect(T.INDENT, "an indented list of ambience lines")
        lines: list = []
        while not self.check(T.DEDENT):
            if self.check(T.NEWLINE):
                self.advance()
                continue
            lline = self.cur.line
            if self.check_kw("do") or (self.check(T.NAME) and self.cur.value == "do"):
                self.advance()
                name = self.expect_name("a block name after 'do'").value
                lwhen = None
                if self.check_kw("when"):
                    self.advance()
                    lwhen = self.parse_expr()
                self.expect_newline()
                lines.append(ast.AmbienceLine(None, name, lwhen, lline))
            else:
                text = self.expect(T.STRING, "an ambience line")
                lwhen = None
                if self.check_kw("when"):
                    self.advance()
                    lwhen = self.parse_expr()
                self.expect_newline()
                lines.append(ast.AmbienceLine(self._build_string(text), None, lwhen, lline))
        self.expect(T.DEDENT, "the end of the ambience block")
        if not lines:
            raise self._error("an ambience block needs at least one line")
        return ast.AmbienceBlock(mode, rate, once, when, lines, line)

    def _expect_turns(self) -> None:
        # The `turns` word of `about 8 turns`, matching the daemon syntax.
        if self.check_kw("turns") or (self.check(T.NAME) and self.cur.value == "turns"):
            self.advance()
            return
        raise self._error("'turns' after the ambience cadence number")

    def parse_grains_block(self) -> ast.GrainsBlock:
        line = self.cur.line
        self.expect_kw("grains")
        self.expect_newline()
        grains = self._parse_grain_body()
        return ast.GrainsBlock(grains, line)

    def parse_grains_attach(self) -> ast.GrainsAttach:
        line = self.cur.line
        target = self.expect_name("an object name").value
        self.expect_op(".")
        self.expect_kw("grains")
        self.expect_newline()
        grains = self._parse_grain_body()
        return ast.GrainsAttach(target, grains, line)

    def _parse_grain_body(self) -> list[ast.Grain]:
        self.expect(T.INDENT, "an indented grains body")
        grains: list[ast.Grain] = []
        while not self.check(T.DEDENT):
            if self.check(T.NEWLINE):
                self.advance()
                continue
            grains.append(self._parse_grain())
        self.expect(T.DEDENT)
        return grains

    def _parse_grain(self) -> ast.Grain:
        line = self.cur.line
        verbs = [self.expect_name("a grain verb").value]
        while self.check_op(","):
            self.advance()
            verbs.append(self.expect_name("a grain verb").value)
        words = [self._plain_text(self.expect(T.STRING, "a scenery word"))]
        while self.accept_kw("or"):
            words.append(self._plain_text(self.expect(T.STRING, "a scenery word")))
        if self.accept_kw("say"):
            say = self.parse_expr()
            self.expect_newline()
            return ast.Grain(verbs, words, say=say, line=line)
        if self.accept_kw("do"):
            do = self.expect_name("a block name").value
            self.expect_newline()
            return ast.Grain(verbs, words, do=do, line=line)
        if self.check(T.NEWLINE):
            self.advance()
            body = self.parse_stmt_block()
            return ast.Grain(verbs, words, body=body, line=line)
        raise self._error(
            "expected a grain response: 'say', 'do', or an indented body, "
            f"got {self._describe(self.cur)}"
        )

    # -- verbs -------------------------------------------------------------

    def parse_verb(self) -> ast.VerbDecl:
        line = self.cur.line
        self.expect_kw("verb")
        words = [self._plain_text(self.expect(T.STRING, "a verb word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "a verb word")))
        self.expect_newline()
        self.expect(T.INDENT, "an indented grammar body")
        grammar: list[ast.GrammarLine] = []
        while not self.check(T.DEDENT):
            if self.check(T.NEWLINE):
                self.advance()
                continue
            grammar.append(self._parse_grammar_line())
        self.expect(T.DEDENT)
        return ast.VerbDecl(words, grammar, line)

    def parse_language_decl(self) -> ast.LanguageDecl:
        # `language "spanish"`: the self-identifying marker of a language pack.
        # Dispatched as a leading name (not a reserved word).
        line = self.cur.line
        self.advance()  # the leading `language`
        code = self._plain_text(self.expect(T.STRING, "a language code"))
        self.expect_newline()
        return ast.LanguageDecl(code, line)

    def parse_direction(self) -> ast.DirectionDecl:
        # `direction north "north", "n"`: map words to a standard direction
        # property. `direction` is not a reserved word (it is also a grammar slot),
        # so it is dispatched here as a leading name.
        line = self.cur.line
        self.advance()  # the leading `direction`
        # The property is a direction name; `in` is a keyword, so accept a keyword
        # too and let sema check it is actually a direction.
        if self.cur.kind not in (T.NAME, T.KW):
            raise self._error("a direction property name after 'direction'")
        prop = self.advance().value
        words = [self._plain_text(self.expect(T.STRING, "a direction word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "a direction word")))
        self.expect_newline()
        return ast.DirectionDecl(prop, words, line)

    def parse_particle(self) -> ast.ParticleDecl:
        # `particle on "an", "ein"`: map words to a canonical verb particle. Like
        # `direction`, `particle` is not a reserved word, so it is dispatched here
        # as a leading name; the role (`on`/`off`) is checked in sema.
        line = self.cur.line
        self.advance()  # the leading `particle`
        if self.cur.kind not in (T.NAME, T.KW):
            raise self._error("a particle role (on or off) after 'particle'")
        role = self.advance().value
        words = [self._plain_text(self.expect(T.STRING, "a particle word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "a particle word")))
        self.expect_newline()
        return ast.ParticleDecl(role, words, line)

    def parse_pronoun(self) -> ast.PronounDecl:
        # `pronoun it "it"` / `pronoun her "sie"`: map typed words to a canonical
        # pronoun role. Dispatched as a leading name, like direction and particle;
        # the role is checked in sema against prelude._PRONOUN_ROLES.
        line = self.cur.line
        self.advance()  # the leading `pronoun`
        if self.cur.kind not in (T.NAME, T.KW):
            raise self._error("a pronoun role (it, him, her, them) after 'pronoun'")
        role = self.advance().value
        words = [self._plain_text(self.expect(T.STRING, "a pronoun word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "a pronoun word")))
        self.expect_newline()
        return ast.PronounDecl(role, words, line)

    def parse_chain(self) -> ast.ChainDecl:
        # `chain ",", "and", "then"`: the words that chain commands on one line
        # (docs/02 section 8b). Dispatched as a leading name, like direction and
        # particle; all chain words act alike, so there is no role to check.
        line = self.cur.line
        self.advance()  # the leading `chain`
        words = [self._plain_text(self.expect(T.STRING, "a chain word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "a chain word")))
        self.expect_newline()
        return ast.ChainDecl(words, line)

    def parse_all(self) -> ast.AllDecl:
        # `all "all", "everything"`: the takeall granule's all-words (docs/05).
        # Dispatched as a leading name followed by a string, like chain.
        line = self.cur.line
        self.advance()  # the leading `all`
        words = [self._plain_text(self.expect(T.STRING, "an all-word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "an all-word")))
        self.expect_newline()
        return ast.AllDecl(words, line)

    def parse_noise(self) -> ast.NoiseDecl:
        # `noise "the", "a", "an"`: the language layer's known-but-ignored
        # words (articles, fillers). Dispatched like `all` and `chain`.
        line = self.cur.line
        self.advance()  # the leading `noise`
        words = [self._plain_text(self.expect(T.STRING, "a noise word"))]
        while self.check_op(","):
            self.advance()
            words.append(self._plain_text(self.expect(T.STRING, "a noise word")))
        self.expect_newline()
        return ast.NoiseDecl(words, line)

    def _parse_grammar_line(self) -> ast.GrammarLine:
        line = self.cur.line
        action = self.expect_name("an action name").value
        items: list[ast.GrammarItem] = []
        while not self.check(T.NEWLINE):
            items.append(self._parse_grammar_item())
        self.expect_newline()
        return ast.GrammarLine(action, items, line)

    def _parse_grammar_item(self) -> ast.GrammarItem:
        tok = self.cur
        if tok.is_kw("noun"):
            self.advance()
            return ast.Slot("noun")
        if tok.kind == T.NAME and tok.value in _GRAMMAR_SLOTS:
            self.advance()
            return ast.Slot(tok.value)
        # A literal preposition word (in, on, with, to, ...).
        self.advance()
        return ast.Word(tok.value)

    # -- globals, constants, blocks ----------------------------------------

    def parse_global(self) -> ast.GlobalDecl:
        line = self.cur.line
        self.expect_kw("global")
        name = self.expect_name("a global name").value
        self.expect_op("=")
        value = self.parse_expr()
        self.expect_newline()
        return ast.GlobalDecl(name, value, line)

    def parse_constant(self) -> ast.ConstantDecl:
        line = self.cur.line
        self.expect_kw("constant")
        name = self.expect_name("a constant name").value
        self.expect_op("=")
        value = self.parse_expr()
        self.expect_newline()
        return ast.ConstantDecl(name, value, line)

    def parse_block_decl(self) -> ast.BlockDecl:
        line = self.cur.line
        self.expect_kw("block")
        name = self.expect_name("a block name").value
        self.expect_op("(")
        params: list[str] = []
        if not self.check_op(")"):
            params.append(self.expect_name("a parameter name").value)
            while self.check_op(","):
                self.advance()
                params.append(self.expect_name("a parameter name").value)
        self.expect_op(")")
        self.expect_newline()
        body = self.parse_stmt_block()
        return ast.BlockDecl(name, params, body, line)

    # -- statements --------------------------------------------------------

    def parse_statement(self) -> ast.Stmt:
        t = self.cur
        if t.kind == T.KW:
            handler = _STMT_KEYWORDS.get(t.value)
            if handler is not None:
                return handler(self)
        if t.kind == T.NAME:
            # zcolor.font white / zcolor.background black: the base-colour
            # statement (docs/01 section 9a). Dispatched here because zcolor is
            # not a reserved word.
            if t.value == "zcolor":
                return self._parse_zcolor()
            return self._parse_expr_statement()
        raise self._error(f"expected a statement, got {self._describe(t)}")

    def _parse_let(self) -> ast.Let:
        line = self.cur.line
        self.expect_kw("let")
        name = self.expect_name("a local name").value
        self.expect_op("=")
        value = self.parse_expr()
        self.expect_newline()
        return ast.Let(name, value, line)

    def _parse_change(self) -> ast.Change:
        line = self.cur.line
        self.expect_kw("change")
        target = self.parse_postfix()
        if not isinstance(target, (ast.Name, ast.Dot, ast.DynDot)):
            raise self._error(
                "the left side of 'change' must be a local, a global, or a "
                "property"
            )
        self.expect_kw("to")
        value = self.parse_expr()
        self.expect_newline()
        return ast.Change(target, value, line)

    def _parse_now(self) -> ast.Now:
        line = self.cur.line
        self.expect_kw("now")
        target = self.parse_postfix()
        self.expect_kw("is")
        negated = self.accept_kw("not")
        prop = self.expect_name("a boolean property name").value
        self.expect_newline()
        return ast.Now(target, prop, negated, line)

    def _parse_line(self) -> ast.Line:
        line = self.cur.line
        who = self.cur.value  # "you" or "reply"
        self.advance()
        text = self.parse_expr()
        self.expect_newline()
        return ast.Line(who, text, line)

    def _parse_topic_toggle(self) -> ast.TopicToggle:
        line = self.cur.line
        reveal = self.cur.value == "reveal"
        self.advance()
        target = self.expect_name("a topic id").value
        self.expect_newline()
        return ast.TopicToggle(reveal, target, line)

    def _parse_move(self) -> ast.Move:
        line = self.cur.line
        self.expect_kw("move")
        obj = self.parse_postfix()
        self.expect_kw("to")
        dest = self.parse_expr()
        self.expect_newline()
        return ast.Move(obj, dest, line)

    def _parse_add(self) -> ast.Add:
        line = self.cur.line
        self.expect_kw("add")
        value = self.parse_expr()
        self.expect_kw("to")
        target = self.parse_postfix()
        self.expect_newline()
        return ast.Add(value, target, line)

    def _parse_remove(self) -> ast.Remove:
        line = self.cur.line
        self.expect_kw("remove")
        value = self.parse_expr()
        self.expect_kw("from")
        target = self.parse_postfix()
        self.expect_newline()
        return ast.Remove(value, target, line)

    def _parse_say(self) -> ast.Say:
        line = self.cur.line
        self.expect_kw("say")
        # say.yellow "...": a one-shot coloured say. The text prints in the named
        # colour and the base font colour (zcolor.font) is restored afterwards,
        # so there is no state to manage and nothing to forget.
        colour = None
        if self.check_op("."):
            self.advance()
            colour = self.expect_name("a colour name after 'say.'").value
            if colour not in _ZCOLOURS:
                raise self._error(
                    f"unknown colour '{colour}' (use default, black, red, green, "
                    f"yellow, blue, magenta, cyan, or white)"
                )
        value = self.parse_expr()
        self.expect_newline()
        return ast.Say(value, line, colour)

    def _parse_zcolor(self) -> ast.ZColor:
        # `zcolor.font white` / `zcolor.background black`: set a base screen
        # colour. Bare value, no operator, matching the game-block property
        # style. Setting the background also repaints the screen.
        line = self.cur.line
        self.advance()  # the leading `zcolor`
        self.expect_op(".")
        target = self.expect_name(
            "'font', 'background', 'statusline', or 'input' after 'zcolor.'"
        ).value
        if target not in ("font", "background", "statusline", "input"):
            raise self._error(
                f"'{target}' is not a zcolor target (use font, background, "
                f"statusline, or input)"
            )
        colour = self.expect_name("a colour name").value
        if colour not in _ZCOLOURS:
            raise self._error(
                f"unknown colour '{colour}' (use default, black, red, green, "
                f"yellow, blue, magenta, cyan, or white)"
            )
        self.expect_newline()
        return ast.ZColor(target, colour, line)

    def _parse_stop(self) -> ast.Stop:
        line = self.cur.line
        self.expect_kw("stop")
        self.expect_newline()
        return ast.Stop(line)

    def _parse_continue(self) -> ast.Continue:
        line = self.cur.line
        self.expect_kw("continue")
        self.expect_newline()
        return ast.Continue(line)

    def _parse_finish(self) -> ast.Finish:
        line = self.cur.line
        self.expect_kw("finish")
        message = None if self.check(T.NEWLINE) else self.parse_expr()
        self.expect_newline()
        return ast.Finish(message, line)

    def _parse_return(self) -> ast.Return:
        line = self.cur.line
        self.expect_kw("return")
        value = None if self.check(T.NEWLINE) else self.parse_expr()
        self.expect_newline()
        return ast.Return(value, line)

    def _parse_if(self) -> ast.If:
        line = self.cur.line
        self.expect_kw("if")
        cond = self.parse_expr()
        self.expect_newline()
        body = self.parse_stmt_block()
        clauses = [ast.IfClause(cond, body, line)]
        while self.check_kw("else"):
            eline = self.cur.line
            self.advance()
            if self.accept_kw("if"):
                econd = self.parse_expr()
                self.expect_newline()
                ebody = self.parse_stmt_block()
                clauses.append(ast.IfClause(econd, ebody, eline))
            else:
                self.expect_newline()
                ebody = self.parse_stmt_block()
                clauses.append(ast.IfClause(None, ebody, eline))
                break
        return ast.If(clauses, line)

    def _parse_while(self) -> ast.While:
        line = self.cur.line
        self.expect_kw("while")
        cond = self.parse_expr()
        self.expect_newline()
        body = self.parse_stmt_block()
        return ast.While(cond, body, line)

    def _parse_for(self) -> ast.ForEach:
        line = self.cur.line
        self.expect_kw("for")
        self.expect_kw("each")
        var = self.expect_name("a loop variable").value
        if self.accept_kw("in"):
            relation = "in"
        elif self.accept_kw("of"):
            relation = "of"
        else:
            raise self._error("expected 'in' or 'of' in a 'for each' loop")
        source = self.parse_expr()
        self.expect_newline()
        body = self.parse_stmt_block()
        return ast.ForEach(var, relation, source, body, line)

    def _parse_switch(self) -> ast.Switch:
        line = self.cur.line
        self.expect_kw("switch")
        subject = self.parse_expr()
        self.expect_newline()
        self.expect(T.INDENT, "an indented switch body")
        cases: list[ast.Case] = []
        while not self.check(T.DEDENT):
            if self.check(T.NEWLINE):
                self.advance()
                continue
            cline = self.cur.line
            if self.accept_kw("case"):
                values = [self.parse_expr()]
                while self.check_op(","):
                    self.advance()
                    values.append(self.parse_expr())
                self.expect_newline()
                cbody = self.parse_stmt_block()
                cases.append(ast.Case(values, cbody, cline))
            elif self.accept_kw("else"):
                self.expect_newline()
                cbody = self.parse_stmt_block()
                cases.append(ast.Case([], cbody, cline))
            else:
                raise self._error(
                    f"expected 'case' or 'else' in a switch, "
                    f"got {self._describe(self.cur)}"
                )
        self.expect(T.DEDENT)
        return ast.Switch(subject, cases, line)

    def _parse_schedule(self) -> ast.Schedule:
        line = self.cur.line
        every = self.cur.is_kw("every")
        self.advance()  # after or every
        count = self.parse_expr()
        unit = self.expect_name("the word 'turns'")
        if unit.value != "turns":
            raise self._error("expected 'turns' in a scheduling statement", unit)
        self.expect_kw("do")
        event = self.expect_name("an event name").value
        self.expect_newline()
        return ast.Schedule(every, count, event, line)

    def _parse_expr_statement(self) -> ast.ExprStmt:
        line = self.cur.line
        expr = self.parse_expr()
        self.expect_newline()
        return ast.ExprStmt(expr, line)

    # -- expressions -------------------------------------------------------

    def parse_expr(self) -> ast.Expr:
        return self._parse_or()

    def _parse_or(self) -> ast.Expr:
        left = self._parse_and()
        while self.check_kw("or"):
            line = self.cur.line
            self.advance()
            right = self._parse_and()
            left = ast.Logic("or", left, right, line)
        return left

    def _parse_and(self) -> ast.Expr:
        left = self._parse_not()
        while self.check_kw("and"):
            line = self.cur.line
            self.advance()
            right = self._parse_not()
            left = ast.Logic("and", left, right, line)
        return left

    def _parse_not(self) -> ast.Expr:
        if self.check_kw("not"):
            line = self.cur.line
            self.advance()
            return ast.Unary("not", self._parse_not(), line)
        return self._parse_compare()

    def _parse_compare(self) -> ast.Expr:
        left = self._parse_additive()
        while True:
            if self.check_kw("is"):
                line = self.cur.line
                self.advance()
                negated = self.accept_kw("not")
                right = self._parse_additive()
                left = ast.IsTest(left, right, negated, line)
            elif self.check_kw("holds"):
                line = self.cur.line
                self.advance()
                right = self._parse_additive()
                left = ast.Binary("holds", left, right, line)
            elif self.check_kw("in"):
                line = self.cur.line
                self.advance()
                right = self._parse_additive()
                left = ast.Binary("in", left, right, line)
            elif self.cur.kind == T.OP and self.cur.value in ("<", ">", "<=", ">="):
                op = self.cur.value
                line = self.cur.line
                self.advance()
                right = self._parse_additive()
                left = ast.Binary(op, left, right, line)
            else:
                break
        return left

    def _parse_additive(self) -> ast.Expr:
        left = self._parse_mul()
        while self.cur.kind == T.OP and self.cur.value in ("+", "-"):
            op = self.cur.value
            line = self.cur.line
            self.advance()
            right = self._parse_mul()
            left = ast.Binary(op, left, right, line)
        return left

    def _parse_mul(self) -> ast.Expr:
        left = self._parse_unary()
        while (self.cur.kind == T.OP and self.cur.value in ("*", "/")) or self.check_kw(
            "mod"
        ):
            op = self.cur.value
            line = self.cur.line
            self.advance()
            right = self._parse_unary()
            left = ast.Binary(op, left, right, line)
        return left

    def _parse_unary(self) -> ast.Expr:
        if self.check_op("-"):
            line = self.cur.line
            self.advance()
            return ast.Unary("-", self._parse_unary(), line)
        return self.parse_postfix()

    def parse_postfix(self) -> ast.Expr:
        e = self._parse_primary()
        while True:
            if self.check_op("."):
                line = self.cur.line
                self.advance()
                if self.check_op("("):
                    self.advance()
                    index = self.parse_expr()
                    self.expect_op(")")
                    e = ast.DynDot(e, index, line)
                else:
                    prop = self.expect_name("a property name").value
                    e = ast.Dot(e, prop, line)
            elif self.check_op("(") and isinstance(e, ast.Name):
                line = self.cur.line
                self.advance()
                args = self._parse_args()
                self.expect_op(")")
                e = ast.Call(e.ident, args, line)
            else:
                break
        return e

    def _parse_args(self) -> list[ast.Expr]:
        args: list[ast.Expr] = []
        if self.check_op(")"):
            return args
        args.append(self.parse_expr())
        while self.check_op(","):
            self.advance()
            args.append(self.parse_expr())
        return args

    def _parse_primary(self) -> ast.Expr:
        t = self.cur
        if t.kind == T.NUMBER:
            self.advance()
            return ast.Number(t.value, t.line)
        if t.kind == T.STRING:
            self.advance()
            return self._build_string(t)
        if t.kind == T.NAME:
            self.advance()
            return ast.Name(t.value, t.line)
        if t.kind == T.KW:
            if t.value in ("true", "false"):
                self.advance()
                return ast.Bool(t.value == "true", t.line)
            if t.value == "nothing":
                self.advance()
                return ast.Nothing(t.line)
            if t.value in ("self", "player", "here", "noun", "second"):
                self.advance()
                return ast.Name(t.value, t.line)
            # The builtin kinds `thing` and `room` may be named as values, for
            # example as the source of `for each door of room`.
            if t.value in ("thing", "room"):
                self.advance()
                return ast.Name(t.value, t.line)
        if t.is_op("("):
            self.advance()
            e = self.parse_expr()
            self.expect_op(")")
            return e
        raise self._error(f"expected an expression, got {self._describe(t)}")

    # -- strings and interpolation -----------------------------------------

    def _build_string(self, tok: T.Token) -> ast.StringLit:
        out: list[ast.StringPart] = []
        for part in tok.value:
            if isinstance(part, ast.StringText):
                out.append(part)
            else:  # RawInterp
                expr, article, case = self._parse_interp(part)
                out.append(ast.StringInterp(expr, article, case))
        return ast.StringLit(out, tok.line)

    def _parse_interp(self, raw: RawInterp) -> tuple[ast.Expr, str | None, str | None]:
        # Peel an optional leading article, with an optional :case tag, off the raw
        # interpolation source before tokenizing the expression. The article is only
        # taken when a real expression follows it, so ${the} still prints a variable
        # named `the`. The colon is not a lexer token, so this string-level split is
        # how ${the:acc noun} reaches the language layer without touching the lexer.
        source = raw.source
        article = None
        case = None
        m = _ARTICLE_CASE_RE.match(source)
        if m:
            article = m.group(1)
            case = m.group(2)  # None when no :tag was written
            source = m.group(3)
        sub_tokens = tokenize(source, self.filename)
        sub = Parser(sub_tokens, self.filename)
        if sub.cur.kind in (T.NEWLINE, T.EOF):
            raise ArcError(
                "empty interpolation ${...} in string",
                raw.line,
                raw.column,
                self.filename,
            )
        expr = sub.parse_expr()
        if sub.cur.kind == T.NEWLINE:
            sub.advance()
        if sub.cur.kind != T.EOF:
            raise ArcError(
                f"unexpected tokens after interpolation expression "
                f"{Parser._describe(sub.cur)}",
                raw.line,
                raw.column,
                self.filename,
            )
        return expr, article, case

    def _plain_text(self, tok: T.Token) -> str:
        out: list[str] = []
        for part in tok.value:
            if isinstance(part, ast.StringText):
                out.append(part.text)
            else:
                raise ArcError(
                    "interpolation is not allowed here",
                    tok.line,
                    tok.column,
                    self.filename,
                )
        return "".join(out)


# Statement keyword -> the bound method that parses it. Built after the class
# so the methods exist.
_STMT_KEYWORDS = {
    "let": Parser._parse_let,
    "change": Parser._parse_change,
    "now": Parser._parse_now,
    "move": Parser._parse_move,
    "add": Parser._parse_add,
    "remove": Parser._parse_remove,
    "say": Parser._parse_say,
    "stop": Parser._parse_stop,
    "continue": Parser._parse_continue,
    "finish": Parser._parse_finish,
    "return": Parser._parse_return,
    "if": Parser._parse_if,
    "while": Parser._parse_while,
    "for": Parser._parse_for,
    "switch": Parser._parse_switch,
    "after": Parser._parse_schedule,
    "every": Parser._parse_schedule,
    "you": Parser._parse_line,
    "reply": Parser._parse_line,
    "reveal": Parser._parse_topic_toggle,
    "hide": Parser._parse_topic_toggle,
}


def parse(src: str, filename: str = "<source>") -> ast.Program:
    toks = tokenize(src, filename)
    return Parser(toks, filename).parse()
