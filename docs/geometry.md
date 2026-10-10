# The geometry of a TimeSkeleton drawing

This document specifies how a TimeSkeleton document is drawn: the optional
`graphical` block of a document, the layout that turns a document into
**geometry** (`schema/geometry-<version>.schema.json`), and the two writers
that turn geometry into SVG and TikZ text. It is complete: two
implementations that follow it produce the same geometry, byte for byte
through the standard writer `dumps`, and the same SVG and TikZ text. The
golden fixtures under `fixtures/<version>/geometry/` pin it.

Version 0.3.0. Terms in `code` are JSON members; "the root" is the top-level
timeline a block draws.

## 1. Overview

A document is drawn as a column of **blocks**, one per top-level timeline,
in the canonical order of `manifest.timelines` (by id). A block is a
rectangle holding horizontal **rows**: the root timeline on row 0, child
timelines and conversion maps above it, regions and flow-control jumps below
it, flow-control breaks as vertical lines through the whole block, wedges
marking coordinates, and labels.

Layout is a pure function of the document. It measures no text and knows no
page: every horizontal position it writes is exact, every vertical position
is a row or an exact fraction of a row. Only the writers map positions to a
page, under one transform and one number formatting rule (section 8).

## 2. The `graphical` block

```json
"graphical": {
  "styles": [
    {"select": {"element": "label"}, "set": {"colour": "#404040"}}
  ],
  "timelines": {
    "perf": [
      {"select": {"element": "child", "domain": "physical", "modality": "discrete"}, "set": {"line_pattern": "dashed"}}
    ]
  }
}
```

The block is optional. An absent block, and a block without rules, draw
every element with its default style (section 4). Style rules are held by
**containers**: `styles` holds the rules of the document, the outermost
container; `timelines` holds, by timeline id, the rules of the container
formed by that timeline and all its descendants. A rule selects elements
of its container and sets properties on them; the order of the rules in a
list matters, so writers never reorder them. A rule list under the id of a
timeline the document does not hold selects nothing. (Later versions may
add containers, such as groups of timelines, beside `timelines`.)

### 2.1 Elements

Every drawn thing is an **element**. The attributes used for selection are:

- its **type**: `timeline` (the root of a block), `child` (a child timeline
  at any depth), `map` (a conversion map), `region`, `break`, `jump`,
  `wedge` (a coordinate marker) or `label` (a text label);
- its **id**, section 2.2;
- its **domain**, what its timeline's time measures: `graphical` (space on a
  page or an image), `logical` (musical time) or `physical` (clock time),
  from the class of the element's timeline (`ContinuousGraphicalTimeline`
  is graphical, and so on);
- its **modality**, whether its timeline is `continuous` or `discrete`,
  from the same class.

An element belongs to its **timeline**, listed in section 2.2, and through
it to the container of that timeline and of each of its ancestors, and to
the document.

### 2.2 Element ids

Timeline ids are unique within a document. Every other element id is
derived from a timeline id `T` and is compared as a whole string.

| Element | id | timeline |
|---|---|---|
| the root, or a child timeline `T` | `T` | `T` |
| conversion map with id `M` on `T` | `T/map/M` | `T` |
| the region at index `i` of `T`'s `regions` in canonical order | `T/region/i` | `T` |
| the break at index `i` of `T`'s `flow_control.breaks` in canonical order | `T/break/i` | `T` |
| the jump at index `i` of `T`'s `flow_control.jumps` in canonical order | `T/jump/i` | `T` |
| the wedges at the start and end of `T`'s line | `T/start`, `T/end` | `T` |
| the wedges projecting child `T`'s start and end onto the root | `T/projection/start`, `T/projection/end` | `T` |
| the name of an element with id `C` | `C/name` | that element's |
| the length of `T` | `T/length` | `T` |
| the coordinate text of a wedge with id `W` | `W/label` | that wedge's |
| the label of a region, jump or break with id `C` | `C/label` | that element's |

Indices count from 0. Canonical order is the order of the standard writer
(README, "Canonical order").

### 2.3 Selectors

A selector is an object with any of the members `element` (an element
type), `domain`, `modality` and `ids` (a non-empty list of element ids). An
element of the rule's container matches a selector when it matches every
member present: equal type, domain and modality, and an id contained in
`ids`. The empty selector `{}` matches every element of the container.

### 2.4 Properties

