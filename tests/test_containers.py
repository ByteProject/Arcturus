

def test_opening_a_clear_container_reveals_nothing():
    # A field report (Charles Moore Jr., 2026-07-18): the "Inside you
    # find" reveal fired on a clear container, whose contents were never
    # hidden (the knowledge model lists through the glass). Opaque
    # containers keep the reveal.
    from arcturus import cosmos as _c
    from arcturus.codegen import generate as _g
    from arcturus.sema import analyze as _a
    from arcturus.parser import parse as _p
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "H."\n'
        'thing jar of container in hall\n    name "glass jar"\n'
        '    words jar\n    clear\n    openable\n    fixed\n'
        'thing marble in jar\n    name "marble"\n    words marble\n'
        'thing crate of container in hall\n    name "crate"\n'
        '    words crate\n    openable\n    fixed\n'
        'thing chisel in crate\n    name "chisel"\n    words chisel\n'
    )
    story = _g(_a(_c.combined_program(_p(game))))
    io = CaptureIO(script=["open jar", "open crate"])
    try:
        VM(load(story), io).run(max_steps=20_000_000)
    except IndexError:
        pass
    jar_part = io.text.split(">open jar")[-1].split(">")[0]
    crate_part = io.text.split(">open crate")[-1].split(">")[0]
    assert "Inside you find" not in jar_part
    assert "Inside you find a chisel" in crate_part


