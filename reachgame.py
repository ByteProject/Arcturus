import sys
sys.path.insert(0, "/Users/stefan/Fiction/Arcturus")
from arcturus import cosmos
from arcturus.codegen import generate
from arcturus.parser import parse
from arcturus.sema import analyze
src = (
    'game\n    title "Jar"\n    start lab\n'
    'room lab\n    name "Lab"\n    desc "A lab."\n'
    'thing jar of container in lab\n    name "jar"\n    clear\n    openable\n    fixed\n'
    'thing coin in jar\n    name "coin"\n'
    'verb "probe"\n    probe noun\n'
    'on probe\n'
    '    if noun is reachable\n'
    '        say "REACHABLE."\n'
    '        stop\n'
    '    say "Sealed away."\n'
)
open("reach.z5", "wb").write(generate(analyze(cosmos.combined_program(parse(src)))))
print("built")