| Property | Values | Read by element types |
|---|---|---|
| `colour` | `#RRGGBB`, upper-case hexadecimal | all |
| `line_pattern` | `solid`, `dotted`, `dashed` | `timeline`, `child`, `map`, `region`, `break`, `jump` |
| `visible` | `true`, `false` | all |
| `side` | `above`, `below` | `child`, `map`, `region`, `jump`, `wedge`, `break` (where its label goes), `label` (a length label only) |
| `show_length` | `true`, `false` | `timeline`, `child` |
| `show_projected_coordinates` | `true`, `false` | `child` |

A rule may set any property on any element; an element ignores the
properties its type does not read. `visible: false` is the filter: an
element that is not visible is not drawn and takes no row.

### 2.5 The cascade

The cascade is resolved **per property**: for each element and each
property it reads, the value is set by the highest-ranking matching rule
**that sets this property**; rules that match but do not set it are passed
over, so a property no rule of the nearest container sets falls through to
the rules of the containers enclosing it, as in CSS. When no matching rule
of any container sets the property, the default of section 4 applies.

The rank of a matching rule is, from the most to the least significant:

1. whether its selector names the element's id (`ids`): a rule naming the
   element outranks every rule that does not, in any container;
2. the depth of its container: the nearest container (the timeline closest
   to the element among those whose subtree holds it) outranks the ones
   enclosing it, and every timeline outranks the document. The document has
   depth 0, a root timeline depth 1, its children depth 2, and so on;
3. whether its selector names the element type (`element`): within one
   container, a rule naming the type outranks a rule naming only the domain
   and/or the modality;
4. the number of members among `domain` and `modality` its selector names:
   more named members outrank fewer, so type plus domain outranks type
   alone, and domain plus modality outranks domain alone;
5. its position: between rules equal in 1 to 4, the later one in its list
   wins.

## 3. Numbers

### 3.1 Positions along the root

A horizontal position derived from time is a value on the **root's axis**,
written in the JSON number forms of the document:

- a value computed only from integers and Fractions is **exact**. It is
  written as a JSON integer when the root's `number_type` is `int` and the
  value is an integer, and otherwise as a Fraction pair `[numerator,
  denominator]` in lowest terms with a positive denominator (so `[4, 1]` on
  a `fraction` axis);
- a value computed with any float is a **float**, written as a JSON float.

Values combine as Python's numeric tower combines them: the sum of two exact
values is exact; a sum involving a float converts each exact operand to the
nearest double (ties to even) and adds in IEEE 754 binary64 arithmetic with
rounding to nearest, ties to even. Comparisons are exact: a float compares by
its exact binary value. A midpoint `(a + b) / 2` is the tower sum `a + b`
followed by an exact division by 2 (for a float, a division by 2 in binary64).

A coordinate's value is read as its number type selects: a `float` value
is a float; an `int` or `fraction` value is exact (an integral JSON number in
it counts as the integer it equals, as the library reads it).