def test_inventory_keeps_the_closed_qualifier():
    # The chest that lost its "(closed)" on pickup (a field report,
    # 2026-09-19): the inventory line speaks the same qualifier the room
    # listing does, and an open chest drops it in both.
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    game = (
        'game\n    title "T"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "Bare."\n'
        'thing chest of container in hall\n    name "chest"\n    words chest\n'
        '    openable\n'
    )
    io = CaptureIO(script=["get chest", "i", "open chest", "i"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(game))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    first, second = io.text.split(">open chest")
    assert "a chest (closed)" in first
    assert "a chest (closed)" not in second


def test_listing_goes_two_levels_in_prose():
    # auraes's report (2026-09-27): a box put on a table lost its apple
    # from the listing (one level deep). Now a holder among the contents
    # says what it holds in prose, Stefan's shape (2026-10-04), and never
    # a third level: the pea in the tin in the box stays unnamed.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'game\n    title "N"\n    start r\n'
        'room r\n    name "Somewhere"\n    desc "x"\n'
        'thing table of supporter in r\n    name "table"\n    words table\n    fixed\n'
        'thing box of container in table\n    name "box"\n    words box\n    open\n'
        'thing apple in box\n    name "apple"\n    words apple\n'
        'thing salt in box\n    name "salt"\n    words salt\n    indefinite "some"\n'
        'thing tin of container in box\n    name "tin"\n    words tin\n    open\n'
        'thing pea in tin\n    name "pea"\n    words pea\n'
        'thing stool of supporter in table\n    name "stool"\n    words stool\n'
        'thing hanky in stool\n    name "handkerchief"\n    words handkerchief\n'
    )
    io = CaptureIO(script=["look"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert ("a table (on which are a box with an apple, some salt and a tin in it "
            "and a stool with a handkerchief on it)") in out
    assert "pea" not in out


def test_listing_sentence_ends_cleanly_after_a_parenthesis():
    # Stefan's ruling (2026-10-04): "... with a handkerchief on it) here."
    # stumbles, so the frame ends with a period after a parenthesis; the
    # plain sentence keeps its " here." anchor.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'game\n    title "N"\n    start r\n'
        'room r\n    name "Somewhere"\n    desc "x"\n'
        'thing lamp in r\n    name "lamp"\n    words lamp\n'
        'thing stool of supporter in r\n    name "stool"\n    words stool\n'
        'thing hanky in stool\n    name "handkerchief"\n    words handkerchief\n'
        'thing box of container in r\n    name "box"\n    words box\n'
        '    openable\n'
    )
    io = CaptureIO(script=["look", "take stool", "take box", "look",
                           "drop stool", "look"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "a stool (on which is a handkerchief) and a box (closed)." in out
    assert "You can see a lamp here." in out                      # plain: anchored
    # The dropped stool lists first; the last item is the plain lamp, so
    # the anchor stays: only the final item decides the ending.
    assert "You can see a stool (on which is a handkerchief) and a lamp here." in out
    assert ") here." not in out


def test_examine_names_a_holders_contents():
    # auraes's cheese (2026-10-06): the room listing stops at two levels
    # by design, and a closer look must reach the next two. EXAMINE on a
    # holder names its contents under the description; a holder with no
    # desc but contents names them alone; a closed one names memory.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'game\n    title "C"\n    start r\n'
        'room r\n    name "Somewhere"\n    desc "x"\n'
        'thing fridge of container in r\n    name "fridge"\n    words fridge\n'
        '    open\n    fixed\n    openable\n'
        'thing box of container in fridge\n    name "box"\n    words box\n    open\n'
        '    desc "A plain box."\n'
        'thing board of supporter in box\n    name "cheeseboard"\n    words cheeseboard\n'
        'thing cheese in board\n    name "cheese"\n    words cheese\n'
        'thing crate of container in r\n    name "crate"\n    words crate\n    open\n'
    )
    io = CaptureIO(script=["look", "examine fridge", "examine box",
                           "examine cheeseboard", "close fridge",
                           "examine fridge", "examine crate"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "a fridge (contains a box with a cheeseboard in it)" in out
    assert "a cheese on it" not in out.split(">examine fridge")[0]   # the third level, unnamed
    f1 = out.split(">examine fridge")[1].split(">")[0]
    assert "In the fridge you can see a box with a cheeseboard in it." in f1
    assert "rewards a closer look" not in f1
    b = out.split(">examine box")[1].split(">")[0]
    assert "A plain box." in b
    assert "In the box you can see a cheeseboard with a cheese on it." in b
    assert "On the cheeseboard you can see a cheese." in out.split(">examine cheeseboard")[1]
    f2 = out.split(">examine fridge")[2].split(">")[0]
    assert "The fridge (closed) contains a box with a cheeseboard in it." in f2
    assert "rewards a closer look" in out.split(">examine crate")[1]


def test_remember_contents_false_forgets_a_shut_box():
    # auraes (2026-10-12): the closed-holder memory is the designed default,
    # and `constant remember_contents = false` switches it off game-wide.
    # The default build is byte-identical with or without the constant on.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    base = (
        'game\n    title "M"\n    start r\n'
        'room r\n    name "Somewhere"\n    desc "x"\n'
        'thing box of container in r\n    name "box"\n    words box\n'
        '    openable\n    open\n    fixed\n'
        'thing ring in box\n    name "ring"\n    words ring\n'
    )
    def play(src):
        io = CaptureIO(script=["look", "close box", "look", "examine box"])
        try:
            VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
               io).run(max_steps=20_000_000)
        except IndexError:
            pass
        return io.text
    remembered = play(base)
    assert "a box (closed) (contains a ring)" in remembered or "contains a ring" in remembered.split(">close box")[1]
    forgot = play(base + "constant remember_contents = false\n")
    after = forgot.split(">close box")[1]
    assert "ring" not in after
    assert "box (closed)" in after
    plain = generate(analyze(cosmos.combined_program(parse(base))))
    on = generate(analyze(cosmos.combined_program(parse(base + "constant remember_contents = true\n"))))
    assert plain == on


def test_entering_a_shut_container_names_the_lid():
    # auraes (2026-10-12): ENTER on a closed container spoke the flat
    # "can't get inside"; the lid is the reason, so it speaks the shut line.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'game\n    title "E"\n    start r\n'
        'room r\n    name "Somewhere"\n    desc "x"\n'
        'thing crate of container in r\n    name "crate"\n    words crate\n'
        '    openable\n    open false\n    fixed\n'
        'thing rock in r\n    name "rock"\n    words rock\n'
    )
    io = CaptureIO(script=["enter crate", "enter rock"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    assert "The crate is shut. You'll have to open it first." in io.text.split(">enter crate")[1]
    assert "You can't get inside the rock." in io.text.split(">enter rock")[1]


def test_the_sealed_gate_stops_every_touch_through_a_shut_lid():
    # auraes's vitrine (2026-10-13): a closed clear container showed its
    # lantern and let SWITCH ON and PUSH reach through the glass; only TAKE
    # consulted the blocker. The sealed gate now refuses every touching
    # action with take's line; EXAMINE (reachagnostic) still looks.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    src = (
        'game\n    title "G"\n    start hall\n'
        'room hall\n    name "Hall"\n    desc "x"\n    north yard\n'
        'room yard\n    name "Yard"\n    desc "y"\n'
        'thing vitrine of container in hall\n    name "vitrine"\n    words vitrine\n'
        '    clear\n    openable\n    open false\n    fixed\n'
        'thing lantern in vitrine\n    name "lantern"\n    words lantern\n'
        '    binary\n    shiftable\n    desc "Brass."\n'
    )
    io = CaptureIO(script=["turn lantern on", "push lantern north",
                           "examine lantern", "open vitrine", "turn lantern on"])
    try:
        VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
           io).run(max_steps=20_000_000)
    except IndexError:
        pass
    out = io.text
    assert "open the vitrine first" in out.split(">turn lantern on")[1]
    assert "open the vitrine first" in out.split(">push lantern north")[1]
    assert "Brass." in out.split(">examine lantern")[1]
    assert "You switch the lantern on." in out.split(">turn lantern on")[2]


def test_contents_line_false_keeps_examine_to_the_description():
    # improvmonster (2026-10-14), the opposite of auraes's cheese: a story
    # whose descriptions own the contents sentence switches it off game-wide
    # and composes name_contents where it wants it. The default build is
    # byte-identical with the constant on.
    from arcturus import cosmos
    from arcturus.codegen import generate
    from arcturus.parser import parse
    from arcturus.sema import analyze
    from actaea.io import CaptureIO
    from actaea.loader import load
    from actaea.vm import VM
    base = (
        'game\n    title "H"\n    start r\n'
        'room r\n    name "Somewhere"\n    desc "x"\n'
        'thing box of container in r\n    name "box"\n    words box\n'
        '    open\n    fixed\n    desc "A plain box."\n'
        'thing crate of container in r\n    name "crate"\n    words crate\n    open\n'
        'thing ring in box\n    name "ring"\n    words ring\n'
        'thing nail in crate\n    name "nail"\n    words nail\n'
    )
    def play(src):
        io = CaptureIO(script=["examine box", "examine crate"])
        try:
            VM(load(generate(analyze(cosmos.combined_program(parse(src))))),
               io).run(max_steps=20_000_000)
        except IndexError:
            pass
        return io.text
    on = play(base)
    assert "In the box you can see a ring." in on.split(">examine box")[1]
    off = play(base + "constant contents_line = false\n")
    b = off.split(">examine box")[1].split(">")[0]
    assert "A plain box." in b and "you can see" not in b
    c = off.split(">examine crate")[1]
    assert "rewards a closer look" in c and "nail" not in c
    composed = play(base.replace('    desc "A plain box."\n',
                                 '    desc block\n        show("A plain box, holding ")\n'
                                 '        name_contents(self)\n        say "."\n')
                    + "constant contents_line = false\n")
    assert "A plain box, holding a ring." in composed.split(">examine box")[1]
    plain = generate(analyze(cosmos.combined_program(parse(base))))
    same = generate(analyze(cosmos.combined_program(parse(base + "constant contents_line = true\n"))))
    assert plain == same
