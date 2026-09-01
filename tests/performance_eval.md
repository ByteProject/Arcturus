# Performance evaluation: Arcturus vs PunyInform on 8-bit hardware

Measured 2026-09-01 from the Varuna side (the Atari 8-bit reference
interpreter), cycle-exact in SIM6502. Written to answer one question: does
Arcturus need compiler/library-level optimization, and if so, where? The
answer is yes, in ONE place, and the data below names it.

Method: SIM6502 counts 6502 cycles exactly. The interpreter is Varuna 1.1
with the fault-transparency and RNG fixes (Varuna commit f9ab961). Machine
model: bare 64K Atari XL, DD disk image. Disk transfer time is NOT in the
cycle counts (the SIM's SIO is instant); it is added back as a model where
noted. Seconds = cycles / 1,789,790 (NTSC Atari; PAL is within 1%). The two
stories are the SAME GAME: Hibernated 2 built with Arcturus (serial 260830,
130,992 bytes, dynamic memory 6.4K) and the last PunyInform build (serial
260603, 137,728 bytes, dynamic memory 10.0K), driven with the same ten
opening commands through the same interpreter binary.

## 0. Executive summary

- On average, the PunyInform build answers a command in ~1.6s of CPU on a
  64K Atari; the Arcturus build takes ~3.0s. Puny wins the average and every
  VERB turn (take/examine/talk/push, by 2-3x). Arcturus wins every MOVEMENT
  and printing-heavy turn (n/e, by ~1.5x), wins boot disk traffic (59 page
  reads vs 88), and wins memory (6.4K dynamic vs 10.0K, 130,992 bytes vs
  137,728).
- THE THESIS THIS DOCUMENT SUPPORTS: Arcturus SHOULD be the faster system -
  lower memory footprint, denser code - and the data shows that goal is
  ALREADY HALF ACHIEVED. Varuna executes Arcturus z-code at 1,084 cycles per
  instruction against 1,677 for Puny's: the generated code is genuinely
  better, instruction for instruction. The average is lost at RUNTIME, in
  the library: verb turns execute 3.3x more instructions, and the profile
  shows three quarters of a verb turn inside TWO small Cosmos routines
  ($4C61, $6F91) called ~700 times each per command - a per-object walk.
  The codegen already won; the scope/handler walk spends the winnings.
- The fix is therefore surgical, not structural: one Cosmos loop. With it,
  verb turns should drop to or below Puny across the board, because
  everything else already is below. Independently, Varuna's own fetch path
  (section 4) can halve everything again. Both landed: ~0.8-1.2s per warm
  turn on an Atari.

## 1. The headline numbers

Per-turn CPU, command RETURN to next prompt:

  command            ARCTURUS            PUNYINFORM
                     cycles      sec     cycles      sec
  push grill (cold)  6,187,579   3.46s   2,781,311   1.55s
  push grill         6,230,965   3.48s   2,617,718   1.46s
  talk to vlad       7,985,310   4.46s   3,134,117   1.75s
  [menu key 1]       1,983,670   1.11s   1,387,414   0.78s
  n                  2,292,305   1.28s   3,333,329   1.86s
  take spray oil    10,171,787   5.68s   3,999,569   2.23s
  examine terminal   6,529,218   3.65s   2,723,326   1.52s
  talk to vlad       7,867,714   4.40s   2,947,226   1.65s
  [menu key 1]       2,004,769   1.12s   1,505,323   0.84s
  e                  2,231,342   1.25s   3,602,156   2.01s
  ------------------------------------------------------
  ten commands            29.9s               15.7s
  average per turn         3.0s                1.6s

Boot to the first prompt: Arcturus 2.0s CPU + 59 page reads; PunyInform
1.8s CPU + 88 page reads.

To convert to what a player feels, add disk time for the page reads:
- FujiNet / SIO2SD / emulator: effectively the CPU figure alone.
- Real Atari drive at standard SIO (19,200 baud, roughly 150-250ms per
  256-byte page including latency): the cold first command (44-47 reads)
  adds roughly 8-12 seconds, once; warmed-up turns read nothing.
- Extra RAM (130XE, 256K/320K) removes disk time. It NEVER reduces the CPU
  figure. A warm turn costs the same 3.0s/1.6s on a 320K machine as on 64K.

DIRECT ANSWERS to the questions that prompted this document:
- The Puny build's first command: 1.55s CPU + 44 page reads. About 1.6s on
  FujiNet, roughly 9-13s on a real drive.
- Warmed up, the two builds are NOT both at 3.5s. Arcturus averages ~3.0s
  per response (1.1s to 5.7s depending on the verb); PunyInform averages
  ~1.6s (0.8s to 2.2s). PunyInform is about 2x faster per turn in CPU.

## 2. Reading the numbers: it is not uniform, and that is the insight

Is Puny "basically faster at everything"? NO - and the distinction decides
what to optimize. Side by side, on the same interpreter:

  where ARCTURUS is already ahead        where PUNYINFORM is ahead
  - cycles per z-instruction:            - every verb-action turn:
    1,084 vs 1,677 (the codegen)           2-3x fewer instructions
  - movement/printing turns:             - therefore the per-turn AVERAGE:
    n 1.28s vs 1.86s, e 1.25s vs 2.01s     ~1.6s vs ~3.0s
  - story size: 130,992 vs 137,728
  - dynamic memory: 6.4K vs 10.0K
    (= 14 more cache slots on Varuna)
  - boot disk reads: 59 vs 88

Everything in the left column is what Arcturus was designed to deliver, and
it delivers. The right column is one behavior: verb dispatch executes 3.3x
more instructions. Section 3 shows those instructions are concentrated in
two routines, i.e. one loop. Fix that and there is no right column.

Split the turns by kind and the picture inverts in places:

- MOVEMENT AND PRINTING FAVOR ARCTURUS. "n" and "e" print the most text
  (1,100-1,400 characters) and Arcturus does them in 1.25-1.28s against
  PunyInform's 1.86-2.01s. The Arcturus text path is fine; better than fine.
- VERB ACTIONS ARE WHERE ARCTURUS BURNS. take / examine / talk / push run
  6,200-10,300 z-machine instructions per turn against PunyInform's
  1,900-3,000. "take spray oil" is the poster child: 10,258 instructions,
  5.68s, to print 48 characters.
- The interpreter is NOT the difference. Varuna averages 1,084 cycles per
  z-instruction on the Arcturus instruction mix and 1,677 on PunyInform's
  (Puny leans on scan_table and heavier opcodes). Arcturus emits MORE
  instructions, each CHEAPER. The gap is instruction count: 3.3x more per
  verb turn.

## 3. Where the instructions go: one hot loop

Attributing every executed z-instruction to its containing routine (shadow
call stack over @call/@return) across the ten-command session, 53,664
instructions total:

  routine     instr   calls  instr/call  share
  $004C61    18,551     777       23.9    35%
  $006F91    10,450     666       15.7    19%
  $0073A5     5,582       6      930.3    10%
  $006699     1,914      11      174.0     4%
  $007E41     1,712       8      214.0     3%
  (everything else is small and flat)

And inside the worst single turn, "take spray oil" (10,258 instructions):

  $004C61     5,313    52% of the turn
  $006F91     2,668    26% of the turn
  $0073A5       939     9%

So this is NOT "Cosmos is uniformly heavier". Two SMALL routines - 24 and 16
instructions per call - are invoked roughly 700 times each in a single verb
turn, and together they are three quarters of that turn. That call pattern
(tiny leaf x hundreds of calls per command) is the classic signature of a
per-object pass: scope computation, handler resolution, or an each-object
predicate walking the whole object tree for every command. The addresses are
from the 260830 build; whoever knows the Cosmos internals can map $4C61 and
$6F91 to names and will very likely recognize the loop immediately.

For contrast, PunyInform's profile is FLAT: its hottest routine is 8% of the
session, the top ten are all between 776 and 1,683 instructions. There is
nothing comparable to fix there, which is why it is fast.

WHAT THIS MEANS FOR ARCTURUS: the optimization is surgical, not structural.
Cut the calls into $4C61/$6F91 (cache the scope set per turn, early-exit the
walk, or restrict candidates to the location's contents instead of a global
pass) and verb turns should approach the movement turns, i.e. Arcturus at or
below PunyInform across the board - because everything else is already
faster. Secondary observation: those ~1,400 calls per verb turn also pay the
interpreter's @call/@return frame overhead ~1,400 times, so every call
removed pays twice.

## 4. The interpreter floor, and Ozmoo's answer (protocolled)

Independent of the game, Varuna's own cost is ~1,000+ cycles per
z-instruction at only ~4 memory reads per instruction. The bulk is the
instruction fetch itself: every single instruction byte goes through the
fully general paged-memory path (zaddr setup, bounds compare against the
static base, indirect read, 3-byte PC increment) at roughly 80-100 cycles
PER BYTE. A four-byte instruction spends ~350-400 cycles just fetching
itself before it does anything.

Ozmoo's solution, recorded here as the adopted plan: keep a cached direct
pointer to the current Z-PC's page (a zero-page pointer to the page's slot
in the cache, or to dynamic memory), fetch instruction bytes with a plain
(zp),y read at ~10-15 cycles, and invalidate the pointer only when the PC
crosses a page boundary or the pager moves anything (fault, eviction,
restart). Expected effect: roughly HALVES warm-turn CPU for every game on
every machine - Arcturus H2 ~3.0s to ~1.6s, PunyInform ~1.6s to ~1.0s -
multiplicative with any Cosmos fix.