The position of a child timeline is computed downwards from the root: the
root starts at 0 (in the root's number type: `0`, `0.0` or `[0, 1]`) and
ends at its length; a child of a timeline starting at `s` with `offset`
value `o` starts at `s + o` and ends at that start plus its own length. The
sums are taken in this order, from the root down. A region, break or jump of
a timeline starting at `s` lies at `s` plus its coordinate.

### 3.2 Vertical positions

Rows are integers: 0 is the root's row, positive rows lie above it and
negative rows below. A **row band** `r` covers the vertical interval
`[r − 1/2, r + 1/2]`, its line at `r`. Every vertical position of the
geometry except `row` and `rows.min` / `rows.max` is an exact value in row
units, written as a Fraction pair in lowest terms, integral ones included
(`[1, 1]` is row 1, `[-1, 8]` one eighth of a row below row 0).

### 3.3 The frame

The horizontal extent of a block is its **frame**, measured in abstract
units (proportions) from its origin at the block's bottom-left corner. It
holds two extents, each an `offset` and a `length`: `names`, the name
column, at offset 0, and `plot`, the plot area, right after it. The root is
placed in the plot area by a `LinearMap` from the root's unit to `number`
(`placement`, the document schema's definition).

- The frame's numbers are floats when the root's number type is `float`,
  and Fraction pairs otherwise.
- The plot area's length `P` is the root's length (an `int` length `n`
  becomes `[n, 1]`).
- The name column's length `N` is `P / 4`, or 1 when `P` is 0.
- The frame's length is `N + P`; the plot area's offset is `N`.
- `placement` is `{"type": "LinearMap", "id": "placement", "name": null,
  "source_unit": <root unit>, "target_unit": "number", "scalar": 1,
  "offset": 0}`, with `scalar` and `offset` written as `[1, 1]` and `[0, 1]`
  for Fraction frames and as `1.0` and `0.0` for float frames.

A root position `x` lies at frame position `plot.offset + scalar × x +
offset`. The frame is written `{"length", "names": {"offset", "length"},
"plot": {"offset", "length"}}`.

### 3.4 Converting a frame to a graphical timeline

A frame is not a timeline, but it converts to one, so that blocks can be
placed and aligned on a figure as graphical timelines. Given a graphical
unit `u` (`points`, `millimeters`, …) and a scale `k` (units of `u` per
abstract unit), the frame is a `ContinuousGraphicalTimeline` in unit `u` of
length `k × length`, with two child segments of the same class and unit:
the name column at offset `k × names.offset` of length `k × names.length`,
and the plot area at offset `k × plot.offset` of length `k × plot.length`.
The root timeline maps to the plot area segment by `placement` followed by
the scale `k`. The number type of the timeline and its segments is the
frame's (`fraction` or `float`). This specification defines no converter;
writers use the frame directly (section 8.1).

## 4. Defaults

| Property | Default |
|---|---|
| `colour` | `label`: `#000000`; every other element type: the colour of its domain, graphical `#FF0000`, logical `#00CC00`, physical `#0050EF` |
| `line_pattern` | `timeline`, `child`: `solid` when continuous, `dotted` when discrete; `jump`: `dotted`; `map`, `region`, `break`: `solid` |
| `visible` | `true` |
| `side` | `child`, `map`: `above`; `region`, `jump`, `wedge`, `break`: `below`; `label`: `above` |
| `show_length` | `false` |
| `show_projected_coordinates` | `false` |

The block's background colour is `#BAC8D3`; no style rule changes it.

## 5. Text

### 5.1 Coordinate labels

A coordinate is labelled with the text of its value, a space (U+0020) and
the symbol of its unit. The text of a value is its JSON form: an integer in
decimal (`96`), a Fraction pair `[n, d]` as `n/d` (`3/2`), or `n` when `d` is
1; a float as the standard writer spells it, which is Python's `repr`
(`1.5`, `6.0`, `1e-05`).

| Unit | Symbol |
|---|---|
| `quarters` | `♩` (U+2669) |
| `seconds` | `s` |
| `samples` | `smp` |
| `ticks` | `ticks` |
| `pixels` | `px` |
| any other unit | the unit's name (`points`, `whole_note`, …) |

### 5.2 Names

The name of a timeline or a conversion map is its `name`, or its `id` when
`name` is null. A region's label is its `name`; a jump's label is its
`label`, or its `control_type` when `label` is null; a break's label is its
`label`, and a break whose `label` is null has none.

## 6. Layout

`layout(document)` returns `{"meta": {"schema_version": "0.3.0"},
"blocks": [...]}`, one block per top-level timeline in canonical order. The
document is read in canonical order whatever order it was written in.

### 6.1 Traversal

The **traversal** of a block lists its timelines in pre-order: the root, then
each child in canonical order (by offset, then id), each followed by its own
descendants. Every timeline in the traversal has a start and an end on the
root's axis (section 3.1).

### 6.2 Rows

Each side of the root (above, positive rows; below, negative rows) is
filled outwards in four **bands**, in this order: children, maps, regions,
jumps. Each band has a list of elements, given below, and places them one
at a time, in the order of that list whatever their side, by **first fit**:
an element goes to the row nearest the root, at or beyond the band's first
distance on its side and its own minimum, holding no element of the same
band whose extent **conflicts** with its own. The **first distance** of a
band on a side is one more than the largest distance any earlier band took
on that side, or 1 when none took one. A distance `d` on a side is the row
`d` above or `-d` below. Two extents `[a1, b1]` and `[a2, b2]` conflict when
`a1 < b2` and `a2 < b1`, or when `a1 = a2`. So a child that starts where
another ends shares its row, and two elements starting at the same point
never do.

1. **Children.** Every child in traversal order, if visible, on its `side`.
   Its extent is `[start, end]`. Its minimum distance is one more than its
   parent's **anchor** on that side. The
   anchor of the root is 0 on both sides; a placed child's anchor on its own
   side is its distance, and every other anchor of a child is its parent's.
   So a nested child is drawn beyond its parent when both are on one side.
2. **Maps.** The conversion maps of every timeline in traversal order, each
   timeline's maps in canonical order (by id), if visible, on their `side`.
   A map's extent is its timeline's `[start, end]`.
3. **Regions.** The regions of every timeline in traversal order, each
   timeline's regions in canonical order, if visible, on their `side`. The
   extent is `[min(start, end), max(start, end)]` of the region's start and
   end on the root's axis.
4. **Jumps.** The jumps of every timeline, each timeline's in canonical
   order, are first listed in traversal order and then sorted stably by span,
   smallest first. The span is the exact difference `max − min` of the
   exact values of their from and to positions (a float position counts by
   its exact binary value; no binary64 subtraction is involved). Each
   visible jump is placed on its `side` with extent `[min, max]`. Sorting by
   span makes a jump enclosing another lie further out.

The **placement order** of a band is the order of its list above, whatever
the side.

The block's `rows` are `{"min": m, "max": M}`: the smallest and largest row
taken, with 0 always included.

### 6.3 Primitives

The block's `primitives` list is written in this order:

1. **break** primitives, in traversal order, each timeline's breaks in
   canonical order: `{kind, id, timeline, at, bottom, top, colour,
   line_pattern}`, `at` the break's position, `bottom` = `m − 1/2`, `top` =
   `M + 1/2`.
2. **map** primitives in placement order: `{kind, id, timeline, row, start,
   end, colour, line_pattern}`, start and end those of the map's timeline.
3. **region** primitives in placement order: `{kind, id, timeline, row,
   side, start, end, base, apex, colour, line_pattern}` with `o` = 1 above
   and −1 below: `base` = `r − o/4`, `apex` = `r − o/8`. The brace's arms
   end at `base` (towards the root) and its tip is at `apex`.
4. **jump** primitives in placement order: `{kind, id, timeline, row, side,
   from, to, base, apex, colour, line_pattern}`. With `j` the first distance
   of the jump band on the jump's side, `base` = `o × (j − 1/2)` and `apex` =
   `r − o/8`. The arc leaves `from` and arrives at `to`, both at `base`, and
   reaches `apex` between them.
5. the **timeline** primitive of the root, if visible, then the **child**
   primitive of every placed child in traversal order: `{kind, id, timeline,
   row, start, end, colour, line_pattern}`.
6. **wedge** primitives: for each line of step 5 in order, a wedge at its
   start and one at its end, each if visible; then, for every child in
   traversal order whose `show_projected_coordinates` is true, the two
   projection wedges on row 0, each if visible:
   `{kind, id, timeline, row, side, at, tip, base, colour}`, `tip` = `r`,
   `base` = `r − 1/8` below and `r + 1/8` above.
7. **label** primitives: first the name column, one label per row that
   holds lines or maps, from the top row down; then the length labels of
   the lines in line order, the wedge labels in wedge order, the region
   labels in region order, the jump labels in jump order and the break labels
   in break order:
   `{kind, id, timeline, at, anchor, text, colour}` (and `rotate`, which
   layout never writes), `at` = `{"space", "x", "y"}`.

Every primitive's `colour` and `line_pattern` (where present) are the
cascaded values of its element. A primitive's `id` and `timeline` are
those of its element.

### 6.4 Wedges and labels

- A line's wedges exist only when the line is drawn. The wedge at a line's
  start shows the timeline's own start, 0 in its own number type (`0`, `0.0`,
  `[0, 1]`); the wedge at its end shows its own `length`. Both are labelled
  in the timeline's own unit (section 5.1). Their `at` is the line's start
  and end on the root's axis.
- A projection wedge exists when its child's `show_projected_coordinates`
  is true, whether or not the child is drawn. It sits on row 0 at the
  child's start or end on the root's axis and is labelled with that value
  in the root's unit.
- A wedge label is drawn when its wedge is drawn and the label is visible:
  `at` = the wedge's `at` and `base`, anchor `north` below and `south` above.
- A length label is drawn when the line is drawn, its `show_length` is true
  and the label is visible: `at` = the line's midpoint and row, anchor
  `south` when the label's `side` is above and `north` when below; its text
  is the coordinate label of the timeline's `length`.
- A region's or jump's label is drawn when its owner is drawn and the label
  is visible: `at` = the midpoint of the owner's start and end (from and to)
  and its `apex`, anchor `south` above and `north` below.
- A break's label is drawn when the break is drawn, has a label (section
  5.2) and the label is visible. It sits at the end of the break's line on
  the break's `side`: below (the default), `at` = the break's position and
  its `bottom`, anchor `north`; above, its `top`, anchor `south`. It lies
  outside the block's rectangle, which the page margins hold.
