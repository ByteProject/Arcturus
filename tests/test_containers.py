

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
