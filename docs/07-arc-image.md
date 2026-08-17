# arc_image for authors: pictures in your story

How to put pictures in an Arcturus game: authoring the art, the `arcimg`
tool, what plays where today, and what is coming. This is the author's
book. The language surface (the `arc_image` property, `arc_mode`, changing
a room's picture at runtime, the darkness picture `arc_image_dark`, the
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

The pictures ship in a Blorb, the IF world's standard resource
container, with the arc_image numbering carried over exactly (picture
id N is Blorb resource Pict N; Blorb has no filenames, only numbers,
which is exactly the arc_image model). Two shapes, both from one
command:

```
arcimg pack art/ -o mygame.blorb                       pictures only, beside the z5
arcimg pack art/ --zblorb mygame.z5 -o mygame.zblorb   story + pictures, ONE file
```

The `.zblorb` is the shape Blorb-aware interpreters (the Gargoyle
family, and Actaea itself) open directly: your whole game, art
included, in a single file. Actaea plays all of it: a `.zblorb` opened
as the story, or a sibling `.blorb` found next to a plain `.z5`/`.z8`.
Actaea's console and pipe modes, and every other standard interpreter,
play the same story text-only. And the same finished artifacts feed the
web: `proteus mygame.zblorb -o mygame.html` (or the story and its
`.blorb` as a pair) turns the game into one self-contained page that
plays in any browser, pictures and all (docs/09).

(An earlier `.arcres` zip pack was retired on 2026-07-31; the Blorb is
the one pack, readable everywhere the pictures go.)

Masters need not be 320 wide: any resolution at the band's aspect ratio
(40:9 for mode 9, 10:3 for mode 12) packs and displays, and interpreters
scale it to their band. 320 is the reference resolution the retro
conversions derive from, not a ceiling for the modern packs. During development
you can skip the pack and point Actaea at the directory:
`actaea game.z5 --images art/`.

The worked examples are in [examples/arc_image/](../examples/arc_image/),
each shipping its `.blorb` beside the storyarc: `rabenstein.storyarc`
is the MODE 12 demo, and `cloak-of-darkness.storyarc` is the MODE 9
twin: Roger Firth's classic with four Arthur-band scenes (320x72),
where the plot itself is the darkness test, the bar's own dark painting
standing as arc_image_dark until the cloak hangs on its hook. Its retro
conversions live under arc_image/cloak/. Between the two demos an
interpreter exercises both band shapes. The Rabenstein demo is also the
INTERPRETER AUTHOR'S TEST GAME: a compact walk exercising the whole
contract (traversal, a pictureless room that must clear the band,
darkness with its all-black scene, an in-place picture change on an
event, repeatably, and the no-reload rule on LOOK), with the expected
picture id for every step spelled out in the source header. An
interpreter that matches that walkthrough renders arc_image correctly.

## 3. Converting for the retro machines

```
arcimg convert art/ --target C64 -o c64/ --preview previews/
```

derives each master's native version for a target as `<id>.C64` (or
`.AMI`, `.AST`, `.DOS`, `.ZX3`, `.CPC`, ...) beside the story, with PNG
previews. One machine breaks the pattern by design: the TRS-80 Model 4
ships `ARC<id>.TR4`, because TRSDOS caps a suffix at three characters
and wants filenames starting with a letter; the picture id inside the
file stays authoritative either way. Previews land beside the
conversions so you judge every one without an emulator. Pictures
convert in parallel, and only what changed reconverts on the next run.

What the converter does for you, per machine: the right resolution and
palette, the machine's color-cell constraints resolved, dithering only
where it helps, your hinted moons and suns kept visible.

The ZX Spectrum deserves its own honest paragraph. Its screen carries
just two colors per 8x8 cell, sharing one brightness, and no automated
conversion of full-color art survives that constraint gracefully: the
attribute clashes always win. So on this one machine arcimg takes the
deliberate way out: the automated conversion is a reasonable looking
BLACK AND WHITE ARTWORK, a pattern-stipple rendition in bright white
on black, in the manner of the machine's own classic art. It reads
honestly, it never clashes, and it ships as-is.

