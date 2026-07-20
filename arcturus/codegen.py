# codegen.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Code generation for the version 5 backend.

Lays out the complete story file: the header, the global variables, the input
buffers, the object table (objects.py), the abbreviations area, the dictionary
(dictionary.py), and the high-memory code and strings. The entry stub calls a
main routine that prints the banner and runs the `on start` handler, lowered by
lower.py; the assembler (assembler.py) encodes and links the routines.

The full turn loop and the rest of the handlers arrive with Cosmos (B4.5). The
construct-to-opcode mapping is recorded in docs/04-codegen-mapping.md.
"""

from __future__ import annotations

import datetime

from . import __version__
from . import abbrev
from . import assembler
from . import ast
from . import cosmos
from . import dictionary
from . import objects as objmod
from . import storyfile
from . import worldmodel as wm
from .prelude import _DIRECTIONS as _PRELUDE_DIRECTIONS
from . import zstring
from .assembler import Const, Routine, RoutineRef, STACK, Variable, link
from .errors import ArcError
from .lower import Context, compile_block, cond_jump

_CONST_ONE = Const(1)

# Events fired by the turn loop (not by verb dispatch); excluded from react.
_EVENT_NAMES = wm.EVENT_NAMES
_action_numbers = wm.action_numbers  # the shared action -> number map


def _guard_plan(h: wm.Handler, layout, gmap, dirnames=frozenset(), self_num=None):
    """A patterned handler's run-time guards, as [(global name, [values])]:
    every listed global must equal one of its values or the handler does not
    apply this turn (docs/01 section 12). A direction operand (`on go west`,
    `on go south or up`) guards `way` against the directions' property
    numbers; an object operand guards `noun` (and, past a preposition,
    `second`) against object numbers, with `or` alternatives side by side.
    The keyword `noun` as a pattern name leaves its slot unconstrained
    (`on take noun`: any noun). None for a handler with no pattern.

    Patterns compile to react-side tests BEFORE the handler routine is
    called, so a failed guard counts as "this object never addressed the
    action": an all-guarded group with every guard failed still reaches the
    object's `on other` catch-all, exactly as the direction guards always
    behaved."""
    if not h.pattern:
        return None
    plan = []
    slot = "noun"
    for item in h.pattern:
        if isinstance(item, ast.Prep):
            if item.word == ",":
                raise CodegenError(
                    f"line {h.line}: alternatives in a handler pattern join "
                    "with 'or', not a comma (a comma separates verbs)"
                )
            slot = "second"
            continue
        values = []
        wildcard = False
        dirs = [n for n in item.names if n in dirnames]
        if dirs:
            # A direction operand: all alternatives must be directions, and
            # only the go action sets `way` for the guard to read.
            if len(dirs) != len(item.names):
                raise CodegenError(
                    f"line {h.line}: a pattern mixes directions and objects "
                    f"({', '.join(item.names)}); guard one kind per operand"
                )
            if "go" in h.events:
                plan.append(("way", [layout.prop_number[n] for n in dirs]))
                continue
            raise CodegenError(
                f"line {h.line}: a direction pattern needs the go action "
                f"(the parser sets `way` only for go)"
            )
        for name in item.names:
            if name == slot or name == "noun":
                wildcard = True  # `on take noun`: anything in this slot
                continue
            if name == "self":
                # The react routine's own object: an instance handler guards
                # its owner's number, a kind handler guards each instance's
                # own number (react routines are per object, so self_num is
                # always the right one for the copy being compiled).
                if self_num is None:
                    raise CodegenError(
                        f"line {h.line}: 'self' in a handler header needs an "
                        "enclosing object"
                    )
                values.append(self_num)
                continue
            if layout is not None and name in layout.obj_number:
                values.append(layout.obj_number[name])
                continue
            raise CodegenError(
                f"line {h.line}: handler pattern names '{name}', which is "
                "not an object or direction (kinds in patterns are not "
                "supported yet; test the kind inside the handler body "
                "instead)"
            )
        if not wildcard and values:
            plan.append((slot, values))
        slot = "second"
    return plan or None


def _resolved_handlers(world: wm.World, obj: wm.Obj):
    """The object's handlers in resolution order: its own first (most specific),
    then each kind up its inheritance chain, nearest first (docs/01 section 5).
    An instance inherits every handler of its kind chain; put in one list here,
    the react routine runs them in order and a non-consuming handler (one that
    ends with `continue`) falls through to the next, exactly as documented."""
    handlers = list(obj.handlers)
    for kindname in obj.chain:
        kind = world.kinds.get(kindname)
        if kind is not None:
            handlers.extend(kind.handlers)
    return handlers


def _owner_bands(world: wm.World, obj: wm.Obj):
    """The object's handlers grouped by OWNER, nearest first: [instance,
    kind, kind's kind, ...]. Each band is a list of handlers. The react
    routine runs band by band, and each band's `on other` catch-all sits at
    the END of ITS OWN band: the object's default runs before the action
    climbs to the kind (docs/01 section 12, the contract a field report
    held us to), and a kind's default before the next kind up."""
    bands = [list(obj.handlers)]
    for kindname in obj.chain:
        kind = world.kinds.get(kindname)
        if kind is not None and kind.handlers:
            bands.append(list(kind.handlers))
    return [b for b in bands if b]


def _react_handlers(world: wm.World, obj: wm.Obj, actions: dict):
    """The object's dispatchable handlers, own and inherited, as (action,
    handler): verb actions, the life-cycle events the loop fires here (enter,
    each_turn), and `on go <direction>` overrides (guarded on the direction).
    An `on after` handler answers to its action's synthetic after number, so
    it never runs in the main phase; the dispatcher fires it in the after pass
    (docs/02 section 9). Patterned handlers ride along; their operand guards
    are emitted into the react routine (see _guard_plan). Free rules go
    through react_free."""
    out = []
    for h in _resolved_handlers(world, obj):
        for ev in h.events:
            if ev in actions and ev != "other":
                out.append((wm.after_key(ev) if h.after else ev, h))
    return out


def _other_handlers(world: wm.World, obj: wm.Obj):
    """The object's `on other` catch-all handlers, own and inherited: the least
    specific handlers, run when no specific handler consumed the action, before it
    climbs to the room or the Cosmos default (docs/01 section 12). Main band
    only: `on after other` is the AFTER band's catch-all (below), never this
    one (the field bug: it rode here and fired during the main dispatch,
    before the action's own report and on refused actions too)."""
    return [
        h for h in _resolved_handlers(world, obj)
        if "other" in h.events and not h.pattern and not h.after
    ]


def _after_other_handlers(world: wm.World, obj: wm.Obj):
    """The object's `on after other` handlers: the after pass's catch-all, run
    for any completed action the object has no specific `on after` for."""
    return [
        h for h in _resolved_handlers(world, obj)
        if "other" in h.events and not h.pattern and h.after
    ]


def _react_objects(world: wm.World, actions: dict) -> set:
    return {
        name
        for name, obj in world.objects.items()
        if _react_handlers(world, obj, actions)
        or _other_handlers(world, obj)
        or _after_other_handlers(world, obj)
    }


def gen_react_routines(world: wm.World, actions: dict, registry, layout=None, gmap=None, pool=None) -> list:
    """A react_<obj> routine for every object that has react handlers, calling
    the per-handler routines by their registry names. layout/gmap are needed only
    to guard `on go <direction>` overrides on the chosen direction. Also emits
    react_free and the grain routines so the dispatcher can call them all."""
    hname = {id(h): nm for h, nm in registry}
    afloor = wm.after_floor(world) if wm.actions_with_after(world) else None
    dirnames = frozenset(world.directions.values())
    out = []
    for objname, obj in world.objects.items():
        pairs = _react_handlers(world, obj, actions)
        flat_others = _other_handlers(world, obj)
        flat_after = _after_other_handlers(world, obj)
        if not pairs and not flat_others and not flat_after:
            continue
        # `enter` is two things sharing one name: on a ROOM it is the arrival
        # event (fire_enter runs every hook and ignores the results), on a
        # THING it is the ENTER verb, an ordinary consumable action (a scenery
        # shack's `on enter` teleport must consume, docs/01 section 7). The
        # object's category picks the semantic; room kinds and thing kinds
        # follow their instances here.
        events = wm.EVENT_NAMES if obj.category == "room" else wm.EVENT_NAMES - {"enter"}
        # OWNER BANDS (docs/01 section 12): the object's own handlers with
        # its own `on other` at their tail, then each kind's the same way,
        # nearest first. Life-cycle events stay a single merged step (every
        # hook fires, own and inherited; results are ignored), so they are
        # split out of the bands here.
        bands = []
        for owner_handlers in _owner_bands(world, obj):
            band_groups: dict = {}
            for h in owner_handlers:
                for ev in h.events:
                    if ev in actions and ev != "other" and (
                            wm.after_key(ev) if h.after else ev) not in events:
                        key = wm.after_key(ev) if h.after else ev
                        band_groups.setdefault(key, []).append((hname[id(h)], h))
            band_others = [(hname[id(h)], h) for h in owner_handlers
                           if "other" in h.events and not h.pattern and not h.after]
            band_after = [(hname[id(h)], h) for h in owner_handlers
                          if "other" in h.events and not h.pattern and h.after]
            if band_groups or band_others or band_after:
                bands.append((band_groups, band_others, band_after))
        event_groups: dict = {}
        for action, h in pairs:
            if action in events:
                event_groups.setdefault(action, []).append((hname[id(h)], h))
        out.append(_gen_react(
            objname, bands, actions, layout, gmap, afloor, dirnames,
            events, mfloor=wm.meta_floor(world), event_groups=event_groups))
    # react_free and grain_dispatch are always present (even empty) so the turn
    # loop and dispatcher can call them unconditionally.
    out.append(gen_react_free(world, actions, registry, layout, gmap))
    out.extend(gen_grain_routines(world, actions, gmap, layout, pool))
    # after_map(action) backs the after_of intrinsic: the dispatcher's after
    # phase (docs/02 section 9 step 6) asks it which synthetic after action to
    # fire once the real one completed unrefused. Emitted only when an after
    # handler exists; without one, any_after folds the phase (and the only
    # call site) away, so games without `on after` pay nothing.
    withafter = wm.actions_with_after(world)
    if withafter:
        # `on after other` gives the map a FALLBACK: any world action without
        # a specific after takes the synthetic after:other, so the after pass
        # runs for it and the react routines' after-band catch-all answers.
        # Only world actions: the metas (at and past meta_floor) never take an
        # after pass, exactly as they never meet the plain catch-all.
        specifics = [n for n in withafter if n != "other"]
        amap = Routine("after_map", nlocals=1)
        for name in specifics:
            lbl = "yes_" + name
            amap.op("je", Variable(1), Const(actions[name]), branch=(lbl, True))
        if "other" in withafter:
            amap.op("jl", Variable(1), Const(wm.meta_floor(world)),
                    branch=("yes_other", True))
            amap.op("ret", Const(0))
            amap.label("yes_other")
            amap.op("ret", Const(actions[wm.after_key("other")]))
        else:
            amap.op("ret", Const(0))
        for name in specifics:
            amap.label("yes_" + name)
            amap.op("ret", Const(actions[wm.after_key(name)]))
        out.append(amap)
    return out