- **The name column.** For each row, the drawn lines and maps of the row,
  in primitive order, whose name labels are visible contribute their names
  (section 5.2); the row's label text is those names joined by `, `. It is
  written when at least one name contributes: `at` = `{"space": "frame",
  "x": 0, "y": [r, 1]}` with `x` the frame's zero (`[0, 1]` or `0.0`),
  anchor `west`; its `id`, `timeline` and `colour` are those of the first
  contributing name label.

Every other label has `"space": "root"`: its `x` is a position on the root's
axis.

## 7. Geometry

The geometry document validates against `schema/geometry-0.3.0.schema.json`:

```json
{
  "meta": {"schema_version": "0.3.0"},
  "blocks": [
    {
      "id": "<root id>",
      "frame": {"length": [10, 1], "names": {"offset": [0, 1], "length": [2, 1]}, "plot": {"offset": [2, 1], "length": [8, 1]}},
      "placement": {"type": "LinearMap", "id": "placement", "...": "..."},
      "rows": {"min": -1, "max": 2},
      "background": "#BAC8D3",
      "primitives": [{"kind": "timeline", "...": "..."}]
    }
  ]
}
```

The members of every object are written in the order this document lists
them. A primitive's `kind` names the element type it draws; it is the
discriminator of the list of primitives, an open union: a later version may
add primitives with another `kind`, and a reader ignores a primitive whose
`kind` it does not know.

