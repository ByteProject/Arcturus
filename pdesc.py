import sys
sys.path.insert(0, "/Users/stefan/Fiction/Arcturus")
from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
src = (
    'game\n    title "W"\n    start den\n'
    'room den\n    name "Den"\n    desc "Cosy."\n'
    'thing hat in player\n    name "hat"\n    wearable\n    worn\n'
    'player.desc block\n'
    '    show("A fine figure. ")\n'
    '    for each x in player\n'
    '        if x is worn\n'
    '            show("${a x} is worn. ")\n'
    '    say ""\n'
)
try:
    open("pdesc.z5", "wb").write(generate(analyze(cosmos.combined_program(parse(src)))))
    print("COMPILED")
except Exception as e:
    print("ERROR:", e)
