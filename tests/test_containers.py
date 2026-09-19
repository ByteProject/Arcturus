

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
