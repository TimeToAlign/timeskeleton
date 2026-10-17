# Hand-derived drawings

Twenty of the 59 drawings in this directory are derived by hand from the
[drawing specification](../../../docs/drawing.md) and the font metrics
alone. Their `figure.svg` files are never regenerated: the emitting script
compares each with its writer's output instead. Every other figure in this
directory, and every `figure.tex` and `inputs.json`, is emitted (see
[`fixtures/README.md`](../../README.md)). The key arithmetic of each
hand-derived drawing is given below, so that any implementation can check
where it first parts from the specification: the shared start `x0` and the
term that sets it, the largest right edge `R`, the box `W × H`, and the
page.

Section numbers (§) refer to the drawing specification. Every drawing here
is placed alone at `(0, 0)` with scale 1, so the page is `PW = W + 32` by
`PH = H + 32` and the drawing lies at `(16, 16)` (§7.1). Every
`inputs.json` here supplies no application layer, so the layers are the
defaults and the manifest's own `graphical` block (§1). Exact values are
given in full; a value as the writer prints it (§7.3) follows an arrow
(`→`).

| Drawing | Manifest | Non-default inputs |
|---|---|---|
| `bare` | `bare.json` | none |
| `nested` | `nested.json` | none |
| `map` | `map.json` | none |
| `flow_control` | `flow_control.json` | none |
| `with_region` | `with_region.json` | none |
| `styled__score` | `styled__score.json` | none (the manifest's own `graphical` block styles it) |
| `nested__length-800-spacing-2` | `nested.json` | `length` 800, `spacing` 2 |
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
| `styled__score__bands-timeline` | `styled__score.json` | `bands` `{score: ["flow", "children", "regions"]}` |

## Shared quantities

Every manifest is drawn as one box (§8). Fifteen of these drawings show
one ungrouped root, drawn in its card, four one group, drawn as a frame,
and `bundle_ungrouped__places` three ungrouped roots, each in its own
card. Only that drawing's manifest has a `name`, so only its box has a
title; no other manifest has a `name` or an `id`.

Every `data-address` follows §2.2: an element other than a timeline or a
group is addressed through the root whose tree holds it, also in a manifest
of one root (`melody/tempo`, `clt_1/region_1`, `flow:quarters/jump_1`,
`score/intro/label`), and a manifest's title, wherever one is drawn, is
addressed `name`.

- Constants (§6.2): padding `P` = 8 (`P × v` above and below a member
  drawing's content), card padding `K` = 8, frame padding `Q` = 8, gap
  between cards `F` = 8, gap after the names `G'` = 8 whenever a name is
  drawn, card shadow offset 2.
- Each item, a group's frame or an ungrouped root's card, is laid out on
  its own at its place (§8.2, §8.6), whose `x` is `P` = 8 unless `places`
  states another. Its name column starts at `xn = x + K` in an ungrouped
  root's card, 16 at the default place, and at `xn = x + Q + K` in a
  frame, 24 at the default place. `N` is the widest row name of any member
  drawing of the item; a group's title is not a row name.
- An item's shared start (§8.2) is the largest of `xn + N + G'`, of
  `xn + wi / 2 − L × ui` for every centred label `i` of the item, and of
  `xn + N + G' + 8 × wa` for every ancestor line `a` of the item that runs
  on to the left. Each candidate is listed below only when it decides or comes
  close.
- An ungrouped card spans its place's `x` to `R + K`; in a frame, a card
  spans `x + Q` to `R + K` and the frame `x` to `R + K + Q`, `R` the
  item's own largest right edge. Every position is computed in place
  coordinates (§8.4): `Wb` = (`P` plus the largest right edge, a card's
  shadow (`+ 2`) included) − `Xl`, and `Hb` = (`P` plus the largest bottom
  edge, likewise) − `Yt`; the place origin `(Ox, Oy)` = (0 − `Xl`,
  0 − `Yt`) is added to every position last. Only in
  `bundle_ungrouped__places` does an item reach left of or above the
  padding; everywhere else `Xl` = `Yt` = 0 and the origin is (0, 0), so
  `Wb = P` plus the largest right edge and `Hb = P` plus the largest bottom
  edge. No drawing here requests a box size, so `W = Wb` and `H = Hb`.
- Font measures (§5.1) at size 9: `a(9)` = 8.35400390625, `d(9)` =
  2.12255859375, `h(9)` = 10.4765625; at size 11: `h(11)` = 12.8046875.
  With both wedges below and their labels at `u` = 0 and 1 in one tier,
  the root band below reaches `w / 2 + 13 + 2 + h(9)` = 26.9765625 for a
  line of width `w` = 3 (§6.4); a root whose end is open has only its start
  wedge and label, and its root band below reaches the same.
- A region band of one row is `pr − 4 × v` = 18.4765625 wide, `pr` = 6 + 2
  + `h(9)` + 4 = 22.4765625, whether or not its regions have drawn labels
  (§6.2). Below a root band of 26.9765625 it starts at 30.9765625, so the
  below side's outer edge is `Eb` = 49.453125.
- A timeline of unknown length is scaled to its reach `λ` (§3.4). A root's
  open end lies at `Xe = x0 + L`; its line runs on to `Xr = Xe + 4w` and
  the outer of its three chevrons has its tip, and the right edge, at
  `Xr + 5.5w`, `Xr` computed first (§6.6, §6.7): `(x0 + L + 12) + 16.5`
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
each row shows its id.

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

The root ("Flow control", 16 quarters) with a break, a jump and the marker
the jump targets.

- `N` = w(`Flow control`, 11) = 66.9775390625.
- `x0` = 16 + 66.9775390625 + 8 = 90.9775390625 → 90.9775; the jump label,
  centred on the midpoint 5 (`u` = 5/16), gives only −92.957763671875.
- `R` = the end label `16 ♩` at 490.9775390625 + 18.55810546875 / 2 =
  500.256591796875, beyond the arrowhead tip 499.9775390625.
- `Hm` = 84.33203125.
- `W` = 8 + 510.256591796875 = 518.256591796875; `H` = 8 + 94.33203125 =
  102.33203125.
- Page 550.256591796875 × 134.33203125 → **550.2566 × 134.332**.

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
map `ticks`, the region `intro` and the jump `da-capo`, styled by its own
statements: the root's line is 4 wide and its name, at size 12, reads
`Styled score`.

- `N` = max(w(`Styled score`, 12), w(`b`, 11)) = max(74.080078125,
  6.982421875) = 74.080078125.
- `x0` = 16 + 74.080078125 + 8 = 98.080078125 → 98.0801.
- `R` = the arrowhead tip `Xe + 3w` = 498.080078125 + 12 = 510.080078125.
- `Hm` = 54.640625 + 56.28125 + 8 = 118.921875.
- `W` = 8 + 520.080078125 = 528.080078125; `H` = 8 + 128.921875 =
  136.921875.
- Page 560.080078125 × 168.921875 → **560.0801 × 168.9219**.

## `nested__length-800-spacing-2`

`nested` with `L` = 800 and `v` = 2. The horizontal padding stays 8; the
padding above and below the content is `P × v` = 16.

- `x0` = 16 + 25.91552734375 + 8 = 49.91552734375 → 49.9155, as in
  `nested`.
- `R` = the end label `16 ♩` at 49.91552734375 + 800 + 9.279052734375 =
  859.194580078125.
- `Hm` = 86 + 26.9765625 + 16 = 128.9765625.
- `W` = 8 + 869.194580078125 = 877.194580078125; `H` = 8 + 138.9765625 =
  146.9765625.
- Page 909.194580078125 × 178.9765625 → **909.1946 × 178.9766**.

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
in the page of 1754) and the root `audio` (1323000 samples).

- `xn` = 24. `N` = w(`Exposition`, 11) = 57.0302734375.
- `x0` = the chevron term 24 + 57.0302734375 + 8 + 24 = 113.0302734375 →
  113.0303, set by the ancestor lines of `sonata` and `session`, which run
  on to the left; `page` starts with its member and does not.
- `R` = the end label `1323000 smp` at 513.0302734375 + 31.05615234375 =
  544.08642578125.
- `Hm` = 83.953125 for each of the three child members, 49.37890625 for
  `audio`; the frame is 358.04296875 high.
- `W` = 8 + 560.08642578125 = 568.08642578125; `H` = 8 + 366.04296875 =
  374.04296875.
- Page 600.08642578125 × 406.04296875 → **600.0864 × 406.043**.

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
to 8), the marker `marker_1` at 6 and the locked child `coda` (4 at 10).
No timeline has a name.

