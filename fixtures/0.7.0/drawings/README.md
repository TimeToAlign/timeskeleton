# Hand-derived drawings

Twenty-eight of the 70 drawings in this directory are derived by hand from
the [drawing specification](../../../docs/drawing.md) and the font metrics
alone. Their `figure.svg` files are never regenerated: the emitting script
compares each with its writer's output instead. Every other figure in this
directory, and every `figure.tex` and `inputs.json`, is emitted (see
[`fixtures/README.md`](../../README.md)). The key arithmetic of each
hand-derived drawing is given below, so that any implementation can check
where it first parts from the specification: the start and the term that
sets it, the largest right edge `R`, the box `W × H`, and the page.

Section numbers (§) refer to the drawing specification. Every drawing here
is placed alone at `(0, 0)` with the writer's scale `z` = 1, so the page is
`PW = W + 32` by `PH = H + 32` and the drawing lies at `(16, 16)` (§7.1).
An `inputs.json` here supplies an application layer only where the table
names one: the layers are then the defaults, that layer and the manifest's
own `graphical` block (§1), and otherwise the defaults and the manifest's
block. Exact values are given in full; a value as the writer prints it
(§7.3) follows an arrow (`→`).

| Drawing | Manifest | Non-default inputs |
|---|---|---|
| `bare` | `bare.json` | none |
| `nested` | `nested.json` | none |
| `map` | `map.json` | none |
| `flow_control` | `flow_control.json` | none |
| `with_region` | `with_region.json` | none |
| `styled__score` | `styled__score.json` | none (the manifest's own `graphical` block styles it and orders its bands) |
| `nested__length-800-card-spacing-8` | `nested.json` | `length` 800, `places` `{clt_1: {spacing: 8}}` |
| `segment_line` | `segment_line.json` | none |
| `segment_pages_accolades` | `segment_pages_accolades.json` | none |
| `group__group_child_member` | `groups/group_child_member.json` | none |
| `group__group_parents_mixed` | `groups/group_parents_mixed.json` | none |
| `group__group_grandchild` | `groups/group_grandchild.json` | none |
| `unknown_length` | `unknown_length.json` | none |
| `unknown_length_empty` | `unknown_length_empty.json` | none |
| `unknown_length_locked` | `unknown_length_locked.json` | none |
| `unknown_length_child` | `unknown_length_child.json` | none |
| `group__group_unknown_length` | `groups/group_unknown_length.json` | none |
| `unknown_length_segments` | `unknown_length_segments.json` | none |
| `bundle_ungrouped__places` | `bundles/bundle_ungrouped.json` | `places` `{score: {x: -60, y: -150, height: 120}}` |
| `bundle_ungrouped__scale` | `bundles/bundle_ungrouped.json` | `places` `{recording: {scale: 1.5}}` |
| `bundle_ungrouped__spacing` | `bundles/bundle_ungrouped.json` | `spacing` 24, `places` `{score: {spacing: 8}}` |
| `styled_score_flow_inner` | `styled_score_flow_inner.json` | none (the manifest's own `graphical` block styles it and orders its bands) |
| `map_child_band_order` | `map_child_band_order.json` | none |
| `map_root_band_order` | `map_root_band_order.json` | none |
| `joint_rows` | `joint_rows.json` | none |
| `unknown_length_child__regions-shown` | `unknown_length_child.json` | the application layer `[{"select": {"ids": ["movement/regions_1"]}, "set": {"display": "inline"}}]` |
| `unknown_length_segments__regions-shown` | `unknown_length_segments.json` | the application layer `[{"select": {"element": "band", "class": "regions"}, "set": {"display": "inline"}}]` |
| `child_flow_control__flow-shown` | `child_flow_control.json` | the application layer `[{"select": {"ids": ["verse/flow_control_1"]}, "set": {"display": "inline"}}]` |

## Shared quantities

Every manifest is drawn as one box (§8). Twenty-one of these drawings show
one ungrouped root, drawn in its card, four one group, drawn as a frame,
and `bundle_ungrouped__places`, `bundle_ungrouped__scale` and
`bundle_ungrouped__spacing` three ungrouped roots, each in its own card.
Only the manifest of these three has a `name`, so only their box has a
title; no other manifest has a `name` or an
`id`.

Every `data-address` follows §2.2: an element other than a timeline or a
group is addressed through the root whose tree holds it, also in a manifest
of one root (`melody/tempo`, `clt_1/region_1`, `flow:quarters/jump_from_1`,
`score/intro/label`, and `piece/fine`, a flow marker of the child `verse`),
and a manifest's title, wherever one is drawn, is addressed `name`. A band
draws nothing (§2.1), so no element carries a band's address.

- Constants (§6.2): padding `P` = 8 (also above and below a member
  drawing's content), card padding `K` = 8, frame padding `Q` = 8, gap
  after the manifest's title `F` = 8, gap after the names `G'` = 8
  whenever a name is drawn, card shadow offset 2. The spacings take their
  defaults (§8.6) unless the table states one: the box's spacing, the gap
  between its items at their default `y`, is 8; a frame's spacing `Sf`,
  the gap between its cards, is 8; a card's spacing `S`, the gap between
  bands and the `S` of §6.2, is 4, so the row pitch is `p` = max(10 + 4,
  `h(s)`).
- The box has one horizontal layout (§8.2), computed in item coordinates,
  from the item's left edge and before its scale. The name column starts at
  `n = K` = 8 when the box holds no frame and at `n = Q + K` = 16 when it
  holds one. `N` is the widest row name of any member drawing of the box; a
  title is not a row name. The start `s0` is the largest of `n + N + G'`,
  of `n + wj / 2 − Li × uj` for every centred label `j` of every item `i`,
  and of `n + N + G' + 8 × wa` for every ancestor line `a` of the box that
  runs on to the left; each candidate is listed below only when it decides
  or comes close. The right margin `Mr` is the largest of `e − (s0 + Li)`,
  `e` a member drawing's right edge, and an item's right edge is `Ri = s0 +
  Li + Mr` or its group's title's right edge when that is larger.
- Each item, a group's frame or an ungrouped root's card, lies at its place
  (§8.6), whose `x` is `P` = 8 unless `places` states another, and whose
  `scale` is 1 except for `recording` in `bundle_ungrouped__scale`. Only
  two drawings state a spacing: the card spacing `S` = 8 of `clt_1` in
  `nested__length-800-card-spacing-8`, and in `bundle_ungrouped__spacing`
  the box's spacing 24 and the card spacing `S` = 8 of `score`. No
  spacing multiplies another (§8.6): the box's moves its items, a card's
  widens only the gaps inside that card. A
  position `px` in item coordinates is drawn at `x + px` at scale 1 and at
  `x + scale × px` otherwise, and every length of a scaled item (widths,
  heights, radii, stroke widths, dashes, font sizes) is multiplied by its
  scale. In a box of one item `Mr` is that item's own `R − (s0 + L)`, so
  `Ri` is its largest right edge `R`, its group's title included.
- An ungrouped card spans 0 to `Ri + K` in item coordinates; in a frame, a
  card spans `Q` to `Ri + K` and the frame 0 to `Ri + K + Q`. The sections
  of the one-item drawings give every position as drawn at the default
  place, `x` = 8 plus the item-coordinate value: their `xn` is `8 + n`, 16
  in a card and 24 in a frame, and their `x0` is `8 + s0`.
- Every position is computed in place coordinates (§8.4): `Wb` = (`P` plus
  the largest right edge, a card's shadow (`+ 2`) included) − `Xl`, and
  `Hb` = (`P` plus the largest bottom edge, likewise) − `Yt`, with `Xl` the
  smaller of 0 and the smallest left edge minus `P`, and `Yt` the smaller of
  0 and the smallest top minus `Pt`; `Pt` = `P + h(11) + F` = 28.8046875 when
  the manifest's title is displayed and `P` otherwise. The place origin
  `(Ox, Oy)` = (0 − `Xl`, 0 − `Yt`) is added to every position last. Only
  in `bundle_ungrouped__places` does an item reach left of the padding or
  above `Pt`; everywhere else `Xl` = `Yt` = 0 and the origin is (0, 0), so
  `Wb = P` plus the largest right edge and `Hb = P` plus the largest bottom
  edge. No drawing here requests a box size, so `W = Wb` and `H = Hb`.
- Font measures (§5.1) at size 9: `a(9)` = 8.35400390625, `d(9)` =
  2.12255859375, `h(9)` = 10.4765625; at size 11: `a(11)` =
  10.21044921875, `d(11)` = 2.59423828125, `h(11)` = 12.8046875.
  With both wedges below and their labels at `u` = 0 and 1 in one tier,
  the markers band is `w / 2 + 13 + 2 + h(9)` = 26.9765625 wide for a line
  of width `w` = 3 (§6.4), and at level −1, where it starts at `c` = 0, it
  reaches as far below the line; a root whose end is open has only its
  start wedge and label, and its markers band is as wide. Only in
  `map_root_band_order` does another band lie between a root's line and its
  markers band.
- A regions band of one row whose labels have the size 9, or that draws no
  label, is `pr − S` = 18.4765625 wide, `pr` = 6 + 2 + `h(9)` + `S` =
  22.4765625 (§6.2); in `styled__score` and `styled_score_flow_inner` its
  label has the size 10, and `h(10)` = 11.640625 makes it 19.640625 wide. In
  the default band order, beyond a root's markers band of 26.9765625 at
  level −1, it starts at 30.9765625, so the root's below side's outer edge
  is `Eb` = 49.453125 when no band lies beyond it. A regions or flow control
  band at level ±1 of a line of width `w` = 3 that reaches nothing on that
  side starts at `S` beyond `w / 2`, 1.5 + 4 = 5.5, so that its content
  keeps the gap `S` from the line's stroke (§6.4).
- A map stack of one map on a line of width `w` = 3 holds the map centred
  `w / 2 + (g + d) − d / 2` = 1.5 + 5 − 1 = 5.5 from the line, its outline
  from 4.5 to 6.5 from it, and reaches `e` = 1.5 + 5 = 6.5 (§6.4). As the
  only band above a root's line, the conversion maps band puts the line at
  `y_root` = max(`P` + 6.5, `P` + `h(11) / 2`) = `P` + 6.5 = 14.5,
  since 6.5 exceeds `h(11) / 2` = 6.40234375 (§6.5); with the markers band
  below of 26.9765625, `Hm` = 14.5 + 26.9765625 + 8 = 49.4765625. Both
  bands start at `c` = 0, against the line, so no gap between bands and no
  card spacing enters this height.
- A root of unknown length is scaled to its reach `λ` (§3.2, §3.4). A child
  of unknown length is drawn on its root's axis and ends, open, at its
  start plus its own reach (rule 5 of §3.4), with its three chevrons beyond
  that end as a root has; a segment of unknown length ends by rules 3 and 4.
  A root's open end lies at `Xe = x0 + L`; its line runs on to `Xr = Xe +
  4w` and the outer of its three chevrons has its tip, and the right edge,
  at `Xr + 5.5w`, `Xr` computed first (§6.6, §6.7): `(x0 + L + 12) + 16.5`
  for `w` = 3, 28.5 past `Xe`.

## `bare`

The root `bare` ("Bare", 8 quarters), with nothing else.

- `N` = w(`Bare`, 11) = 25.5771484375.
- `x0` = `xn + N + G'` = 16 + 25.5771484375 + 8 = 49.5771484375 → 49.5771;
  the start label `0 ♩` gives only 16 + 6.416015625 − 0 = 22.416015625.
- `R` = the arrowhead tip `Xe + 3w` = 449.5771484375 + 9 = 458.5771484375.
- `Hm` = 14.40234375 + 26.9765625 + 8 = 49.37890625.
- `W` = 8 + (10 + 458.5771484375) = 476.5771484375; `H` = 8 + (10 +
  49.37890625) = 67.37890625.
- Page 508.5771484375 × 99.37890625 → **508.5771 × 99.3789**.

## `nested`

The root `clt_1` (16 quarters), its locked child `clt_3` (8 at 4), and
that child's locked child `clt_2` (2 at 3/2). No timeline has a name, so
each row shows its ID.

- `N` = w(`clt_1`, 11) = 25.91552734375, the same for all three.
- `x0` = 16 + 25.91552734375 + 8 = 49.91552734375 → 49.9155.
- `R` = the end label `16 ♩` at 449.91552734375 + 9.279052734375 =
  459.194580078125.
- `Hm` = 43 + 26.9765625 + 8 = 77.9765625.
- `W` = 8 + 469.194580078125 = 477.194580078125; `H` = 8 + 87.9765625 =
  95.9765625.
- Page 509.194580078125 × 127.9765625 → **509.1946 × 127.9766**.

## `map`

The root `melody` ("Melody", 8 quarters) with the map `tempo` and the child
`phrase` ("Phrase", 4 at 2) with the map `ticks`, addressed `melody/tempo`
and `melody/ticks`.

- `N` = max(w(`Melody`, 11), w(`Phrase`, 11)) = max(39.53662109375,
  37.36669921875) = 39.53662109375.
- `x0` = 16 + 39.53662109375 + 8 = 63.53662109375 → 63.5366.
- `R` = the arrowhead tip 463.53662109375 + 9 = 472.53662109375.
- `Hm` = 32.5 + 26.9765625 + 8 = 67.4765625.
- `W` = 8 + 482.53662109375 = 490.53662109375; `H` = 8 + 77.4765625 =
  85.4765625.
- Page 522.53662109375 × 117.4765625 → **522.5366 × 117.4766**.

## `flow_control`

The root `flow:quarters` ("Flow control", 16 quarters) with the jump
targets `jump_to_1` (repeat start) at 2 and `jump_to_2` (segno) at 4, which
draw nothing, the jump origin `jump_from_1` ("Repeat") from 8 to `jump_to_1`, the
flow marker `flow_marker_1` ("Fine") at 12 and the jump origin `jump_from_2` ("D.S.")
from 16 to `jump_to_2`. Above the line no band is present; below it lie the
markers band at level −1 and the flow control band at level −2 (its
regions band is absent).

- `N` = w(`Flow control`, 11) = 66.9775390625.
- `x0` = 16 + 66.9775390625 + 8 = 90.9775390625 → 90.9775; the jump-origin
  labels, `Repeat` (32.08447265625 wide) centred on the midpoint 5 (`u` =
  5/16) and `D.S.` (18.36474609375 wide) on the midpoint 10 (`u` = 10/16),
  give only −92.957763671875 and −224.817626953125.
- `R` = the end label `16 ♩` at 490.9775390625 + 18.55810546875 / 2 =
  500.256591796875, beyond the arrowhead tip 499.9775390625; the arc of
  `jump_from_2` reaches no further right than its from `x(16)` = 490.9775390625,
  and the label `Fine` ends at `x(12)` + 3 + 18.91845703125 =
  412.89599609375.
- Above: no band, so `Ea` = 0 and `y_root` = max(8 + 0, 8 + 6.40234375) =
  14.40234375.
- Below: the markers band of 26.9765625 (Shared quantities); the flow
  control band from 26.9765625 + 4 = 30.9765625. The label `Fine` fills one
  flow-marker label tier, `T` = 1, so the flow row lies at `f0` =
  30.9765625 + 10.4765625 = 41.453125. The jump origins, sorted by span,
  are `jump_from_1` (span 6) and `jump_from_2` (span 12). `jump_from_1`'s extent is [50,
  200], its label's [107.957763671875, 142.042236328125] inside it: row 1.
  `jump_from_2`'s is [100, 400] and conflicts with it: row 2. With `pj` = 6 + 4
  + 10.4765625 = 20.4765625 the apexes lie at 41.453125 + 8 = 49.453125
  and 49.453125 + 20.4765625 = 69.9296875. The band is 10.4765625 + 8 +
  20.4765625 + 2 + 10.4765625 = 51.4296875 wide, so `Eb` = 82.40625.
- `Hm` = 14.40234375 + 82.40625 + 8 = 104.80859375 → 104.8086.
- Drawn, each ordinate the card's top 8 plus its item-coordinate value: the
  line at 22.40234375 → 22.4023 and the flow row at 63.85546875 →
  63.8555.
- The flow marker at `x(12)` = 390.9775390625 → 390.9775, from the flow row
  to `P`, drawn at 16; its label from 393.9775390625 → 393.9775 with its
  baseline at 63.85546875 − 2.12255859375 = 61.73291015625 → 61.7329.
- `jump_from_1` from `Xf` = `x(8)` = 290.9775390625 to `Xt` = `x(2)` =
  140.9775390625 (§6.6), in item coordinates: `q` = −37.5, `yc` =
  55.85546875 + 4/3 × 8 = 66.52213541666667, `C1` = (253.4775390625,
  `yc`), `C2` = (178.4775390625, `yc`); `ℓ` = 38.98753362009166, `(ux, uy)`
  = (−0.9618459163232351, −0.2735917273097203), `Bh` =
  (144.82492272779294, 56.94983565923888). Drawn: `yc` 74.5221, `Bh`
  (144.8249, 64.9498), the head's corners (144.2777, 66.8735) and
  (145.3721, 63.0261), its label centred on `x(5)` = 215.9775390625 with
  its baseline at 8 + ((14.40234375 + (49.453125 + 2)) + 8.35400390625) =
  82.20947265625 → 82.2095.
- `jump_from_2` from `Xf` = `x(16)` = 490.9775390625 to `Xt` = `x(4)` =
  190.9775390625: `q` = −75, `ya` = 14.40234375 + 69.9296875 =
  84.33203125, `yc` = 55.85546875 + 4/3 × 28.4765625 = 93.82421875, `C1` =
  (415.9775390625, `yc`), `C2` = (265.9775390625, `yc`); `ℓ` =
  84.06322606563764, `(ux, uy)` = (−0.8921856025539521,
  −0.4516689612929382), `Bh` = (194.5462814727158, 57.66214459517175).
  Drawn: `yc` 101.82421875 → 101.8242, `Bh` (194.5463, 65.6621), the
  head's corners (193.6429, 67.4465) and (195.4496, 63.8778), its label
  centred on `x(10)` = 340.9775390625 with its baseline at 8 +
  ((14.40234375 + (69.9296875 + 2)) + 8.35400390625) = 102.68603515625 →
  102.686.
- `W` = 8 + 510.256591796875 = 518.256591796875; `H` = 8 + (10 +
  104.80859375) = 122.80859375.
- Page 550.256591796875 × 154.80859375 → **550.2566 × 154.8086**.

## `with_region`

The root `clt_1` (12 quarters) with two children and the region `theme`
(2 to 6).

- `N` = 25.91552734375 (`clt_1`, `clt_2`, `clt_3` alike).
- `x0` = 16 + 25.91552734375 + 8 = 49.91552734375 → 49.9155.
- `R` = the end label `12 ♩` at 459.194580078125.
- `Hm` = 43 + 49.453125 + 8 = 100.453125.
- `W` = 8 + (10 + 459.194580078125) = 477.194580078125; `H` = 8 + (10 +
  100.453125) = 118.453125.
- Page 509.194580078125 × 150.453125 → **509.1946 × 150.4531**.

## `styled__score`

The root `score` (8 quarters) with the children `a` (hidden) and `b`, the
map `ticks`, the region `intro` and the jump origin `da-capo`, styled by its
own statements: the root's line is 4 wide and its name, at size 12, reads
`Styled score`. Its band order `score/children_1`, `score/markers_1`,
`score`, `score/conversion_maps_1`, `score/regions_1`,
`score/flow_control_1` (§6.4) lays the markers band against the line above
it and the children band beyond, and below it the conversion maps band, then
the regions band and the flow control band.

- `N` = max(w(`Styled score`, 12), w(`b`, 11)) = max(74.080078125,
  6.982421875) = 74.080078125.
- `x0` = 16 + 74.080078125 + 8 = 98.080078125 → 98.0801.
- `R` = the arrowhead tip `Xe + 3w` = 498.080078125 + 12 = 510.080078125.
- `Hm` = 54.640625 + 56.28125 + 8 = 118.921875.
- `W` = 8 + 520.080078125 = 528.080078125; `H` = 8 + 128.921875 =
  136.921875.
- Page 560.080078125 × 168.921875 → **560.0801 × 168.9219**.

## `nested__length-800-card-spacing-8`

`nested` with `L` = 800 and the card spacing `S` = 8 of its one card,
`places` `{clt_1: {spacing: 8}}` (§8.6). `S` is the gap between bands and
enters the row pitch, `p` = `p0` = max(10 + 8, `h(11)`) = 18 (§6.2); the
padding `P` = 8 above and below the content does not change with it
(§6.5), and neither does the horizontal layout.

- `x0` = 16 + 25.91552734375 + 8 = 49.91552734375 → 49.9155, as in
  `nested`.
- `R` = the end label `16 ♩` at 49.91552734375 + 800 + 9.279052734375 =
  859.194580078125.
- The children bands of `clt_1` and of `clt_3` lie above their lines,
  which reach nothing there, so each starts at the larger of `S` beyond
  `w / 2`, 1.5 + 8 = 9.5, and `p / 2` = 9: 9.5 (§6.4, Where a band lies).
  At `S` = 4 the half pitch, 7, was the larger.
- The row of `clt_2` has the halves 9 and 9, so `clt_2`'s line lies 9.5 +
  9 = 18.5 above `clt_3`'s, and `clt_3`'s band is 18 wide: `clt_3`'s
  above edge is 9.5 + 18 = 27.5, and its below edge 0. The row of `clt_3`
  has the inner half max(9, 0) = 9 and the outer half max(9, 27.5) =
  27.5, so `clt_3`'s line lies 9.5 + 9 = 18.5 above `clt_1`'s, the band
  is 9 + 27.5 = 36.5 wide, and `Ea` = 9.5 + 36.5 = 46.
- `y_root` = max(8 + 46, 8 + 6.40234375) = 54. Below, the markers band
  lies against the line from `c` = 0 and reaches `Eb` = 26.9765625
  (Shared quantities), whatever `S`. `Hm` = 54 + 26.9765625 + 8 =
  88.9765625 → 88.9766.
- Drawn, each line at the card's top 8 plus its ordinate: `clt_1` at 62,
  `clt_3` at 62 − 18.5 = 43.5 and `clt_2` at 43.5 − 18.5 = 25; the names'
  baselines at each line's ordinate plus (`a(11)` − `d(11)`) / 2 =
  3.80810546875, 65.80810546875 → 65.8081, 47.30810546875 → 47.3081 and
  28.80810546875 → 28.8081; the diamonds' corners `1.2w` = 3.6 above and
  below their lines, from 39.9 to 47.1 (`clt_3`) and from 21.4 to 28.6
  (`clt_2`); the wedges from 63.5 to 76.5, and their labels' baseline at
  (62 + 16.5) + `a(9)` = 86.85400390625 → 86.854.
- `W` = 8 + 869.194580078125 = 877.194580078125; `H` = 8 + (10 +
  88.9765625) = 106.9765625.
- Page 909.194580078125 × 138.9765625 → **909.1946 × 138.9766**.

## `segment_line`

The nested segment line `form` ("Form", 32 quarters) of the segments `a`
(8), `b` (12) and `c` (12), each a segment line itself; `b` holds `b1` and
`b2` (6 each).

- `N` = w(`Form`, 11) = 28.294921875.
- `x0` = 16 + 28.294921875 + 8 = 52.294921875 → 52.2949; the segment
  labels give at most `A` −30.921630859375 and the start label
  22.416015625.
- `R` = the end label `32 ♩` at 461.573974609375, beyond the arrowhead tip
  461.294921875.
- `Hm` = 60.953125 + 26.9765625 + 8 = 95.9296875.
- `W` = 8 + ((8 + 2) + 461.573974609375) = 479.573974609375; `H` = 8 +
  105.9296875 = 113.9296875.
- Page 511.573974609375 × 145.9296875 → **511.574 × 145.9297**.

## `segment_pages_accolades`

The unlocked segment line `pages` ("Pages", 7016 pixels) of four pages of
1754 pixels, each a segment line of four accolades of 400, 450, 452 and 452
pixels. A row of segment lines has no name, so `Pages` is the only one.

- `N` = w(`Pages`, 11) = 32.85498046875.
- `x0` = 16 + 32.85498046875 + 8 = 56.85498046875 → 56.855; the label of
  the first accolade, `u` = 200 / 7016, gives only 7.460528557493586.
- `R` = the end label `7016 px` at 456.85498046875 + 18.402099609375 =
  475.257080078125.
- `Hm` = 60.953125 + 26.9765625 + 8 = 95.9296875.
- `W` = 8 + 485.257080078125 = 493.257080078125; `H` = 8 + 105.9296875 =
  113.9296875.
- Page 525.257080078125 × 145.9296875 → **525.2571 × 145.9297**.

## `group__group_child_member`

The group "Second half" in the display order `second-half`, `recording`:
the child `second-half` (8 quarters at 8) of the piece `piece` (16
quarters), and the root `recording` (10.0 seconds). The member
`second-half` carries the ancestor line of `piece`, which runs on to the
left.

- `xn` = 24 (a frame). `N` = w(`Second half`, 11) = 64.61962890625, of
  `Second half`, `Piece` and `Recording`.
- `x0` = the chevron term `xn + N + G' + 8 × wa` = 24 + 64.61962890625 + 8
  + 24 = 120.61962890625 → 120.6196, above `xn + N + G'` =
  96.61962890625; the outer chevron's tip `x0 − 8w` lies exactly at the
  latter.
- `R` = the end label `10.0 s` at 520.61962890625 + 13.79443359375 =
  534.4140625.
- `Hm` = 83.953125 (`second-half`, its ancestor band above) and
  49.37890625 (`recording`); the frame is 8 + 12.8046875 + 4 + 83.953125
  + 8 + 49.37890625 + 8 = 174.13671875 high.
- `W` = 8 + (534.4140625 + 8 + 8) = 558.4140625; `H` = 8 + (8 +
  174.13671875) = 190.13671875.
- Page 590.4140625 × 222.13671875 → **590.4141 × 222.1367**.

## `group__group_parents_mixed`

The group "Exposition" in the display order `exposition`, `take`,
`system`, `audio`: three child members of different parents (the
exposition, 32 quarters at 16 in the locked sonata of 48; the take, 25.5
seconds at 30.0 in the session of 90.0 seconds; the system, 600 pixels at 0
in the page of 1754) and the root `audio` (1323000 samples). `take` holds
the map `cmap_1` (`SecondsToSamples`) and `audio` the map `cmap_1`
(`SamplesToSeconds`), addressed through the roots whose trees hold them,
`session/cmap_1` and `audio/cmap_1` (§2.2), although `session` is drawn
only as an ancestor line. Both maps lie above their lines and take the
colour of the physical domain they convert to, the first dotted `1 1`
(samples are discrete), the second solid (§4).

- `xn` = 24. `N` = w(`Exposition`, 11) = 57.0302734375.
- `x0` = the chevron term 24 + 57.0302734375 + 8 + 24 = 113.0302734375 →
  113.0303, set by the ancestor lines of `sonata` and `session`, which run
  on to the left; `page` starts with its member and does not.
- `R` = the end label `1323000 smp` at 513.0302734375 + 31.05615234375 =
  544.08642578125. Each map spans its member's line, from `x0` to `x0 + L`
  = 513.0302734375, and reaches no further right.
- The map stacks: each holds one map, 5.5 above its member's line and
  reaching `e` = 6.5 (Shared quantities). Neither member draws a wedge
  above, so above lies its conversion maps band alone, reaching 6.5; below,
  every member's markers band reaches 26.9765625.
- `audio` has no other band above: `Ea` = 6.5, so `y_root` = 14.5 and `Hm`
  = 49.4765625 (Shared quantities).
- `take` meets its ancestor band (§8.3) beyond the map: the band starts at
  the larger of `p0 / 2` = 7 and the outer edge of the above side plus `S`,
  6.5 + 4 = 10.5. The row of `session` has the inner half 7 and the outer half
  26.9765625 (its marks and their labels in one tier), so the line of
  `session` lies 10.5 + 7 = 17.5 above `take`'s and `Ea` = 10.5 +
  33.9765625 = 44.4765625; `y_root` = 52.4765625 and `Hm` = 52.4765625 +
  26.9765625 + 8 = 87.453125. `exposition` and `system` have no map: their
  ancestor bands start at 7, their ancestor lines lie 14 above their own,
  and `Hm` = 48.9765625 + 26.9765625 + 8 = 83.953125. Every ancestor line so
  lies 34.9765625 below its card's top, and the map of `take` lies between
  `take`'s line and that of `session`, which stand 17.5 apart instead of 14.
- The frame's rows (§8.4): the cards start at 8 + (8 + 12.8046875 + 4) =
  32.8046875 → 32.8047 (`exposition`) and each the frame's spacing `Sf` =
  8 below the one before, at 124.7578125 → 124.7578 (`take`), 220.2109375
  → 220.2109 (`system`) and
  312.1640625 → 312.1641 (`audio`); the frame is 8 + 12.8046875 + 4 +
  83.953125 + 8 + 87.453125 + 8 + 83.953125 + 8 + 49.4765625 + 8 =
  361.640625 → 361.6406 high.
- Drawn, each line at its card's top plus `y_root`: `take` at 177.234375 →
  177.2344, its map's outline from 170.734375 → 170.7344 to 172.734375 →
  172.7344 and the line of `session` at 159.734375 → 159.7344; `audio` at
  326.6640625 → 326.6641, its map's outline from 320.1640625 → 320.1641 to
  322.1640625 → 322.1641.
- `W` = 8 + 560.08642578125 = 568.08642578125; `H` = 8 + 369.640625 =
  377.640625.
- Page 600.08642578125 × 409.640625 → **600.0864 × 409.6406**.

## `group__group_grandchild`

The group "Theme" in the display order `theme`, `recording`: the grandchild
`theme` (8 quarters at 8 in the movement of 16 quarters at 16 in the score
of 64) and the root `recording` (12.0 seconds). `theme` carries two
ancestor lines, `movement` and `score`, both running on to the left.

- `xn` = 24. `N` = w(`Recording`, 11) = 55.70361328125, of `Theme`,
  `Score`, `Movement` and `Recording`.
- `x0` = the chevron term 24 + 55.70361328125 + 8 + 24 = 111.70361328125 →
  111.7036.
- `R` = the outer chevron tip of `score`, which also runs on to the right,
  `Xr + 4w` = (111.70361328125 + 400 + 12) + 12 = 535.70361328125 (§8.3).
- `Hm` = 82.953125 + 26.9765625 + 8 = 117.9296875 (`theme`, two ancestor
  rows above) and 49.37890625 (`recording`); the frame is 208.11328125
  high.
- `W` = 8 + 551.70361328125 = 559.70361328125; `H` = 8 + 216.11328125 =
  224.11328125.
- Page 591.70361328125 × 256.11328125 → **591.7036 × 256.1133**.

## `unknown_length`

The root `score` (quarters, length `null`) with the region `region_1` (2
to 8), the jump target `jump_to_1` at 6 and the locked child `coda` (4 at 10).
No timeline has a name.

- The reach is the end of `coda`, 10 + 4 = 14, beyond the region's end 8 and
  the jump target 6, so `λ` = 14 and `u(t)` = `t / 14`, rounded once: `x(2)`
  = 110.94168526785714 → 110.9417, `x(10)` = 339.5131138392857 → 339.5131.
  `coda` ends at 14, known, in its diamond at `x0 + L`.
- `N` = w(`score`, 11) = 29.798828125.
- `x0` = 16 + 29.798828125 + 8 = 53.798828125 → 53.7988; the start label
  `0 ♩` gives only 22.416015625.
- `R` = the outer chevron tip `Xr + 5.5w` = 465.798828125 + 16.5 =
  482.298828125. The root has no end wedge and no end label.
- `Hm` = 29 + 49.453125 + 8 = 86.453125: `coda` in the children band above
  (`Ea` = 21), the start wedge in the markers band below and the region in
  the regions band beyond it.
- `W` = 8 + (10 + 482.298828125) = 500.298828125; `H` = 8 + (10 +
  86.453125) = 104.453125.
- Page 532.298828125 × 136.453125 → **532.2988 × 136.4531**.

## `unknown_length_empty`

The root `score` (quarters, length `null`) with no content.

- The reach is 0, so every `u` is 0 (§3.2), and the line is still drawn
  `L` long, from `x0` to `Xe = x0 + L` (§3.4).
- `N` = 29.798828125; `x0` = 53.798828125 → 53.7988.
- `R` = the outer chevron tip 482.298828125.
- `Hm` = 14.40234375 + 26.9765625 + 8 = 49.37890625: nothing above, so
  `y_root` = `P + h(11) / 2`.
- `W` = 500.298828125; `H` = 8 + (10 + 49.37890625) = 67.37890625.
- Page 532.298828125 × 99.37890625 → **532.2988 × 99.3789**.

## `unknown_length_locked`

The locked root `score` (quarters, length `null`) with the locked child
`coda` (4 at 12).

- The reach is 12 + 4 = 16 = `λ`; `x(12)` = 353.798828125. The root's end
  is open, and the three chevrons come before the end circle of a locked
  root in §6.6, so the root ends in the chevrons; `coda` ends in its diamond
  at `x0 + L`.
- `N` = 29.798828125; `x0` = 53.798828125 → 53.7988.
- `R` = the outer chevron tip 482.298828125.
- `Hm` = 29 + 26.9765625 + 8 = 63.9765625.
- `W` = 500.298828125; `H` = 8 + (10 + 63.9765625) = 81.9765625.
- Page 532.298828125 × 113.9765625 → **532.2988 × 113.9766**.

## `unknown_length_child`

The root `score` (32 quarters) and its locked child `movement` at 8, of
length `null`, holding the region `region_1` (0 to 6). No timeline has a
name. The defaults hide the regions band of every timeline held by a band
(§4), so `movement`'s regions band and its region are not drawn. `score`
holds no region, so its own regions band is absent.

- `λ` = 32, the root's length. The reach of `movement` on its own axis is
  6, the end of its region, which counts although it is not displayed
  (§3.4). So `movement` ends under rule 5 of §3.4 at 8 + 6 = 14, open:
  `Xs` = `x(8)` = 183.490234375 → 183.4902, `Xe` = `x(14)` =
  258.490234375, `Xr` = 270.490234375 → 270.4902, and the outer chevron's
  tip lies at 286.990234375 → 286.9902. Its first-fit extent runs from 100
  on `9.5w` past its end, to 175 + 28.5 = 203.5.
- `N` = w(`movement`, 11) = 59.490234375, wider than `score`
  (29.798828125).
- `x0` = 16 + 59.490234375 + 8 = 83.490234375 → 83.4902. The start label
  `0 ♩` gives only 16 + 6.416015625 = 22.416015625.
- `R` = the end label `32 ♩` at 483.490234375 + 9.279052734375 =
  492.769287109375, beyond the arrowhead tip 492.490234375.
- Above, the children band alone. `score`'s line reaches nothing there, so
  the band's own start is the larger of 1.5 + 4 = 5.5 and `p0 / 2` = 7: 7.
  `movement` draws no band, so its row's halves are both 7: its line lies
  14 above `score`'s, and `Ea` = 7 + 14 = 21. So `y_root` = 8 + 21 = 29.
  Below, the markers band alone: `Eb` = 26.9765625 (Shared quantities).
- `Hm` = 29 + 26.9765625 + 8 = 63.9765625 → 63.9766. Drawn, `score`'s line
  lies at 37 and `movement`'s at 23.
- `W` = 8 + (10 + 492.769287109375) = 510.769287109375; `H` = 8 + (10 +
  63.9765625) = 81.9765625.
- Page 542.769287109375 × 113.9765625 → **542.7693 × 113.9766**.

## `group__group_unknown_length`

The group "Edition" in the display order `performance`, `score`: the root
`performance` (seconds, length `null`) with the region `region_1` (0.0 to
9.5), and the root `score` (12 quarters).

- `performance` is scaled to its reach 9.5, a float: `u(9.5)` = 1.0, so the
  region spans `x0` to `x0 + L`, and its tip lies at the midpoint (0.0 +
  9.5) / 2 = 4.75, `u` = 0.5, `x` = 302.640625 (§3.1). Its start label is
  `0.0 s`.
- `xn` = 24. `N` = w(`performance`, 11) = 70.640625.
- `x0` = 24 + 70.640625 + 8 = 102.640625 → 102.6406; the start label
  `0.0 s` gives only 34.931396484375.
- `R` = the outer chevron tip of `performance`, `Xr + 5.5w` = (102.640625 +
  400 + 12) + 16.5 = 531.140625, beyond the end label `12 ♩` of `score` at
  511.919677734375.
- `Hm` = 71.85546875 (`performance`, its regions band below) and
  49.37890625 (`score`); the frame is 8 + 12.8046875 + 4 + 71.85546875 + 8
  + 49.37890625 + 8 = 162.0390625 high.
- `W` = 8 + (531.140625 + 8 + 8) = 555.140625; `H` = 8 + (8 +
  162.0390625) = 178.0390625.
- Page 587.140625 × 210.0390625 → **587.1406 × 210.0391**.

## `unknown_length_segments`

The unlocked segment line `form` (quarters, length `null`) of three
segments, none a segment line and none named: `a` at 0, of length `null`,
holding the region `region_1` (0 to 4); `b` (6 at 8); `c` at 14, of length
`null`, holding the region `region_2` (0 to 3). The segments lie in
`form`'s children band, so the defaults hide their regions bands (§4) and
neither region is drawn; `form`'s own regions band holds nothing and is
absent (§6.4).

- The reach is the largest of 0 + 4, 8 + 6 and 14 + 3, so `λ` = 17; the
  hidden regions count all the same (§3.4). `a` ends where `b` starts
  (rule 3 of §3.4), and `c` where `form` ends (rule 4), open. The three
  chevrons come before the open arrowhead of a segment line in §6.6.
- The boundaries of `b` and `c` lie at `x(8)` = 238.07562614889704 →
  238.0756 and `x(14)` = 379.2520967371323 → 379.2521, and reach `k` = 8
  to both sides. No band is present above: the children band holds only
  segments without a line and draws nothing, and there is no map. The
  above side's outer edge is therefore the line's reach, `Ea` = 8, and
  `y_root` = 8 + 8 = 16 in the member drawing. No segment has a label.
- Below, the markers band lies against the line at level −1, the start
  wedge and its label `0 ♩` in one tier, 26.9765625 wide and beyond the
  boundaries' 8: `Eb` = 26.9765625.
- `N` = w(`form`, 11) = 25.84033203125.
- `x0` = 16 + 25.84033203125 + 8 = 49.84033203125 → 49.8403; the start
  label `0 ♩` gives only 22.416015625.
- `R` = the outer chevron tip 478.34033203125.
- `Hm` = 16 + 26.9765625 + 8 = 50.9765625.
- `W` = 8 + (10 + 478.34033203125) = 496.34033203125; `H` = 8 + (10 +
  50.9765625) = 68.9765625.
- Page 528.34033203125 × 100.9765625 → **528.3403 × 100.9766**.

## `bundle_ungrouped__places`

The box "Sketches" of three ungrouped roots, in drawing order the segment
line `pages` ("Pages", 5262 pixels, the segments `Page 1` to `Page 3` of
1754 each, none a segment line and none with a map) with the map `cmap_1` to
points, the root `recording` ("Recording", 441000 samples) with the map
`cmap_1` to seconds, and the root `score` ("Score", 16 quarters) with the
map `cmap_1` to ticks, the flow marker `flow_marker_1` ("Fine") at 8 and the jump
origin `jump_from_1` ("D.C. al Fine") from 16 to 0. The place of `score` is
stated as `{x: -60, y: -150, height: 120}`, left of the padding and above
the title's slot. The three cards share one horizontal layout (§8.2), so
they are equally wide; every place not stated takes its default (§8.6).
Every position below is in item coordinates until it is drawn at its place,
and in place coordinates until the place origin is added, last (§8.4).

- The layout, in item coordinates: `n` = `K` = 8 (no frame); `N` =
  w(`Recording`, 11) = 55.70361328125, of `Pages` (32.85498046875),
  `Recording` and `Score` (31.05029296875); `s0` = `n + N + G'` = 8 +
  55.70361328125 + 8 = 71.70361328125, above the largest label term, the
  start label `0 smp` of `recording`, 8 + 13.8779296875 − 0 =
  21.8779296875; the jump-origin label `D.C. al Fine`, centred on `u` = 1/2,
  gives only 8 + 25.7958984375 − 200 = −166.2041015625. The shared end is
  `s0 + L` = 471.70361328125.
- The right margin: the right edges are the end labels `5262 px` at
  471.70361328125 + 18.402099609375 = 490.105712890625 (`pages`), `441000
  smp` at 471.70361328125 + 28.193115234375 = 499.896728515625 (`recording`)
  and `16 ♩` at 471.70361328125 + 9.279052734375 = 480.982666015625
  (`score`), so `Mr` = 499.896728515625 − 471.70361328125 = 28.193115234375,
  from `recording`, and `Ri` = 471.70361328125 + 28.193115234375 =
  499.896728515625 for every card. The maps end at the shared end, the jump
  origin at its start `x(16)` = 471.70361328125, and the flow-marker label
  `Fine` at 274.70361328125 + 18.91845703125 = 293.6220703125. Each card
  spans 0 to `Ri + K` = 507.896728515625.
- The map stacks: each root's one map lies above its line (§4), 5.5 above
  it, its outline from 6.5 to 4.5 above it and from `s0` to `s0 + L`, and
  the stack reaches `e` = 6.5 (Shared quantities). Each map takes the
  colour and pattern of its `target_unit` (§2.1, §4): solid red to points
  on `pages`, solid blue to seconds on `recording`, green dashed `1 1` to
  ticks on `score`.
- Heights: on `pages`, a segment line with drawn boundaries, the stack lies
  within the boundaries' `k`: its line reaches above max(`e`, `k`) =
  max(6.5, 8) = 8, plus 2 + `h(9)` for its one tier of segment labels
  (§6.4), so the map changes nothing of it: `y_root` = 8 + (8 + 2 +
  10.4765625) = 28.4765625, its segment labels' baseline 28.4765625 − (8 +
  2) − `d(9)` = 16.35400390625, and `Hm` = 28.4765625 + 26.9765625 + 8 =
  63.453125. `recording` and `score` have their conversion maps band as
  their only band above, `Ea` = 6.5, so `y_root` = 14.5 (Shared
  quantities); `recording` has `Hm` = 49.4765625 → 49.4766.
- The flow control band of `score` (§6.4) lies below at level −2, beyond its
  markers band of 26.9765625 (its regions band is absent), from 26.9765625 +
  4 = 30.9765625. The label `Fine` fills one flow-marker label tier, `T` =
  1, so the flow row lies at `f0` = 30.9765625 + 10.4765625 = 41.453125; the
  jump origin fills one jump row, its apex at 41.453125 + 8 = 49.453125. The
  band is 10.4765625 + 8 + 0 + 2 + 10.4765625 = 30.953125 wide, so `Eb` =
  61.9296875, `Hm` = 14.5 + 61.9296875 + 8 = 84.4296875, and the card of
  `score` is max(84.4296875, 120) = 120 high.
- The flow of `score`, in item coordinates: the flow marker at `x(8)` =
  71.70361328125 + 400 × 1/2 = 271.70361328125, from the flow row `yf` =
  14.5 + 41.453125 = 55.953125 to `P` = 8, its label from 274.70361328125
  with its baseline at `yf − d(9)` = 53.83056640625 (tier 1). The jump
  origin from `Xf` = `x(16)` = 471.70361328125 to `Xt` = `x(0)` =
  71.70361328125 (§6.6): `q` = −100, `ya` = 14.5 + 49.453125 = 63.953125,
  `yc` = 55.953125 + 4/3 × 8 = 66.61979166666667, `C1` = (371.70361328125,
  `yc`), `C2` = (171.70361328125, `yc`); `ℓ` = 100.56727985670975, `(ux,
  uy)` = (−0.9943592005519288, −0.10606498139220578), `Bh` =
  (75.68105008345772, 56.377384925568826) and the head's corners
  (75.4689201206733, 58.366103326672686) and (75.89318004624214,
  54.388666524464966). Its label is centred on `x(8)`, baseline (14.5 +
  (49.453125 + 2)) + `a(9)` = 74.30712890625.
- Places (§8.6): `pages` at (8, 28.8046875), the first item, `P + h(11) +
  F`; `recording` at (8, 100.2578125), the box's spacing 8 below the
  bottom edge `d` = 28.8046875 + 63.453125 = 92.2578125 of `pages`' card,
  its shadow not counted; `score` at (−60, −150). Every `length` is 400
  and every `scale` 1, so an item-coordinate position `px` lies at `x +
  px`.
- The box: `Pt` = 28.8046875, `Xl` = min(0, −60 − 8) = −68 and `Yt` =
  min(0, −150 − 28.8046875) = −178.8046875, so `(Ox, Oy)` = (68,
  178.8046875). `Xr` = 8 + (515.896728515625 + 2) = 525.896728515625, from
  the shadows of `pages` and `recording`, which end at 8 +
  507.896728515625 + 2; `Yb` = 8 + (100.2578125 + (49.4765625 + 2)) =
  159.734375, from `recording`'s shadow. `W` = 525.896728515625 − (−68) =
  593.896728515625 and `H` = 159.734375 − (−178.8046875) = 338.5390625.
- The title `Sketches` lies at the box's top left: `x` = `Xl + P` = −60,
  baseline (−178.8046875 + 8) + 10.21044921875 = −160.59423828125, right
  edge −60 + 49.951171875 = −10.048828125, slot ending at −178.8046875 + 8
  + 12.8046875 = −158, `F` above the top of `score`.
- Drawn, each position plus (68, 178.8046875): the title at `x` 8 with its
  baseline at −160.59423828125 + 178.8046875 = 18.21044921875 → 18.2104,
  where it lies in a box with no places; the cards of `score` at (8,
  28.8046875 → 28.8047), where the first item lies by default, of `pages` at
  (76, 207.609375 → 207.6094) and of `recording` at (76, 279.0625), each
  507.896728515625 → 507.8967 wide; the starts (8 + 71.70361328125) + 68 =
  147.70361328125 → 147.7036 (`pages`, `recording`) and (−60 +
  71.70361328125) + 68 = 79.70361328125 → 79.7036 (`score`); the lines at
  `y` 236.0859375 → 236.0859 (`pages`), 293.5625 (`recording`) and
  43.3046875 → 43.3047 (`score`), and their maps' outlines from 229.5859375
  → 229.5859 to 231.5859375 → 231.5859, from 287.0625 to 289.0625 and from
  36.8046875 → 36.8047 to 38.8046875 → 38.8047; the boundaries of `pages` at
  `u` = 1/3 and 2/3, item x 205.03694661458331 and 338.37027994791663, →
  281.0369 and 414.3703; the flow marker of `score` at `x` 279.70361328125 →
  279.7036, from the flow row at 84.7578125 → 84.7578 to 36.8046875 →
  36.8047, where the top of its map's outline lies too, and its jump origin
  from (479.7036, 84.7578) to (79.7036, 84.7578), its shaft ending at `Bh`
  (83.68105008345772, 85.18207242556883) → (83.6811, 85.1821). The shadow of
  `score`'s card ends at 150.8046875, 56.8046875 above the card of `pages`,
  and no card overlaps another or the title.
- Page 625.896728515625 × 370.5390625 → **625.8967 × 370.5391**.

## `bundle_ungrouped__scale`

The manifest of `bundle_ungrouped__places` with `places` `{recording:
{scale: 1.5}}` and nothing else stated: every item at its default place,
`recording` drawn half as large again, its map and text included. A scale
changes neither the layout in item coordinates nor any other item, except
that the items after a scaled one start below its drawn bottom (§8.6).

- The layout and the member drawings are those of
  `bundle_ungrouped__places`, which no place changes: `n` = 8, `s0` =
  71.70361328125, `Mr` = 28.193115234375, `Ri` = 499.896728515625, every
  card 0 to 507.896728515625 in item coordinates, `Hm` = 63.453125
  (`pages`), 49.4765625 (`recording`) and 84.4296875 (`score`).
- Places: `pages` at (8, 28.8046875); `recording` at (8, 100.2578125),
  scale 1.5, its drawn bottom 100.2578125 + 1.5 × 49.4765625 =
  174.47265625; `score` at (8, 182.47265625), the box's spacing 8 below
  that. Every `length` is 400.
- `recording`, drawn at `(8 + 1.5 × px, 100.2578125 + 1.5 × py)`: its card
  at (8, 100.2578125), 1.5 × 507.896728515625 = 761.8450927734375 →
  761.8451 wide and 1.5 × 49.4765625 = 74.21484375 → 74.2148 high, `rx`
  7.5, stroke width 1.125; its shadow at the item position (2, 2), drawn
  at (11, 103.2578125); its line from 8 + 1.5 × 71.70361328125 =
  115.555419921875 → 115.5554 to 8 + 1.5 × 471.70361328125 =
  715.555419921875 → 715.5554 at `y` 100.2578125 + 1.5 × 14.5 =
  122.0078125 → 122.0078, 4.5 wide, dashed `4.5 4.5`, its start circle of
  radius 4.5 and its arrowhead's tip at 8 + 1.5 × 480.70361328125 =
  729.055419921875 → 729.0554; its map's outline as long as its line, from
  100.2578125 + 1.5 × 8 = 112.2578125 → 112.2578 to 100.2578125 + 1.5 × 10
  = 115.2578125 → 115.2578, stroke width 1.5; its wedges from
  100.2578125 + 1.5 × 16 = 124.2578125 → 124.2578 to 100.2578125 + 1.5 ×
  29 = 143.7578125 → 143.7578, 9 wide; its name at `x` 8 + 1.5 × 8 = 20 in
  size 16.5, baseline 100.2578125 + 1.5 × 18.30810546875 =
  127.719970703125 → 127.72; its labels in size 13.5, baseline 100.2578125
  + 1.5 × 39.35400390625 = 159.288818359375 → 159.2888.
- `pages` and `score` are drawn as in a box with no places, `score`
  24.73828125 = 0.5 × 49.4765625 lower: its line at 182.47265625 + 14.5 =
  196.97265625 → 196.9727, its flow row at 182.47265625 + 55.953125 =
  238.42578125 → 238.4258.
- The box: `Xl` = `Yt` = 0 (the first item lies at `Pt` = 28.8046875), so
  the origin is (0, 0) and the title at (8, 18.21044921875 → 18.2104).
  `W` = 8 + (8 + 1.5 × (507.896728515625 + 2)) = 8 + 772.8450927734375 =
  780.8450927734375, from `recording`'s shadow; `H` = 8 + (182.47265625 +
  (84.4296875 + 2)) = 8 + 268.90234375 = 276.90234375, from `score`'s
  shadow. No card overlaps another or the title.
- Page 812.8450927734375 × 308.90234375 → **812.8451 × 308.9023**.

## `bundle_ungrouped__spacing`

The manifest of `bundle_ungrouped__places` with the box's `spacing` 24 and
`places` `{score: {spacing: 8}}`, nothing else stated: every item at its
default place. The box's spacing is the gap between its items at their
default `y` (§8.6), so `recording` lies 24 below `pages` and `score` 24
below `recording`; the gap `F` = 8 after the title does not change. The
card spacing `S` = 8 of `score` is the gap between that card's bands
(§6.2, §6.4): its conversion maps band above and its markers band below
lie against its line, from `c` = 0, and do not move, but its flow control
band at level −2 starts `S` beyond its markers band and its first jump
depth is `4 + S`, so that band lies 4 further out and is 4 wider, and the
card is 8 higher than at `S` = 4. Its row pitch `p0` = max(10 + 8,
`h(11)`) = 18 places no row, since its children band holds nothing, and
its padding `P` = 8 does not change (§8.6). No spacing multiplies another:
`pages` and `recording` keep `S` = 4 and are drawn as in a box with no
places, only lower.

- The layout is that of `bundle_ungrouped__places`, which no place
  changes: `n` = 8, `s0` = 71.70361328125, `Mr` = 28.193115234375, `Ri` =
  499.896728515625, every card 0 to 507.896728515625 in item coordinates,
  `Hm` = 63.453125 (`pages`) and 49.4765625 (`recording`).
- `score` (§6.4, §6.5): `Ea` = 6.5, its map stack's reach, so `y_root` =
  14.5, as at `S` = 4. Its flow control band starts at 26.9765625 + 8 =
  34.9765625, beyond its markers band; the label `Fine` fills one
  flow-marker label tier, `T` = 1, so the flow row lies at `f0` = 34.9765625
  + 10.4765625 = 45.453125, and the jump origin fills one jump row, its apex
  at 45.453125 + (4 + 8) = 57.453125. The band is 10.4765625 + (4 + 8) + 0 +
  2 + 10.4765625 = 34.953125 wide, so `Eb` = 34.9765625 + 34.953125 =
  69.9296875 and `Hm` = 14.5 + 69.9296875 + 8 = 92.4296875 → 92.4297.
- The flow of `score`, in item coordinates: the flow marker at `x(8)` =
  271.70361328125, from the flow row `yf` = 14.5 + 45.453125 = 59.953125 to
  `P` = 8, its label from 274.70361328125 with its baseline at `yf − d(9)` =
  57.83056640625. The jump origin from `Xf` = `x(16)` = 471.70361328125 to
  `Xt` = `x(0)` = 71.70361328125 (§6.6): `q` = −100, `ya` = 14.5 + 57.453125
  = 71.953125, `yc` = 59.953125 + 4/3 × 12 = 75.953125 (the double nearest
  4/3, times 12, lies halfway between 16 and the double below it and rounds
  to 16, ties to even), `C1` = (371.70361328125, `yc`), `C2` =
  (171.70361328125, `yc`); `ℓ` = √(100 × 100 + 16 × 16) =
  101.27191120937731, `(ux, uy)` = (−0.9874406319167053,
  −0.15799050110667284), `Bh` = (75.65337580891682, 60.58508700442669) and
  the head's corners (75.33739480670347, 62.5599682682601) and
  (75.96935681113017, 58.61020574059328). Its label is centred on `x(8)`,
  baseline (14.5 + (57.453125 + 2)) + `a(9)` = 82.30712890625.
- Places: `pages` at (8, 28.8046875), the first item, `P + h(11) + F`, its
  bottom 28.8046875 + 63.453125 = 92.2578125; `recording` at (8,
  92.2578125 + 24 = 116.2578125 → 116.2578), its bottom 116.2578125 +
  49.4765625 = 165.734375; `score` at (8, 165.734375 + 24 = 189.734375 →
  189.7344). Every `length` is 400 and every `scale` 1, so a position
  `(px, py)` in item coordinates is drawn at `(8 + px, y + py)` (§8.6).
- `recording`, 16 lower than in a box with no places: its card at (8,
  116.2578125), 507.896728515625 → 507.8967 wide and 49.4766 high, its
  shadow at (10, 118.2578125); its map's outline from 116.2578125 + 8 =
  124.2578125 → 124.2578 to 126.2578125 → 126.2578; its line at `y`
  116.2578125 + 14.5 = 130.7578125 → 130.7578, from 79.70361328125 →
  79.7036 to 479.70361328125 → 479.7036, the arrowhead's base from
  126.2578 to 135.2578; its wedges from 116.2578125 + 16 = 132.2578125 →
  132.2578 to 116.2578125 + 29 = 145.2578125 → 145.2578; its name at `x`
  16, baseline 116.2578125 + (14.5 + 3.80810546875) = 134.56591796875 →
  134.5659; its labels at baseline 116.2578125 + ((14.5 + 16.5) +
  8.35400390625) = 155.61181640625 → 155.6118.
- `score`, 32 lower than in a box with no places: its card at (8,
  189.734375), 507.8967 wide and 92.4297 high, its shadow at (10, 191.734375
  → 191.7344); its line at 189.734375 + 14.5 = 204.234375 → 204.2344, its
  map's outline from 197.734375 → 197.7344 to 199.734375 → 199.7344, its
  name's baseline at 208.04248046875 → 208.0425, its labels' at
  229.08837890625 → 229.0884, all as at `S` = 4; its flow row at 189.734375
  + 59.953125 = 249.6875, the flow marker from there to 189.734375 + 8 =
  197.734375 → 197.7344 and its label's baseline at 189.734375 +
  57.83056640625 = 247.56494140625 → 247.5649; the jump origin's controls at
  189.734375 + 75.953125 = 265.6875, its shaft ending at `Bh`
  (83.65337580891682, 250.3194620044267) → (83.6534, 250.3195), the head's
  corners → (83.3374, 252.2943) and (83.9694, 248.3446), and its label's
  baseline at 189.734375 + 82.30712890625 = 272.04150390625 → 272.0415.
- The box: `Xl` = `Yt` = 0, so the origin is (0, 0) and the title at (8,
  18.21044921875 → 18.2104). `W` = 8 + (8 + (507.896728515625 + 2)) =
  525.896728515625, from the shadows of all three cards; `H` = 8 +
  (189.734375 + (92.4296875 + 2)) = 8 + 284.1640625 = 292.1640625, from
  `score`'s shadow. No card overlaps another or the title.
- Page 557.896728515625 × 324.1640625 → **557.8967 × 324.1641**.

## `styled_score_flow_inner`

The manifest of `styled__score` with the band order `score/children_1`,
`score/markers_1`, `score`, `score/conversion_maps_1`,
`score/flow_control_1`, `score/regions_1` in its `graphical.order`
(§6.4). Above the root's line, the markers band lies against the line and
the children band beyond it, as in `styled__score`. Below, the conversion
maps band lies against the line, the flow control band next to it, and the
regions band beyond that. `b` follows the root's band order (§6.4) but
draws nothing there: it has no maps and no children, and the defaults hide
its other bands (§4). `a` is hidden and takes no room.

- Above: the markers band lies at level 1 from `c` = 0. Its labels, at size
  10, fill one tier, so it is `w / 2 + 13 + 2 + h(10)` = 2 + 13 + 2 +
  11.640625 = 28.640625 wide. The children band lies at level 2 from
  max(28.640625 + 4, `p0 / 2` = 7) = 32.640625. Its one row, `b`, has the
  halves 7 and 7, so `b`'s line lies 39.640625 out and `Ea` = 46.640625.
  `y_root` = 8 + 46.640625 = 54.640625. The root's line is drawn at
  62.640625 → 62.6406 and `b`'s at 23.
- Below: the conversion maps band lies at level −1 from `c` = 0. The map
  `ticks` is centred `w / 2 + (g + d) − d / 2` = 2 + 5 − 1 = 6 below the
  line, its outline from 67.640625 → 67.6406 to 69.640625 → 69.6406, and the
  band reaches `e` = 2 + 5 = 7. The flow control band lies at level −2 from
  7 + 4 = 11. It has no flow-marker label tier, so the flow row lies at 11
  (73.640625 → 73.6406) and the jump origin's apex at 11 + 8 = 19
  (81.640625). The band is 0 + 8 + 2 + 11.640625 = 21.640625 wide, so its
  outer edge is 32.640625. The regions band lies at level −3 from 32.640625
  + 4 = 36.640625. With `pr` = 6 + 2 + `h(10)` + 4 = 23.640625 it is
  19.640625 wide, so `Eb` = 56.28125. The flow control and regions bands
  swap places and widths with those of `styled__score`, so `Eb` and the
  height stay that drawing's.
- The jump origin `da-capo` runs from `Xf` = `x(8)` = 498.080078125 to `Xt` =
  `x(0)` = 98.080078125, with `w` = 2:
  - `q` = −100 and `yc` = 73.640625 + 4/3 × 8 = 84.30729166666667 →
    84.3073;
  - `ℓ` = 100.56727985670975 and `(ux, uy)` = (−0.9943592005519288,
    −0.10606498139220578);
  - `Bh` = (106.03495172941543, 74.48914485113765) → (106.035, 74.4891);
  - the head's corners are (105.6106918038466, 78.46658165334537) →
    (105.6107, 78.4666) and (106.45921165498424, 70.51170804892993) →
    (106.4592, 70.5117);
  - its label is centred on `x(4)` = 298.080078125, with its baseline at
    62.640625 + (19 + 2) + `a(10)` = 92.9228515625 → 92.9229.
- The region `intro` runs from `x(0)` to `x(2)` = 198.080078125, with its
  tip at `x(1)` = 148.080078125. Its arms lie at 62.640625 + 36.640625 =
  99.28125 → 99.2812 and its tip at 105.28125 → 105.2812. Its label's
  baseline is 62.640625 + 44.640625 + `a(10)` = 116.5634765625 → 116.5635.
- As in `styled__score`: `x0` = 98.080078125 → 98.0801, `R` =
  510.080078125, `Hm` = 54.640625 + 56.28125 + 8 = 118.921875, `W` =
  528.080078125 and `H` = 136.921875.
- Page 560.080078125 × 168.921875 → **560.0801 × 168.9219**.

## `map_child_band_order`

The manifest of `map` with the band order `phrase/children_1`, `phrase`,
`phrase/conversion_maps_1`, `phrase/markers_1`, `phrase/regions_1`,
`phrase/flow_control_1` for the child `phrase` in its `graphical.order`
(§6.4). So `phrase`'s map `ticks`, addressed `melody/ticks`, lies against
its line below it. `melody` has no entry and keeps the default band order
(§4).

- Above `melody`'s line: the conversion maps band lies at level 1, with
  `tempo` centred 5.5 above the line and reaching `e` = 6.5 (Shared
  quantities). The children band lies at level 2 from max(6.5 + 4, `p0 / 2`
  = 7) = 10.5.
- `phrase` lies in that band's row 1. Its conversion maps band lies at
  level −1 below its own line from `c` = 0, with `ticks` centred 5.5 below.
  Its other bands draw nothing, so its below edge is 6.5 and its above edge
  0. The row's inner half, towards `melody`'s line, is max(7, 6.5) = 7, and
  its outer half is max(7, 0) = 7. In `map` the two edges are the other way
  round, and the halves are the same. So `phrase`'s line lies 10.5 + 7 =
  17.5 above `melody`'s, `Ea` = 10.5 + 14 = 24.5 and `y_root` = 32.5.
- Below `melody`'s line: the markers band lies at level −1 and is 26.9765625
  wide (Shared quantities), so `Hm` = 32.5 + 26.9765625 + 8 = 67.4765625.
- Drawn: `melody`'s line at 40.5, with `tempo`'s outline from 34 to 36.
  `phrase`'s line at 23, with the outline of `ticks` from 27.5 to 29.5 and
  from `x(2)` = 163.53662109375 → 163.5366 to `x(6)` = 363.53662109375 →
  363.5366, between `phrase`'s line and `melody`'s map.
- As in `map`: `x0` = 63.53662109375 → 63.5366, `R` = 472.53662109375, `W`
  = 490.53662109375 and `H` = 85.4765625. The figure differs from `map`'s
  only in the outline of `ticks`.
- Page 522.53662109375 × 117.4765625 → **522.5366 × 117.4766**.

## `map_root_band_order`

The manifest of `map` with the band order `melody/children_1`, `melody`,
`melody/conversion_maps_1`, `melody/markers_1`, `melody/regions_1`,
`melody/flow_control_1` for the root `melody` in its `graphical.order`.
`phrase` has no entry, so it follows `melody`'s order band by band ID
(§6.4). Both lines therefore have their maps against them, below. Above
`melody`'s line lies its children band alone. Below it, the markers band
lies beyond the maps.

- Above: the line reaches 0 there, since its map stack lies below. So the
  children band at level 1 starts at the larger of 1.5 + 4 = 5.5 and `p0 /
  2` = 7: 7. Its row 1 holds `phrase`, whose edges are 6.5 below (its map)
  and 0 above, so the halves are 7 and 7. `phrase`'s line lies 14 above
  `melody`'s, and `Ea` = 21.
- `y_root` = max(8 + 21, 8 + 6.40234375) = 29.
- Below: the conversion maps band lies at level −1 from `c` = 0, with
  `tempo` centred 5.5 below the line, so its outer edge is 6.5. The markers
  band lies at level −2 from 6.5 + 4 = 10.5 and is 26.9765625 wide, so `Eb`
  = 37.4765625. The wedges' tips lie 10.5 + 1.5 = 12 below the line and
  their bases 12 + 13 = 25 below it. The labels' tier starts 25 + 2 = 27
  below it.
- `Hm` = 29 + 37.4765625 + 8 = 74.4765625 → 74.4766.
- Drawn, `melody`:
  - its line at 37, with its arrowhead from 32.5 to 41.5;
  - `tempo`'s outline from 41.5 to 43.5;
  - the wedges from 49 to 62;
  - their labels' baseline at 37 + 27 + `a(9)` = 72.35400390625 → 72.354;
  - the name `Melody`'s baseline at 40.80810546875 → 40.8081.
- Drawn, `phrase`, as in `map_child_band_order`: its line at 23, the
  outline of `ticks` from 27.5 to 29.5, and the name `Phrase`'s baseline at
  26.80810546875 → 26.8081.
- As in `map`: `x0` = 63.53662109375 → 63.5366 and `R` = 472.53662109375.
  `W` = 490.53662109375 and `H` = 8 + (10 + 74.4765625) = 92.4765625.
- Page 522.53662109375 × 124.4765625 → **522.5366 × 124.4766**.

## `joint_rows`

The root `piece` ("Piece", 16 quarters) with two branches of nested
children, every child locked: `b` ("B", 6 at 0) with the map `ticks_b`
holds `b1` ("B1", 4 at 1), which holds `b11` ("B11", 2 at 1); `d` ("D", 8
at 8) holds `d1` ("D1", 4 at 2) with the maps `tempo_d1` and `ticks_d1`,
which holds `d11` ("D11", 2 at 1) with the maps `tempo_d11` and
`ticks_d11`. Maps lie in canonical order, by ID, so each `tempo_*` (to
seconds, solid blue) lies nearest its line and each `ticks_*` (to ticks,
green dashed `1 1`) beyond it (§2.1, §4). Every children band lies above
its line, beyond the line's conversion maps band where it has one, and the
children bands of the lines of one row are laid out together (§6.4,
Children).

- The rows, by first fit (§6.3, extents `L × u` with `u` = t / 16): `b`
  (0 to 150) and `d` (200 to 400) share row 1 of the children band of
  `piece`; `b1` (25 to 125) and `d1` (250 to 350), each in row 1 of its
  parent's band, form row 1 of those two bands laid out together; so do
  `b11` (50 to 100) and `d11` (275 to 325). The rows are `{piece}`,
  `{b, d}`, `{b1, d1}` and `{b11, d11}`, every name of size 11, so every
  pitch is `p` = `p0` = max(10 + 4, `h(11)`) = 14 (§6.2).
- One map reaches `e` = 6.5 from its line (Shared quantities); two maps
  reach `e` = 1.5 + 2 × 5 = 11.5, centred 5.5 and 10.5 from the line.
- Distances, from the deepest row up (§6.4):
  - row `{b11, d11}`: inner half 7, outer half max(7, 11.5) = 11.5, the
    conversion maps band of `d11`;
  - the children bands of `b1` and `d1`: own starts max(1.5 + 4, 7) = 7
    (`b1`, no map) and max(11.5 + 4, 7) = 15.5 (`d1`, beyond its conversion
    maps band), so both start at `c0` = 15.5, row 1 lies 15.5 + 7 = 22.5
    out, each band is 7 + 11.5 = 18.5 wide, and the above edges of `b1` and
    `d1` are both 15.5 + 18.5 = 34;
  - row `{b1, d1}`: inner 7, outer 34;
  - the children bands of `b` and `d`: own starts max(6.5 + 4, 7) = 10.5
    (`b`) and 7 (`d`), so `c0` = 10.5, row 1 at 10.5 + 7 = 17.5, each band
    7 + 34 = 41 wide, both above edges 51.5;
  - row `{b, d}`: inner 7, outer 51.5;
  - `piece` has no map: its children band starts at `p0 / 2` = 7, row 1
    at 14, 7 + 51.5 = 58.5 wide, so `Ea` = 65.5; below, its markers band
    reaches `Eb` = 26.9765625 (Shared quantities).
- Laid out alone, the children bands of `d` and of `b1` would start at 7,
  `d1` lying 14 above `d` and `b11` 14 above `b1`; laid out together they
  lie 17.5 and 22.5 above, in the rows of `b1` and of `d11`.
- `y_root` = max(8 + 65.5, 8 + 6.40234375) = 73.5 and `Hm` = 73.5 +
  26.9765625 + 8 = 108.4765625 → 108.4766 (§6.5).
- Drawn, each line at the card's top 8 plus its ordinate: `piece` at 81.5,
  `b` and `d` at 81.5 − 14 = 67.5, `b1` and `d1` at 67.5 − 17.5 = 50,
  `b11` and `d11` at 50 − 22.5 = 27.5. The maps' outlines: `ticks_b` from
  61 to 63; `tempo_d1` from 43.5 to 45.5 and `ticks_d1` from 38.5 to 40.5;
  `tempo_d11` from 21 to 23 and `ticks_d11` from 16 to 18, at `P` below
  the card's top exactly. The wedges' tips at 83, their bases at 96.
- Names (§6.6), one text per row, the row's names joined in traversal
  order and addressed by its first name, each baseline the row's ordinate
  plus (`a(11)` − `d(11)`) / 2 = 3.80810546875: `B11, D11` (`b11/name`) at
  31.30810546875 → 31.3081, `B1, D1` (`b1/name`) at 53.80810546875 →
  53.8081, `B, D` (`b/name`) at 71.30810546875 → 71.3081, `Piece` at
  85.30810546875 → 85.3081.
- `N` = w(`B11, D11`, 11) = 51.00390625, of `Piece` (29.2724609375),
  `B, D` (23.009765625), `B1, D1` (37.0068359375) and `B11, D11`.
- `x0` = 16 + 51.00390625 + 8 = 75.00390625 → 75.0039; the start label
  `0 ♩` gives only 22.416015625. Every position lies a multiple of 25 from
  `x0`: `b` from 75.0039 to 225.0039, `b1` from 100.0039 to 200.0039,
  `b11` from 125.0039 to 175.0039, `d` from 275.0039 to 475.0039, `d1`
  from 325.0039 to 425.0039, `d11` from 350.0039 to 400.0039; each map
  spans its timeline.
- `R` = the end label `16 ♩` at 475.00390625 + 9.279052734375 =
  484.282958984375, beyond the arrowhead tip 484.00390625 and the diamond
  corner of `d` at 479.50390625.
- `W` = 8 + (10 + 484.282958984375) = 502.282958984375; `H` = 8 + (10 +
  108.4765625) = 126.4765625.
- Page 534.282958984375 × 158.4765625 → **534.283 × 158.4766**.

## `unknown_length_child__regions-shown`

`unknown_length_child` with the application layer `[{"select": {"ids":
["movement/regions_1"]}, "set": {"display": "inline"}}]`. It outranks the
default that hides that band (§2.5, §4), so the region `score/region_1` is
drawn in `movement`'s regions band, at `movement`'s line. `movement` has no
band order of its own and follows `score`'s, the default, band by band ID
(§6.4), so its regions band lies below its line, towards `score`'s. Its
markers band draws nothing, so the regions band is at level −1 and the only
band `movement` draws.

- Horizontally the drawing is that of `unknown_length_child`: the region
  has no label and its brace lies inside `movement`'s span, so `x0` =
  83.490234375 → 83.4902 and `R` = 492.769287109375.
- The regions band of `movement` (§6.4, Where a band lies): `movement`'s
  line has no map and no boundary, so it reaches 0 below, less than `w / 2`
  = 1.5. The band therefore starts at `S` beyond `w / 2`, `c` = 1.5 + 4 =
  5.5, and its brace keeps the gap `S` from the line's stroke. It has one
  row, so it is `pr − S` = 18.4765625 wide (Shared quantities), and
  `movement`'s edge below is 5.5 + 18.4765625 = 23.9765625; its edge above
  is 0.
- Above `score`, the children band alone, at level 1. `score`'s line
  reaches nothing there, so the band's own start is the larger of 1.5 + 4 =
  5.5 and `p0 / 2` = 7: 7. Its one row holds `movement`: the outer half is
  `movement`'s above side, max(7, 0) = 7, and the inner half its below
  side, max(7, 23.9765625) = 23.9765625. So `movement`'s line lies `l1` =
  7 + 23.9765625 = 30.9765625 above `score`'s, the band is 23.9765625 + 7 =
  30.9765625 wide, and `Ea` = 7 + 30.9765625 = 37.9765625. Below, the
  markers band alone: `Eb` = 26.9765625 (Shared quantities).
- `y_root` = 8 + 37.9765625 = 45.9765625; `Hm` = 45.9765625 + 26.9765625 +
  8 = 80.953125 → 80.9531.
- Drawn, each ordinate the card's top 8 plus its item-coordinate value:
  - `score`'s line at 53.9765625 → 53.9766, and `movement`'s at 53.9765625
    − 30.9765625 = 23, as in `unknown_length_child`;
  - the brace's arms at 23 + 5.5 = 28.5, from `x(8)` = 183.490234375 →
    183.4902 to `x(14)` = 258.490234375 → 258.4902; its tip at 23 + (5.5 +
    6) = 34.5 on `x(11)` = 220.990234375 → 220.9902, `u` = 11/32, the
    midpoint of 8 and 14 on `score`'s axis (§3.1); its path's `Ym` = 31.5
    and `k` = 3 (§7.2);
  - the wedges from 53.9765625 + 1.5 = 55.4765625 → 55.4766 to 53.9765625
    + 14.5 = 68.4765625 → 68.4766, and their labels' baseline at
    (53.9765625 + 16.5) + 8.35400390625 = 78.83056640625 → 78.8306;
  - the names' baselines at 23 + 3.80810546875 = 26.80810546875 → 26.8081
    (`movement`) and 53.9765625 + 3.80810546875 = 57.78466796875 → 57.7847
    (`score`).
- `W` = 510.769287109375; `H` = 8 + (10 + 80.953125) = 98.953125.
- Page 542.769287109375 × 130.953125 → **542.7693 × 130.9531**.

## `unknown_length_segments__regions-shown`

`unknown_length_segments` with the application layer `[{"select":
{"element": "band", "class": "regions"}, "set": {"display": "inline"}}]`,
which outranks the defaults (§2.5) and shows every regions band. The
regions bands of `a` and `c` are displayed, and what they hold joins
`form`'s regions band, after `form`'s own content (none), segment after
segment in traversal order (§6.4, Segments without a line): `form/region_1`
and then `form/region_2`, laid out by one first fit.

- `λ` = 17, the boundaries, `Ea` = 8, `y_root` = 16, `x0` = 49.8403 and
  `R` = 478.34033203125 are those of `unknown_length_segments`. Neither
  region has a label, and both braces end at or before `x(17)` = `x0 + L` =
  449.84033203125.
- The regions band lies at level −2, beyond the markers band, and starts
  at 26.9765625 + 4 = 30.9765625. On `form`'s axis the regions span 0 to
  4 and 14 to 17, so both lie in row 1. The band is therefore 18.4765625
  wide and `Eb` = 49.453125 (Shared quantities).
- The braces have their arms at 24 + 30.9765625 = 54.9765625 → 54.9766
  and their tips at 24 + 36.9765625 = 60.9765625 → 60.9766, and open
  towards `form`'s line.
  - `form/region_1` runs from `x(0)` = 49.8403 to `x(4)` =
    143.95797909007354 → 143.958, with its tip at `x(2)` =
    96.89915556066177 → 96.8992.
  - `form/region_2` runs from `x(14)` = 379.2521 to `x(17)` = 449.8403,
    with its tip at `x(31/2)` = 414.54621438419116 → 414.5462.
- `Hm` = 16 + 49.453125 + 8 = 73.453125.
- `W` = 496.34033203125; `H` = 8 + (10 + 73.453125) = 91.453125.
- Page 528.34033203125 × 123.453125 → **528.3403 × 123.4531**.

## `child_flow_control__flow-shown`

The root `piece` ("Piece", 16 quarters) and its locked child `verse`
("Verse", 8 at 4), which holds the flow marker `fine` ("Fine") at 4 and the
jump origin `da_capo_al_fine` ("D.C. al Fine") from 8 back to 0, on
`piece`'s axis at 8 and from 12 to 4. The application layer `[{"select":
{"ids": ["verse/flow_control_1"]}, "set": {"display": "inline"}}]` outranks
the default that hides the flow control band of every timeline held by a
band (§2.5, §4), so the flow marker and the jump origin, addressed
`piece/fine` and `piece/da_capo_al_fine` (§2.2), are drawn at `verse`'s own
line (§6.4). `verse` has no band order of its own and follows `piece`'s
default one band by band ID, so its flow control band lies below its line.
Its markers band and regions band draw nothing, so the flow control band is
at level −1. `verse` has no map and no boundary, so its line reaches 0
below, less than `w / 2` = 1.5, and the band starts at `S` beyond `w / 2`:
`c` = 1.5 + 4 = 5.5.

- `N` = w(`Verse`, 11) = 31.3134765625, above w(`Piece`, 11) =
  29.2724609375.
- `x0` = 16 + 31.3134765625 + 8 = 55.3134765625 → 55.3135; the start label
  `0 ♩` gives only 22.416015625, and the jump-origin label, centred on `u` =
  8/16 = 1/2, 16 + 25.7958984375 − 200 = −158.2041015625. `x(4)` =
  155.3134765625, `x(8)` = 255.3134765625 and `x(12)` = 355.3134765625.
- `R` = the end label `16 ♩` at 455.3134765625 + 9.279052734375 =
  464.592529296875, beyond the arrowhead tip 464.3134765625; the diamond of
  `verse` reaches 359.8134765625, the jump-origin label 281.109375 and the
  flow-marker label 258.3134765625 + 18.91845703125 = 277.23193359375.
- The flow control band of `verse` (§6.4): the label `Fine` fills one
  flow-marker label tier, `T` = 1, so the flow row lies 5.5 + 10.4765625 =
  15.9765625 below `verse`'s line; the jump origin fills one jump row, its
  apex at 15.9765625 + 8 = 23.9765625. The band is 10.4765625 + 8 + 0 + 2 +
  10.4765625 = 30.953125 wide, so `verse`'s edge below is 5.5 + 30.953125 =
  36.453125. Its above side has no band, and its line reaches 0 there.
- The children band of `piece` lies above it at level 1. `piece`'s line
  reaches nothing there, so the band's own start is the larger of 1.5 + 4
  = 5.5 and `p0 / 2` = 7, `p0` = `p` = max(10 + 4, `h(11)`) = 14: 7. Its one
  row holds `verse`, whose below side lies in the row's inner half: the
  inner half is max(7, 36.453125) = 36.453125, the outer half 7. `verse`'s
  line lies `l1` = 7 + 36.453125 = 43.453125 above `piece`'s, the band is
  36.453125 + 7 = 43.453125 wide, and `Ea` = 7 + 43.453125 = 50.453125.
- Below `piece`, the markers band reaches `Eb` = 26.9765625 (Shared
  quantities).
- `y_root` = 8 + 50.453125 = 58.453125; `Hm` = 58.453125 + 26.9765625 + 8 =
  93.4296875 → 93.4297.
- Drawn: `piece`'s line at 8 + 58.453125 = 66.453125 → 66.4531, `verse`'s
  at 66.453125 − 43.453125 = 23, the flow row at 23 + 15.9765625 =
  38.9765625 → 38.9766 and the apex at 23 + 23.9765625 = 46.9765625 →
  46.9766.
- The flow marker (§6.4, Flow markers) at `x(8)`: `E` is the outer edge of
  `verse`'s above side, 0, and `s` the name size 11 of its row, so `m` =
  max(0, `h(11) / 2`) = 6.40234375. The flow marker runs from the flow row
  up across `verse`'s line to 23 − 6.40234375 = 16.59765625 → 16.5977,
  inside the row's outer half of 7. Its label starts at 258.3134765625 →
  258.3135, with its baseline at `yf − d(9)` = 38.9765625 − 2.12255859375 =
  36.85400390625 → 36.854 (tier 1), so the label's ascent ends at 28.5, `S`
  below the edge of `verse`'s stroke at 24.5.
- The jump origin (§6.6), from `Xf` = `x(12)` to `Xt` = `x(4)`, computed in
  item coordinates and then drawn at the card's place (§8.6): `q` = −50,
  `yc` = 38.9765625 + 4/3 × 8 = 49.643229166666664 → 49.6432, `C1` =
  (305.3134765625, `yc`), `C2` = (205.3134765625, `yc`); `ℓ` =
  51.125118853434245, `(ux, uy)` = (−0.9779928364243076,
  −0.2086384717705189), `Bh` = (159.22544790819722, 39.81111638708208) →
  (159.2254, 39.8111) and the head's corners → (158.8082, 41.7671) and
  (159.6427, 37.8551). Its label is centred on `x(8)`, with its baseline at
  (23 + (23.9765625 + 2)) + `a(9)` = 57.33056640625 → 57.3306.
- The names: `Verse` with its baseline at 23 + 3.80810546875 =
  26.80810546875 → 26.8081, `Piece` at 66.453125 + 3.80810546875 =
  70.26123046875 → 70.2612. The wedges run from 67.953125 → 67.9531 to
  80.953125 → 80.9531, and their labels' baseline is 66.453125 + 16.5 +
  8.35400390625 = 91.30712890625 → 91.3071.
- `W` = 8 + (10 + 464.592529296875) = 482.592529296875; `H` = 8 + (10 +
  93.4296875) = 111.4296875.
- Page 514.592529296875 × 143.4296875 → **514.5925 × 143.4297**.
