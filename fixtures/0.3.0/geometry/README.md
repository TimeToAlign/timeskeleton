# Golden geometry of schema 0.3.0

One directory per document fixture of `fixtures/0.3.0/`, named after it:
`geometry.json` (the document laid out by `docs/geometry.md`, written by
`dumps`), `figure.svg` and `figure.tex` (the geometry written by the SVG and
TikZ profiles with the default options: width 400, row height 32,
standalone TikZ).

Provenance:

- the geometry of the seven specimens below is **derived by hand** from the
  specification; the arithmetic is written out here and the files were
  authored from it, not from an implementation;
- the geometry of the other thirteen and every figure are written by the
  TimeLineEditor (`app/packages/writers/scripts/emit-geometry.ts`), whose
  layout reproduces the seven hand-derived files byte for byte and whose
  script refuses to run otherwise. A second implementation must reproduce
  all of them byte for byte.

`fixtures/0.3.0/geometry-rejections/` holds geometries the geometry schema
rejects, each one change to `bare/geometry.json`, with the path a validator
reports.

## Conventions used below

`P`, `N` and `F` are the plot area, name column and frame lengths in
abstract units
(section 3.3): `P` is the root's length, `N = P / 4`, `F = N + P`. A
**wedge pair** of a line on row `r` drawn below is the two wedges at its
start and end with `tip = [r, 1]` and `base = r − 1/8`, and their labels at
`(x, base)`, anchor `north`, text `0 ♩` and `<length> ♩` (the timeline's
own coordinates). Colours are the defaults unless stated: logical
`#00CC00`, physical `#0050EF`, labels `#000000`. Every line is `solid`
(continuous). Name labels are at `{"space": "frame", "x": <frame zero>,
"y": [r, 1]}`, anchor `west`.

## `bare`

Root `bare` (Bare), 8 quarters, `fraction`.

- Frame: `P = 8`, `N = 8/4 = 2`, `F = 10`: `{"length": [10, 1], "names":
  {"offset": [0, 1], "length": [2, 1]}, "plot": {"offset": [2, 1],
  "length": [8, 1]}}`; placement scalar `[1, 1]`, offset `[0, 1]`.
- Rows: only the root, row 0: `rows = {min 0, max 0}`.
- Primitives: the root line `[0, 1]`–`[8, 1]` on row 0; its wedge pair
  (`base = −1/8`, texts `0 ♩`, `8 ♩`); the name label `Bare` on row 0; the
  two wedge labels.

## `contiguous`

Root `piece` (Piece), 8 quarters; children `a` (3 at 0), `c` (2 at 1), `b`
(5 at 3), names null. Traversal (children by offset): `piece`, `a`, `c`,
`b`.

- Frame as `bare`: `P = 8`, `N = 2`, `F = 10`.
- Children band above, from distance 1:
  - `a` = `[0, 3]` → row 1 (empty);
  - `c` = `[1, 3]`: against `a`, `1 < 3` and `0 < 3`: conflict → row 2;
  - `b` = `[3, 8]`: against `a`, `0 < 8` but `3 < 3` is false, and the starts
    differ: no conflict → row 1, `b`'s circle on `a`'s diamond at 3.
- `rows = {min 0, max 2}`.
- Lines in order `piece` (0), `a` (1, `[0, 1]`–`[3, 1]`), `c` (2,
  `[1, 1]`–`[3, 1]`), `b` (1, `[3, 1]`–`[8, 1]`); wedge pairs in the same
  order with bases `−1/8`, `7/8`, `15/8`, `7/8` and texts `0 ♩` and `8 ♩`,
  `3 ♩`, `2 ♩`, `5 ♩`.
- Name column, top row first: row 2 `c`; row 1 `a, b` (the label's id
  `a/name`, timeline `a`); row 0 `Piece`. Then the eight wedge labels.

## `nested`

Root `tl:24`, 16 quarters; `tl:23` (8) at 4; inside it `tl:22` (2) at 3/2.

- Frame: `P = 16`, `N = 4`, `F = 20`.
- `tl:23` = `[4, 4 + 8] = [4, 12]` → row 1; its anchor above becomes 1.
- `tl:22` starts at `4 + 3/2 = 11/2` and ends at `11/2 + 2 = 15/2`; its
  minimum distance is its parent's anchor plus one, 2 → row 2.