Color on the Spectrum belongs to authors, and an author can supply
their own image for ANY picture, at ANY time; hand-drawn Spectrum art
outclasses conversion on this machine, and the tool treats it as the
first-class path:

```
arcimg scr 8.ZX3 -o 8.scr        # a standard .scr any editor opens
arcimg unscr 8.scr --id 8 -o zx3/  # the polished file back, protected
```

`scr` writes any conversion (or a master directly) as a standard
6912-byte .scr that every Spectrum art tool opens: the picture band on
top, a black bar below. Draw or repaint as much as you like, from a few
color washes to a full replacement, in SevenuP, img2spec, or the editor
of your choice. `unscr` takes the finished screen back into the
portfolio, strips the bar, lints it, and stamps the file HAND-AUTHORED:
from then on `arcimg convert` will never overwrite it, with or without
--force. Delete the file to return that picture to the automated path.

The 16-bit targets compress with LZSA2: if Emmanuel Marty's `lzsa` tool
is installed (or named in `$ARCIMG_LZSA`) it packs a few percent
smaller; without it arcimg's built-in packer is used and nothing else
is needed. Everything else is built in.

## 4. What plays where

| Target | Status |
|---|---|
| Modern (Actaea window) | PLAYS TODAY (`.zblorb`, or `.blorb` beside the z5) |
| The web (Proteus) | PLAYS TODAY (`proteus mygame.zblorb -o mygame.html`) |
| Modern (Gargoyle) | implemented; ships with the next Gargoyle release |
| DOS (VGA) | blueprint proven; interpreter support planned |
| Amiga (OCS/ECS) | PLAYS TODAY (Eris) |
| Atari ST(E) | PLAYS TODAY (Eris) |
| Commodore 64 / C128 | blueprint proven; interpreter support planned |
| ZX Spectrum +3 | PLAYS TODAY (Triton); b/w conversion ships, color is the author's (see above) |
| Amstrad CPC | PLAYS TODAY (Haumea) |
| Commodore Plus/4 | blueprint proven; interpreter support planned |
| Atari 8-bit | PLAYS TODAY (Varuna) |
| TRS-80 Model 4 | blueprint proven; Shawn Sijnstra's interpreter adopts it |
| MSX1 and MSX2 | blueprint proven; interpreter support planned |
| Agon Light | blueprint proven; Shawn Sijnstra's Canopus adopts it |
| Spectrum Next | blueprint proven (conversion is the identity for ST-class masters) |
| MEGA65 | blueprint proven (conversion is the identity for any master up to 255 colors) |
| Apple II (DHGR, 128K) | blueprint proven (best on a composite display, the machine's own; an RGB card shows the sixteen flat) |

"Blueprint proven" means the machine's picture loader is designed,
built, and demonstrated on the real hardware's emulator; the interpreter
work that adopts it comes next, per machine. Your assets and your story
do not change as targets arrive: the same masters, the same ids, the
same z5. Convert and ship for the targets that exist when you release,
and a later interpreter picks the same files up.

## 5. The commands, all of them

```
arcimg pack SOURCES... -o game.blorb       the modern pack (a Blorb)
arcimg pack ... --zblorb game.z5 -o game.zblorb   story + pictures in one Blorb
arcimg prep SOURCE --id N --mode MODE      size and number a source
arcimg info SOURCE                         a PNG's size / a pack's contents
arcimg convert SOURCES... --target TAG     derive a machine's native art
arcimg targets                             the target list
arcimg render FILE -o out.png              preview any converted picture
arcimg slice9 FILE --id N -o out           a mode-9 picture as the top
                                           slice of a mode-12 conversion
                                           (same picture, same colours)
arcimg scr / arcimg unscr                  the Spectrum polish loop
```

`arcimg` ships like `arcc` and `actaea`: one self-contained file
(build/arcimg), pure Python, no installation.
