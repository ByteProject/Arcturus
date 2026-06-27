"""The B1 done-test: both conformance example games parse cleanly, plus
structural checks that the parse captured the right shapes."""

import os

from arcturus import ast
from arcturus.parser import parse

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def load(name):
    path = os.path.join(EXAMPLES, name)
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read(), path)


def objects(prog):
    return {d.name: d for d in prog.decls if isinstance(d, ast.ObjectDecl)}


def test_brass_lantern_parses_cleanly():
    prog = load("brass-lantern.storyarc")
    # game, on start, 2 rooms, 4 things, 1 verb = 9 declarations.
    assert len(prog.decls) == 9
    assert isinstance(prog.decls[0], ast.GameBlock)

    objs = objects(prog)
    assert set(objs) >= {"hallway", "cellar", "lantern", "pedestal", "lever", "ruby"}
    assert objs["hallway"].category == "room"
    assert objs["lantern"].category == "thing"

    # The lever's pull handler ends by exposing the ruby and printing.
    lever = objs["lever"]
    pull = next(m for m in lever.members if isinstance(m, ast.Handler))
    assert pull.event == "pull"

    # The ruby's take handler finishes with an interpolated message (${turns}).
    ruby = objs["ruby"]
    take = next(m for m in ruby.members if isinstance(m, ast.Handler))
    finish = next(s for s in take.body if isinstance(s, ast.Finish))
    interps = [p for p in finish.message.parts if isinstance(p, ast.StringInterp)]
    assert any(getattr(p.expr, "ident", None) == "turns" for p in interps)

    # The cellar each_turn handler carries a `when` guard.
    cellar = objs["cellar"]
    guarded = [
        m
        for m in cellar.members
        if isinstance(m, ast.Handler) and m.event == "each_turn"
    ]
    assert guarded and guarded[0].when is not None


def test_cloak_of_darkness_parses_cleanly():
    prog = load("cloak-of-darkness.storyarc")
    # game, global, on start, 4 rooms, 3 things, 2 verbs = 11 declarations.
    assert len(prog.decls) == 11
    assert any(isinstance(d, ast.GlobalDecl) and d.name == "disturbed" for d in prog.decls)

    objs = objects(prog)
    assert set(objs) >= {"foyer", "cloakroom", "bar", "hook", "cloak", "message"}

    # The hook is a supporter; its examine handler uses `hook holds cloak`.
    hook = objs["hook"]
    assert hook.parent == "supporter"

    # The foyer overrides `go north` and carries a grain for the chandeliers.
    foyer = objs["foyer"]
    go_north = [
        m
        for m in foyer.members
        if isinstance(m, ast.Handler) and m.event == "go"
    ]
    assert go_north and go_north[0].pattern[0].names == ["north"]
    assert any(isinstance(m, ast.GrainsBlock) for m in foyer.members)

    # The message's examine handler reaches both finish endings.
    message = objs["message"]
    examine = next(m for m in message.members if isinstance(m, ast.Handler))
    finishes = _collect_finishes(examine.body)
    assert len(finishes) == 2


def _collect_finishes(stmts):
    found = []
    for s in stmts:
        if isinstance(s, ast.Finish):
            found.append(s)
        elif isinstance(s, ast.If):
            for clause in s.clauses:
                found.extend(_collect_finishes(clause.body))
        elif isinstance(s, (ast.While, ast.ForEach)):
            found.extend(_collect_finishes(s.body))
        elif isinstance(s, ast.Switch):
            for case in s.cases:
                found.extend(_collect_finishes(case.body))
    return found