- `rows = {min 0, max 2}`; lines `tl:24` (0), `tl:23` (1, `[4, 1]`–`[12, 1]`),
  `tl:22` (2, `[11, 2]`–`[15, 2]`); wedge texts `16 ♩`, `8 ♩`, `2 ♩`; names
  by id (all names are null), rows 2, 1, 0.

## `map`

Root `melody` (Melody), 8 quarters, carrying the `ScalarMap` `tempo`
(Tempo); child `phrase` (Phrase, 4 at 2) carrying `QuartersToTicks`
`ticks` (Ticks).

- Frame: `P = 8`, `N = 2`, `F = 10`.
- Children: `phrase` = `[2, 6]` → row 1. The map band above starts at 2.
- Maps in traversal order: `melody/map/tempo`, extent `[0, 8]` → row 2;
  `phrase/map/ticks`, extent `[2, 6]`, conflicts with `[0, 8]` → row 3.
- `rows = {min 0, max 3}`. Primitives: the two maps (`solid`), the lines,
  the wedge pairs (texts `8 ♩` and `4 ♩`), names from the top: `Ticks`
  (id `phrase/map/ticks/name`, timeline `phrase`), `Tempo`, `Phrase`,
  `Melody`; the wedge labels.

## `with_region`

Root `tl:19`, 12 quarters; `tl:20` (4) at 1/3, `tl:21` (3) at 2; region
`theme` from 2 to 6.

- Frame: `P = 12`, `N = 3`, `F = 15`.
- `tl:20` = `[1/3, 13/3]` → row 1; `tl:21` = `[2, 5]`, against `tl:20`:
  `1/3 < 5` and `2 < 13/3`: conflict → row 2.
- No maps. The region band below starts at distance 1 (nothing below): the
  region goes to row −1, `o = −1`: `base = −1 + 1/4 = −3/4`, `apex = −1 +
  1/8 = −7/8`.
- `rows = {min −1, max 2}`. Primitives: the region (`[2, 1]`–`[6, 1]`), the
  lines, the wedge pairs (texts `12 ♩`, `4 ♩`, `3 ♩`), names on rows 2, 1, 0
  (row −1 holds no line or map, so no name), the wedge labels, the region
  label at `x = (2 + 6) / 2 = [4, 1]`, `y = [−7, 8]`, anchor `north`, text
  `theme`.

## `flow_control`

Root `flow:quarters` (Flow control), 16 quarters; a break at 12 and a jump
from 8 to 2 labelled `Repeat`.

- Frame: `P = 16`, `N = 4`, `F = 20`.
- The jump band below starts at 1 (no children, maps or regions): the jump
  goes to row −1; `j = 1`, `base = −(1 − 1/2) = −1/2`, `apex = −1 + 1/8 =
  −7/8`; `dotted` by default.
- `rows = {min −1, max 0}`; the break spans `bottom = −1 − 1/2 = −3/2` to
  `top = 0 + 1/2 = 1/2` at `[12, 1]`.
- Primitives in order: break, jump, line, wedge pair (`16 ♩`), name, wedge
  labels, the jump label at `(8 + 2) / 2 = [5, 1]`, `y = [−7, 8]`, anchor
  `north`, text `Repeat`, and last the break's label: the break's `label` is
  `Fine` and its side is `below` (the default), so the label sits at the
  bottom of its line, `x = [12, 1]`, `y = bottom = [−3, 2]`, anchor
  `north`, id `flow:quarters/break/0/label`, colour `#000000`.

## `styled`

Two roots, `perf` before `score`. The rules, by container (depth: the
document 0, a root 1, its children 2), each with its rank key (names the
id, depth, names the type, number of domain and modality named):

- document (depth 0):
  - D1 `{}` sets `show_length: true` — (0, 0, 0, 0);
  - D2 `{element: label}` sets `colour: #404040` — (0, 0, 1, 0);
  - D3 `{element: map}` sets `side: below` — (0, 0, 1, 0);
  - D4 `{ids: [a]}` sets `visible: false` — (1, 0, 0, 0);
- `score` (depth 1; its subtree is `score`, `a`, `b`):
  - S1 `{element: wedge}` sets `side: above`, `colour: #006600` — (0, 1, 1, 0);
  - S2 `{domain: logical}` sets `colour: #000080` — (0, 1, 0, 1);
  - S3 `{element: region}` sets `colour: #800000` — (0, 1, 1, 0);
  - S4 `{element: region}` sets `colour: #008080` — (0, 1, 1, 0), later;
  - S5 `{element: child}` sets `visible: true` — (0, 1, 1, 0);
