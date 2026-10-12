# Hand-derived drawings

Seven of the drawings in this directory are derived by hand from the
[drawing specification](../../../docs/drawing.md) and the font metrics
alone. The arithmetic below lets any implementation check itself against
the specification line by line: every intermediate value is given, and each
`figure.svg` is reproduced at the end of its section. These seven SVG files
are never regenerated. Every other figure in this directory, and every
`figure.tex`, is emitted (see [`fixtures/README.md`](../../README.md)).

Section numbers (§) refer to the drawing specification. Every drawing is
placed alone at `(0, 0)` with scale 1 (§7.1); the page translates it by
`(16, 16)` and is `W + 32` by `H + 32`. Exact values are given in full; a
value as the writer prints it (§7.3) follows an arrow (`→`). Every
`inputs.json` here supplies no application layer, so the layers are the
defaults and the manifest's own `graphical` block (§1).

The vertical padding is `P × v` (§6.5), `v` the placement's `spacing`: 8
in every drawing here but `nested__length-800-spacing-2`, where it is 16.
The horizontal padding is `P = 8` throughout (§6.6, §6.7). Every root
`<svg>` element carries `font-family="DejaVu Sans"`,
`text-rendering="geometricPrecision"` and the `style` that turns kerning
and ligatures off (§7.3).

Every element is addressed by its own id (§2.2): a map, region, break or
jump carries its id as its `data-address`, a wedge `T/start` or `T/end`
for the root `T`, and a name or label the address of its element followed
by `/name` or `/label` (`jump_1/label`, `clt_1/end/label`).

