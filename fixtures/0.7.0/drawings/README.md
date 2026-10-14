# Hand-derived drawings

Twelve of the 46 drawings in this directory are derived by hand from the
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

## Shared quantities

Every file is drawn as a bundle (§8): the nine timeline files as an
anonymous bundle holding one ungrouped root in its card, the three group
files as an anonymous bundle holding one frame. None has a title.

- Constants (§6.2): padding `P` = 8 (`P × v` above and below a member
  drawing's content), card padding `K` = 8, frame padding `Q` = 8, gap
  between cards `F` = 8, gap after the names `G'` = 8 whenever a name is
  drawn, card shadow offset 2.
- The name column (§8.2) starts at `xn = P + K` = 16 without a frame and at
  `xn = P + Q + K` = 24 with one. `N` is the widest row name of any member
  drawing; a group's title is not a row name.
- The shared start (§8.2) is the largest of `xn + N + G'`, of
  `xn + wi / 2 − L × ui` for every centred label `i`, and of
  `xn + N + G' + 8 × wa` for every ancestor line `a` that runs on to the
  left. Each candidate is listed below only when it decides or comes
  close.
- An ungrouped card spans `x = P` to `R + K`; in a frame, a card spans
  `x = P + Q` to `R + K` and the frame `x = P` to `R + K + Q`. `Wb = P` plus
  the largest right edge, a card's shadow (`+ 2`) included; `Hb = P` plus
  the largest bottom edge, likewise (§8.4). No drawing here requests a box
  size, so `W = Wb` and `H = Hb`.
- Font measures (§5.1) at size 9: `a(9)` = 8.35400390625, `d(9)` =
  2.12255859375, `h(9)` = 10.4765625; at size 11: `h(11)` = 12.8046875.
  With both wedges below and their labels at `u` = 0 and 1 in one tier,
  the root band below reaches `w / 2 + 13 + 2 + h(9)` = 26.9765625 for a
  line of width `w` = 3 (§6.4).

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
`phrase` ("Phrase", 4 at 2) with the map `ticks`.

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
  `x0 + L + 8w` = 535.70361328125.
- `Hm` = 82.953125 + 26.9765625 + 8 = 117.9296875 (`theme`, two ancestor
  rows above) and 49.37890625 (`recording`); the frame is 208.11328125
  high.
- `W` = 8 + 551.70361328125 = 559.70361328125; `H` = 8 + 216.11328125 =
  224.11328125.
- Page 591.70361328125 × 256.11328125 → **591.7036 × 256.1133**.