def _all_grains(world: wm.World):
    """Every grain attached to an object, as (index, grain, owner_name), in a
    deterministic order shared by codegen and the dictionary. Kind grains are not
    placed yet (they would need per-instance scope)."""
    out = []
    for objname, obj in world.objects.items():
        for grain in obj.grains:
            out.append((len(out), grain, objname))
    return out


def gen_grain_routines(world, actions, gmap, layout, pool) -> list:
    """A grain<i>(action) routine per grain (answer the grain's verbs, else the
    scenery default) plus grain_dispatch(id, action) that routes to it. Grains are
    scenery: words with a response but no object entry (docs/01 section 14).
    grain_dispatch is always emitted (even with no grains) so Cosmos dispatch can
    call it unconditionally."""
    grains = _all_grains(world)
    routines = []
    for idx, grain, owner in grains:
        routines.append(_compile_grain(world, gmap, layout, pool, grain, idx, owner, actions))
    disp = Routine("grain_dispatch", nlocals=2)  # local 1 = id (index+1), 2 = action
    for idx, _g, _o in grains:
        disp.op("je", Variable(1), Const(idx + 1), branch=(f"g{idx}", True))
    disp.op("ret", Const(0))
    for idx, _g, _o in grains:
        disp.label(f"g{idx}")
        disp.op("call_vn", RoutineRef(f"grain{idx}"), Variable(2))
        disp.op("ret", _CONST_ONE)
    routines.append(disp)
    return routines


def _compile_grain(world, gmap, layout, pool, grain, idx, owner, actions) -> Routine:
    """grain<i>(action): if the action is one the grain answers, run its response;
    otherwise print the scenery default. The grain always consumes the action."""
    owner_num = layout.obj_number.get(owner, 0)
    ctx = Context(
        world, gmap, params=["__action__"], layout=layout,
        in_handler=True, string_pool=pool, self_value=Const(owner_num),
    )
    if grain.say is not None:
        body = [ast.Say(grain.say)]
    elif grain.do is not None:
        body = [ast.ExprStmt(ast.Call(grain.do, []))]
    else:
        body = grain.body
    rt = Routine(f"grain{idx}", nlocals=1)
    for v in grain.verbs:
        if v in actions:
            rt.op("je", Variable(1), Const(actions[v]), branch=("respond", True))
    # An unanswered verb gets the scenery brush-off, and that is a refusal: a
    # chained line must stop here rather than run its remaining commands.
    rt.op("store", Const(ctx.globals["refused"]), _CONST_ONE)
    rt.op("call_vn", RoutineRef("blk_msg_scenery"))
    rt.op("ret", _CONST_ONE)
    rt.label("respond")
    ctx.prescan(body)
    compile_block(rt, ctx, body)
    rt.op("ret", _CONST_ONE)
    rt.nlocals = ctx.nlocals()
    return rt


# The free-rule precedence: a story rule outranks a granule's, which outranks
# the Cosmos default, so `on xyzzy` in a game reskins the easter egg and
# `continue` defers back down the chain (docs/01 section 12, docs/05).
_ORIGIN_RANK = {None: 0, "granule": 1, "library": 2}


def _free_react_handlers(world: wm.World, actions: dict):
    """Free-standing rules (owner None), as (action, handler): the game's
    `on start`, free `on each_turn` pulses, and (from B4.5e.3) the Cosmos default
    verbs. These have no object owner, so they run through react_free, most
    specific origin first (game, then granule, then library)."""
    out = []
    ranked = sorted(
        world.free_handlers,
        key=lambda h: _ORIGIN_RANK.get(getattr(h, "origin", None), 0),
    )
    for h in ranked:
        for ev in h.events:
            if ev in actions and ev != "other":
                out.append((wm.after_key(ev) if h.after else ev, h))
    return out


def _free_other_handlers(world: wm.World):
    """Free-standing `on other` rules: a global catch-all fired last, for any
    action nothing more specific consumed; ordered like the specific rules.
    Main band only; `on after other` is the after band's (below)."""
    ranked = sorted(
        world.free_handlers,
        key=lambda h: _ORIGIN_RANK.get(getattr(h, "origin", None), 0),
    )
    return [h for h in ranked
            if "other" in h.events and not h.pattern and not h.after]


def _free_after_other_handlers(world: wm.World):
    """Free-standing `on after other` rules: the after pass's global
    catch-all, for any completed action with no specific `on after` here."""
    ranked = sorted(
        world.free_handlers,
        key=lambda h: _ORIGIN_RANK.get(getattr(h, "origin", None), 0),
    )
    return [h for h in ranked
            if "other" in h.events and not h.pattern and h.after]


def gen_react_free(world: wm.World, actions: dict, registry, layout=None, gmap=None) -> Routine:
    """react_free(action): the free-rule equivalent of a react_<obj> routine.
    The turn loop calls it for life-cycle events (start, each_turn) and the
    dispatcher calls it last in the action chain. Always emitted (empty when
    there are no free rules) so callers can reference it unconditionally.
    layout/gmap serve the operand and direction guards of patterned free
    rules, exactly as in the per-object routines."""
    hname = {id(h): nm for h, nm in registry}
    groups: dict = {}
    for action, h in _free_react_handlers(world, actions):
        # In the no-Cosmos fallback `on start` is compiled into main, not
        # registered; skip any free handler without a routine.
        if id(h) in hname:
            groups.setdefault(action, []).append((hname[id(h)], h))
    others = [(hname[id(h)], h) for h in _free_other_handlers(world) if id(h) in hname]
    after_others = [(hname[id(h)], h)
                    for h in _free_after_other_handlers(world) if id(h) in hname]
    afloor = wm.after_floor(world) if wm.actions_with_after(world) else None
    dirnames = frozenset(world.directions.values())
    # Free `on enter` rules are the ENTER verb (the Cosmos default action, and
    # any game rule over it), never the room-arrival event: fire_enter calls
    # only the room's own react. So the verb semantics apply here too, and the
    # most specific consuming rule wins like any other verb.
    event_groups = {a: hs for a, hs in groups.items()
                    if a in (wm.EVENT_NAMES - {"enter"})}
    main_groups = {a: hs for a, hs in groups.items() if a not in event_groups}
    return _gen_react(
        "free", [(main_groups, others, after_others)], actions, layout, gmap,
        afloor, dirnames, wm.EVENT_NAMES - {"enter"},
        mfloor=wm.meta_floor(world), event_groups=event_groups,
    )


def _gen_react(objname: str, bands: list, actions: dict, layout=None, gmap=None, afloor=None, dirnames=frozenset(), event_names=wm.EVENT_NAMES, mfloor=None, event_groups=None) -> Routine:
    """react_<obj>(action), OWNER-BANDED (docs/01 section 12): the object's
    own handlers form band 0 with its own `on other` at the band's tail, then
    each kind's handlers band by band up the chain, each with ITS `on other`
    at its own tail. The object's default therefore runs BEFORE the action
    climbs to the kind (the field bug this rewrite fixed: a kind's specific
    verb pierced the instance's catch-all), and a kind's default before the
    next kind up. Within a band the rules are unchanged: specific handlers
    run in order, one that consumes (returns 1) ends the dispatch, one that
    continues falls onward; a band whose specifics ADDRESSED the action (ran
    and continued, or exists unguarded) skips its own catch-all and falls to
    the next band; a band that never addressed it runs its catch-all first.
    Life-cycle events (start, enter, each_turn) are not banded: every hook
    fires, own and inherited, results ignored, exactly as before. The
    `afloor`/`mfloor` banding also holds per band: a plain catch-all answers
    only main actions, `on after other` only the synthetic after numbers,
    metas climb silently."""
    event_groups = event_groups or {}
    rt = Routine("react_" + objname, nlocals=2)  # 1 = action, 2 = a guard ran
    # An owned handler is called with this react routine's own object as its
    # self argument (docs/01 section 9); free rules are called with none.
    self_num = layout.obj_number.get(objname) if layout is not None else None

    def self_args(h):
        if h.owner is not None and self_num is not None:
            return (Const(self_num),)
        return ()

    # -- life-cycle events: one merged step, every hook fires ---------------
    ev_label = {}
    for i, action in enumerate(event_groups):
        ev_label[action] = f"ev{i}"
        rt.op("je", Variable(1), Const(actions[action]), branch=(ev_label[action], True))
    ev_bodies = list(event_groups.items())

    # -- the bands ----------------------------------------------------------
    skip_n = 0
    nb = len(bands)

    def band_label(k):
        return "__climb__" if k >= nb else f"band{k}"

    first = True
    for k, (groups, others, after_others) in enumerate(bands):
        if not first:
            rt.label(f"band{k}")
        first = False
        nxt = band_label(k + 1)
        run_label = {}
        for i, action in enumerate(groups):
            run_label[action] = f"b{k}run{i}"
            rt.op("je", Variable(1), Const(actions[action]),
                  branch=(run_label[action], True))
        rt.jump(f"b{k}other")  # nothing specific here: this band's catch-all
        for action, handlers in groups.items():
            rt.label(run_label[action])
            plans = [_guard_plan(h, layout, gmap, dirnames, self_num)
                     for _, h in handlers]
            all_guarded = all(p is not None for p in plans)
            if all_guarded:
                rt.op("store", Const(2), Const(0))
            for (hn, h), plan in zip(handlers, plans):
                if plan is not None:
                    skip = f"skipg{skip_n}"
                    skip_n += 1
                    for gvar, values in plan:
                        chunks = [values[i:i + 3] for i in range(0, len(values), 3)]
                        if len(chunks) == 1:
                            rt.op("je", Variable(gmap[gvar]),
                                  *[Const(v) for v in chunks[0]],
                                  branch=(skip, False))
                        else:
                            ok = f"gok{skip_n}_{gvar}"
                            for c in chunks:
                                rt.op("je", Variable(gmap[gvar]),
                                      *[Const(v) for v in c], branch=(ok, True))
                            rt.jump(skip)
                            rt.label(ok)
                    if all_guarded:
                        rt.op("store", Const(2), _CONST_ONE)
                    rt.op("call_vs", RoutineRef(hn), *self_args(h), store=Variable(STACK))
                    rt.op("je", Variable(STACK), _CONST_ONE, branch=("__handled__", True))
                    rt.label(skip)
                else:
                    rt.op("call_vs", RoutineRef(hn), *self_args(h), store=Variable(STACK))
                    rt.op("je", Variable(STACK), _CONST_ONE, branch=("__handled__", True))
            if all_guarded:
                # Every match was guarded: if none ran, this band never
                # addressed the action, so its catch-all still gets a turn.
                rt.op("jz", Variable(2), branch=(f"b{k}other", True))
            rt.jump(nxt)  # addressed but deferred: fall to the next band
        if k == nb - 1:
            # life-cycle event bodies sit in the last band's body region so
            # the final catch-all section can fall straight into __climb__
            for action, handlers in ev_bodies:
                rt.label(ev_label[action])
                for hn, h in handlers:
                    rt.op("call_vn", RoutineRef(hn), *self_args(h))
                rt.jump("__climb__")
        rt.label(f"b{k}other")
        if others or after_others:
            # The catch-alls answer the player's verbs, never the life-cycle
            # events the loop fires (start, enter, each_turn).
            for ev in _EVENT_NAMES:
                if ev in actions:
                    rt.op("je", Variable(1), Const(actions[ev]), branch=(nxt, True))
            if afloor is not None:
                if after_others:
                    rt.op("jl", Variable(1), Const(afloor), branch=(f"b{k}mo", True))
                    rt.op("jl", Variable(1), Const(mfloor), branch=(f"b{k}ao", True))
                    rt.jump(nxt)
                    rt.label(f"b{k}mo")
                else:
                    rt.op("jl", Variable(1), Const(afloor), branch=(nxt, False))
            for hn, h in others:
                rt.op("call_vs", RoutineRef(hn), *self_args(h), store=Variable(STACK))
                rt.op("je", Variable(STACK), _CONST_ONE, branch=("__handled__", True))
            if after_others:
                rt.jump(nxt)
                rt.label(f"b{k}ao")
                for hn, h in after_others:
                    rt.op("call_vs", RoutineRef(hn), *self_args(h), store=Variable(STACK))
                    rt.op("je", Variable(STACK), _CONST_ONE, branch=("__handled__", True))
        if nxt != "__climb__":
            rt.jump(nxt)
        else:
            # the last band falls through to __climb__; event bodies were
            # already emitted just before its catch-all section
            pass
    if not bands:
        rt.jump("__climb__")
        for action, handlers in ev_bodies:
            rt.label(ev_label[action])
            for hn, h in handlers:
                rt.op("call_vn", RoutineRef(hn), *self_args(h))
            rt.jump("__climb__")
    rt.label("__climb__")
    rt.op("ret", Const(0))  # nothing consumed it: let it climb the chain
    rt.label("__handled__")
    rt.op("ret", _CONST_ONE)
    return rt

