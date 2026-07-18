

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