## 8. Writers

### 8.1 The page

Writers place blocks on a page measured in **page units** (pixels in SVG,
points in TikZ). Two options choose the scale: `width` (default 400), the
width of every block, and `row_height` (default 32), the height of a row.
Option names follow each language's convention (`row_height` in Python,
`rowHeight` in TypeScript). Every other measure is fixed:

| Measure | Page units |
|---|---|
| gap between blocks | 16 |
| SVG margin around the page | 16 |
| line width | 0.8 |
| font size | 7 |
| label inner separation | 2 |
| circle diameter (line start) | 4 |
| open diamond (child end): length, width | 6, 4 |
| stealth (root end, jump end): length, width, inset | 6, 4, 2 |
| wedge base width | 6 |
| map rectangle height | 4 |
| character width (name column) | 4.2 (0.6 of the font size) |

Blocks are stacked from the top in block order. Block `k` has height
`H_k = (M_k − m_k + 1) × row_height`; its top lies `T_k = Σ_{j<k} (H_j +
16)` below the top of the page, and the page is `S = Σ H_k + 16 × (n − 1)`
high (0 for no block).

With `F` the frame's length, the page abscissa of a frame position `f` is
`f × width / F`, and of a root position `x` it is that of the frame position
`plot.offset + scalar × x + offset` (section 3.3). The page ordinate of a vertical
position `y` (rows) is, in SVG (downwards) `T_k + (M_k + 1/2 − y) ×
row_height`, and in TikZ (upwards) `S − T_k − H_k + (y − m_k + 1/2) ×
row_height`.

All of this is computed **exactly**: a float in the geometry enters as its
exact binary value, and every page coordinate is an exact rational until it
is written.

### 8.2 Number formatting

Every number a writer writes is formatted by one rule: take the exact
value, round it to the nearest multiple of 1/10000, ties to the even
multiple; write it in decimal without exponent, with no leading `+`, with
the integer part (`0` when it is zero) and, when the rounded value is not an
integer, a point and its fractional digits without trailing zeros. A value
that rounds to zero is written `0`, never `-0`. Examples: `80`, `12.5`,
`0.3333`, `-6`, `0.0002` for 0.00025, `0.0004` for 0.00035.

### 8.3 Text in writers

Every code point from U+0000 to U+001F in a label becomes a space. A
name-column label (space `frame`) holds at most `c = ⌊(names.length × width / F − 4) /
4.2⌋` code points: a longer text is cut to its first `c − 1` code points
followed by `…` (U+2026), and the label is not written when `c` is less
than 1.