- The reach is the end of `coda`, 10 + 4 = 14, beyond the region's end 8
  and the marker 6, so `λ` = 14 and `u(t)` = `t / 14`, rounded once: `x(2)`
  = 110.94168526785714 → 110.9417, `x(10)` = 339.5131138392857 →
  339.5131. `coda` ends at 14, known, in its diamond at `x0 + L`.
- `N` = w(`score`, 11) = 29.798828125.
- `x0` = 16 + 29.798828125 + 8 = 53.798828125 → 53.7988; the start label
  `0 ♩` gives only 22.416015625.
- `R` = the outer chevron tip `Xr + 5.5w` = 465.798828125 + 16.5 =
  482.298828125. The root has no end wedge and no end label.
- `Hm` = 29 + 49.453125 + 8 = 86.453125: `coda` in the children band above
  (`Ea` = 21), the start wedge and the region band below.
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
length `null`, holding the region `region_1` (0 to 6).

- `λ` = 32, the root's length. The reach of `movement` on its own axis is
  6, so it ends under rule 5 of §3.4 at 8 + 6 = 14, open: `Xe` = `x(14)` =
  258.490234375, `Xr` = 270.490234375, the outer chevron's tip
  286.990234375. Its first-fit extent runs on `9.5w` past its end, to
  203.5.