# Region sizes and the input-buffer layout (the buffer constants live in
# storyfile so the lowering can share them; re-exported here for callers/tests).
_GLOBALS_BYTES = storyfile.GLOBALS_BYTES
_PROP_DEFAULTS_BYTES = 63 * 2  # property defaults table (v4+: 63 words)
_ABBREV_BYTES = 96 * 2  # 96 abbreviation entries, empty for now
TEXT_BUFFER_ADDR = storyfile.TEXT_BUFFER_ADDR
TEXT_BUFFER_MAX = storyfile.TEXT_BUFFER_MAX
_TEXT_BUFFER_BYTES = storyfile.TEXT_BUFFER_BYTES
PARSE_BUFFER_ADDR = storyfile.PARSE_BUFFER_ADDR
PARSE_BUFFER_MAX = storyfile.PARSE_BUFFER_MAX
_PARSE_BUFFER_BYTES = storyfile.PARSE_BUFFER_BYTES


class CodegenError(ArcError):
    pass


class StringPool:
    """Strings allocated during lowering (text-property writes, dynamic text).
    build_story lays them out in high memory and backpatches their addresses.
    Identical text is stored ONCE and shared: two rooms with the same desc, or
    a string constant used in several properties, cost one packed string."""

    def __init__(self) -> None:
        self.strings: dict[str, str] = {}
        self._by_text: dict[str, str] = {}

    def add(self, text: str) -> str:
        sid = self._by_text.get(text)
        if sid is None:
            sid = f"s{len(self.strings)}"
            self.strings[sid] = text
            self._by_text[text] = sid
        return sid


def _meta(world: wm.World) -> dict:
    out: dict = {}
    if world.game is not None:
        for m in world.game.meta:
            out[m.key] = m.value
    return out


def _compiler_version() -> str:
    return ".".join(__version__.split(".")[:2])


def _banner_parts(world: wm.World):
    """The banner's fixed pieces: (title line, explicit headline or None, author,
    release line). The words BETWEEN them ("by", and the default headline when a
    game sets none) belong to the language layer; see _emit_banner."""
    m = _meta(world)
    title = m.get("title", "Untitled")
    headline = m.get("headline")  # None -> the language layer's default
    author = m.get("author", "Anonymous")
    release = m.get("release", 1)
    serial = m.get("serial") or datetime.date.today().strftime("%y%m%d")
    cosmos_v = ".".join(cosmos.COSMOS_VERSION.split(".")[:2])
    line3 = (
        f"Release {release} / Serial number {serial} / "
        f"Arcturus {_compiler_version()} / Cosmos {cosmos_v}"
    )
    return title, headline, author, line3


def banner_text(world: wm.World) -> str:
    """The whole banner as one string: the fallback for a bare build (no Cosmos),
    where no language layer supplies the connecting words. English throughout."""
    title, headline, author, line3 = _banner_parts(world)
    line2 = f"{headline or 'An Interactive Fiction'} by {author}"
    # End on a single newline; the blank line that separates the banner from the
    # first text is a paragraph break the turn loop requests (run_game), so the
    # spacing is owned by the one paragraph model instead of hardcoded here (which
    # otherwise doubled up with describe_room's par on the opening screen).
    return f"\n{title}\n{line2}\n{line3}\n"


def _emit_banner(main: Routine, world: wm.World) -> None:
    """Print the banner from __main__. The structure (title, headline, author,
    release line) is the compiler's; the WORDS between the parts come from the
    language layer, so a pack localizes them: line_by prints the connector
    (" by ", " von ", " de ") and banner_headline the default headline when a
    game sets none. A bare build (no Cosmos) falls back to the one-string
    English banner."""
    # Flush a pending paragraph break first: print_banner() may be called
    # mid-handler right after prose (H2's launch sequence), and the banner's
    # raw prints do not flush, so the first library block inside it (line_by)
    # would otherwise burst the break into the middle of the headline line.
    slot = _globals_map(world)["par_pending"]
    main.op("jz", Variable(slot), branch=("bnr_nopar", True))
    main.op("new_line")
    main.op("store", Const(slot), Const(0))
    main.label("bnr_nopar")
    if "line_by" not in world.blocks:
        # The bare build styles its title too: set_text_style is v5 core and
        # an unable interpreter must simply ignore it, so this costs nothing
        # anywhere and reads bold where bold exists.
        title, headline, author, line3 = _banner_parts(world)
        line2 = f"{headline or 'An Interactive Fiction'} by {author}"
        main.op("print", text="\n")
        main.op("set_text_style", Const(2))
        main.op("print", text=f"{title}\n")
        main.op("set_text_style", Const(0))
        main.op("print", text=f"{line2}\n{line3}\n")
        return
    # No leading blank: at game start the banner sits directly under the
    # status bar (where Inform leaves a stray line), and a mid-game banner
    # gets its space from the pending break the preceding prose marked.
    # The title prints bold, the classic library presentation (Stefan's
    # polish ruling): style up, the one line, style roman again.
    title, headline, author, line3 = _banner_parts(world)
    main.op("set_text_style", Const(2))
    main.op("print", text=f"{title}\n")
    main.op("set_text_style", Const(0))
    if headline is not None:
        main.op("print", text=headline)
    elif "banner_headline" in world.blocks:
        main.op("call_vn", RoutineRef("blk_banner_headline"))
    else:
        main.op("print", text="An Interactive Fiction")
    main.op("call_vn", RoutineRef("blk_line_by"))
    main.op("print", text=f"{author}\n{line3}\n")
    # The banner manages its own trailing space: mark the pending break so
    # whatever prints next (the opening prose, a room description) stands
    # one blank line below, with no par() in any story.
    main.op("store", Const(slot), Const(1))


def _start_handler(world: wm.World):
    for h in world.free_handlers:
        if "start" in h.events:
            return h
    return None



# Builtin references get fixed global slots; game globals follow. turns/score/
# max_score are numbers; player/here/noun/second hold object numbers at run time.
# turns/score/max_score are numbers; player/here/noun/second hold object numbers;
# way/grain are the parser's direction and scenery; par_pending is the library's
# paragraph-break flag (internal, set by par(), honored by the print layer).
# parse_fault flags that the player named an object that is not in scope (the
# turn loop reports "you can't see that" and skips the turn); meta_turn flags an
# action that does not advance the world (score, save, a cancelled quit), so the
# loop skips the per-turn pulse and the turn count.
# last_* remember the previous non-meta command (its action and resolved
# operands) so "again" can replay it.
_BUILTIN_GLOBALS = [
    "turns", "score", "max_score", "player", "here", "noun", "second",
    "way", "grain", "par_pending", "parse_fault", "unknown_at", "two_reverse",
    "line_act", "meta_turn",
    "last_act", "last_noun", "last_second", "last_way", "last_grain",
    # 1 when the ending was a `death` (the post-mortem then offers UNDO).
    "died",
    # 1 once a handler spoke this action's report (`alter`); the default's
    # success line then stays silent. Cleared per dispatch.
    "altered",
    "altered_self",
    # last_here is the room the remembered command ran in, so a replayed
    # scenery-grain quip refuses in another room.
    "last_here",
    # 1 while AGAIN replays: it restores resolved operands, not typed words,
    # so anything reading the raw input at dispatch time (a topic's subject)
    # knows to answer what it answered last time instead.
    "replaying",
    # oops_ready flags that the previous command had an unrecognized word;
    # oops_word is that word's parse-buffer index, for "oops" to correct.
    "oops_ready", "oops_word",
    # shut_in holds the closed container a named object is known to be inside but
    # shut away in, so the loop can answer "open it first" instead of "can't see".
    "shut_in",
    # __catalogs__ holds the byte address of the catalog region (docs/01,
    # catalogs); entry/calculate/dice lower to loadw/storew against it.
    "__catalogs__",
    # __timers__ holds the base address of the scheduling table (after/every), set
    # at startup; 0 when the story schedules nothing.
    "__timers__",
    # __strings__ is the first packed string address, set at startup, stored with
    # its TOP BIT FLIPPED (+0x8000 mod 2^16). A computed (`<name> block`) text
    # property stores its block routine's packed address, which is below the
    # threshold; a plain one stores a string address, at or above it, so a read of
    # such a property compares against it to "print or run". Packed addresses are
    # unsigned but jl compares signed, so both sides carry the sign bias: this
    # global is pre-biased here, the property value gets +0x8000 at the compare
    # (see lower._emit_prop_print_or_run).
    "__strings__",
    # __routines__ is the LOWEST packed routine address, pre-biased +0x8000 like
    # __strings__. A computed EXIT (a direction property that is a block) stores
    # the block routine's packed address, at or above this; a plain exit stores a
    # small room object number, below it. exit_dest compares against this to
    # "read or run" (docs/02 section 11a). It claims a fixed global slot only, and
    # exit_dest folds to a plain get_prop when the game has no computed exit.
    "__routines__",
    # The base font colour (zcolor.font), which say.<colour> restores to.
    # Seeded to 1 (the interpreter default) in build_story.
    "__zcfont__",
    # The status-line and input colours (zcolor.statusline / zcolor.input).
    # 0 means unset: the status bar and the input reader skip their colour ops
    # entirely, so a game without them pays two cheap tests and nothing more.
    "__zcstatus__", "__zcinput__",
    # The pronoun referents (docs/02 section 8a), written by the language
    # layer's note_pronouns and read back when a pronoun word resolves.
    "pron_it", "pron_him", "pron_her", "pron_them",
    # The ambience table's base address (summon.ambience), 0 when no block
    # exists; the granule's driver walks it each turn.
    "__ambience__",
    # The opening-description title skip (a status bar already names the room).
    "hide_title",
    # arc_image (B11): the picture id currently on screen, so describe_room skips
    # the draw when the room's picture has not changed (the re-LOOK dedup).
    "shown_image",
    # Scoring: the award earned-bytes table, the rank ladder, the labelled
    # pools for the fullscore breakdown.
    "__awards__", "__ranks__", "__pooltab__",
    # Command chaining (docs/02 section 8b): refused flags a command a refusal
    # path could not carry out (stops the rest of a chained line); chain_pos is
    # the text-buffer offset of the queued rest of the line (0 when none);
    # chain_max is the full typed length chain_next restores before it
    # re-tokenizes the tail.
    "refused", "chain_pos", "chain_max",
    # The disambiguation ask (docs/02 section 8): the tied phrase's word range
    # and winning score, and the offset where an answer weaves back in.
    "ask_lo", "ask_hi", "ask_score", "ask_at",
    # The held tiebreak's per-command direction (1 in-hand, 0 not-held).
    "tie_want",
    # TAKE ALL (the takeall granule): the parser's hand-off flag to run_all.
    "all_go",
    # The plurals granule: the matched group word for the sweep, the remembered
    # one for THEM, and the previous chained action for verb-less segments.
    "plural_go", "last_plural", "chain_prev",
]