A label at page point `(X, Y)` is a node anchored at that point, as TikZ
anchors it, with the inner separation of 2. Horizontally, an anchor
containing `west` puts the text's start at `X + 2`, one containing `east`
puts its end at `X − 2`, and any other centres it on `X`. Vertically (in
SVG's downward ordinate) the text baseline lies at `Y + 7.25` for `north`,
`north west` and `north east`; at `Y − 3.75` for `south`, `south west` and
`south east`; at `Y` for `base`, `base west` and `base east`; and at
`Y + 1.75` for `center`, `east`, `west`, `mid`, `mid west` and `mid east`.
A label with `rotate` `θ` is rotated by `θ` degrees counter-clockwise about
`(X, Y)`.

### 8.4 SVG profile

The output is UTF-8, one element per line, no indentation, final newline:

```
<svg xmlns="http://www.w3.org/2000/svg" width="{W+32}" height="{S+32}" viewBox="-16 -16 {W+32} {S+32}" font-family="DejaVu Sans, sans-serif" font-size="7">
...
</svg>
```

Per block, the background
`<rect x="0" y="{T}" width="{W}" height="{H}" fill="#BAC8D3"/>`, then each
primitive. Below, `(X, Y)` are page coordinates, `c` the colour, `{dash}` is
empty for `solid`, ` stroke-dasharray="0.8 1"` for `dotted` and
` stroke-dasharray="3 3"` for `dashed`, and `{stroke}` is
`stroke="{c}" stroke-width="0.8"{dash}`. Path data is written as an
upper-case command letter followed by its coordinates, every number
separated from the next by one space and no space before a command letter
(`M80 16L74 14`).

| Primitive | Elements |
|---|---|
| timeline | `<line x1="{Xs}" y1="{Y}" x2="{Xe − 4}" y2="{Y}" {stroke}/>`, `<circle cx="{Xs}" cy="{Y}" r="2" fill="{c}"/>`, `<path d="M{Xe} {Y}L{Xe−6} {Y−2}L{Xe−4} {Y}L{Xe−6} {Y+2}Z" fill="{c}"/>` |
| child | `<line x1="{Xs}" y1="{Y}" x2="{Xe − 3}" y2="{Y}" {stroke}/>`, `<circle cx="{Xs}" cy="{Y}" r="2" fill="{c}"/>`, `<path d="M{Xe−3} {Y}L{Xe} {Y−2}L{Xe+3} {Y}L{Xe} {Y+2}Z" fill="none" stroke="{c}" stroke-width="0.8"/>` |
| map | `<rect x="{min(Xs, Xe)}" y="{Y − 2}" width="{abs(Xe − Xs)}" height="4" fill="none" {stroke}/>` |
| region | `<path d="{brace}" fill="none" {stroke}/>` |
| jump | `<path d="M{P0}C{C1} {C2} {P3}" fill="none" {stroke}/>` and the stealth at `P3` |
| break | `<line x1="{X}" y1="{Y(top)}" x2="{X}" y2="{Y(bottom)}" {stroke}/>` |
| wedge | `<path d="M{X} {Y(tip)}L{X−3} {Y(base)}L{X+3} {Y(base)}Z" fill="{c}"/>` |
| label | `<text x="{x}" y="{baseline}" text-anchor="{start|middle|end}"{ transform="rotate({−θ} {X} {Y})"} fill="{c}">{text}</text>` |

In text, `&`, `<` and `>` are written `&amp;`, `&lt;` and `&gt;`.

**The brace** of a region from `X1` (start) to `X2` (end) with arms at
`Yb` (page of `base`) and tip at `Ya` (page of `apex`): with `Ym = (Yb +
Ya) / 2`, `k = |Ya − Yb| / 2` and `Xm = (X1 + X2) / 2`, the path is
`M X1 Yb Q X1 Ym X1+k Ym L Xm−k Ym Q Xm Ym Xm Ya Q Xm Ym Xm+k Ym L X2−k Ym
Q X2 Ym X2 Yb`, written in the path data form above.

**The jump arc** from `P0` = (page of `from`, page of `base`) to `P3` =
(page of `to`, page of `base`) is the cubic Bézier curve with controls `C1`
= (page of `from`, `Yc`) and `C2` = (page of `to`, `Yc`), `Yc` the page of
`base + 4/3 × (apex − base)`, so that it reaches `apex` halfway. The stealth
at `P3 = (X, Y)` points away from `C2`: up (`C2` below `P3` on the page) as
`<path d="M{X} {Y}L{X−2} {Y+6}L{X} {Y+4}L{X+2} {Y+6}Z" fill="{c}"/>`, down as
`<path d="M{X} {Y}L{X−2} {Y−6}L{X} {Y−4}L{X+2} {Y−6}Z" fill="{c}"/>` (SVG
ordinates).

### 8.5 TikZ profile

The picture uses TikZ with the `arrows.meta` library; coordinates are bare
numbers in points. With `standalone` (the default) the output is a complete
LuaLaTeX document:

```
\documentclass{standalone}
\usepackage{fontspec}
\setsansfont{DejaVu Sans}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\begin{document}
\begin{tikzpicture}[x=1pt,y=1pt,line width=0.8pt,inner sep=2pt,font=\sffamily\fontsize{7}{8.4}\selectfont]
\definecolor{ts00CC00}{HTML}{00CC00}
...
\end{tikzpicture}
\end{document}
```

Without it, the output is the `tikzpicture` environment alone; the
including document loads TikZ, `arrows.meta` and a sans-serif font that has
`♩` (U+2669). Every line ends with a newline. The colours defined are those
of every block's background and of every primitive of a known `kind`,
including a label the writer leaves out (section 8.3); each is defined once,
right after `\begin{tikzpicture}`, as `\definecolor{ts<RRGGBB>}{HTML}{<RRGGBB>}`,
sorted by its hexadecimal digits. `{c}` stands for `ts<RRGGBB>`, `{pattern}` for `,densely dotted`
(dotted), `,dashed` (dashed) or nothing (solid).

| Primitive | Command |
|---|---|
| background | `\fill[tsBAC8D3] (0,{Ybottom}) rectangle ({W},{Ytop});` |
| timeline | `\draw[{c}{pattern},{Circle[length=4pt]}-{Stealth[length=6pt,width=4pt,inset=2pt]},shorten <=-2pt] ({Xs},{Y}) -- ({Xe},{Y});` |
| child | `\draw[{c}{pattern},{Circle[length=4pt]}-{Diamond[open,length=6pt,width=4pt]},shorten <=-2pt,shorten >=-3pt] ({Xs},{Y}) -- ({Xe},{Y});` |
| map | `\draw[{c}{pattern}] ({Xs},{Y−2}) rectangle ({Xe},{Y+2});` |
| region | the brace, below |
| jump | `\draw[{c}{pattern},-{Stealth[length=6pt,width=4pt,inset=2pt]}] ({P0}) .. controls ({C1}) and ({C2}) .. ({P3});` |
| break | `\draw[{c}{pattern}] ({X},{Y(bottom)}) -- ({X},{Y(top)});` |
| wedge | `\fill[{c}] ({X},{Y(tip)}) -- ({X−3},{Y(base)}) -- ({X+3},{Y(base)}) -- cycle;` |
| label | `\node[anchor={anchor}{,rotate=θ},text={c}] at ({X},{Y}) {{text}};` |

The shortenings centre the circle on the start and the diamond on the end,
so a contiguous successor's filled circle is drawn over its predecessor's
open diamond.

**The brace** in TikZ is the SVG brace of section 8.4 in TikZ ordinates,
written as one path starting at its first point and continuing segment by
segment, each part separated from the next by one space:

```
\draw[{c}{pattern}] (X1,Yb) .. controls (A1) and (B1) .. (X1+k,Ym) -- (Xm−k,Ym) .. controls (A2) and (B2) .. (Xm,Ya) .. controls (A3) and (B3) .. (Xm+k,Ym) -- (X2−k,Ym) .. controls (A4) and (B4) .. (X2,Yb);
```

Each quadratic segment `Q C P` of the SVG path, drawn from the **current
point** `P0` (the end of the previous segment, or the first point), becomes
the cubic with controls `A = P0 + 2/3 × (C − P0)` and `B = P + 2/3 × (C − P)`;
each `L P` becomes `-- (P)`.

In text, `\` becomes `\textbackslash{}`, `~` becomes `\textasciitilde{}`,
`^` becomes `\textasciicircum{}`, and each of `# $ % & _ { }` is preceded by
`\`.