- `b` (depth 2): B1 `{}` sets `colour: #FF8000`,
  `show_projected_coordinates: true` — (0, 2, 0, 0);
- `perf` (depth 1): P1 `{element: wedge, domain: physical}` sets
  `colour: #7F00FF` — (0, 1, 1, 1).

**`perf`** (Performance), 10.0 seconds, `float`; child `p1` (4.0 at 1.0).
Its elements see D1 to D4 and P1 (no container for `p1`).

- Frame of floats: `P = 10.0`, `N = 2.5`, `F = 12.5`: `{"length": 12.5,
  "names": {"offset": 0.0, "length": 2.5}, "plot": {"offset": 2.5,
  "length": 10.0}}`; placement scalar `1.0`, offset `0.0`.
- `p1` = `[1.0, 5.0]`, side default above → row 1. `rows = {min 0, max 1}`.
- Lines: no rule sets their colour → `#0050EF`; D1 sets `show_length`.
- Wedges: P1 matches (wedge, physical) and sets the colour, `#7F00FF`; no
  rule sets the side → `below`; bases `−1/8` and `7/8`; texts `0.0 s`,
  `10.0 s` and `0.0 s`, `4.0 s`.
- Labels: D2 → `#404040`. Names `p1` (row 1) and `Performance` (row 0);
  length labels, side default above so anchor `south`: `perf` at
  `(0.0 + 10.0) / 2 = 5.0`, text `10.0 s`; `p1` at `(1.0 + 5.0) / 2 = 3.0`
  on row 1, text `4.0 s`; then the wedge labels, anchor `north`.

**`score`** (Score), 8 quarters; children `a` (4 at 0), `b` (4 at 4); map
`ticks` (Ticks); region `intro` from 0 to 2; jump from 8 to 0, `da_capo`,
labelled `D.C.`. All of it is logical and continuous.

- Frame: `P = 8`, `N = 2`, `F = 10`.
- `a`: `visible` is set by D4 (1, 0, 0, 0) and S5 (0, 1, 1, 0); the id rule
  wins although its container is outer → hidden, no row.
- `b`: S5 → visible; no rule sets its side → above, row 1. Colour: B1
  (0, 2, 0, 0) outranks S2 (0, 1, 0, 1), the nearest container →
  `#FF8000`.
- `score`'s line: colour only from S2 → `#000080`.
- The map: side only from D3 (no rule of `score` sets a side for it, so the
  property falls through to the document) → below; the map band below
  starts at 1 → row −1. Colour S2 → `#000080`.
- The region: colour from S3, S4 (0, 1, 1, 0) over S2 (0, 1, 0, 1), the type
  outranking the domain; S3 and S4 tie and the later wins → `#008080`. Side
  default below; band starts at 2 → row −2, `base = −2 + 1/4 = −7/4`,
  `apex = −15/8`.
- The jump: colour S2 → `#000080`; dotted, below; band starts at 3 → row
  −3, `base = −(3 − 1/2) = −5/2`, `apex = −3 + 1/8 = −23/8`.
- `rows = {min −3, max 1}`.
- `score`'s wedges: S1 (0, 1, 1, 0) outranks S2 (0, 1, 0, 1) for the colour
  → `#006600`, and sets the side → above, base `1/8`.
- `b`'s wedges: colour from B1 (depth 2) → `#FF8000`; B1 sets no side, so the
  side falls through to S1 → above, base `9/8`. B1 also sets `b`'s
  projections: two wedges on row 0 at 4 and 8, the same styles,
  texts `4 ♩` and `8 ♩` (root coordinates).
- Labels: those of `score`'s elements take S2 (0, 1, 0, 1), which outranks
  D2 (0, 0, 1, 0) from the outer container → `#000080`; those of `b` take
  B1 → `#FF8000`. Names: row 1 `b`, row 0 `Score`, row −1 `Ticks` (the map's
  name, timeline `score`). Length labels, anchor `south`: `score` at
  `[4, 1]` (`8 ♩`), `b` at `(4 + 8) / 2 = [6, 1]` on row 1 (`4 ♩`). Wedge
  labels, anchor `south`: `score` `0 ♩` and `8 ♩`, `b` `0 ♩` and `4 ♩`,
  projections `4 ♩` and `8 ♩`. The region label at `[1, 1]`,
  `y = [−15, 8]`, `north`, `intro`; the jump label at `[4, 1]`,
  `y = [−23, 8]`, `north`, `D.C.`.