Supporting data (one warm "push grill" turn, instrumented): Arcturus mix
6,239 z-instructions performing 25,415 zmem_get_byte calls, 871 get_word,
329 @calls; Puny mix 1,885 instructions, 10,461 get_byte, 684 get_word,
158 @calls. That is ~4 memory reads per instruction on both mixes - most of
them the instruction's own bytes - which is why the fetch path dominates the
per-instruction cost and why caching the current PC page pays on any game.

Related interpreter lever, measured by implication: a verb turn makes
~1,400 @call/@return pairs into the two hot Cosmos routines, paying Varuna's
frame setup each time. Every call the Cosmos fix removes is paid back twice:
once in the routine's instructions, once in the interpreter's frame work.

Status: NOT built. Varuna currently has 104 bytes of code headroom before
its BSS, and the change belongs after the planned memory-map re-plan (see
Varuna's PROGRESS.md, which carries this same finding). Recorded so nobody
optimizes blind: the measurement came before the tuning.

## 5. What this means for Ganymede (C64)

Three multipliers separate a C64 interpreter from these Atari numbers:

- CLOCK: the C64 runs at 0.985 MHz (PAL) / 1.023 MHz (NTSC) against the
  Atari's 1.77/1.79. Identical 6502 code is ~1.75x slower on wall clock.
  The warm Arcturus turn above lands around 5.3-6.3s on a C64 from clock
  alone. This is physics, not implementation.
- DISK: a stock 1541 moves ~300-400 bytes/s; standard Atari SIO ~1.5-2KB/s.
  Ganymede already ships a fastloader - that was the single most important
  decision, worth more than any code tuning; a good fastloader brings the
  1541 to a few KB/s and makes the cold-turn story comparable to SIO.
- SCREEN MODEL: the bitmap-screen worry is SECOND-ORDER for turn latency.
  Arithmetic: a turn prints 50-1,400 characters. Rendering a glyph into a
  bitmap costs perhaps 100-200 cycles more than a character-matrix write;
  even 1,400 characters x 200 cycles is 0.28M cycles, under 5% of a 6M-cycle
  turn. Scrolling is the worse case (a bitmap scroll moves 8KB against a
  text screen's 1KB), but at a handful of scrolls per turn it is still well
  under 10%. If Ganymede feels "utterly slow" PER TURN, the place to look is
  the same place as here: cycles per z-instruction (the fetch path, the
  @call frame path), then the game's instruction count - not the screen.
  The bitmap choice mainly costs perceived smoothness of text flow, and it
  buys proportional fonts or 64+ columns; that trade can be judged on its
  own merits, not blamed for turn time.
- MEASURE IT THE SAME WAY: Ganymede adopted SIM6502, so this entire
  evaluation is reproducible there in an afternoon - cycle stamps at each
  @aread/@read_char, a MAIN_LOOP counter for z-instructions, a shadow call
  stack for per-routine attribution. The harness pattern is in Varuna's
  tools/test_modules.py (test_fault_transparency) and this document's
  numbers came from exactly that scaffolding. Comparable tables from
  Ganymede would immediately show whether its cycles-per-z-instruction is
  in Varuna's ~1,100 range (then everything above transfers) or far above
  it (then the interpreter, not the game, is the first target).

## 6. The decision, framed

Two levers, and they multiply:

  1. COSMOS: cut the $4C61/$6F91 call storm. Target: verb turns down 2-3x,
     to parity with or below PunyInform. Compiler/library work, no
     interpreter involvement. The profile says this is one loop.
  2. VARUNA (and siblings): the cached-PC-page fetch path. Target: ~2x on
     everything, both games, every machine. Interpreter work, planned after
     the memory-map re-plan.

  Both landed: a warm Arcturus H2 turn ~0.8-1.2s on an Atari, ~1.5-2.2s on
  a C64 behind a fastloader. That is a responsive 8-bit text adventure.

One caution for honest bookkeeping: these figures are from ten commands in
H2's opening on one interpreter. The shape (flat Puny profile, concentrated
Arcturus profile, movement-vs-verb split) is robust; the exact ratios will
wobble by game region. Re-run before and after any fix - the scaffolding
exists and takes minutes.

## 7. Addendum: the Cosmos/compiler levers landed (2026-09-01, same day)

Measured with probes/zi_count.py (Actaea's VM as the instruction counter,
seeded, validated against section 3's tables to a tenth of a percent
before any change). Same ten commands, same game, three compiler states:

  command            ARCTURUS 1.x   levers 1+2   ARCTURUS 2.0 (owner index)
  push grill  (warm)     6,249         4,474         1,280
  talk to vlad          10,135         8,367         5,203
  n                      1,716         1,716         1,716
  take spray oil        10,272         5,197         1,733
  examine terminal       6,445         4,779         1,511
  e                      1,880         1,880         1,880
  ten-command session   53,385        39,684        20,110

What shipped, in order:
- LEVERS 1+2 (Cosmos 1.17.5): in_scope gates the score in both sweeps
  (the same AND, cheap side first), and phrase_score inlines the word
  walk with the words property fetched once per object. Movement turns
  identical to the instruction; the hot pair roughly halves.
- LEVER 4 (arcc 2.0.0, the owner index): the compiler emits, per
  dictionary entry, the chain of objects owning it (words, plurals,
  adjectives; keyed by ENTRY ADDRESS so nine-z-char prefix collapse
  unions its owners); the matcher scores each typed word's few owners
  instead of sweeping the object table. The index proposes, phrase_score
  decides; one shared block holds the tie rules for the indexed and the
  classic path, and the full behavioral suite runs green on both. The
  110-turn walkthrough is transcript-identical, seeded, either way.

Where that lands against section 1, using this document's measured
cycles-per-instruction (the 2.0 instruction mix has fewer calls, so the
true figure needs the cycle-exact re-run; treat seconds as the model):

- Verb turns now run FEWER instructions than PunyInform's (push grill
  1,280 vs 1,885; take ~1,733 vs ~2,400), on top of the cheaper
  per-instruction mix. The average warm turn models at ~1.1-1.2s on the
  Atari against Puny's ~1.6s, with movement/printing still ahead.