- `N` = w(`movement`, 11) = 59.490234375.
- `x0` = 16 + 59.490234375 + 8 = 83.490234375 → 83.4902.
- `R` = the end label `32 ♩` at 483.490234375 + 9.279052734375 =
  492.769287109375, beyond the arrowhead tip 492.490234375.
- `Hm` = 29 + 49.453125 + 8 = 86.453125.
- `W` = 8 + (10 + 492.769287109375) = 510.769287109375; `H` = 8 + (10 +
  86.453125) = 104.453125.
- Page 542.769287109375 × 136.453125 → **542.7693 × 136.4531**.

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
- `Hm` = 71.85546875 (`performance`, its region band below) and
  49.37890625 (`score`); the frame is 8 + 12.8046875 + 4 + 71.85546875 + 8
  + 49.37890625 + 8 = 162.0390625 high.
- `W` = 8 + (531.140625 + 8 + 8) = 555.140625; `H` = 8 + (8 +
  162.0390625) = 178.0390625.
- Page 587.140625 × 210.0390625 → **587.1406 × 210.0391**.

## `unknown_length_segments`

The unlocked segment line `form` (quarters, length `null`) of three
segments, none a segment line and none named: `a` at 0, of length `null`,
holding the region `region_1` (0 to 4); `b` (6 at 8); `c` at 14, of length
`null`, holding the region `region_2` (0 to 3).

- The reach is the largest of 0 + 4, 8 + 6 and 14 + 3, so `λ` = 17. `a`
  ends where `b` starts (rule 3 of §3.4), and `c` where `form` ends (rule
  4), open. The three chevrons come before the open arrowhead of a
  segment line in §6.6.
- The boundaries of `b` and `c` lie at `x(8)` = 238.07562614889704 →
  238.0756 and `x(14)` = 379.2520967371323 → 379.2521, and reach `k` = 8
  to both sides, so the root band above is present and 8 wide (§6.4): `Ea`
  = 8 and `y_root` = 8 + 8 = 16 in the member drawing. No segment has a
  label.
- `N` = w(`form`, 11) = 25.84033203125.
- `x0` = 16 + 25.84033203125 + 8 = 49.84033203125 → 49.8403.
- `R` = the outer chevron tip 478.34033203125.
- `Hm` = 16 + 49.453125 + 8 = 73.453125: both regions in one row of the
  region band.
- `W` = 8 + (10 + 478.34033203125) = 496.34033203125; `H` = 8 + (10 +
  73.453125) = 91.453125.
- Page 528.34033203125 × 123.453125 → **528.3403 × 123.4531**.

## `bundle_ungrouped__places`

The box "Sketches" of three ungrouped roots, in drawing order the segment
line `pages` ("Pages", 5262 pixels, the segments `Page 1` to `Page 3` of
1754 each), the root `recording` ("Recording", 441000 samples) and the
root `score` ("Score", 16 quarters), with the place of `score` stated as
`{x: -60, y: -150, height: 120}`, left of and above the padding. Each card
is laid out on its own at its place, with its own `x0` and `R`; every
place not stated takes its default (§8.6). Every position below is in
place coordinates until the place origin is added, last (§8.4).