| Drawing | Manifest | Non-default inputs |
|---|---|---|
| `bare` | `bare.json` | none |
| `nested` | `nested.json` | none |
| `map` | `map.json` | none |
| `nested__length-800-spacing-2` | `nested.json` | `length` 800, `spacing` 2 |
| `flow_control` | `flow_control.json` | none |
| `with_region` | `with_region.json` | none |
| `styled__score` | `styled__score.json` | none (the manifest's own `graphical` block styles it) |

## Shared quantities

Font measures (§5.1):

| Measure | s = 9 | s = 10 | s = 11 | s = 12 |
|---|---|---|---|---|
| `a(s) = 1901 × s / 2048` | 8.35400390625 | 9.2822265625 | 10.21044921875 | 11.138671875 |
| `d(s) = 483 × s / 2048` | 2.12255859375 | 2.3583984375 | 2.59423828125 | 2.830078125 |
| `h(s) = 2384 × s / 2048` | 10.4765625 | 11.640625 | 12.8046875 | 13.96875 |
| name baseline shift `(a(s) − d(s)) / 2` (§6.6) | | | 3.80810546875 | 4.154296875 |

Text widths `w(text, s) = A × s / 2048`, `A` the sum of the advances:

| Text | Advances | `A` | Size | Width |
|---|---|---|---|---|
| `Bare` | 1405 1255 842 1260 | 4762 | 11 | 25.5771484375 |
| `clt_1`, `clt_2`, `clt_3` | 1126 569 803 1024 1303 | 4825 | 11 | 25.91552734375 |
| `Melody` | 1767 1260 569 1253 1300 1212 | 7361 | 11 | 39.53662109375 |
| `Phrase` | 1235 1298 842 1255 1067 1260 | 6957 | 11 | 37.36669921875 |
| `Flow control` | 1178 569 1253 1675 651 1126 1253 1298 803 842 1253 569 | 12470 | 11 | 66.9775390625 |
| `Styled score` | 1300 803 1212 569 1260 1300 651 1067 1126 1253 842 1260 | 12643 | 12 | 74.080078125 |
| `b` | 1300 | 1300 | 11 | 6.982421875 |
| `0 ♩`, `8 ♩` | 1303 651 966 | 2920 | 9 / 10 | 12.83203125 / 14.2578125 |
| `12 ♩`, `16 ♩` | 1303 1303 651 966 | 4223 | 9 | 18.55810546875 |
| `Repeat` | 1423 1260 1300 1260 1255 803 | 7301 | 9 | 32.08447265625 |
| `Fine` | 1178 569 1298 1260 | 4305 | 9 | 18.91845703125 |
| `theme` | 803 1298 1260 1995 1260 | 6616 | 9 | 29.07421875 |
| `intro` | 569 1298 803 842 1253 | 4765 | 10 | 23.2666015625 |
| `D.C.` | 1577 651 1430 651 | 4309 | 10 | 21.0400390625 |

**The default cascade** (§2.5, §4) styles every drawing but `styled__score`:

- block: `fill` `#F3F4F6`, `rx` 10;
- every timeline here is a `ContinuousLogicalTimeline`: `stroke` and `fill`
  `#00CC00`, `stroke-width` 3, `stroke-dasharray` `none`; a child has `side`
  `above`;
- wedges: `fill` `#000000` (`{element: wedge}` outranks `{domain:
  logical}`), `side` the initial `below`;
- breaks: `stroke` `#FF0000`, `stroke-width` 1.5, dash `2 2`; jumps:
  `stroke` and `fill` `#000000`, `stroke-width` 1.5; regions: `stroke`
  `#000000`, `stroke-width` 1, dash `none` inherited from the timeline; all
  three `side` `below`;
- labels: `fill` `#000000`, `font-size` 9; names: `fill` `#000000`,
  `font-size` 11, `max-width` 160 (no name here is cut).

So `w = 3` for every line, every name size is 11 and the row pitch is
`p = p0 = max(14 × v, 12.8046875)` (§6.2).

**The default root band below.** With both wedges below and their labels,
at `u = 0` and `u = 1`, far apart, first fit puts the labels in one tier
(§6.3), `T = 1`. The band reaches (§6.4)

    w / 2 + 13 + 2 + T × h(9) = 1.5 + 13 + 2 + 10.4765625 = 26.9765625

and the wedges have tip `y_root + 1.5`, base `y_root + 14.5` and corners
`X ∓ 3`; the labels' baseline is `y_root + 16.5 + a(9)` (§6.6). This band
is the whole below side, `Eb = 26.9765625`, in `bare`, `nested`, `map` and
`nested__length-800-spacing-2`.

**A locked child** (`w = 3`) ends its line at `Xe − 4.5`; its diamond is
`(Xe − 4.5, y)`, `(Xe, y − 1.2 × 3)`, `(Xe + 4.5, y)`, `(Xe, y + 1.2 × 3)`,
where `1.2 × 3 = 3.5999999999999996` prints `3.6`, stroked in the child's
`stroke` with width 1.5 (§7.2). An unlocked root's arrowhead is
`(Xe + 9, y)`, `(Xe, y ∓ 4.5)`.

## `bare`

The root `bare` (name `Bare`), 8 quarters, not locked, with no maps,
children, regions or flow control.

- Above: nothing, so no band and `Ea = 0` (§6.4).
- `y_root = max(8 + 0, 8 + 12.8046875 / 2) = 14.40234375` (§6.5).
- `Hc = 14.40234375 + 26.9765625 + 8 = 49.37890625`.
- `N = 25.5771484375`, `G' = 8`; the label `0 ♩` asks for
  `8 + 6.416015625 − 0 = 14.416015625`, `8 ♩` for less;
  `x0 = max(8 + 25.5771484375 + 8, 14.416015625) = 41.5771484375` (§6.7).
- Root from `41.5771484375` to `441.5771484375`; arrowhead tip
  `450.5771484375`, base ordinates `9.90234375` and `18.90234375`.
- Wedges: tip `15.90234375`, base `28.90234375`; labels' baseline
  `14.40234375 + 16.5 + 8.35400390625 = 39.25634765625`.
- Name at `x = 8`, baseline `14.40234375 + 3.80810546875 = 18.21044921875`.
- Right edges (§6.7): the arrow tip `450.5771484375` beats the label `8 ♩`
  (`447.9931640625`); `W = 458.5771484375`, `H = 49.37890625`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="490.5771" height="81.3789" viewBox="0 0 490.5771 81.3789" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="458.5771" height="49.3789" rx="10" fill="#F3F4F6"/>
<line data-address="bare" x1="41.5771" y1="14.4023" x2="441.5771" y2="14.4023" stroke="#00CC00" stroke-width="3"/>
<circle data-address="bare" cx="41.5771" cy="14.4023" r="3" fill="#00CC00"/>
<polygon data-address="bare" points="450.5771,14.4023 441.5771,9.9023 441.5771,18.9023" fill="#00CC00"/>
<polygon data-address="bare/start" points="41.5771,15.9023 38.5771,28.9023 44.5771,28.9023" fill="#000000"/>
<polygon data-address="bare/end" points="441.5771,15.9023 438.5771,28.9023 444.5771,28.9023" fill="#000000"/>
<text data-address="bare/name" x="8" y="18.2104" text-anchor="start" font-size="11" fill="#000000">Bare</text>
<text data-address="bare/start/label" x="41.5771" y="39.2563" text-anchor="middle" font-size="9" fill="#000000">0 ♩</text>
<text data-address="bare/end/label" x="441.5771" y="39.2563" text-anchor="middle" font-size="9" fill="#000000">8 ♩</text>
</g>
</svg>
```

## `nested`

The root `clt_1`, 16 quarters, not locked; its child `clt_3` (offset 4,
length 8, locked) holds `clt_2` (offset 3/2, length 2, locked). All names
are null, so each timeline is named by its id (§5.3).

- On the root's axis (§3.1) `clt_3` spans `[4, 12]` and `clt_2`
  `[11/2, 15/2]`; `L × u` (§3.2) gives 100, 300, 137.5 and 187.5.
- Above, the children band is the first band and starts at
  `c0 = p0 / 2 = 7` (§6.4). `clt_3` takes row 1; `clt_2`, whose minimum row
  is its parent's row plus 1, row 2. No child has maps, so every half is
  `7`: `l1 = 7 + 7 = 14`, `l2 = 14 + (7 + 7) = 28`, `Ea = 7 + 28 = 35`.
- `y_root = max(8 + 35, 14.40234375) = 43`; `clt_3` at `43 − 14 = 29`,
  `clt_2` at `43 − 28 = 15`.
- `Hc = 43 + 26.9765625 + 8 = 77.9765625`.
- `N = 25.91552734375`; `x0 = max(8 + 25.91552734375 + 8, 14.416015625) =
  41.91552734375`.
- Root from `41.91552734375` to `441.91552734375`, tip `450.91552734375`,
  base ordinates `38.5` and `47.5`. `clt_3` from `141.91552734375` to
  `341.91552734375` (line end `337.41552734375`); `clt_2` from
  `179.41552734375` to `229.41552734375` (line end `224.91552734375`).
- Wedges: tip `44.5`, base `57.5`; labels' baseline `67.85400390625`.
- Names, top row down (§6.6): `clt_2`, `clt_3`, `clt_1` at `15`, `29`, `43`
  plus `3.80810546875`.
- Right edges: the label `16 ♩`, `441.91552734375 + 9.279052734375 =
  451.194580078125`, beats the arrow tip; `W = 459.194580078125`,
  `H = 77.9765625`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="491.1946" height="109.9766" viewBox="0 0 491.1946 109.9766" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="459.1946" height="77.9766" rx="10" fill="#F3F4F6"/>
<line data-address="clt_1" x1="41.9155" y1="43" x2="441.9155" y2="43" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_1" cx="41.9155" cy="43" r="3" fill="#00CC00"/>
<polygon data-address="clt_1" points="450.9155,43 441.9155,38.5 441.9155,47.5" fill="#00CC00"/>
<line data-address="clt_3" x1="141.9155" y1="29" x2="337.4155" y2="29" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_3" cx="141.9155" cy="29" r="3" fill="#00CC00"/>
<polygon data-address="clt_3" points="337.4155,29 341.9155,25.4 346.4155,29 341.9155,32.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<line data-address="clt_2" x1="179.4155" y1="15" x2="224.9155" y2="15" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_2" cx="179.4155" cy="15" r="3" fill="#00CC00"/>
<polygon data-address="clt_2" points="224.9155,15 229.4155,11.4 233.9155,15 229.4155,18.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<polygon data-address="clt_1/start" points="41.9155,44.5 38.9155,57.5 44.9155,57.5" fill="#000000"/>
<polygon data-address="clt_1/end" points="441.9155,44.5 438.9155,57.5 444.9155,57.5" fill="#000000"/>
<text data-address="clt_2/name" x="8" y="18.8081" text-anchor="start" font-size="11" fill="#000000">clt_2</text>
<text data-address="clt_3/name" x="8" y="32.8081" text-anchor="start" font-size="11" fill="#000000">clt_3</text>
<text data-address="clt_1/name" x="8" y="46.8081" text-anchor="start" font-size="11" fill="#000000">clt_1</text>
<text data-address="clt_1/start/label" x="41.9155" y="67.854" text-anchor="middle" font-size="9" fill="#000000">0 ♩</text>
<text data-address="clt_1/end/label" x="441.9155" y="67.854" text-anchor="middle" font-size="9" fill="#000000">16 ♩</text>
</g>
</svg>
```

## `map`

The root `melody` (`Melody`, 8 quarters, not locked) has the map `tempo`
(target `seconds`: physical, continuous, so `stroke` `#0050EF`) and the
child `phrase` (`Phrase`, offset 2, length 4, locked), which has the map
`ticks` (target `ticks`: logical, discrete, so `stroke` `#00CC00` and dash
`1 1`). Both maps have `stroke-width` 1 and `side` `above`.

- Map stacks (§6.4), `g = 3`, `d = 2`, `w = 3`: map 1 is centred
  `1.5 + 1 × 5 − 1 = 5.5` from its line; a stack of one reaches
  `e = 1.5 + 5 = 6.5`.
- Above, the root band is `tempo`'s stack, 6.5 wide. The children band
  starts at `max(6.5 + 4, 7) = 10.5`. `phrase` takes row 1; its `above` map
  lies in the row's outer half, and `6.5 < 7` leaves both halves 7:
  `l1 = 17.5`, `Ea = 10.5 + 14 = 24.5`.
- `y_root = 8 + 24.5 = 32.5`; `phrase` at `32.5 − 17.5 = 15`.
- `Hc = 32.5 + 26.9765625 + 8 = 67.4765625`.
- `N = 39.53662109375`; `x0 = 55.53662109375`.
- Root from `55.53662109375` to `455.53662109375`, tip `464.53662109375`,
  base ordinates `28` and `37`. `phrase` from `155.53662109375` to
  `355.53662109375`.
- `tempo`: `yc = 32.5 − 5.5 = 27`, outline at `26` and `28`, from the
  root's `Xs` to `Xe` (§6.6). `ticks`: `yc = 15 − 5.5 = 9.5`, outline at
  `8.5` and `10.5`, spanning `phrase`.
- Wedges: tip `34`, base `47`; labels' baseline `57.35400390625`.
- Names: `Phrase` at `15 + 3.80810546875`, `Melody` at
  `32.5 + 3.80810546875`.
- Right edges: the arrow tip `464.53662109375` (the label `8 ♩` reaches
  `461.95263671875`); `W = 472.53662109375`, `H = 67.4765625`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="504.5366" height="99.4766" viewBox="0 0 504.5366 99.4766" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="472.5366" height="67.4766" rx="10" fill="#F3F4F6"/>
<polygon data-address="tempo" points="55.5366,26 455.5366,26 455.5366,28 55.5366,28" fill="none" stroke="#0050EF" stroke-width="1"/>
<polygon data-address="ticks" points="155.5366,8.5 355.5366,8.5 355.5366,10.5 155.5366,10.5" fill="none" stroke="#00CC00" stroke-width="1" stroke-dasharray="1 1"/>
<line data-address="melody" x1="55.5366" y1="32.5" x2="455.5366" y2="32.5" stroke="#00CC00" stroke-width="3"/>
<circle data-address="melody" cx="55.5366" cy="32.5" r="3" fill="#00CC00"/>
<polygon data-address="melody" points="464.5366,32.5 455.5366,28 455.5366,37" fill="#00CC00"/>
<line data-address="phrase" x1="155.5366" y1="15" x2="351.0366" y2="15" stroke="#00CC00" stroke-width="3"/>
<circle data-address="phrase" cx="155.5366" cy="15" r="3" fill="#00CC00"/>
<polygon data-address="phrase" points="351.0366,15 355.5366,11.4 360.0366,15 355.5366,18.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<polygon data-address="melody/start" points="55.5366,34 52.5366,47 58.5366,47" fill="#000000"/>
<polygon data-address="melody/end" points="455.5366,34 452.5366,47 458.5366,47" fill="#000000"/>
<text data-address="phrase/name" x="8" y="18.8081" text-anchor="start" font-size="11" fill="#000000">Phrase</text>
<text data-address="melody/name" x="8" y="36.3081" text-anchor="start" font-size="11" fill="#000000">Melody</text>
<text data-address="melody/start/label" x="55.5366" y="57.354" text-anchor="middle" font-size="9" fill="#000000">0 ♩</text>
<text data-address="melody/end/label" x="455.5366" y="57.354" text-anchor="middle" font-size="9" fill="#000000">8 ♩</text>
</g>
</svg>
```

## `nested__length-800-spacing-2`

`nested` with `L = 800` and `v = 2`.

- Stretched distances (§6.2): `p = p0 = max(28, 12.8046875) = 28`, `B = 8`;
  the vertical padding is `P × v = 16` (§6.5). The wedges and their labels
  keep their size: `Eb = 26.9765625`, and `x0 = 41.91552734375` as in
  `nested`, the horizontal padding staying 8.
- Children band: `c0 = 14`, halves 14: `l1 = 28`, `l2 = 56`, `Ea = 70`.
- `y_root = max(16 + 70, 16 + 6.40234375) = 86`; `clt_3` at `86 − 28 = 58`,
  `clt_2` at `86 − 56 = 30`.
- `Hc = 86 + 26.9765625 + 16 = 128.9765625` → `128.9766`.
- `L × u` gives 200, 600, 275, 375 and 800: the root from `41.91552734375`
  to `841.91552734375` (tip `850.91552734375`, base ordinates `81.5` and
  `90.5`), `clt_3` from `241.91552734375` to `641.91552734375` (diamond
  ordinates `54.4` and `61.6`), `clt_2` from `316.91552734375` to
  `416.91552734375` (diamond ordinates `26.4` and `33.6`).
- Wedges: tip `87.5`, base `100.5`; labels' baseline
  `86 + 16.5 + 8.35400390625 = 110.85400390625` → `110.854`.
  Names at `33.80810546875`, `61.80810546875` and `89.80810546875`.
- Right edges: the label `16 ♩` at `851.194580078125`;
  `W = 859.194580078125`, `H = 128.9765625`; the page is
  `891.194580078125` by `160.9765625` → `891.1946` by `160.9766`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="891.1946" height="160.9766" viewBox="0 0 891.1946 160.9766" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="859.1946" height="128.9766" rx="10" fill="#F3F4F6"/>
<line data-address="clt_1" x1="41.9155" y1="86" x2="841.9155" y2="86" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_1" cx="41.9155" cy="86" r="3" fill="#00CC00"/>
<polygon data-address="clt_1" points="850.9155,86 841.9155,81.5 841.9155,90.5" fill="#00CC00"/>
<line data-address="clt_3" x1="241.9155" y1="58" x2="637.4155" y2="58" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_3" cx="241.9155" cy="58" r="3" fill="#00CC00"/>
<polygon data-address="clt_3" points="637.4155,58 641.9155,54.4 646.4155,58 641.9155,61.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<line data-address="clt_2" x1="316.9155" y1="30" x2="412.4155" y2="30" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_2" cx="316.9155" cy="30" r="3" fill="#00CC00"/>
<polygon data-address="clt_2" points="412.4155,30 416.9155,26.4 421.4155,30 416.9155,33.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<polygon data-address="clt_1/start" points="41.9155,87.5 38.9155,100.5 44.9155,100.5" fill="#000000"/>
<polygon data-address="clt_1/end" points="841.9155,87.5 838.9155,100.5 844.9155,100.5" fill="#000000"/>
<text data-address="clt_2/name" x="8" y="33.8081" text-anchor="start" font-size="11" fill="#000000">clt_2</text>
<text data-address="clt_3/name" x="8" y="61.8081" text-anchor="start" font-size="11" fill="#000000">clt_3</text>
<text data-address="clt_1/name" x="8" y="89.8081" text-anchor="start" font-size="11" fill="#000000">clt_1</text>
<text data-address="clt_1/start/label" x="41.9155" y="110.854" text-anchor="middle" font-size="9" fill="#000000">0 ♩</text>
<text data-address="clt_1/end/label" x="841.9155" y="110.854" text-anchor="middle" font-size="9" fill="#000000">16 ♩</text>
</g>
</svg>
```

## `flow_control`

The root `flow:quarters` (`Flow control`), 16 quarters, not locked, with
no children, maps or regions; one break `break_1` at 12 labelled `Fine`
and one jump `jump_1` from 8 to 2 labelled `Repeat`. The marker
`marker_1` at 2, the jump's target, is not drawn and takes no room (§2.2).

**Layout.**

- Above: nothing, `Ea = 0`; `y_root = 14.40234375`.
- Below: the default root band, 26.9765625. The flow band starts at
  `26.9765625 + 4 = 30.9765625`; one break label, one tier, so the flow row
  lies at `f0 = 30.9765625 + 10.4765625 = 41.453125`. One jump, `K = 1`,
  apex at `f0 + 8 = 49.453125`. The band is
  `10.4765625 + 8 + 0 + 2 + 10.4765625 = 30.953125` wide, `Eb = 61.9296875`.
- `Hc = 14.40234375 + 61.9296875 + 8 = 84.33203125` → `84.332`.

**Horizontal.** `N = 66.9775390625`, `G' = 8`; the largest label candidate is `0 ♩`'s
14.416015625, so `x0 = 8 + 66.9775390625 + 8 = 82.9775390625`.

| Position | `u` | `x` |
|---|---|---|
| 0 | 0 | 82.9775390625 |
| 2 (jump to) | 0.125 | 132.9775390625 |
| 5 (jump label) | 0.3125 | 207.9775390625 |
| 8 (jump from) | 0.5 | 282.9775390625 |
| 12 (break) | 0.75 | 382.9775390625 |
| 16 | 1 | 482.9775390625 |

**Elements.**

- Root at `14.40234375`, arrowhead tip `491.9775390625`, base ordinates
  `9.90234375` and `18.90234375`. Wedges: tip `15.90234375`, base
  `28.90234375`; labels' baseline `39.25634765625`.
- Flow row `yf = 14.40234375 + 41.453125 = 55.85546875`; apex
  `ya = 14.40234375 + 49.453125 = 63.85546875`.
- Break: from `(382.9775390625, yf)` to `(382.9775390625, 8)`, `P × v = 8` (§6.4). Its
  label at `x + 3 = 385.9775390625`, tier 1, baseline
  `yf − d(9) = 53.73291015625`.
- Jump (`w = 1.5`, §6.6, evaluated as §3.3 orders it):
  - `q = (132.9775390625 − 282.9775390625) / 4 = −37.5`;
  - `yc = yf + 4/3 × (ya − yf) = 55.85546875 + 10.666666666666666 =
    66.52213541666667`;
  - `C1 = (245.4775390625, yc)`, `C2 = (170.4775390625, yc)`;
  - `Xt − Cx = −37.5`, `yf − yc = −10.666666666666671`,
    `ℓ = sqrt(1406.25 + 113.77777777777789) = 38.98753362009166`;
    `ux = −0.9618459163232351`, `uy = −0.2735917273097203`;
  - `Bh = (Xt − 6 × ux, yf − 6 × uy) = (138.74861456043942,
    57.49701911385832)`;
  - `n = (0.2735917273097203, −0.9618459163232351)`;
    `Bh − 3 × n = (137.92783937851027, 60.382556862828025)`,
    `Bh + 3 × n = (139.56938974236857, 54.61148136488862)`;
  - the label `Repeat` at `x(5)`, baseline
    `14.40234375 + (49.453125 + 2) + 8.35400390625 = 74.20947265625`.
- Name at `x = 8`, baseline `18.21044921875`.

**Box.** The largest right edge is the label `16 ♩`,
`482.9775390625 + 9.279052734375 = 492.256591796875` (the arrow tip is
`491.9775390625`); `W = 500.256591796875`, `H = 84.33203125`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="532.2566" height="116.332" viewBox="0 0 532.2566 116.332" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="500.2566" height="84.332" rx="10" fill="#F3F4F6"/>
<line data-address="break_1" x1="382.9775" y1="55.8555" x2="382.9775" y2="8" stroke="#FF0000" stroke-width="1.5" stroke-dasharray="2 2"/>
<path data-address="jump_1" d="M282.9775 55.8555C245.4775 66.5221 170.4775 66.5221 138.7486 57.497" fill="none" stroke="#000000" stroke-width="1.5"/>
<polygon data-address="jump_1" points="132.9775,55.8555 137.9278,60.3826 139.5694,54.6115" fill="#000000"/>
<line data-address="flow:quarters" x1="82.9775" y1="14.4023" x2="482.9775" y2="14.4023" stroke="#00CC00" stroke-width="3"/>
<circle data-address="flow:quarters" cx="82.9775" cy="14.4023" r="3" fill="#00CC00"/>
<polygon data-address="flow:quarters" points="491.9775,14.4023 482.9775,9.9023 482.9775,18.9023" fill="#00CC00"/>
<polygon data-address="flow:quarters/start" points="82.9775,15.9023 79.9775,28.9023 85.9775,28.9023" fill="#000000"/>
<polygon data-address="flow:quarters/end" points="482.9775,15.9023 479.9775,28.9023 485.9775,28.9023" fill="#000000"/>
<text data-address="flow:quarters/name" x="8" y="18.2104" text-anchor="start" font-size="11" fill="#000000">Flow control</text>
<text data-address="flow:quarters/start/label" x="82.9775" y="39.2563" text-anchor="middle" font-size="9" fill="#000000">0 ♩</text>
<text data-address="flow:quarters/end/label" x="482.9775" y="39.2563" text-anchor="middle" font-size="9" fill="#000000">16 ♩</text>
<text data-address="jump_1/label" x="207.9775" y="74.2095" text-anchor="middle" font-size="9" fill="#000000">Repeat</text>
<text data-address="break_1/label" x="385.9775" y="53.7329" text-anchor="start" font-size="9" fill="#000000">Fine</text>
</g>
</svg>
```

## `with_region`

The root `clt_1`, 12 quarters, not locked; children in canonical order
(§6.1, by offset) `clt_2` (offset 1/3, length 4, locked) and `clt_3`
(offset 2, length 3, locked); one region `region_1` named `theme` from 2
to 6. All timeline names are null.

**Layout.**

- Above, first fit (§6.3), minimum row 1 for both: `clt_2` spans
  `[x(1/3), x(13/3)]` and takes row 1; `clt_3`, `[x(2), x(5)]`, conflicts
  with it and takes row 2. As in `nested`: `c0 = 7`, rows at 14 and 28,
  `Ea = 35`, `y_root = 43`, `clt_2` at `29`, `clt_3` at `15`.
- Below: the default root band, 26.9765625. The region band starts at
  `r0 = 26.9765625 + 4 = 30.9765625`; `pr = 6 + 2 + 10.4765625 + 4 =
  22.4765625`; one row, `22.4765625 − 4 = 18.4765625` wide;
  `Eb = 49.453125`.
- `Hc = 43 + 49.453125 + 8 = 100.453125`.

**Horizontal.** Every name is 25.91552734375 wide; the label `theme` asks
for `8 + 14.537109375 − 133.33333333333331 = −110.79622395833331`, so
`x0 = 8 + 25.91552734375 + 8 = 41.91552734375`.

| Position | `u` | `400 × u` | `x` |
|---|---|---|---|
| 0 | 0 | 0 | 41.91552734375 |
| 1/3 | 0.027777777777777776 | 11.11111111111111 | 53.026638454861114 |
| 2 | 0.16666666666666666 | 66.66666666666666 | 108.58219401041666 |
| 4 (region midpoint) | 0.3333333333333333 | 133.33333333333331 | 175.24886067708331 |
| 13/3 | 0.3611111111111111 | 144.44444444444443 | 186.35997178819443 |
| 5 | 0.4166666666666667 | 166.66666666666669 | 208.58219401041669 |
| 6 | 0.5 | 200 | 241.91552734375 |
| 12 | 1 | 400 | 441.91552734375 |

**Elements.**

- Root at `43`, tip `450.91552734375`, base ordinates `38.5` and `47.5`.
  `clt_2` from `x(1/3)` to `x(13/3)` at `29`, line end
  `181.85997178819443` → `181.86`; `clt_3` from `x(2)` to `x(5)` at `15`,
  line end `204.08219401041669`. Wedges: tip `44.5`, base `57.5`; labels'
  baseline `67.85400390625`.
- Brace (§7.2): `X1 = x(2)`, `X2 = x(6)`, `Xm = x(4)`; arms
  `Yb = 43 + 30.9765625 = 73.9765625`, tip `Ya = 79.9765625`,
  `Ym = 76.9765625`, `k = 3`. The label `theme` at `Xm`, baseline
  `43 + (30.9765625 + 6 + 2) + 8.35400390625 = 90.33056640625`.
- Names, top row down: `clt_3`, `clt_2`, `clt_1` at `15`, `29`, `43` plus
  `3.80810546875`.

**Box.** The largest right edge is the label `12 ♩`, `441.91552734375 +
9.279052734375 = 451.194580078125`; `W = 459.194580078125`,
`H = 100.453125`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="491.1946" height="132.4531" viewBox="0 0 491.1946 132.4531" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="459.1946" height="100.4531" rx="10" fill="#F3F4F6"/>
<path data-address="region_1" d="M108.5822 73.9766Q108.5822 76.9766 111.5822 76.9766L172.2489 76.9766Q175.2489 76.9766 175.2489 79.9766Q175.2489 76.9766 178.2489 76.9766L238.9155 76.9766Q241.9155 76.9766 241.9155 73.9766" fill="none" stroke="#000000" stroke-width="1"/>
<line data-address="clt_1" x1="41.9155" y1="43" x2="441.9155" y2="43" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_1" cx="41.9155" cy="43" r="3" fill="#00CC00"/>
<polygon data-address="clt_1" points="450.9155,43 441.9155,38.5 441.9155,47.5" fill="#00CC00"/>
<line data-address="clt_2" x1="53.0266" y1="29" x2="181.86" y2="29" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_2" cx="53.0266" cy="29" r="3" fill="#00CC00"/>
<polygon data-address="clt_2" points="181.86,29 186.36,25.4 190.86,29 186.36,32.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<line data-address="clt_3" x1="108.5822" y1="15" x2="204.0822" y2="15" stroke="#00CC00" stroke-width="3"/>
<circle data-address="clt_3" cx="108.5822" cy="15" r="3" fill="#00CC00"/>
<polygon data-address="clt_3" points="204.0822,15 208.5822,11.4 213.0822,15 208.5822,18.6" fill="none" stroke="#00CC00" stroke-width="1.5"/>
<polygon data-address="clt_1/start" points="41.9155,44.5 38.9155,57.5 44.9155,57.5" fill="#000000"/>
<polygon data-address="clt_1/end" points="441.9155,44.5 438.9155,57.5 444.9155,57.5" fill="#000000"/>
<text data-address="clt_3/name" x="8" y="18.8081" text-anchor="start" font-size="11" fill="#000000">clt_3</text>
<text data-address="clt_2/name" x="8" y="32.8081" text-anchor="start" font-size="11" fill="#000000">clt_2</text>
<text data-address="clt_1/name" x="8" y="46.8081" text-anchor="start" font-size="11" fill="#000000">clt_1</text>
<text data-address="clt_1/start/label" x="41.9155" y="67.854" text-anchor="middle" font-size="9" fill="#000000">0 ♩</text>
<text data-address="clt_1/end/label" x="441.9155" y="67.854" text-anchor="middle" font-size="9" fill="#000000">12 ♩</text>
<text data-address="region_1/label" x="175.2489" y="90.3306" text-anchor="middle" font-size="9" fill="#000000">theme</text>
</g>
</svg>
```

## `styled__score`

The root `score` (`Score`), 8 quarters, not locked; children `a` (offset 0,
length 4, locked) and `b` (offset 4, length 4, locked); one conversion map
`ticks` (`QuartersToTicks`, target `ticks`: logical, discrete); the region
`intro` (named `intro`) from 0 to 2; the jump `da-capo` from 8 to 0
labelled `D.C.`. The layers are the
defaults and the manifest's `graphical` block, whose statements are called
`S0` to `S20` here in their written order.

**Cascade** (§2.5). Rank keys, most significant first: layer, `ids`,
`within` depth (`score` 1, `b` 2), `class`, `element`, the number of
`domain` and `modality`, position.

| Element | Property | Value | Deciding statement |
|---|---|---|---|
| block | `rx`; `fill` | 4; `#F3F4F6` | `S4`; the default (the block has no domain) |
| `score` | `stroke`, `fill`, `stroke-width`, `opacity` | `#1D4ED8`, `#1D4ED8`, 4, 0.8 | `S5` (the style `accent`), written on the line, circle and arrowhead |
| `a` | `display` | `none` | `S3` (`ids`) over `S13` (`within` only) |
| `b` | `stroke`, `fill` | `#EA580C` | `S14` (`within` depth 2) over `logical-domain` |
| `b` | `stroke-width`, `side`, `opacity` | 3, `above`, 1 | defaults; `S5` selects `timeline`, not `child`, and opacity is not inherited |
| `ticks` | `stroke`, `stroke-width` | `#7C3AED`, 1.5 | `S6` (`class`) |
| `ticks` | `stroke-dasharray`; `side` | `4 2`; `below` | `S7`; `S2` |
| `intro` | `stroke` | `#0F766E` | `S9` over `S8`: equal rank, later position |
| `da-capo` | `stroke`, `fill`, `stroke-width` | `#DB2777`, `#DB2777`, 2 | `S10` |
| `score/start` | `fill`, `side` | `#65A30D`, `above` | `S11`; its `stroke` is not read by a wedge (§2.4) |
| `score/end` | `fill`; `side` | `#B45309`; `above` | `S12` (`ids`) over `S11`; `S11` |
| `score/start/label` | `fill`, `font-size` | `#4D7C0F`, 10 | `S15` (`within` depth 1) over `S0` |
| `score/end/label` | `fill`, `font-size` | `#A16207`, 10 | `S16` (`ids`); `S15` |
| `intro/label` | `fill`, `font-size` | `#0E7490`, 10 | `S17`; `S15` |
| `da-capo/label` | `fill`, `font-size` | `#9D174D`, 10 | `S18`; `S15` |
| `score/name` | `fill`, `font-size`, `content`, `max-width` | `#111827`, 12, `Styled score`, 120 | `S19` |
| `b/name` | `fill`; `font-size`, `max-width` | `#0369A1`; 11, 160 | `S20` (depth 2) over `S1`; the default |

The `stroke` that `S0` and `S1` set is not read by labels and names.

**Layout.** The root's name size is 12, so `p0 = max(14, 13.96875) = 14`;
every label is 10.

- Above, root band: both wedges lie above; their labels share tier 1. Reach
  `4 / 2 + 13 + 2 + 11.640625 = 28.640625`.
- Above, children band: starts at `28.640625 + 4 = 32.640625`, beyond
  `p0 / 2`. Only `b` is displayed, in row 1, halves 7: `l1 = 39.640625`,
  `Ea = 46.640625`.
- `y_root = 8 + 46.640625 = 54.640625`.
- Below, root band: the map stack, `J = 1`, `w = 4`: centre
  `4 / 2 + 1 × (3 + 2) − 2 / 2 = 6`, reach `e = 4 / 2 + 1 × (3 + 2) = 7`.
- Below, region band: `r0 = 7 + 4 = 11`; `pr = 6 + 2 + 11.640625 + 4 =
  23.640625`; one row, `19.640625` wide, outer edge `30.640625`.
- Below, flow band: starts at `34.640625`; no break label, so the flow row
  is at `f0 = 34.640625`; `K = 1`, apex at `42.640625`; width
  `0 + 8 + 0 + 2 + 11.640625 = 21.640625`; `Eb = 56.28125`.
- `Hc = 54.640625 + 56.28125 + 8 = 118.921875`.

**Horizontal.** The root's row shows its `content`, `Styled score`,
74.080078125 wide, under its `max-width` 120; `b`'s row shows `b`.
`N = 74.080078125`; the largest label candidate is `0 ♩`'s 15.12890625, so
`x0 = 8 + 74.080078125 + 8 = 90.080078125` and `x(t) = x0 + 50 × t`:
`x(0) = 90.080078125`, `x(1) = 140.080078125`, `x(2) = 190.080078125`,
`x(4) = 290.080078125`, `x(8) = 490.080078125`.

**Elements.**

- Map (below): `yc = 54.640625 + 6 = 60.640625`, outline at `59.640625`
  and `61.640625`, from `x(0)` to `x(8)`.
- Brace: arms `Yb = 54.640625 + 11 = 65.640625`, tip `Ya = 71.640625`,
  `Ym = 68.640625`, `k = 3`, `Xm = x(1)`. The label `intro` at `x(1)`,
  baseline `54.640625 + (11 + 6 + 2) + 9.2822265625 = 82.9228515625`.
- Jump (`w = 2`): `yf = 54.640625 + 34.640625 = 89.28125` → `89.2812` (a
  tie, rounded to the even multiple); `ya = 97.28125`.
  - `q = (90.080078125 − 490.080078125) / 4 = −100`;
    `C1 = (390.080078125, yc)`, `C2 = (190.080078125, yc)`;
  - `yc = 89.28125 + 10.666666666666666 = 99.94791666666667`;
  - `Xt − Cx = −100`, `yf − yc = −10.666666666666671`,
    `ℓ = 100.56727985670975`, `ux = −0.9943592005519288`,
    `uy = −0.10606498139220578`;
  - `Bh = (Xt − 8 × ux, yf − 8 × uy) = (98.03495172941543,
    90.12976985113765)`;
  - `Bh − 4 × n = (97.6106918038466, 94.10720665334537)`,
    `Bh + 4 × n = (98.45921165498424, 86.15233304892993)`;
  - the label `D.C.` at `x(4)`, baseline
    `54.640625 + (42.640625 + 2) + 9.2822265625 = 108.5634765625`.
- Root at `54.640625`, `w = 4`: circle `r = 4`, arrowhead tip
  `x(8) + 12 = 502.080078125`, base ordinates `54.640625 ∓ 6`.
- `b` at `54.640625 − 39.640625 = 15`, from `x(4)` to the line end
  `x(8) − 4.5 = 485.580078125`, its diamond as for any locked child.
- Wedges (above): tip `54.640625 − 2 = 52.640625`, base
  `54.640625 − 15 = 39.640625`; the labels' tier starts `2 + 13 + 2 = 17`
  out, at `37.640625`, baseline `37.640625 − 2.3583984375 = 35.2822265625`.
- Names, top row down: `b` at `15 + 3.80810546875 = 18.80810546875`;
  `Styled score` at `54.640625 + 4.154296875 = 58.794921875`.

**Box.** The largest right edge is the arrow tip `502.080078125` (the label
`8 ♩` reaches `497.208984375`, `b`'s diamond `494.580078125`);
`W = 510.080078125`, `H = 118.921875`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="542.0801" height="150.9219" viewBox="0 0 542.0801 150.9219" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate(16 16)">
<rect x="0" y="0" width="510.0801" height="118.9219" rx="4" fill="#F3F4F6"/>
<polygon data-address="ticks" points="90.0801,59.6406 490.0801,59.6406 490.0801,61.6406 90.0801,61.6406" fill="none" stroke="#7C3AED" stroke-width="1.5" stroke-dasharray="4 2"/>
<path data-address="intro" d="M90.0801 65.6406Q90.0801 68.6406 93.0801 68.6406L137.0801 68.6406Q140.0801 68.6406 140.0801 71.6406Q140.0801 68.6406 143.0801 68.6406L187.0801 68.6406Q190.0801 68.6406 190.0801 65.6406" fill="none" stroke="#0F766E" stroke-width="1"/>
<path data-address="da-capo" d="M490.0801 89.2812C390.0801 99.9479 190.0801 99.9479 98.035 90.1298" fill="none" stroke="#DB2777" stroke-width="2"/>
<polygon data-address="da-capo" points="90.0801,89.2812 97.6107,94.1072 98.4592,86.1523" fill="#DB2777"/>
<line data-address="score" x1="90.0801" y1="54.6406" x2="490.0801" y2="54.6406" stroke="#1D4ED8" stroke-width="4" opacity="0.8"/>
<circle data-address="score" cx="90.0801" cy="54.6406" r="4" fill="#1D4ED8" opacity="0.8"/>
<polygon data-address="score" points="502.0801,54.6406 490.0801,48.6406 490.0801,60.6406" fill="#1D4ED8" opacity="0.8"/>
<line data-address="b" x1="290.0801" y1="15" x2="485.5801" y2="15" stroke="#EA580C" stroke-width="3"/>
<circle data-address="b" cx="290.0801" cy="15" r="3" fill="#EA580C"/>
<polygon data-address="b" points="485.5801,15 490.0801,11.4 494.5801,15 490.0801,18.6" fill="none" stroke="#EA580C" stroke-width="1.5"/>
<polygon data-address="score/start" points="90.0801,52.6406 87.0801,39.6406 93.0801,39.6406" fill="#65A30D"/>
<polygon data-address="score/end" points="490.0801,52.6406 487.0801,39.6406 493.0801,39.6406" fill="#B45309"/>
<text data-address="b/name" x="8" y="18.8081" text-anchor="start" font-size="11" fill="#0369A1">b</text>
<text data-address="score/name" x="8" y="58.7949" text-anchor="start" font-size="12" fill="#111827">Styled score</text>
<text data-address="score/start/label" x="90.0801" y="35.2822" text-anchor="middle" font-size="10" fill="#4D7C0F">0 ♩</text>
<text data-address="score/end/label" x="490.0801" y="35.2822" text-anchor="middle" font-size="10" fill="#A16207">8 ♩</text>
<text data-address="intro/label" x="140.0801" y="82.9229" text-anchor="middle" font-size="10" fill="#0E7490">intro</text>
<text data-address="da-capo/label" x="290.0801" y="108.5635" text-anchor="middle" font-size="10" fill="#9D174D">D.C.</text>
</g>
</svg>
```