def _globals_map(world: wm.World) -> dict:
    m: dict = {}
    n = 16
    for name in _BUILTIN_GLOBALS:
        m[name] = n
        n += 1
    for name in world.globals:
        if name not in m:
            m[name] = n
            n += 1
    return m


def build_story(
    world: wm.World, entry: Routine, routines: list, layout=None, string_pool=None,
    version: int = 5, stats=None,
) -> bytes:
    """Assemble a complete z5 (or z8) image from the entry stub and routines,
    laying out the standard memory regions. Shared by generate() and the backend
    tests. `layout` is the object table (objects.Layout); without it the object
    area is just the empty property-defaults table. `version` is 5 (default) or 8;
    the two differ only in the header version byte, the file-length scale (both in
    StoryFile), and the packed-address unit (4 for z5, 8 for z8)."""
    sf = storyfile.StoryFile(version=version)
    scale = 8 if version == 8 else 4

    # Dynamic memory: globals, the input buffers, and the object table.
    globals_addr = sf.append(bytes(_GLOBALS_BYTES))
    text_buf = bytearray(_TEXT_BUFFER_BYTES)
    text_buf[0] = TEXT_BUFFER_MAX
    sf.append(bytes(text_buf))  # lands at TEXT_BUFFER_ADDR
    parse_buf = bytearray(_PARSE_BUFFER_BYTES)
    parse_buf[0] = PARSE_BUFFER_MAX
    sf.append(bytes(parse_buf))  # lands at PARSE_BUFFER_ADDR
    sf.append(bytes(storyfile.OOPS_PARSE_BYTES))  # lands at OOPS_PARSE_ADDR
    sf.append(bytes(storyfile.ASK_TEXT_BYTES))  # lands at ASK_TEXT_ADDR
    if layout is not None:
        objects_addr = sf.append(bytes(layout.table))
        # Make the property-table pointers absolute now the base is known.
        for ptr_pos, target in layout.prop_pointers:
            sf.set_word(objects_addr + ptr_pos, objects_addr + target)
    else:
        objects_addr = sf.append(bytes(_PROP_DEFAULTS_BYTES))

    # The scheduling table for after/every: two words per slot (a countdown and a
    # reload), zeroed so every timer starts disarmed. It lives in dynamic memory
    # (the turn loop writes it); its base goes in the __timers__ global below.
    n_timers = len(world.schedule_index)
    timers_addr = sf.append(bytes(n_timers * 4)) if n_timers else 0

    # Scoring (docs/01): one earned byte per award site and pool, zeroed, in
    # dynamic memory; the base goes in __awards__ below. max_score sums
    # itself: every anonymous site, each pool once at its maximum, and five
    # points per auto-scored room and thing. Never typed by hand.
    n_awards = len(world.award_anon) + len(world.award_pools)
    awards_addr = sf.append(bytes(n_awards)) if n_awards else 0
    from .lower import _prop_truthy as _scored_set
    n_scored = sum(
        1 for o in world.objects.values() if _scored_set(o.props.get("scored"))
    )
    auto_max = (
        sum(world.award_anon)
        + sum(best for (_i, best, _l) in world.award_pools.values())
        + 5 * n_scored
    )

    # Static memory: abbreviations and the dictionary built from the program's
    # vocabulary. The 96-word abbreviation table comes first; when a set is
    # installed (set in generate(), empty in the driven backend tests) each
    # abbreviation string is laid out just after the table, encoded literally so
    # it holds no nested reference, and its table word points at the string's word
    # address (byte address / 2). Unused entries share one empty string.
    static_base = sf.here()
    abbrev_addr = sf.append(bytes(_ABBREV_BYTES))
    abbrevs = zstring.active_abbreviations()
    if abbrevs:
        empty_addr = sf.here()
        sf.append(zstring.encode("", abbrevs=[]))
        for k, s in enumerate(abbrevs):
            while sf.here() % 2 != 0:
                sf.append(b"\x00")
            saddr = sf.here()
            sf.append(zstring.encode(s, abbrevs=[]))
            sf.set_word(abbrev_addr + k * 2, saddr // 2)
        for k in range(len(abbrevs), _ABBREV_BYTES // 2):
            sf.set_word(abbrev_addr + k * 2, empty_addr // 2)
    dprops = dictionary.direction_props(layout, world) if layout is not None else None
    # Scenery grain chains. One word can serve several grains in several rooms
    # ("steps" in the hallway AND the cellar), so the dictionary entry cannot hold
    # a single (grain, owner) pair. Instead each grain word points at a chain: a
    # static run of (grain id, owner) word pairs, zero-id terminated, and the
    # parser answers with the first grain whose owner is in scope. The chains sit
    # right before the dictionary; their addresses go into the entries' data bytes.
    scenery = {}
    if layout is not None:
        word_grains: dict = {}
        for idx, grain, owner in _all_grains(world):
            onum = layout.obj_number.get(owner, 0)
            for w in grain.words:
                word_grains.setdefault(w.lower(), []).append((idx + 1, onum))
        if word_grains:
            chains = bytearray()
            chains_base = sf.here()
            for w in sorted(word_grains):
                scenery[w] = chains_base + len(chains)
                for gid, onum in word_grains[w]:
                    chains += bytes(
                        [(gid >> 8) & 0xFF, gid & 0xFF, (onum >> 8) & 0xFF, onum & 0xFF]
                    )
                chains += b"\x00\x00"  # terminator: grain id 0
            sf.append(bytes(chains))
    # Positional grammar tables (docs/02 section 8c): one static table per verb
    # the flag model cannot represent (worldmodel.needs_table). Each table is a
    # run of lines in matcher order (worldmodel.table_line_order): an action
    # byte, then one byte per token (1 noun, 2 held, 3 multi, 4 text; 5 is a
    # literal word and carries its dictionary address in the next two bytes),
    # a zero closing the line, and a zero in action position closing the table.
    # The literal addresses are backpatched once the dictionary is placed, the
    # same way object `words` properties are. The tables sit with the grain
    # chains, right before the dictionary; a game with no tabled verb emits
    # nothing here and its story file is byte-identical.
    grammar_tables: dict = {}
    grammar_fixups: list = []  # (absolute position, literal word)
    # 6 is a `direction` slot: it consumes one direction-flagged word (the
    # value rides `way`, which the parser binds before the tables run).
    slot_codes = {"noun": 1, "held": 2, "multi": 3, "text": 4, "direction": 6}
    tabled = wm.tabled_verbs(world) if layout is not None else []
    if tabled:
        actions_map = _action_numbers(world)
        tb = bytearray()
        tbase = sf.here()
        for verb in tabled:
            taddr = tbase + len(tb)
            for phrase in verb.words:
                grammar_tables[phrase.lower()] = taddr  # sema: single words only
            for gline in wm.table_line_order(verb.grammar):
                tb.append(actions_map[gline.action] & 0xFF)
                for it in gline.items:
                    if isinstance(it, ast.Slot):
                        tb.append(slot_codes.get(it.kind, 1))
                    else:
                        tb.append(5)
                        grammar_fixups.append((tbase + len(tb), it.text.lower()))
                        tb += b"\x00\x00"
                tb.append(0)  # end of line
            tb.append(0)  # end of table (a zero where an action would be)
        sf.append(bytes(tb))
    dict_bytes, word_offsets = dictionary.build(
        world, _action_numbers(world), dprops, scenery, grammar_tables
    )
    dict_addr = sf.append(dict_bytes)
    # Now the dictionary is placed, point each literal token at its word.
    for pos, word in grammar_fixups:
        sf.set_word(pos, dict_addr + word_offsets[word])

    # High memory: the entry stub and routines, run from the initial PC.
    high_base = sf.here()
    blob, initial_pc, strrefs, packed_routines = link(entry, routines, high_base, scale)
    blob_start = sf.here()
    sf.append(blob)

    # Packed strings (object descriptions and strings allocated during lowering)
    # live in high memory, scale-aligned so their packed addresses are exact.
    all_strings: dict[str, str] = {}
    if layout is not None:
        all_strings.update(layout.strings)
    if string_pool is not None:
        all_strings.update(string_pool.strings)
    # The strings all sit above the routines, so the packed address where they
    # begin is the threshold that tells a computed property's routine address (below
    # it) from a plain string address (at or above it): the __timers__/__strings__
    # "print or run" test in lower.py.
    while sf.here() % scale != 0:
        sf.append(b"\x00")
    strings_start_packed = sf.here() // scale
    # Identical text is laid out ONCE and every reference shares the address:
    # two rooms with the same desc, a string constant used across several
    # properties, a repeated message. Smallest possible z-code is the charter.
    string_packed: dict[str, int] = {}
    text_packed: dict[str, int] = {}
    for sid, text in all_strings.items():
        at = text_packed.get(text)
        if at is None:
            while sf.here() % scale != 0:
                sf.append(b"\x00")
            at = sf.here() // scale
            sf.append(zstring.encode(text))
            text_packed[text] = at
        string_packed[sid] = at
    # Backpatch the object table (desc properties and react routine addresses)
    # and the code (string refs).
    if layout is not None:
        for offset, sid in layout.string_fixups:
            sf.set_word(objects_addr + offset, string_packed[sid])
        for offset, rname in layout.routine_fixups:
            sf.set_word(objects_addr + offset, packed_routines[rname])
        # Each words-property entry gets its word's absolute dictionary address.
        for offset, word in layout.word_fixups:
            sf.set_word(objects_addr + offset, dict_addr + word_offsets[word])
        # Text globals: the initializer's packed string address into the slot.
        for gname, sid in layout.global_strings:
            sf.set_word(
                globals_addr + (_globals_map(world)[gname] - 16) * 2,
                string_packed[sid],
            )
    for pos, sid in strrefs:
        sf.set_word(blob_start + pos, string_packed[sid])

    # Bootstrap the location globals so the turn loop starts in the right place:
    # here = the start room, player = the player object. Globals default to 0, so
    # without this the loop would begin in "nothing". Driven tests still set their
    # own values at run time; this only seeds the defaults.
    if layout is not None:
        gmap = _globals_map(world)
        start = world.start_room
        if start and start in layout.obj_number:
            sf.set_word(globals_addr + (gmap["here"] - 16) * 2, layout.obj_number[start])
        if "player" in layout.obj_number:
            sf.set_word(globals_addr + (gmap["player"] - 16) * 2, layout.obj_number["player"])
        # The scheduling table base, so after/every can reach it at run time.
        sf.set_word(globals_addr + (gmap["__timers__"] - 16) * 2, timers_addr)
        # The catalog region's byte address (docs/01, catalogs); zero, and
        # never read, in a game with no author catalogs, no spilled kind, no
        # matrix, and no stateful vary site (all of which share this region
        # and read through this base).
        if (layout.catalogs or layout.kind_catalog or layout.matrices
                or getattr(world, "vary_slots", 0)):
            sf.set_word(
                globals_addr + (gmap["__catalogs__"] - 16) * 2,
                objects_addr + layout.catalog_region_off,
            )
        # The string-area threshold, for the computed-property "print or run"
        # test, pre-biased by +0x8000 so the runtime's signed jl orders the two
        # biased sides as the unsigned packed addresses they really are.
        sf.set_word(
            globals_addr + (gmap["__strings__"] - 16) * 2,
            (strings_start_packed + 0x8000) & 0xFFFF,
        )
        # The routines threshold (computed exits, exit_dest): the lowest packed
        # routine address, pre-biased the same way. A stored value at or above
        # it is a block routine to run; below it is a plain room number.
        if packed_routines:
            routines_start_packed = min(packed_routines.values())
            sf.set_word(
                globals_addr + (gmap["__routines__"] - 16) * 2,
                (routines_start_packed + 0x8000) & 0xFFFF,
            )
        # The base font colour starts as the interpreter default (1), so a
        # say.<colour> before any zcolor.font still restores sanely.
        sf.set_word(globals_addr + (gmap["__zcfont__"] - 16) * 2, 1)
    # Seed every game global's declared initial value (they were silently
    # zero before ambience_rate = 8 became the first nonzero initializer):
    # numbers and booleans directly, an object reference by its number.
    for gname, g in world.globals.items():
        val = None
        v = g.value
        if isinstance(v, ast.Number):
            val = v.value & 0xFFFF
        elif isinstance(v, ast.Bool):
            val = 1 if v.value else 0
        elif isinstance(v, ast.Name):
            if v.ident == "nothing":
                val = 0
            elif layout is not None and v.ident in layout.obj_number:
                val = layout.obj_number[v.ident]
            elif layout is not None and v.ident in layout.catalogs:
                # a catalog reference: its region word offset, the same
                # value the name means in any expression (the field bug:
                # this fell through silently and the global aliased the
                # region's FIRST occupant through a zero)
                val = layout.catalogs[v.ident]
            elif layout is not None and v.ident in layout.matrices:
                val = layout.matrices[v.ident]
            elif layout is not None and v.ident in layout.prop_number \
                    and v.ident in _PRELUDE_DIRECTIONS:
                # a direction: its property number, as everywhere
                val = layout.prop_number[v.ident]
        if val:
            sf.set_word(globals_addr + (gmap[gname] - 16) * 2, val)
    if layout is not None and layout.ambience_off >= 0:
        sf.set_word(
            globals_addr + (gmap["__ambience__"] - 16) * 2,
            objects_addr + layout.ambience_off,
        )
    if awards_addr:
        sf.set_word(globals_addr + (gmap["__awards__"] - 16) * 2, awards_addr)
    if auto_max:
        sf.set_word(globals_addr + (gmap["max_score"] - 16) * 2, auto_max)
    if layout is not None and layout.ranks_off >= 0:
        sf.set_word(
            globals_addr + (gmap["__ranks__"] - 16) * 2,
            objects_addr + layout.ranks_off,
        )
        # The thresholds: pinned entries at their percent of max, the rest
        # spread evenly; the last rank always means full score.
        for pos, pin, i, count in layout.rank_sites:
            if pin is not None and pin[0] == "points":
                # A definite pin: the author's exact threshold, verbatim.
                pts = pin[1]
            elif pin is not None:
                pts = auto_max * pin[1] // 100
            elif count > 1:
                pts = auto_max * i // (count - 1)
            else:
                pts = 0
            sf.set_word(objects_addr + pos, pts)
    m = _meta(world)
    # Flags 2: the story's own announcements (Standard 1.1 section 11.1). Bit 4:
    # the game uses undo (Cosmos ships save_undo in the meta verbs). Bit 6: the
    # game uses colours; interpreters like Frotz enable their colour machinery
    # only when the story declares this, so without it set_colour is ignored.
    flags2 = 1 << 4
    if world.uses_colours:
        flags2 |= 1 << 6
    sf.set_word(storyfile.H_FLAGS2, flags2)
    sf.set_word(storyfile.H_RELEASE, m.get("release", 1))
    sf.set_word(storyfile.H_HIGH_BASE, high_base)
    sf.set_word(storyfile.H_INITIAL_PC, initial_pc)
    sf.set_word(storyfile.H_DICTIONARY, dict_addr)
    sf.set_word(storyfile.H_OBJECTS, objects_addr)
    sf.set_word(storyfile.H_GLOBALS, globals_addr)
    sf.set_word(storyfile.H_STATIC_BASE, static_base)
    sf.set_word(storyfile.H_ABBREV, abbrev_addr)
    serial = m.get("serial") or datetime.date.today().strftime("%y%m%d")
    sf.set_serial(serial)

    img = sf.finalize()
    if stats is not None:
        # The image-level numbers for the --stats report (the world-model numbers
        # are filled by _generate). Ceilings travel with the values so the report
        # never hardcodes a limit the compiler does not enforce.
        strings_begin = blob_start + len(blob)
        stats.update(
            award_sites=len(world.award_anon),
            award_pools=len(world.award_pools),
            scored_auto=n_scored,
            max_score=auto_max,
            ranks=len(world.ranks),
            dict_words=len(set(word_offsets.values())),
            abbrevs=len(abbrevs),
            abbrevs_max=zstring.ABBREV_MAX,
            readable_bytes=high_base,
            readable_max=65536,
            code_bytes=len(blob),
            string_bytes=len(img) - strings_begin,
            story_bytes=len(img),
            story_max=65536 * scale,
        )
    return img


def _self_operand(world: wm.World, handler: wm.Handler, layout):
    """What `self` is inside a handler routine (docs/01 section 9: the enclosing
    object). An OWNED handler (on an object or a kind) reads its self object from
    the routine's first argument: the per-object react routine passes its own
    object, so a kind handler shared by many objects sees the RIGHT instance,
    even when dispatched on the second noun (a container's `on put`) or the room
    (a room kind's `on enter`), not the noun. A free-standing rule has no owner,
    so its self is the noun, the object the rule acts on."""
    if handler.owner is not None:
        return Variable(1)
    return Variable(_globals_map(world)["noun"])


def _hoist_alters(world, gmap, layout, pool, handler, name):
    """Every `alter` in this handler becomes its own tiny routine: the
    statement REGISTERS the replacement report (its packed address lands in
    the `altered` global) and the library calls it at report time, only if
    the action succeeds (the field report from Charles Moore Jr.: the old
    eager print narrated success before validation, and the drunk staggered
    west into "there is no exit"). `self` is captured at registration into
    altered_self, so a kind's alter names the right instance at fire time.
    Handler locals cannot cross into the deferred routine (no closures on
    the Z-machine); the body reads globals, noun, and self."""
    from .lower import _walk_contains, _say
    found = []

    def collect(n):
        if isinstance(n, ast.Alter):
            found.append(n)
        return False  # keep walking; collection wants every site

    for stmt in handler.body:
        _walk_contains(stmt, collect)
    extras, amap = [], {}
    for i, node in enumerate(found):
        rname = f"{name}_a{i}"
        aux = Routine(rname, nlocals=0)
        ctx = Context(world, gmap, layout=layout,
                      self_value=Variable(gmap["altered_self"]),
                      string_pool=pool)
        # The alter body is a deferred report routine, not handler flow, so
        # `continue` is illegal here; the marker lets the error name where
        # continue belongs (the handler body, one indent out).
        ctx.in_alter_block = True
        if node.value is not None:
            _say(aux, ctx, node.value)
        else:
            ctx.prescan(node.body)
            compile_block(aux, ctx, node.body)
        aux.op("rtrue")
        aux.nlocals = ctx.nlocals()
        extras.append(aux)
        amap[id(node)] = rname
    return extras, amap


def _compile_handler(world, gmap, layout, pool, handler, name) -> Routine:
    # An owned handler takes its self object as the routine's first argument
    # (the per-object react routine passes it); a free rule takes none and reads
    # the noun. The reserved slot keeps the body's own locals starting after it.
    params = ("__self__",) if handler.owner is not None else ()
    rt = Routine(name, nlocals=len(params))
    ctx = Context(
        world,
        gmap,
        params=params,
        layout=layout,
        self_value=_self_operand(world, handler, layout),
        in_handler=True,
        string_pool=pool,
    )
    extras, amap = _hoist_alters(world, gmap, layout, pool, handler, name)
    ctx.alter_map = amap
    ctx.prescan(handler.body)
    # A `when` guard: if the condition is false the handler does not apply, so
    # skip the body and pass the action on (return 0).
    skip = None
    if handler.when is not None:
        skip = ctx.new_label()
        cond_jump(rt, ctx, handler.when, skip, False)
    if not compile_block(rt, ctx, handler.body):
        rt.op("ret", _CONST_ONE)  # falling off the end consumes the action
    if skip is not None:
        rt.label(skip)
        rt.op("ret", Const(0))
    rt.nlocals = ctx.nlocals()
    return [rt] + extras


def _compile_block(world, gmap, layout, pool, blk) -> Routine:
    rt = Routine("blk_" + blk.name, nlocals=len(blk.params))
    ctx = Context(world, gmap, params=blk.params, layout=layout, string_pool=pool)
    ctx.prescan(blk.body)
    if not compile_block(rt, ctx, blk.body):
        rt.op("rfalse")  # default return value if the block does not return one
    rt.nlocals = ctx.nlocals()
    return rt


def build_routines(world: wm.World, gmap: dict, layout, pool):
    """Emit a routine for the main entry, every `block`, and every handler
    except `on start` (which runs inside main for now). Returns the main
    routine, the extra routines, and a registry mapping each handler to its
    routine name for the dispatcher (B4.5b)."""
    # __main__ prints the banner and then hands control to the Cosmos turn loop
    # (block run_game). When Cosmos is absent (unit tests on a bare world) there
    # is no loop, so __main__ falls back to running `on start` inline, preserving
    # the older behavior those tests rely on.
    main = Routine("__main__", nlocals=0)
    # The banner lives in its own routine so a game can defer it: `banner false`
    # in the game block stops the automatic print, and the print_banner()
    # intrinsic calls the routine whenever the author wants it (a quote box or
    # pregame prelude first, the banner after). Never called at all, DCE drops
    # it (H2's "return 2" pattern).
    banner_rt = Routine("cosmos_banner", nlocals=0)
    _emit_banner(banner_rt, world)
    banner_rt.op("rfalse")
    if "run_game" in world.blocks:
        # The turn loop (run_game) prints the banner itself, AFTER `on start`,
        # so a game that sets its screen colours in `on start` has them in place
        # first and the banner is not erased (the Inform Initialise order). It
        # respects `banner false` through the auto_banner flag.
        main.op("call_vn", RoutineRef("blk_run_game"))
    else:
        # No Cosmos turn loop (bare-world unit tests): print the banner here and
        # run `on start` inline, the older behavior those tests rely on.
        if _meta(world).get("banner") is not False:
            main.op("call_vn", RoutineRef("cosmos_banner"))
        start = _start_handler(world)
        if start is not None:
            ctx = Context(world, gmap, layout=layout, in_handler=True, string_pool=pool)
            ctx.prescan(start.body)
            compile_block(main, ctx, start.body)
            main.nlocals = ctx.nlocals()
    main.op("rfalse")

    routines = [banner_rt]
    for blk in world.blocks.values():
        routines.append(_compile_block(world, gmap, layout, pool, blk))

    # Every handler becomes a routine the dispatcher / turn loop can call; `start`
    # is no longer special (it runs through react_free via the loop).
    inline_start = "run_game" not in world.blocks
    registry = []
    n = 0
    for handler in world.all_handlers():
        if inline_start and "start" in handler.events:
            continue  # compiled into main in the no-Cosmos fallback
        name = f"h{n}"
        n += 1
        routines.extend(_compile_handler(world, gmap, layout, pool, handler, name))
        registry.append((handler, name))

    return main, routines, registry


def gen_exit_routines(layout) -> list:
    """The backing routines for the exit_prop / exit_name intrinsics: je-chains
    over this program's direction properties, indexed in the same order as
    lower.exit_directions. cosmos_exit_prop(i) returns the i-th direction's
    property number; cosmos_exit_name(i) prints its canonical name. Emitted only
    when those intrinsics are actually called (gated in generate), so an
    unsummoned verbose_exits granule adds nothing to the story file."""
    from .lower import exit_directions

    dirs = exit_directions(layout)

    prop = Routine("cosmos_exit_prop", nlocals=1)  # local 1 holds the index
    for i in range(len(dirs)):
        prop.op("je", Variable(1), Const(i), branch=(f"p{i}", True))
    prop.op("ret", Const(0))  # index out of range
    for i, name in enumerate(dirs):
        prop.label(f"p{i}")
        prop.op("ret", Const(layout.prop_number[name]))

    dn = Routine("cosmos_dir_name", nlocals=1)  # local 1 = the property number
    for i, name in enumerate(dirs):
        dn.op("je", Variable(1), Const(layout.prop_number[name]),
              branch=(f"d{i}", True))
    dn.op("rtrue")  # no direction (way 0): print nothing
    for i, name in enumerate(dirs):
        dn.label(f"d{i}")
        dn.op("print", text=name)
        dn.op("rtrue")

    nm = Routine("cosmos_exit_name", nlocals=1)
    for i in range(len(dirs)):
        nm.op("je", Variable(1), Const(i), branch=(f"n{i}", True))
    nm.op("rtrue")  # index out of range: print nothing
    for i, name in enumerate(dirs):
        nm.label(f"n{i}")
        nm.op("print", text=name)
        nm.op("rtrue")
    return [prop, nm, dn]


def _topic_objects(world: wm.World):
    """Objects carrying `topic` declarations, as (name, obj). Kind-level topics
    are deferred for the same reason kind grains are (they need per-instance
    scope), so only instances are placed."""
    return [(n, o) for n, o in world.objects.items() if o.topics]


def gen_ambience_routines(world: wm.World, gmap: dict, layout, pool) -> list:
    """For every ambience block (summon.ambience): a play routine (je-dispatch
    over the lines: say the string, or call the do-block), a block guard when
    the header has a `when`, and a line-guard routine when any line does. The
    ambience table (objects.py) names them by fixup, which also roots them for
    dead-code elimination, exactly like the topic routines."""
    routines = []
    for name, obj in world.objects.items():
        owner_num = layout.obj_number.get(name, 0)
        for idx, amb in enumerate(obj.ambiences):
            # The play routine: local 1 is the line index.
            rt = Routine(objmod.amb_play_name(name, idx), nlocals=1)
            ctx = Context(
                world, gmap, params=["__k__"], layout=layout,
                in_handler=True, string_pool=pool, self_value=Const(owner_num),
            )
            labels = [f"l{k}" for k in range(len(amb.lines))]
            for k, lbl in enumerate(labels):
                rt.op("je", Variable(1), Const(k), branch=(lbl, True))
            rt.op("ret", Const(0))
            for k, (line, lbl) in enumerate(zip(amb.lines, labels)):
                rt.label(lbl)
                body = [ast.Say(line.text)] if line.text is not None else [
                    ast.ExprStmt(ast.Call(line.do, []))
                ]
                ctx.prescan(body)
                compile_block(rt, ctx, body)
                rt.op("ret", _CONST_ONE)
            rt.nlocals = ctx.nlocals()
            routines.append(rt)
            # The block guard: returns 1 while the header condition holds.
            if amb.when is not None:
                routines.append(_compile_amb_cond(
                    world, gmap, layout, pool, owner_num,
                    objmod.amb_guard_name(name, idx), amb.when))
            # The line guards: local 1 is the line index; unguarded lines pass.
            if any(l.when is not None for l in amb.lines):
                lg = Routine(objmod.amb_lg_name(name, idx), nlocals=1)
                lctx = Context(
                    world, gmap, params=["__k__"], layout=layout,
                    in_handler=False, string_pool=pool, self_value=Const(owner_num),
                )
                lctx.prescan([])
                for k, line in enumerate(amb.lines):
                    if line.when is None:
                        continue
                    yes = lctx.new_label()
                    skip = lctx.new_label()
                    lg.op("je", Variable(1), Const(k), branch=(yes, True))
                    lg.jump(skip)
                    lg.label(yes)
                    ok = lctx.new_label()
                    cond_jump(lg, lctx, line.when, ok, True)
                    lg.op("ret", Const(0))
                    lg.label(ok)
                    lg.op("ret", _CONST_ONE)
                    lg.label(skip)
                lg.op("ret", _CONST_ONE)
                lg.nlocals = lctx.nlocals()
                routines.append(lg)
    return routines


def _compile_amb_cond(world, gmap, layout, pool, owner_num, rname, when) -> Routine:
    """A 1/0 condition routine, the topicwhen shape, under the given name."""
    rt = Routine(rname, nlocals=0)
    ctx = Context(
        world, gmap, layout=layout, self_value=Const(owner_num),
        in_handler=False, string_pool=pool,
    )
    ctx.prescan([])
    yes = ctx.new_label()
    cond_jump(rt, ctx, when, yes, True)
    rt.op("ret", Const(0))
    rt.label(yes)
    rt.op("ret", _CONST_ONE)
    rt.nlocals = ctx.nlocals()
    return rt


def gen_topic_routines(world: wm.World, gmap: dict, layout, pool) -> list:
    """For every person with topics, a body routine per topic and a when-guard
    routine for each topic that has a `when`. The topic table (objects.py)
    references these by their deterministic names, so they are always emitted
    when topics exist, independent of whether a conversation granule walks the
    table. Mirrors the react / grain routine pattern."""
    routines = []
    for name, obj in _topic_objects(world):
        owner_num = layout.obj_number.get(name, 0)
        for idx, topic in enumerate(obj.topics):
            routines.append(
                _compile_topic_body(world, gmap, layout, pool, obj.topics, owner_num, name, idx, topic)
            )
            if topic.when is not None:
                routines.append(
                    _compile_topic_when(world, gmap, layout, pool, owner_num, name, idx, topic.when)
                )
    return routines


def _compile_topic_body(world, gmap, layout, pool, topics, owner_num, name, idx, topic) -> Routine:
    """topic_<obj>_<idx>(): run the topic's exchange. `self` is the person, so a
    `reply` line attributes to their name and `reveal`/`hide` address sibling
    topics by index (resolved from the subject -> index map)."""
    rt = Routine(objmod.topic_routine_name(name, idx), nlocals=0)
    ctx = Context(
        world, gmap, layout=layout, self_value=Const(owner_num),
        in_handler=True, string_pool=pool,
    )
    # reveal/hide name a sibling topic; resolve the subject to its table index now.
    ctx.topic_index = {t.subject: i for i, t in enumerate(topics)}
    ctx.prescan(topic.body)
    if not compile_block(rt, ctx, topic.body):
        rt.op("rtrue")
    rt.nlocals = ctx.nlocals()
    return rt


def _compile_topic_when(world, gmap, layout, pool, owner_num, name, idx, when) -> Routine:
    """topicwhen_<obj>_<idx>(): the topic's visibility guard. Returns 1 when the
    `when` condition holds, else 0, so cosmos_topic_visible can gate on it."""
    rt = Routine(objmod.topic_when_name(name, idx), nlocals=0)
    ctx = Context(
        world, gmap, layout=layout, self_value=Const(owner_num),
        in_handler=False, string_pool=pool,
    )
    ctx.prescan([])
    yes = ctx.new_label()
    cond_jump(rt, ctx, when, yes, True)
    rt.op("ret", Const(0))
    rt.label(yes)
    rt.op("ret", _CONST_ONE)
    rt.nlocals = ctx.nlocals()
    return rt


def gen_topic_helpers(layout) -> list:
    """The cosmos_topic_* backing routines the conversation granules call to walk
    a person's topic table without knowing its byte layout. Emitted only when
    referenced (gated in generate), so a game with topics but no conversation
    granule pays only for the table itself. The record layout is objmod.TOPIC_*."""
    tp = layout.prop_number["topics"]
    rec = objmod.TOPIC_REC

    # cosmos_topics_count(person): the number of topics (0 if the person has none).
    count = Routine("cosmos_topics_count", nlocals=2)  # 1=person, 2=table
    count.op("get_prop", Variable(1), Const(tp), store=Variable(2))
    count.op("jz", Variable(2), branch=("none", True))
    count.op("loadw", Variable(2), Const(0), store=Variable(STACK))
    count.op("ret", Variable(STACK))
    count.label("none")
    count.op("ret", Const(0))

    # cosmos_topic_rec(person, i): the address of topic i's record (table + 2 +
    # i*rec). Callers pass an index drawn from the count, so the table exists.
    recrt = Routine("cosmos_topic_rec", nlocals=3)  # 1=person, 2=i, 3=table
    recrt.op("get_prop", Variable(1), Const(tp), store=Variable(3))
    recrt.op("mul", Variable(2), Const(rec), store=Variable(STACK))
    recrt.op("add", Variable(3), Variable(STACK), store=Variable(STACK))
    recrt.op("add", Variable(STACK), Const(2), store=Variable(STACK))
    recrt.op("ret", Variable(STACK))

    # cosmos_topic_label(person, i): print topic i's menu label (no newline). The
    # label packed-string address is the word at rec+2 (loadw index 1).
    label = Routine("cosmos_topic_label", nlocals=2)
    label.op("call_vs", RoutineRef("cosmos_topic_rec"), Variable(1), Variable(2), store=Variable(STACK))
    label.op("loadw", Variable(STACK), Const(1), store=Variable(STACK))
    label.op("print_paddr", Variable(STACK))
    label.op("rtrue")

    # cosmos_topic_visible(person, i): 1 when topic i is in view: not retired, not
    # hidden, and its `when` guard (rec+4) absent or true.
    vis = Routine("cosmos_topic_visible", nlocals=4)  # 1=person,2=i,3=rec,4=when
    vis.op("call_vs", RoutineRef("cosmos_topic_rec"), Variable(1), Variable(2), store=Variable(3))
    vis.op("loadb", Variable(3), Const(9), store=Variable(STACK))  # live state byte
    vis.op("and", Variable(STACK), Const(objmod.TOPIC_RETIRED | objmod.TOPIC_HIDDEN), store=Variable(STACK))
    vis.op("jz", Variable(STACK), branch=("live", True))
    vis.op("rfalse")  # retired or hidden
    vis.label("live")
    vis.op("loadw", Variable(3), Const(2), store=Variable(4))  # when-guard at rec+4
    vis.op("jz", Variable(4), branch=("shown", True))  # no guard: visible
    vis.op("call_vs", Variable(4), store=Variable(STACK))
    vis.op("ret", Variable(STACK))
    vis.label("shown")
    vis.op("rtrue")

    # cosmos_topic_run(person, i): run topic i's body, then retire it if `once`.
    run = Routine("cosmos_topic_run", nlocals=3)  # 1=person,2=i,3=rec
    run.op("call_vs", RoutineRef("cosmos_topic_rec"), Variable(1), Variable(2), store=Variable(3))
    run.op("loadw", Variable(3), Const(0), store=Variable(STACK))  # body routine addr
    run.op("call_vs", Variable(STACK), store=Variable(STACK))
    run.op("loadb", Variable(3), Const(8), store=Variable(STACK))  # flags byte
    run.op("and", Variable(STACK), Const(objmod.TOPIC_ONCE), store=Variable(STACK))
    run.op("jz", Variable(STACK), branch=("done", True))
    run.op("loadb", Variable(3), Const(9), store=Variable(STACK))  # state byte
    run.op("or", Variable(STACK), Const(objmod.TOPIC_RETIRED), store=Variable(STACK))
    run.op("storeb", Variable(3), Const(9), Variable(STACK))
    run.label("done")
    run.op("rtrue")

    # cosmos_topic_matches(person, i, word): 1 if topic i's match-word array holds
    # the dictionary address `word` (the ask/tell subject). 0 if no words.
    match = Routine("cosmos_topic_matches", nlocals=5)  # 1=person,2=i,3=word,4=arr,5=k
    match.op("call_vs", RoutineRef("cosmos_topic_rec"), Variable(1), Variable(2), store=Variable(STACK))
    match.op("loadw", Variable(STACK), Const(3), store=Variable(4))  # words sub-array (rec+6)
    match.op("jz", Variable(4), branch=("no", True))
    match.op("loadw", Variable(4), Const(0), store=Variable(5))  # word count
    match.label("loop")
    match.op("jz", Variable(5), branch=("no", True))
    match.op("loadw", Variable(4), Variable(5), store=Variable(STACK))  # the k-th word
    match.op("je", Variable(STACK), Variable(3), branch=("yes", True))
    match.op("sub", Variable(5), _CONST_ONE, store=Variable(5))
    match.jump("loop")
    match.label("yes")
    match.op("rtrue")
    match.label("no")
    match.op("rfalse")

    # cosmos_topic_retire(person, i): set topic i's RETIRED state bit, so the menu
    # drops it after it is picked. Like cosmos_topic_run's once-path, but forced.
    retire = Routine("cosmos_topic_retire", nlocals=3)  # 1=person,2=i,3=rec
    retire.op("call_vs", RoutineRef("cosmos_topic_rec"), Variable(1), Variable(2), store=Variable(3))
    retire.op("loadb", Variable(3), Const(9), store=Variable(STACK))  # state byte
    retire.op("or", Variable(STACK), Const(objmod.TOPIC_RETIRED), store=Variable(STACK))
    retire.op("storeb", Variable(3), Const(9), Variable(STACK))
    retire.op("rtrue")

    # cosmos_topic_idle(person, i): 1 if topic i is the ask/tell fallback (the
    # IDLE flag bit), else 0. infocom_talking runs the first visible idle topic
    # when no worded topic matched; the menu presentation skips idle topics.
    idle = Routine("cosmos_topic_idle", nlocals=3)  # 1=person,2=i,3=rec
    idle.op("call_vs", RoutineRef("cosmos_topic_rec"), Variable(1), Variable(2), store=Variable(3))
    idle.op("loadb", Variable(3), Const(8), store=Variable(STACK))  # flags byte
    idle.op("and", Variable(STACK), Const(objmod.TOPIC_IDLE), store=Variable(STACK))
    idle.op("jz", Variable(STACK), branch=("no", True))
    idle.op("rtrue")
    idle.label("no")
    idle.op("rfalse")

    return [count, recrt, label, vis, run, match, retire, idle]


_TOPIC_HELPER_NAMES = (
    "cosmos_topics_count", "cosmos_topic_label", "cosmos_topic_visible",
    "cosmos_topic_run", "cosmos_topic_matches", "cosmos_topic_retire",
    "cosmos_topic_idle",
)


def gen_computed_prop_routines(world: wm.World, layout, gmap: dict, pool) -> list:
    """A prop_<obj>_<pname>() routine for every computed (`<name> block`) property,
    running its block with `self` bound to the object. A text property's block says
    its text (the routine returns nothing useful); a value property's returns a
    value. The property table stores each routine's packed address (objects.py)."""
    routines = []
    for objname, pname, is_text, decl in layout.computed_props:
        if not is_text and pname not in world.direction_props:
            # A read of a value property cannot tell a routine address from a plain
            # value, so a general computed value property is unsupported. The one
            # exception is a computed EXIT (a direction property that is a block):
            # its value is a room object NUMBER, always small, so an exit read can
            # tell it from the block routine's large packed address (exit_dest,
            # docs/02 section 11a).
            raise CodegenError(
                f"computed property '{pname}' must be a text property, or a "
                f"direction (a computed exit); a general computed value "
                f"property is not supported",
                getattr(decl, "line", None),
            )
        owner_num = layout.obj_number.get(objname, 0)
        rt = Routine(objmod.prop_routine_name(objname, pname), nlocals=0)
        ctx = Context(
            world, gmap, layout=layout, self_value=Const(owner_num),
            in_handler=True, string_pool=pool,
        )
        ctx.prescan(decl.body)
        if not compile_block(rt, ctx, decl.body):
            rt.op("rtrue")
        rt.nlocals = ctx.nlocals()
        routines.append(rt)
    return routines


def _walk_schedules(body, out: dict) -> None:
    """Collect the block named by every `after`/`every` statement in a body, and
    inside the control-flow that can hold one, in first-seen order."""
    for s in body:
        if isinstance(s, ast.Schedule):
            if s.event not in out:
                out[s.event] = len(out)
        elif isinstance(s, ast.If):
            for c in s.clauses:
                _walk_schedules(c.body, out)
        elif isinstance(s, ast.While):
            _walk_schedules(s.body, out)
        elif isinstance(s, ast.ForEach):
            _walk_schedules(s.body, out)
        elif isinstance(s, ast.Switch):
            for c in s.cases:
                _walk_schedules(c.body, out)


def _collect_schedules(world: wm.World) -> dict:
    """Every distinct block scheduled by an `after`/`every` statement anywhere in
    the program, mapped to its timer slot (docs/02 section 13). Each slot is two
    words in the timer table: a countdown and a reload (0 for a one-shot `after`,
    the period for a recurring `every`)."""
    out: dict = {}
    for blk in world.blocks.values():
        _walk_schedules(blk.body, out)
    for h in world.all_handlers():
        _walk_schedules(h.body, out)
    for h in world.free_handlers:
        _walk_schedules(h.body, out)
    for obj in world.objects.values():
        for topic in obj.topics:
            _walk_schedules(topic.body, out)
    return out


def gen_schedule_tick(world: wm.World, gmap: dict) -> Routine:
    """schedule_tick(): once per turn, count down each armed timer and fire the
    ones that reach zero, reloading the recurring ones. The table base is in the
    __timers__ global; slot i holds its countdown at word 2i and its reload at word
    2i+1. Always emitted (empty when nothing is scheduled) so the turn loop can call
    it unconditionally; the `after`/`every` statement arms a slot (lower.py)."""
    tg = gmap["__timers__"]
    rt = Routine("schedule_tick", nlocals=1)  # local 1 = a slot's countdown, then reload
    for name, i in world.schedule_index.items():
        skip, fire = f"skip{i}", f"fire{i}"
        rt.op("loadw", Variable(tg), Const(2 * i), store=Variable(1))
        rt.op("jz", Variable(1), branch=(skip, True))  # disarmed
        rt.op("sub", Variable(1), _CONST_ONE, store=Variable(1))
        rt.op("storew", Variable(tg), Const(2 * i), Variable(1))
        rt.op("jz", Variable(1), branch=(fire, True))  # reached zero: fire it
        rt.jump(skip)
        rt.label(fire)
        rt.op("call_vn", RoutineRef("blk_" + name))
        rt.op("loadw", Variable(tg), Const(2 * i + 1), store=Variable(1))  # reload
        rt.op("jz", Variable(1), branch=(skip, True))  # one-shot: stays disarmed
        rt.op("storew", Variable(tg), Const(2 * i), Variable(1))  # recurring: re-arm
        rt.label(skip)
    rt.op("rtrue")
    return rt


def _references_routine(routines: list, name: str) -> bool:
    """True if any built routine calls the named routine (a call fixup targets
    it), used to emit a backing routine only when something actually needs it."""
    for r in routines:
        for f in r.fixups:
            if f.kind == "call" and f.target == name:
                return True
    return False


def _prune_unreachable(entry: Routine, routines: list, layout) -> list:
    """Whole-program dead-code elimination: drop every routine the running story
    can never reach (docs/00 section 5, the first size lever).

    The reachability sweep walks the call graph from a set of roots, following
    only `call` fixups (the static "this routine calls that one" edges). The
    subtlety is that not every live routine is reached by a call: the dispatcher
    invokes a handler INDIRECTLY, reading a react or topic routine's packed
    address out of the object table (objects.py routine_fixups) and calling it by
    address, an edge no static scan of the code can see. So we SEED the sweep with
    the entry stub plus every routine the data names (`layout.routine_fixups`),
    then mark transitively. Whatever stays unmarked is compiled in but never run:
    in a given game that is most of Cosmos (the message and verb-default blocks the
    story never triggers, the `you`/`reply` conversation framing when no topic
    runs, the statusline/menu seams when neither granule is summoned). Dropping it
    is safe because a kept routine's call targets are themselves kept (we followed
    them) and its data references are roots (kept), so the linker never dangles."""
    by_name = {r.name: r for r in routines}
    by_name[entry.name] = entry  # the entry stub is linked separately, but seeds the sweep
    reachable: set = set()
    stack: list = [entry.name]
    # Roots reached by address from data: react_<obj>, topic bodies, when-guards.
    for _offset, rname in layout.routine_fixups:
        stack.append(rname)
    while stack:
        nm = stack.pop()
        if nm in reachable:
            continue
        reachable.add(nm)
        r = by_name.get(nm)
        if r is None:
            continue
        for f in r.fixups:
            if f.kind == "call" and f.target not in reachable:
                stack.append(f.target)
    return [r for r in routines if r.name in reachable]


def generate(world: wm.World, version: int = 5, stats=None) -> bytes:
    """Lower the world model to a complete z5 (or z8) story file image.

    The entry stub calls the main routine and quits; main prints the banner and
    runs `on start`. Every other handler and every block is compiled to its own
    routine. The dispatcher and turn loop that drive the handlers arrive with
    Cosmos (B4.5b onward). Pass a dict as `stats` to have it filled with the
    compile statistics the --stats report prints (each value beside its
    ceiling)."""
    # Install the abbreviation set before any text is encoded: the assembler packs
    # inline print text as the routines are built, so the set has to be in force
    # for the whole codegen pass, not just the string layout. Reset afterward so a
    # later driven test (which never installs a set) is not contaminated.
    zstring.set_abbreviations(_abbreviations_for(world))
    try:
        return _generate(world, version, stats)
    finally:
        zstring.set_abbreviations([])


_LAST_LIVE_ROUTINES: set = set()


def harvest_strings(world: wm.World) -> list:
    """Every string the compiler would encode into `world`, gathered with
    abbreviations off so the raw program text is captured, not the abbreviation
    strings themselves. The --make-abbreviations pass and tools/arcabbr.py pool
    this to compute a set. The banner line (story-specific) is dropped, and so
    is the inline text of routines dead-code elimination prunes: encoding
    happens as routines are built, before the prune, so without this filter
    the tuner would spend abbreviation slots on text that never ships (found
    when two long dead prompt strings tipped a tuned set below the default)."""
    saved_default = abbrev.DEFAULT_ABBREVS
    saved_world = world.abbreviations
    abbrev.DEFAULT_ABBREVS = []
    world.abbreviations = None
    zstring.begin_harvest()
    assembler.TEXT_LOG = []
    try:
        generate(world)
    finally:
        strings = zstring.end_harvest()
        log = assembler.TEXT_LOG
        assembler.TEXT_LOG = None
        abbrev.DEFAULT_ABBREVS = saved_default
        world.abbreviations = saved_world
    live = _LAST_LIVE_ROUTINES
    for rname, text in log:
        if rname not in live:
            try:
                strings.remove(text)
            except ValueError:
                pass
    return [s for s in strings if "Serial number" not in s]


def _non_default_language(world: wm.World) -> bool:
    """True when the game selects a language other than English (summon.language
    "spanish"). The baked default abbreviation set is tuned to the English library,
    so it does not apply to another language."""
    for s in getattr(world, "summons", []):
        if getattr(s, "form", None) == "feature" and s.target == "language":
            if s.arg and s.arg.lower() != "english":
                return True
    return False


def _abbreviations_for(world: wm.World) -> list:
    """The abbreviation set for this compile: a summoned abbreviations.granule's
    tuned set when the program supplies one (the --make-abbreviations opt-in),
    otherwise the baked-in default. The override path is wired in B6.2d.

    The baked default is tuned to English, so a non-English game gets no default:
    applying English abbreviations to, say, Spanish text costs the abbreviation
    strings for almost no compression (a small net loss). A foreign-language game
    runs `arcc --make-abbreviations` for a set tuned to its own text; Cosmos does
    not bake a standard set per language."""
    override = getattr(world, "abbreviations", None)
    if override:
        return override
    if _non_default_language(world):
        return []
    return abbrev.DEFAULT_ABBREVS


def _generate(world: wm.World, version: int = 5, stats=None) -> bytes:
    gmap = _globals_map(world)
    # Assign a timer slot to every scheduled block before anything is lowered, so
    # the `after`/`every` statements can arm their slot by index (docs/02 s.13).
    world.schedule_index = _collect_schedules(world)
    actions = _action_numbers(world)
    layout = objmod.build_layout(world, react_objects=_react_objects(world, actions))
    # Text properties computed by a block: a read of one is "print or run" (below).
    world.computed_text_props = {p for _o, p, is_text, _d in layout.computed_props if is_text}
    pool = StringPool()

    entry = Routine("__entry__", entry=True)
    entry.op("call_vn", RoutineRef("__main__"))
    entry.op("quit")

    main, routines, registry = build_routines(world, gmap, layout, pool)
    react_routines = gen_react_routines(world, actions, registry, layout, gmap, pool)
    # Topic body and when-guard routines: emitted whenever a person has topics,
    # because the topic table references them by name. The granule-facing
    # cosmos_topic_* helpers are gated below.
    topic_routines = gen_topic_routines(world, gmap, layout, pool)
    # Ambience play/guard routines (summon.ambience): emitted whenever a block
    # exists; the ambience table roots them by fixup.
    topic_routines += gen_ambience_routines(world, gmap, layout, pool)
    # The per-turn timer sweep for after/every (always emitted, empty when nothing
    # is scheduled; the turn loop calls it through the tick_timers intrinsic).
    schedule_tick = gen_schedule_tick(world, gmap)
    # One routine per computed (`<name> block`) property; the property table stores
    # each one's packed address.
    computed_routines = gen_computed_prop_routines(world, layout, gmap, pool)
    all_routines = [main] + routines + react_routines + topic_routines + [schedule_tick] + computed_routines

    # Emit the exit-enumeration backing routines only if something calls the
    # exit_prop / exit_name intrinsics (the verbose_exits granule). Unsummoned,
    # they are never referenced and never ship.
    if any(_references_routine(all_routines, n)
           for n in ("cosmos_exit_prop", "cosmos_exit_name",
                     "cosmos_dir_name")):
        all_routines += gen_exit_routines(layout)

    # The cosmos_topic_* helpers ship only if a conversation granule calls one
    # (ask/tell dispatch or the menu). A game with topics but no such granule
    # carries the table and bodies but none of the walking machinery.
    if any(_references_routine(all_routines, n) for n in _TOPIC_HELPER_NAMES):
        all_routines += gen_topic_helpers(layout)

    # Whole-program dead-code elimination (B6, the first size lever): the library
    # is compiled in full, but a given game reaches only a fraction of it. Drop the
    # rest before laying out high memory.
    all_routines = _prune_unreachable(entry, all_routines, layout)
    # The survivors, for the abbreviation harvest (harvest_strings): text in
    # a pruned routine never ships, so the tuner must not see it.
    global _LAST_LIVE_ROUTINES
    _LAST_LIVE_ROUTINES = {r.name for r in all_routines} | {entry.name}

    if stats is not None:
        # The world-model numbers for the --stats report, each beside its ceiling
        # where the format has one (the image-level numbers are filled by
        # build_story). Counted after dead-code elimination, so the routine count
        # is what actually ships.
        stats.update(
            objects=len(layout.obj_number),
            kinds=len(world.kinds),
            grains=len(_all_grains(world)),
            topics=sum(len(o.topics) for o in world.objects.values())
            + sum(len(k.topics) for k in world.kinds.values()),
            timers=len(world.schedule_index),
            # Genuine object attributes: the author's real budget, the only
            # thing the 48-attribute ceiling truly bounds. Kinds are shown
            # separately (below), never folded into this, so a kind is never
            # mistaken for an attribute ceiling.
            attributes=len(layout.attr_number),
            attributes_max=objmod._MAX_ATTRIBUTES,
            # Kinds borrow the attribute slots the real attributes leave free
            # (attribute-backed, the fast test) and spill to catalog scans
            # beyond, so kinds are effectively unlimited.
            kinds_backed=len(layout.kind_attr),
            kinds_spilled=len(layout.kind_spilled),
            properties=len(layout.prop_number),
            properties_max=objmod._MAX_PROPERTIES,
            # Matrices (summon.matrix): count, and the dynamic-memory bytes
            # they reserve (header + capacity cells, words in Phase 1). Zero
            # in a game that summons none.
            matrices=len(world.matrices),
            matrix_bytes=sum(
                (m.rows * m.cols + 1) // 2 * 2 if (m.is_2d and m.cell == "byte")
                else m.rows * m.cols * 2 if m.is_2d
                else (2 + m.capacity) * 2
                for m in world.matrices.values()),
            globals=len(gmap),
            globals_max=_GLOBALS_BYTES // 2,
            verbs=len(world.verbs),
            grammar_lines=sum(len(v.grammar) for v in world.verbs),
            actions=len(actions),
            routines=len(all_routines) + 1,  # plus the entry stub
        )

    return build_story(
        world,
        entry,
        all_routines,
        layout=layout,
        string_pool=pool,
        version=version,
        stats=stats,
    )
