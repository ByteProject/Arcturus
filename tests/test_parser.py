# test_parser.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Parser unit tests: one or more focused cases per construct in docs/01
appendix B, asserting AST structure."""

import pytest

from arcturus import ast
from arcturus.errors import ArcError
from arcturus.parser import parse


def only(src):
    prog = parse(src)
    assert len(prog.decls) == 1
    return prog.decls[0]


def one_stmt(stmt_src):
    """Parse a single statement inside a block routine and return it."""
    block = only(f"block t()\n    {stmt_src}\n")
    assert isinstance(block, ast.BlockDecl)
    assert len(block.body) == 1
    return block.body[0]


def expr_of(src):
    """Parse an expression as a global initializer and return it."""
    decl = only(f"global g = {src}\n")
    return decl.value


# -- declarations ----------------------------------------------------------


def test_game_block_metadata():
    decl = only(
        'game\n'
        '    title "T"\n'
        '    headline "H"\n'
        '    author "A"\n'
        '    release 3\n'
        '    serial "260626"\n'
        '    UUID 7f3a9c20-1e44-4b8a-9d51-6c2f0b9a7e10\n'
        '    start hallway\n'
    )
    assert isinstance(decl, ast.GameBlock)
    meta = {m.key: m.value for m in decl.meta}
    assert meta["title"] == "T"
    assert meta["release"] == 3
    assert meta["serial"] == "260626"
    assert meta["UUID"] == "7f3a9c20-1e44-4b8a-9d51-6c2f0b9a7e10"
    assert meta["start"] == "hallway"


def test_object_of_and_in():
    decl = only("thing hook of supporter in cloakroom\n    fixed\n")
    assert isinstance(decl, ast.ObjectDecl)
    assert decl.category == "thing"
    assert decl.name == "hook"
    assert decl.parent == "supporter"
    assert decl.location == "cloakroom"


def test_object_in_player_keyword():
    decl = only("thing cloak in player\n    worn\n")
    assert decl.location == "player"


def test_kind_chain():
    decl = only("kind lamp_kind of thing\n    lit false\n")
    assert isinstance(decl, ast.KindDecl)
    assert decl.parent == "thing"


def test_property_forms():
    decl = only(
        "thing x\n"
        "    name \"X\"\n"
        "    switchable\n"
        "    lit false\n"
        "    words red, blood, ruby\n"
        "    bag list 5\n"
        "    desc block\n"
        "        return \"computed\"\n"
    )
    props = {m.name: m for m in decl.members if isinstance(m, ast.PropertyDecl)}
    assert props["name"].form == ast.PROP_VALUE
    assert props["switchable"].form == ast.PROP_BOOL
    assert props["lit"].form == ast.PROP_VALUE
    assert isinstance(props["lit"].values[0], ast.Bool)
    assert props["words"].form == ast.PROP_VALUE
    assert len(props["words"].values) == 3
    assert props["bag"].form == ast.PROP_LIST and props["bag"].capacity == 5
    assert props["desc"].form == ast.PROP_BLOCK
    assert isinstance(props["desc"].body[0], ast.Return)


def test_direction_property():
    decl = only("room hallway\n    north cellar\n")
    prop = decl.members[0]
    assert prop.name == "north"
    assert isinstance(prop.values[0], ast.Name) and prop.values[0].ident == "cellar"


# -- handlers --------------------------------------------------------------


def test_handler_simple():
    decl = only("thing lever\n    on pull\n        now lever is pulled\n")
    h = decl.members[0]
    assert isinstance(h, ast.Handler)
    assert h.events == ["pull"]
    assert h.pattern == []


def test_handler_on_start_keyword_event():
    decl = only("on start\n    say \"hi\"\n")
    assert isinstance(decl, ast.Handler)
    assert decl.events == ["start"]


def test_handler_with_operand_and_prep():
    decl = only("on put ruby in chest\n    say \"ok\"\n")
    h = decl
    assert h.events == ["put"]
    assert isinstance(h.pattern[0], ast.Operand)
    assert h.pattern[0].names == ["ruby"]
    assert isinstance(h.pattern[1], ast.Prep) and h.pattern[1].word == "in"
    assert h.pattern[2].names == ["chest"]


def test_handler_or_alternatives():
    decl = only("on put ruby or ring in chest\n    say \"ok\"\n")
    assert decl.pattern[0].names == ["ruby", "ring"]


def test_handler_go_direction():
    decl = only("on go north\n    say \"no\"\n")
    assert decl.events == ["go"]
    assert decl.pattern[0].names == ["north"]


def test_handler_after_and_when():
    decl = only("on after take when ruby is hidden\n    say \"x\"\n")
    assert decl.after is True
    assert isinstance(decl.when, ast.IsTest)


def test_handler_match_noun_keyword():
    decl = only("on take noun\n    say \"x\"\n")
    assert decl.pattern[0].names == ["noun"]


def test_handler_multi_verb():
    decl = only(
        "thing rock\n"
        "    on attack, push, pull\n"
        "        say \"It is too far away for this.\"\n"
        "        stop\n"
    )
    h = decl.members[0]
    assert isinstance(h, ast.Handler)
    assert h.events == ["attack", "push", "pull"]
    assert h.pattern == []


def test_handler_multi_verb_with_operand():
    decl = only("on push, pull lever\n    say \"stuck\"\n")
    assert decl.events == ["push", "pull"]
    assert isinstance(decl.pattern[0], ast.Operand)
    assert decl.pattern[0].names == ["lever"]


def test_handler_on_other():
    decl = only("thing statue\n    on other\n        say \"silence\"\n")
    h = decl.members[0]
    assert isinstance(h, ast.Handler)
    assert h.events == ["other"]
    assert h.pattern == []


# -- verbs -----------------------------------------------------------------


def test_verb_grammar():
    decl = only('verb "put", "place"\n    put noun in noun\n    put noun on noun\n')
    assert isinstance(decl, ast.VerbDecl)
    assert decl.words == ["put", "place"]
    line0 = decl.grammar[0]
    assert line0.action == "put"
    assert isinstance(line0.items[0], ast.Slot) and line0.items[0].kind == "noun"
    assert isinstance(line0.items[1], ast.Word) and line0.items[1].text == "in"


def test_verb_direction_slot():
    decl = only('verb "go"\n    go direction\n')
    assert decl.grammar[0].items[0].kind == "direction"


# -- grains ----------------------------------------------------------------


def test_grains_say_and_or_words():
    decl = only(
        'room foyer\n'
        '    grains\n'
        '        touch, examine "chandeliers" or "hall" say "Nice."\n'
    )
    grains = decl.members[0]
    assert isinstance(grains, ast.GrainsBlock)
    g = grains.grains[0]
    assert g.verbs == ["touch", "examine"]
    assert g.words == ["chandeliers", "hall"]
    assert isinstance(g.say, ast.StringLit)


def test_grains_do_and_body():
    decl = only(
        'room foyer\n'
        '    grains\n'
        '        examine "ceiling" do describe_ceiling\n'
        '        examine "carpet"\n'
        '            change foyer.noticed to true\n'
    )
    grains = decl.members[0].grains
    assert grains[0].do == "describe_ceiling"
    assert grains[1].body and isinstance(grains[1].body[0], ast.Change)


def test_grains_attach_toplevel():
    decl = only('foyer.grains\n    examine "molding" say "Plaster."\n')
    assert isinstance(decl, ast.GrainsAttach)
    assert decl.target == "foyer"
    assert decl.grains[0].words == ["molding"]


# -- statements ------------------------------------------------------------


def test_let_and_change():
    assert isinstance(one_stmt("let n = 0"), ast.Let)
    ch = one_stmt("change ruby.desc to \"x\"")
    assert isinstance(ch, ast.Change)
    assert isinstance(ch.target, ast.Dot)


def test_now_is_and_is_not():
    s1 = one_stmt("now self is lit")
    assert isinstance(s1, ast.Now) and s1.prop == "lit" and s1.negated is False
    s2 = one_stmt("now door is not locked")
    assert s2.negated is True and s2.prop == "locked"


def test_move_add_remove():
    assert isinstance(one_stmt("move knife to player"), ast.Move)
    assert isinstance(one_stmt("move note to nothing"), ast.Move)
    assert isinstance(one_stmt('add "ruby" to ruby.synonyms'), ast.Add)
    assert isinstance(one_stmt('remove "old" from chest.synonyms'), ast.Remove)


def test_say_stop_continue_finish_return():
    assert isinstance(one_stmt('say "hi"'), ast.Say)
    assert isinstance(one_stmt("stop"), ast.Stop)
    assert isinstance(one_stmt("continue"), ast.Continue)
    assert one_stmt("finish").message is None
    assert isinstance(one_stmt('finish "*** won ***"').message, ast.StringLit)
    assert one_stmt("return").value is None
    assert isinstance(one_stmt("return item.value * 2").value, ast.Binary)


def block_body(body_src):
    """Parse a block routine whose body is `body_src` (lines indented by four
    spaces) and return the body statement list."""
    decl = only("block t()\n" + body_src)
    assert isinstance(decl, ast.BlockDecl)
    return decl.body


def test_if_elseif_else():
    body = block_body(
        "    if a is lit\n"
        "        say \"1\"\n"
        "    else if a is hidden\n"
        "        say \"2\"\n"
        "    else\n"
        "        say \"3\"\n"
    )
    stmt = body[0]
    assert isinstance(stmt, ast.If)
    assert len(stmt.clauses) == 3
    assert stmt.clauses[0].cond is not None
    assert stmt.clauses[2].cond is None  # the else


def test_while_and_for_each():
    w = block_body("    while count > 0\n        change count to count - 1\n")[0]
    assert isinstance(w, ast.While)
    f1 = block_body("    for each item in player\n        say \"x\"\n")[0]
    assert isinstance(f1, ast.ForEach) and f1.relation == "in"
    f2 = block_body("    for each door of room\n        say \"y\"\n")[0]
    assert f2.relation == "of"


def test_switch():
    s = block_body(
        "    switch answer\n"
        "        case \"yes\", \"y\"\n"
        "            say \"good\"\n"
        "        else\n"
        "            say \"what\"\n"
    )[0]
    assert isinstance(s, ast.Switch)
    assert len(s.cases) == 2
    assert len(s.cases[0].values) == 2
    assert s.cases[1].values == []  # else


def test_schedule_after_and_every():
    a = one_stmt("after 3 turns do collapse_tunnel")
    assert isinstance(a, ast.Schedule) and a.every is False and a.event == "collapse_tunnel"
    e = one_stmt("every 5 turns do tide_shifts")
    assert e.every is True


def test_expr_statement_call():
    s = one_stmt("describe_ceiling")
    assert isinstance(s, ast.ExprStmt) and isinstance(s.expr, ast.Name)
    s2 = one_stmt("points_for(ruby)")
    assert isinstance(s2.expr, ast.Call)


# -- expressions -----------------------------------------------------------


def test_is_test_and_property():
    e = expr_of("lantern is lit")
    assert isinstance(e, ast.IsTest) and e.negated is False
    e2 = expr_of("noun is not ruby")
    assert isinstance(e2, ast.IsTest) and e2.negated is True


def test_holds_and_in():
    assert expr_of("player holds lantern").op == "holds"
    assert expr_of("lantern in player").op == "in"


def test_and_or_not_precedence():
    e = expr_of("player holds lantern and lantern is lit")
    assert isinstance(e, ast.Logic) and e.op == "and"
    assert isinstance(e.left, ast.Binary) and e.left.op == "holds"
    assert isinstance(e.right, ast.IsTest)
    n = expr_of("not (a and b)")
    assert isinstance(n, ast.Unary) and n.op == "not"


def test_arithmetic_precedence():
    e = expr_of("1 + 2 * 3")
    assert isinstance(e, ast.Binary) and e.op == "+"
    assert isinstance(e.right, ast.Binary) and e.right.op == "*"
    assert expr_of("7 mod 3").op == "mod"


def test_dot_chain_and_dyndot_and_call():
    assert isinstance(expr_of("hallway.north.name"), ast.Dot)
    dd = expr_of("here.(dir)")
    assert isinstance(dd, ast.DynDot)
    c = expr_of("points_for(ruby)")
    assert isinstance(c, ast.Call) and c.name == "points_for"


def test_unary_minus():
    e = expr_of("-5")
    assert isinstance(e, ast.Unary) and e.op == "-"


def test_literals():
    assert isinstance(expr_of("true"), ast.Bool) and expr_of("true").value is True
    assert isinstance(expr_of("false"), ast.Bool)
    assert isinstance(expr_of("nothing"), ast.Nothing)
    assert isinstance(expr_of("42"), ast.Number)


# -- interpolation ---------------------------------------------------------


def test_interpolation_plain():
    e = expr_of('"turns: ${turns}"')
    interp = [p for p in e.parts if isinstance(p, ast.StringInterp)]
    assert len(interp) == 1
    assert isinstance(interp[0].expr, ast.Name) and interp[0].expr.ident == "turns"
    assert interp[0].article is None


def test_interpolation_articles():
    e = expr_of('"${the noun} and ${The ruby} and ${a lever}"')
    interp = [p for p in e.parts if isinstance(p, ast.StringInterp)]
    assert interp[0].article == "the"
    assert interp[1].article == "The"
    assert interp[2].article == "a"
    assert interp[0].expr.ident == "noun"


# -- summon, global, constant, block --------------------------------------


def test_summon_forms():
    f = only('summon "extensions/lockpicking.storyarc"\n')
    assert isinstance(f, ast.Summon) and f.is_feature is False
    ext = only("summon weather\n")
    assert ext.target == "weather" and ext.is_feature is False
    feat = only('summon.language "Spanish"\n')
    assert feat.is_feature is True and feat.target == "language" and feat.arg == "Spanish"
    feat2 = only("summon.conversations\n")
    assert feat2.is_feature is True and feat2.arg is None


def test_global_constant_block():
    g = only("global score = 0\n")
    assert isinstance(g, ast.GlobalDecl) and g.name == "score"
    c = only("constant max_score = 100\n")
    assert isinstance(c, ast.ConstantDecl)
    b = only("block points_for(item)\n    return item.value * 2\n")
    assert isinstance(b, ast.BlockDecl) and b.params == ["item"]


# -- error cases -----------------------------------------------------------


def test_error_change_non_lvalue():
    with pytest.raises(ArcError):
        parse("block t()\n    change 5 to 1\n")


def test_error_missing_expression():
    with pytest.raises(ArcError):
        parse("global g =\n")


def test_error_unknown_toplevel():
    with pytest.raises(ArcError):
        parse("wibble foo\n")
