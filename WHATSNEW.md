# What's new in Arcturus

The most significant recent additions and achievements, newest work
first. The five most recent entries are kept here; history beyond that
lives in the commit log.

- **Kinds without a ceiling.** A kind is Arcturus's class sugar, and it used to
  spend one of the Z-machine's 48 precious attributes even when you only meant
  to organize objects or span scenery. Not any more: a kind costs an attribute
  only where you actually test `obj is <kind>`, so the kinds you use purely to
  share behavior or distribute scenery are free. Test more kinds than the spare
  attribute slots hold and the rest fall back automatically to a fast membership
  scan, built on Arcturus's own catalog feature (what you know as lists in other
  languages), so you can declare as many kinds as your world wants. This is very
  efficient on memory and performance on 8-bit hardware compared to Inform's
  classes. The only real ceiling is now the Z-machine's own, 48 genuine object
  attributes, and `arcc -s` shows attributes and kinds separately so you always
  read your true budget (`attributes 26/48, kinds 63`). It grew from a large
  real-world port hitting the old wall, and it is exactly what that port asked
  for.
- **Matrices: a catalog you can grow, and tables Inform makes you hand-roll.**
  When a collection genuinely changes length as the game plays, `summon.matrix`
  gives you its mutable sibling: `append` and `remove` (order-preserving, or an
  O(1) `swapping`) and `insert`, all bounds-safe, with the same reads you
  already know (`entry`, `calculate`, `for each`, `in`). And a matrix comes in
  a two-dimensional form, `matrix bed 3 by 3`, a real declared table you index
  by `entry(m, row, col)`, with `of byte` packing a large grid one cell per byte
  (half the memory, so a 16x16 map costs 256 bytes) and compile-time bounds
  checks Inform's raw arrays never had. It stays out of the base language, a
  summoned feature that costs zero bytes unused; the mutators live in editable
  Cosmos, and underneath there is still no heap, only the same static region a
  catalog uses. Most games never need it (Hibernated 2, Rabenstein, and Ghosts
  never did) and the docs say so plainly, but when you want the trusty array, it
  is here ([worked example](examples/features/matrix.storyarc)).
- **vary: prose that varies by itself.** The feature authors of Inform 7 and
  Dialog name among their favorites (`[one of]`, `(select)`), in Arcturus's
  own readable form: `vary loop` followed by your variant lines speaks a
  different one each time, and the policy word picks how - `sequence`
  (advance once, stick on the last: room descriptions), `loop` (round-robin),
  `mutate` (random, never the same twice running), `dice` (the honest roll).
  Each site keeps one invisible word of state the compiler allocates -
  correct across save, undo, and restart, never named by you - and a bare
  string line is a whole variant, so the common case has zero ceremony. It
  plugs in anywhere prose is made: a computed description, any handler, an
  alter report, each_turn, a message override. Underneath it is a load, a
  store, and a jump chain in native Z-machine operations, a handful of
  instructions per site; a game that never varies is byte-identical.
- **arc_image reaches the retro machines.** The same numbered pictures a
  modern build shows now convert to the 8-bit and 16-bit machines' own
  formats: paint ONE master per scene, and `arcimg convert` derives the
  native version for the Commodore 64, ZX Spectrum +3, Amstrad CPC, Amiga,
  Atari ST, and DOS, resolving each machine's palette and color-cell
  constraints, with PNG previews to judge without an emulator, an author
  hint that keeps a moon or sun visible on the narrowest palettes, and a
  polish loop that round-trips Spectrum art through any .scr editor.
  Reference loaders are proven on real emulators for four machines so far,
  and the interpreter blueprints ship with the toolkit
  ([docs/07-arc-image.md](docs/07-arc-image.md) for authors).
- **`perform` and `appearance`: the classic bridges, grown from the field.**
  `perform("take", book)` runs any action as part of the current turn,
  refusals, messages, and after-phase included, with the action name checked
  at compile time (Inform's `<<take book>>`, Dialog's `(try ...)`); the
  `appearance` property is the paragraph an object always owns in a room
  description ("The keeper is trimming the wick."), worded by state when
  computed, beside `intro`'s until-first-taken rule. Both came from early
  adopters porting real games, and both cost nothing in a game that never
  uses them; component objects (a lever that is `component` of its machine)
  arrived the same way. Worked examples:
  [perform](examples/features/perform.storyarc),
  [appearance](examples/features/appearance.storyarc),
  [components](examples/features/components.storyarc).