- Story cost: the index adds a few hundred bytes to an example-sized
  game and 2.9K to Hibernated 2 (now 133,924 bytes, still under the
  PunyInform build's 137,728, dynamic memory still 6.4K vs 10.0K).
- The talk turns' remaining weight is conversation machinery, not the
  matcher; a separate question for a separate measurement.

Section 4 (the cached-PC-page fetch path) remains open on the Varuna
side and multiplies with all of the above. The re-run of THIS document's
cycle-exact tables against the 2.0 build (distributed to the four test
directories) is the next measurement.

## 8. The cycle-exact re-run (2026-09-01, evening): measured, both builds,
## one interpreter, one day

Section 7's seconds were modeled; these are measured. Both stories
through the SAME current interpreter build (the head of the tree, the
zmem fix included), same harness, same ten commands, cycle-exact on the
64K Atari model. The PunyInform artifact is the original serial-260603
build, recovered from the interpreter repo's first-milestone commit; the
Arcturus story is the shipping 2.0 build (serial 260901).

  command            ARCTURUS 2.0         PUNYINFORM
                     cycles      sec      cycles      sec
  push grill         1,606,937   0.90s    3,030,157   1.69s
  push grill         1,653,948   0.92s    2,856,996   1.60s
  talk to vlad       3,476,560   1.94s    3,426,546   1.91s
  [menu key 1]       2,115,220   1.18s    1,501,859   0.84s
  n                  2,525,600   1.41s    3,626,271   2.03s
  take spray oil     2,320,093   1.30s    4,377,921   2.45s
  examine terminal   2,019,084   1.13s    2,969,702   1.66s
  talk to vlad       3,330,257   1.86s    3,230,425   1.80s
  [menu key 1]       2,126,603   1.19s    1,634,302   0.91s
  e                  2,421,243   1.35s    3,930,120   2.20s
  ------------------------------------------------------
  ten commands            13.2s               17.1s
  average per turn         1.3s                1.7s

Two days ago this table read 29.9s against 15.7s. The average and every
object-verb turn now belong to Arcturus (TAKE SPRAY OIL 1.30s against
2.45s, the turn that opened this document at 5.68s); movement kept its
lead. The conversation menus are the one place PunyInform still answers
faster (its menu redraw is lighter), a separate, small question for a
separate measurement. Memory, same builds: story 133,924 against
137,728 bytes; dynamic memory 6,535 against 10,078 bytes, which on this
interpreter is also 14 more cache slots for the pager. The section 4
fetch-path lever remains unbuilt and would move both columns down
together.