- Places (§8.6): `pages` at (8, 28.8046875), the first item, `P + h(11) +
  F` below the title; `recording` at (8, 100.2578125), `F` below the
  bottom edge `d` = 28.8046875 + 63.453125 = 92.2578125 of `pages`' card,
  its shadow not counted; `score` at (−60, −150), its card max(49.37890625,
  120) = 120 high. Every `length` is 400.
- `pages`: `xn` = 8 + 8 = 16; `x0` = 16 + w(`Pages`, 11) + 8 = 16 +
  32.85498046875 + 8 = 56.85498046875; `R` = the end label `5262 px` at
  456.85498046875 + 18.402099609375 = 475.257080078125; `Hm` = 28.4765625
  + 26.9765625 + 8 = 63.453125; the card spans x 8 to 483.257080078125 and
  y 28.8046875 to 92.2578125.
- `recording`: `xn` = 16; `x0` = 16 + w(`Recording`, 11) + 8 = 16 +
  55.70361328125 + 8 = 79.70361328125; `R` = the end label `441000 smp` at
  479.70361328125 + 28.193115234375 = 507.896728515625; `Hm` =
  49.37890625; the card spans x 8 to 515.896728515625 and y 100.2578125 to
  149.63671875.
- `score`: `xn` = −60 + 8 = −52; `x0` = −52 + w(`Score`, 11) + 8 = −52 +
  31.05029296875 + 8 = −12.94970703125; `R` = the end label `16 ♩` at
  387.05029296875 + 9.279052734375 = 396.329345703125; the card spans x
  −60 to 404.329345703125 and y −150 to −30.
- The title `Sketches`: `x` = 8, baseline 8 + `a(11)` = 8 +
  10.21044921875, right edge 8 + 49.951171875 = 57.951171875, slot ending
  at 8 + `h(11)` = 20.8046875.
- The box: `Xl` = min(0, −60 − 8) = −68 and `Yt` = min(0, −150 − 8) =
  −158, so `(Ox, Oy)` = (68, 158). `W` = (8 + (515.896728515625 + 2)) −
  (−68) = 593.896728515625 and `H` = (8 + (149.63671875 + 2)) − (−158) =
  317.63671875, both from `recording`'s shadow.
- Drawn, each position plus (68, 158): the shared starts 124.85498046875 →
  124.855 (`pages`), 147.70361328125 → 147.7036 (`recording`) and
  55.05029296875 → 55.0503 (`score`); the cards at (76, 186.8046875),
  (76, 258.2578125) and (8, 8); the boundaries of `pages` at `u` = 1/3 and
  2/3 → 258.1883 and 391.5216; the title at `x` 76 with its baseline at
  (8 + 10.21044921875) + 158 = 176.21044921875 → 176.2104. The shadow of
  `score`'s card ends 36 above the title's slot, and no card overlaps
  another or the title.
- Page 625.896728515625 × 349.63671875 → **625.8967 × 349.6367**.

## `styled__score__bands-timeline`

`styled__score` with the `bands` `{"score": ["flow", "children",
"regions"]}`: the root's own band order outranks `order`, which keeps its
default (§1, §6.4). Below the root, the flow band now lies next to the root
band and the region band beyond it; above, the children band follows the
root band as before, since the region and flow bands are absent there and
add no `B`.

- Band order: `flow`, `children`, `regions`, from the root's own id.
- Above, unchanged: the root band to 28.640625, the children band from
  max(28.640625 + 4, `p0 / 2` = 7) = 32.640625 to 46.640625 = `Ea`.
- Below: the root band to 7 (the map `ticks`); the flow band 11 to
  32.640625, the flow row at 62.640625 + 11 = 73.640625 → 73.6406 and the
  jump's apex at 81.640625; the region band 36.640625 to 56.28125 = `Eb`,
  the region's arms at 99.28125 → 99.2812. The two bands' widths swap, so
  `Eb` and the height stay those of `styled__score`.
- `x0` = 98.080078125 → 98.0801, `R` = 510.080078125, `Hm` = 118.921875,
  `W` = 528.080078125, `H` = 136.921875.
- Page 560.080078125 × 168.921875 → **560.0801 × 168.9219**.
