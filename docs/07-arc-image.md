# arc_image for authors: pictures in your story

How to put pictures in an Arcturus game: authoring the art, the `arcimg`
tool, what plays where today, and what is coming. This is the author's
book. The language surface (the `arc_image` property, `arc_mode`, the
conformance guarantee) is specified in 01 section 6b; how interpreters
display the pictures is 08 (you never need it to ship a game); the design
record behind the conversion machinery lives with the working set in
arc_image/reference/design.md.

The one-paragraph version: you paint ONE master picture per scene as a
PNG, number it, and say `arc_image <number>` on the room. Your story
remains a conformant z5 file that plays text-only on every standard
interpreter; on a picture-aware interpreter the band shows your art. For
the retro machines, `arcimg` derives each machine's native version from
your master automatically, so you never hand-paint fourteen versions of
anything.

## 1. Authoring the masters

One PNG per picture id, in the game's band shape (declared once with
`constant arc_mode`, 01 section 6b):

| Mode | Pixels | The look |
|---|---|---|
| 9 (Infocom) | 320x72 | the upper third, the classic Arthur style |
| 12 (DAAD) | 320x96 | the upper half, the Rabenstein style |

Pixel art is the medium: interpreters integer-scale, so crisp pixels stay
crisp. Paint at the quality of the least constrained machines (an Amiga
or ST palette is a comfortable ceiling); the tool derives downward from
there. Name the files by id: `8.png` is picture 8.

Two authoring aids:

- `arcimg prep SOURCE --id N --mode {infocom,daad}` sizes any source
  image to the band shape and numbers it (a PNG already at the exact
  size is just copied).
- A picture with a bright celestial disc (a moon, a sun) can carry a
  hint sidecar, `8.hint` beside `8.png`, one line of JSON:
  `{"salient": [[cx, cy, r]]}` naming the disc in pixel coordinates.
  On machines whose palette cannot hold the disc apart from its sky,
  the conversion promotes it to the brightest color instead of losing
  it. Seconds of work, and every target benefits.

## 2. Shipping for modern systems (playable today)

```
arcimg pack art/ -o mygame.arcres
```

zips the numbered PNGs into one `.arcres` beside the z5. Actaea's window
shows the pictures; Actaea's console and pipe modes, and every other
standard interpreter, play the same file text-only. During development
you can skip the pack and point Actaea at the directory:
`actaea game.z5 --images art/`.

The worked example is [examples/arc_image/](../examples/arc_image/):
`rabenstein.storyarc`, its art pack, and the built z5.

## 3. Converting for the retro machines

```
arcimg convert art/ --target C64 -o c64/ --preview previews/
```

derives each master's native version for a target as `<id>.C64` (or
`.AMI`, `.AST`, `.DOS`, `.ZX3`, `.CPC`, ...) beside the story, with PNG
previews so you judge every conversion without an emulator. Pictures
convert in parallel, and only what changed reconverts on the next run.

What the converter does for you, per machine: the right resolution and
palette, the machine's color-cell constraints resolved, dithering only
where it helps, your hinted moons and suns kept visible. The Spectrum
deserves one honest note: its conversions are strong starting points,
and depending on the image you may want to polish a few cells by hand.
That loop is first-class:

```
arcimg scr 8.ZX3 -o 8.scr        # a standard .scr any editor opens
arcimg unscr 8.scr --id 8 -o zx3/  # the polished file back, protected
```

A hand-polished picture is marked in its file, and `arcimg convert`
will never overwrite it; delete it to reconvert from the master.

The 16-bit targets compress with LZSA2: if Emmanuel Marty's `lzsa` tool
is installed (or named in `$ARCIMG_LZSA`) it packs a few percent
smaller; without it arcimg's built-in packer is used and nothing else
is needed. Everything else is built in.

## 4. What plays where

| Target | Status |
|---|---|
| Modern (Actaea window) | PLAYS TODAY (`.arcres` beside the z5) |
| DOS (VGA) | blueprint proven; interpreter support planned |
| Amiga (OCS/ECS) | blueprint proven; planned for Eris |
| Atari ST(E) | blueprint proven; planned for Eris |
| Commodore 64 / C128 | blueprint proven; interpreter support planned |
| ZX Spectrum +3 | conversion ready; blueprint in progress |
| Amstrad CPC | conversion ready; planned for Haumea |
| Plus/4, MSX1/2, Atari 8-bit, Apple II, Spectrum Next, MEGA65, C128 VDC | planned |

"Blueprint proven" means the machine's picture loader is designed,
built, and demonstrated on the real hardware's emulator; the interpreter
work that adopts it comes next, per machine. Your assets and your story
do not change as targets arrive: the same masters, the same ids, the
same z5. Convert and ship for the targets that exist when you release,
and a later interpreter picks the same files up.

## 5. The commands, all of them

```
arcimg pack SOURCES... -o game.arcres      the modern pack
arcimg prep SOURCE --id N --mode MODE      size and number a source
arcimg info SOURCE                         a PNG's size / a pack's contents
arcimg convert SOURCES... --target TAG     derive a machine's native art
arcimg targets                             the target list
arcimg render FILE -o out.png              preview any converted picture
arcimg scr / arcimg unscr                  the Spectrum polish loop
```

`arcimg` ships like `arcc` and `actaea`: one self-contained file
(build/arcimg), pure Python, no installation.
