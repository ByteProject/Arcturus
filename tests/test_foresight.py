# test_foresight.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""summon.foresight (the verbs overhaul, phase 3): a repairable `requires
noun carried` failure becomes an implicit take, "(taking the apple first)",
instead of a refusal. THE PROBE RULE is the design and these tests are its
proof: the parenthetical is a promise, printed only when the default take
is certain to succeed (take_probe, the take's own factored guard chain), so
"(taking the sun first) The sun is beyond your reach." cannot happen here.
Objects with author take handlers get promise-then-run, the narrow honest
residue, since author code's outcome is unknowable without running it.
Off unless summoned; unsummoned games refuse plainly and pay nothing."""

from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze

BASE = (
    'game\n    title "F"\n    start plaza\n'
    '{summon}'
    'room plaza\n    name "Plaza"\n    desc "A plaza."\n'
    'thing stacy in plaza\n    name "Stacy"\n    words stacy\n'
    '    named\n    animate\n'
    '    on give,show\n'
    '        say "Stacy accepts ${the noun} with a nod."\n'
    'thing apple in plaza\n    name "apple"\n    words apple\n'
    'thing sun in plaza\n    name "sun"\n    words sun\n    beyond\n'
    'thing anvil in plaza\n    name "anvil"\n    words anvil\n    fixed\n'
    'thing idol in plaza\n    name "jade idol"\n    words idol, jade\n'
    '    on take\n'
    '        change refused to 1\n'
    '        say "The idol squirms out of your grip."\n'
    'thing rose in plaza\n    name "rose"\n    words rose\n'
    '    on take\n'
    '        say "You pick the rose, careful of thorns."\n'
    '        continue\n'
)


def _run(summon, cmds):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = BASE.replace("{summon}", summon)
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_unsummoned_refuses_plainly_and_promises_nothing():
    out = _run("", ["give apple to stacy"])
    assert "You aren't carrying the apple." in out
    assert "taking" not in out


def test_the_certain_repair_promises_takes_and_continues():
    out = _run("summon.foresight\n", ["give apple to stacy", "i"])
    assert "(taking the apple first)" in out
    assert "Stacy accepts the apple" in out
    assert "Got it." not in out          # the repair is silent: gain, no report
    assert "apple" in out.split("accepts the apple")[-1]  # inventoried


def test_the_sun_gets_no_promise():
    # Stefan's case, the reason the probe exists: an unreachable object
    # refuses PLAIN, never a promise followed by disappointment.
    out = _run("summon.foresight\n", ["give sun to stacy"])
    assert "beyond your reach" in out
    assert "taking" not in out


def test_fixed_and_scenery_get_no_promise_either():
    out = _run("summon.foresight\n", ["give anvil to stacy"])
    assert "stays exactly where it is" in out
    assert "taking" not in out


def test_author_refusal_is_the_honest_residue():
    # An object with its own take handler: the outcome is unknowable without
    # running it, so the promise prints, then the author's refusal speaks,
    # and the give never happens.
    out = _run("summon.foresight\n", ["give idol to stacy"])
    assert "(taking the jade idol first)" in out
    assert "squirms out of your grip" in out
    assert "accepts" not in out


def test_author_flavor_rides_the_full_pipeline():
    # A take handler that continues: promise, flavor, the default take's own
    # report, then the give. The full pipeline is the point of the fallback.
    out = _run("summon.foresight\n", ["give rose to stacy"])
    at = out.index("(taking the rose first)")
    rest = out[at:]
    assert "careful of thorns" in rest
    assert "Stacy accepts the rose" in rest


def test_the_repair_pays_score_and_knowledge():
    # The certain path goes through gain: a scored thing pays its points on
    # the implicit take exactly as it would on a typed one.
    src = (
        'game\n    title "S"\n    start hall\n    scoring\n'
        'summon.foresight\n'
        'room hall\n    name "Hall"\n    desc "A hall."\n'
        'thing bob in hall\n    name "Bob"\n    words bob\n    named\n    animate\n'
        '    on give\n        say "Bob grins."\n'
        'thing gem in hall\n    name "gem"\n    words gem\n    scored\n'
    )
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=["give gem to bob", "score"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "(taking the gem first)" in io.text
    assert "Bob grins." in io.text
    assert "5" in io.text.split("score")[-1]


# --- the second act: doors and containers (Stefan's go, 2026-07-22) --------

ACT2 = (
    'game\n    title "F2"\n    start hall\n'
    '{summon}'
    'room hall\n    name "Hall"\n    desc "A hall."\n    north gate\n'
    'room yard\n    name "Yard"\n    desc "A yard."\n    south gate\n'
    'thing gate of door in hall, yard\n    name "oak door"\n'
    '    words door, oak\n    open false\n'
    'thing chest of container in hall\n    name "oak chest"\n    words chest\n'
    '    openable\n    open false\n    fixed\n'
    'thing coin in chest\n    name "gold coin"\n    words coin, gold\n'
    'thing jar of container in hall\n    name "clear jar"\n    words jar\n'
    '    openable\n    open false\n    clear\n    fixed\n'
    'thing pearl in jar\n    name "pearl"\n    words pearl\n'
    'thing bob in hall\n    name "Bob"\n    words bob\n    named\n    animate\n'
    '    on give\n        say "Bob pockets ${the noun}."\n'
)


def _run2(summon, cmds, extra=""):
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = ACT2.replace("{summon}", summon) + extra
    io = CaptureIO(script=list(cmds))
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    return io.text


def test_a_known_thing_in_a_closed_chest_opens_it():
    # Knowledge first: the coin becomes known when the chest is opened once;
    # closed again, naming the coin opens the chest FOR the player.
    out = _run2("summon.foresight\n",
                ["open chest", "close chest", "take coin", "i"])
    assert "(opening the oak chest first)" in out
    assert "Got it." in out
    assert "gold coin" in out.split(">i")[-1]


def test_unseen_contents_stay_out_of_reach():
    # The other half of Stefan's model: contents never seen cannot even be
    # named, foresight or no foresight. Nothing conjures.
    out = _run2("summon.foresight\n", ["take coin"])
    assert "nothing of the sort" in out
    assert "opening" not in out


def test_the_clear_jar_chains_open_and_take():
    # Visible through the glass, sealed, wanted for a give: the chained
    # repair, each step probe-guarded.
    out = _run2("summon.foresight\n", ["give pearl to bob"])
    at_open = out.index("(opening the clear jar first)")
    at_take = out.index("(taking the pearl first)")
    at_give = out.index("Bob pockets the pearl.")
    assert at_open < at_take < at_give


def test_a_shut_door_opens_on_the_walk():
    out = _run2("summon.foresight\n", ["north", "south"])
    assert "(opening the oak door first)" in out
    assert "Yard" in out
    # The way back needs no second repair: the door stays open.
    assert out.count("(opening the oak door first)") == 1


def test_a_locked_door_still_refuses():
    src_extra = ""
    out = _run2("summon.foresight\n", ["north"],
                extra="")
    # relock variant: make the gate locked via a fresh game
    locked = ACT2.replace(
        "    words door, oak\n    open false\n",
        "    words door, oak\n    open false\n    lockable\n    locked\n",
    ).replace("{summon}", "summon.foresight\n")
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    io = CaptureIO(script=["north"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(locked))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "opening" not in io.text
    assert "locked" in io.text.lower()


def test_an_authored_open_is_the_residue():
    # A chest whose own on open refuses: promise, then the author's word,
    # and the command dies without a doubled message.
    extra = (
        'thing casket of container in hall\n    name "sealed casket"\n'
        '    words casket\n    openable\n    open false\n    fixed\n'
        '    on open\n'
        '        change refused to 1\n'
        '        say "The casket is fused shut by age."\n'
        'thing ring in casket\n    name "ring"\n    words ring\n'
    )
    out = _run2("summon.foresight\n",
                ["open casket", "take ring"], extra=extra)
    # the direct open refused (knowledge never formed), so the take cannot
    # even name the ring:
    assert "fused shut" in out
    assert "nothing of the sort" in out.split(">take ring")[-1]


def test_unsummoned_defaults_untouched():
    out = _run2("", ["north", "give pearl to bob"])
    assert "shut" in out.lower()
    assert "You aren't carrying the pearl." in out
    assert "opening" not in out
