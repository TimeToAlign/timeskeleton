# Drawing a TimeSkeleton manifest

This specification states how one TimeSkeleton manifest is drawn: the
`graphical` block of style statements (section 2), the arithmetic of
positions (section 3), the default style (section 4), the font that
measures every text (section 5), the layout that turns a manifest into a
**drawing** (section 6), and the writers that serialize a drawing as SVG and
TikZ text (section 7). Two implementations that follow it draw the same
manifest, with the same inputs, as the same SVG and TikZ text, byte for
byte.

A drawing is derived and never stored: there is no drawing schema, and no
JSON form of a drawing is exchanged. This specification pins the drawing.

This version specifies the drawing of one manifest: its top-level timeline,
called **the root**, with all its descendants. How several manifests are
arranged together, in timeline groups and alignment bundles, is not
specified yet. Terms in `code` are JSON members.

## 1. Inputs and output

`draw(manifest, placement, layers, metrics)` returns the manifest's drawing.

- `manifest`: a manifest, read in canonical order (README, "Canonical
  order") whatever order it was written in.
- `placement`: chosen by whoever places the drawing, such as an editor's
  canvas or a script:
  - `length`, the **graphical length** `L` of the root, in canvas units
    (default 400): the distance from the root's start to its end;
  - `spacing`, the **vertical stretch** `v`, a positive number (default 1)
    that multiplies the vertical distances of section 6.2;
  - `width` and `height`, the requested **box size** in canvas units, or
    `null` (the default) for the content's own size;
  - `order`, the **band order**: the groups `children`, `maps`, `regions`
    and `flow`, each once, in the order their bands lie outwards from the
    root on either side (default `["children", "maps", "regions",
    "flow"]`; section 6.4). An editor changes it by dragging a group.
- `layers`: the statement lists that style the drawing, from the lowest to
  the highest precedence: the defaults of section 4, then any lists an
  application supplies (such as an editor's settings), then the manifest's
  own `graphical` block, then the overrides of whoever places the drawing.
  Section 2 defines them.
- `metrics`: the advance widths of the font of section 5.

The drawing is a **box** of width `W` and height `H` and a list of drawn
**elements** in box-local canvas units, origin at the box's top-left corner,
y downwards. Every element carries its **address** (section 2.2) and, where
it shows a coordinate, the exact coordinate it shows. Canvas units become
pixels in SVG and points in TikZ (section 7).

A drawing does not depend on its position on a canvas, nor on its zoom: a
canvas or a writer places the box at a position and scales it uniformly by
a **zoom** factor `z` (section 7.1). The three ways of resizing a drawing
change one input each:

| Resize | Input changed | Effect |
|---|---|---|
| Scale | zoom `z` | everything scales, proportions kept, text included |
| Box | `width`, `height` | only the box changes; the content keeps its place at the top left; the box never becomes smaller than the content (section 6.7) |
| Stretch | `length` (horizontal), `spacing` (vertical), both (a corner) | distances stretch: along time horizontally, between rows and bands vertically; markers, line widths and text keep their size |

## 2. The `graphical` block

```json
"graphical": {
  "styles": {
    "highlight": {"stroke": "#7F00FF", "fill": "#7F00FF"}
  },
  "statements": [
    {"select": {"element": "label"}, "set": {"fill": "#404040"}},
    {"select": {"element": "wedge", "within": "performance"}, "set": "highlight"},
    {"select": {"ids": ["performance/region/0"]}, "set": {"display": "none"}}
  ]
}
```

The block is optional; an absent block draws with the other layers alone.
`styles` maps a style name to a **declaration**, an object of properties
(section 2.4) and their values. `statements` is a list of **statements**,
each a selector (`select`, section 2.3) and either a declaration or the name
of a style in the same layer's `styles` (`set`). The order of the
statements matters, so writers never reorder them. Every layer of section 1
has this shape.

A reader that meets statements naming styles its `styles` does not hold
issues one warning naming every missing style, and adds each to `styles` as
an empty declaration; such a statement then sets nothing, and the block is
valid.

### 2.1 Elements

Every drawn thing is an **element** of one **type**:

| Type | What it is |
|---|---|
| `block` | the box's background |
| `timeline` | the root's line |
| `child` | a child timeline's line, at any depth |
| `map` | a conversion map, drawn as a double line |
| `region` | a region, drawn as a brace |
| `break` | a flow-control break, drawn as a vertical line |
| `jump` | a flow-control jump, drawn as an arc with an arrowhead |
| `wedge` | a marker of a coordinate of the root's own: its start and its end |
| `name` | the name of a row, in the name column |
| `label` | any other text: a coordinate, or the label of a region, jump or break |

An element **belongs** to a timeline (section 2.2); the `block` belongs to
none. An element has the **domain** (`graphical`, `logical` or `physical`)
and the **modality** (`continuous` or `discrete`) of its timeline's
`class` (`ContinuousGraphicalTimeline` is continuous and graphical, and so
on). A map and its name and label instead have the domain and modality of
the map's `target_unit`, so a map is drawn in the style of the timelines it
converts to:

| Domain | Units |
|---|---|
| `logical` | `floating_measures`, `whole_note`, `quarters`, `ticks` |
| `physical` | `milliseconds`, `seconds`, `minutes`, `samples`, `frames` |
| `graphical` | `pixels`, `meters`, `centimeters`, `millimeters`, `inches`, `points` |

`ticks`, `samples`, `frames` and `pixels` are discrete, every other unit
continuous. A map whose `target_unit` is null or not in the table has no
domain and no modality, so no selector naming them matches it and it
inherits its timeline's style (section 2.5). An element's **class** is its
timeline's `class`, except that a map and its name and label have the map's
`type` (`QuartersToTicks`, …).

Elements form a **tree** that carries inheritance (section 2.5): the
`block` holds the `timeline`; a `timeline` or `child` holds its maps,
regions, breaks, jumps, wedges and child timelines; an element holds its
own `name` and `label` where it has one (section 5.3; a map has a name and
no label).

### 2.2 Addresses

Timeline ids are unique within a manifest. Every other address is derived
from a timeline id `T` and is compared as a whole string. Indices count
from 0, in canonical order.

| Element | Address | Belongs to |
|---|---|---|
| the root, or a child timeline `T` | `T` | `T` |
| conversion map with id `M` on `T` | `T/map/M` | `T` |
| the region at index `i` of `T`'s `regions` | `T/region/i` | `T` |
| the break at index `i` of `T`'s `flow_control.breaks` | `T/break/i` | `T` |
| the jump at index `i` of `T`'s `flow_control.jumps` | `T/jump/i` | `T` |
| the root's wedges at its start and end | `T/start`, `T/end` | `T` |
| the name of an element with address `C` | `C/name` | that element's timeline |
| the label of an element with address `C` | `C/label` | that element's timeline |

The block has no address.

### 2.3 Selectors

A selector is an object with any of these members:

- `element`: an element type;
- `ids`: a non-empty list of distinct addresses;
- `domain`, `modality`: a domain, a modality;
- `class`: a timeline class or a conversion-map type;
- `within`: a timeline id; it matches the elements belonging to that
  timeline or to any of its descendants.

An element matches a selector when it matches every member present. The
empty selector `{}` matches every element.

### 2.4 Properties

Presentation properties carry SVG's names and values; the writers map them
to TikZ (section 7.4).

| Property | Values | Inherited | Read by |
|---|---|---|---|
| `stroke` | `#RRGGBB` (upper-case) or `none` | yes | every type but `block`, `name` and `label` |
| `stroke-width` | a number ≥ 0 | yes | as `stroke` |
| `stroke-dasharray` | `none`, or numbers separated by single spaces | yes | as `stroke` |
| `fill` | `#RRGGBB` or `none` | yes | `block`, `timeline`, `child` (the circle at their start; the root's arrowhead), `jump` (its arrowhead), `wedge`, `name`, `label` |
| `opacity` | a number from 0 to 1 | no | every type |
| `font-size` | a number > 0 | yes | `name`, `label` |
| `rx` | a number ≥ 0 | no | `block` (its corner radius) |
| `display` | `inline` or `none` | no | every type but `block` |
| `side` | `above` or `below` | no | `child`, `map`, `region`, `jump`, `wedge`, `break` |
| `content` | a text, or `none` | no | `name` (a row's own name, section 6.6) |
| `max-width` | a number > 0, or `none` | no | `name` (section 6.6) |

A statement may set any property on any element; an element ignores the
properties its type does not read. `display: none` is the filter: an element
that is not displayed is not drawn and takes no room.

### 2.5 The cascade

The value of a property on an element is found per property:

1. Of the statements matching the element that set this property, the
   highest-ranking sets it.
2. When none sets it and the property is inherited, the element takes its
   parent's value in the tree of section 2.1.
3. Otherwise the property's initial value applies: `stroke` `none`,
   `stroke-width` 1, `stroke-dasharray` `none`, `fill` `none`, `opacity` 1,
   `font-size` 9, `rx` 0, `display` `inline`, `side` `below`, `content`
   `none`, `max-width` `none`.

The rank of a statement is, from the most to the least significant:

1. its layer: a statement of a later layer outranks every statement of an
   earlier one;
2. whether its selector names `ids`;
3. the depth of its `within`: none is 0, the root 1, its children 2, and
   so on; deeper outranks shallower;
4. whether its selector names `class`;
5. whether its selector names `element`;
6. how many of `domain` and `modality` its selector names;
7. its position: the later statement of one list wins.

## 3. Numbers

### 3.1 Positions on the root's axis

A position derived from time is a value on the **root's axis**: a
coordinate of a timeline is carried to the root by adding the offsets of
its ancestors, from the root down. The root starts at 0 (in its number
type) and ends at its length; a child of a timeline starting at `s`, with
offset `o`, starts at `s + o` and ends at that start plus its own length; a
region, break or jump of a timeline starting at `s` lies at `s` plus its
coordinate.

A coordinate's value is read as its number type selects: a `float` value is
a float, an `int` or `fraction` value is exact. Values combine as Python's
numeric tower combines them: the sum of two exact values is exact; a sum
involving a float converts each exact operand to the nearest double (ties
to even) and adds in IEEE 754 binary64 arithmetic, rounding to nearest,
ties to even.

### 3.2 From the axis to the canvas

A position `t` on the root's axis, with the root's length `λ`, becomes the
**proportion** `u = t / λ`: an exact quotient when both are exact, then
rounded once to the nearest double; a binary64 division when either is a
float; 0 when `λ` is 0. Its x in the box is

    x(t) = x0 + L × u

in binary64, `x0` the start of the root's line (section 6.7). This is the
only step from an exact value to a double, at any depth of nesting. Labels
show the exact coordinate, never the double.

### 3.3 Canvas arithmetic

Every other number of a drawing is a double, computed in IEEE 754 binary64
in the order its formula is written, left to right, multiplications and
divisions before additions and subtractions. `max` and `min` compare
exactly.

## 4. Defaults

The defaults are the lowest layer; an application may supply layers above
them (section 1).

```json
{
  "styles": {
    "graphical-domain": {"stroke": "#FF0000", "fill": "#FF0000"},
    "logical-domain": {"stroke": "#00CC00", "fill": "#00CC00"},
    "physical-domain": {"stroke": "#0050EF", "fill": "#0050EF"}
  },
  "statements": [
    {"select": {"element": "block"}, "set": {"fill": "#F3F4F6", "rx": 10}},
    {"select": {"domain": "graphical"}, "set": "graphical-domain"},
    {"select": {"domain": "logical"}, "set": "logical-domain"},
    {"select": {"domain": "physical"}, "set": "physical-domain"},
    {"select": {"element": "timeline"}, "set": {"stroke-width": 3}},
    {"select": {"element": "child"}, "set": {"stroke-width": 3}},
    {"select": {"element": "timeline", "modality": "continuous"}, "set": {"stroke-dasharray": "none"}},
    {"select": {"element": "timeline", "modality": "discrete"}, "set": {"stroke-dasharray": "3 3"}},
    {"select": {"element": "child", "modality": "continuous"}, "set": {"stroke-dasharray": "none"}},
    {"select": {"element": "child", "modality": "discrete"}, "set": {"stroke-dasharray": "3 3"}},
    {"select": {"element": "child"}, "set": {"side": "above"}},
    {"select": {"element": "map"}, "set": {"stroke-width": 1, "side": "above"}},
    {"select": {"element": "map", "modality": "continuous"}, "set": {"stroke-dasharray": "none"}},
    {"select": {"element": "map", "modality": "discrete"}, "set": {"stroke-dasharray": "3 3"}},
    {"select": {"element": "wedge"}, "set": {"fill": "#000000"}},
    {"select": {"element": "region"}, "set": {"stroke-width": 1}},
    {"select": {"element": "jump"}, "set": {"stroke": "#000000", "fill": "#000000", "stroke-width": 1.5}},
    {"select": {"element": "break"}, "set": {"stroke": "#FF0000", "stroke-width": 1.5, "stroke-dasharray": "2 2"}},
    {"select": {"element": "label"}, "set": {"fill": "#000000", "font-size": 9}},
    {"select": {"element": "name"}, "set": {"fill": "#000000", "font-size": 11, "max-width": 160}}
  ]
}
```

So a timeline and its regions take the colour of its domain, dotted when
discrete and solid when continuous; a conversion map takes the colour and
pattern of the domain and modality it converts to; wedges are black; jumps
are black and breaks dotted red. Children and maps lie above the root,
everything else below; a name longer than 160 is cut (section 6.6).

## 5. Text

### 5.1 The font

Every text is drawn in **DejaVu Sans 2.37**, the file `DejaVuSans.ttf` of
that release (SHA-256
`7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954`),
shipped in this repository under `fonts/` with its licence. Kerning and
ligatures are off everywhere.

Text is measured from the font's advance widths, never from a rendering.
`fonts/dejavu-sans-2.37.metrics.json` holds them: `units_per_em` (2048),
`ascender` (1901) and `descender` (483, as a positive depth) from the `hhea`
table, `fallback` (the advance of glyph 0, 1229), and `advances`, the
advance of every code point the font maps, keyed by the code point in
decimal. With `A` the sum of the advances of a text's code points (an
integer; an unmapped code point counts `fallback`, and the drawing lists
it), the text at font size `s` has

| Measure | Value |
|---|---|
| width | `w(text, s) = A × s / 2048` |
| ascent | `a(s) = 1901 × s / 2048` |
| descent | `d(s) = 483 × s / 2048` |
| line height | `h(s) = 2384 × s / 2048` |

A name may hold any code point. Every code point from U+0000 to U+001F in a
text becomes a space before it is measured or written, since SVG and TeX
cannot carry most of them. Ids hold none: the schema refuses them.

### 5.2 Coordinates

A coordinate is labelled with the text of its value, a space (U+0020) and
the symbol of its unit. The text of a value is its JSON form: an integer in
decimal (`96`), a Fraction pair `[n, d]` as `n/d` (`3/2`), or `n` when `d`
is 1; a float as the standard writer spells it, which is Python's `repr`
(`1.5`, `6.0`, `1e-05`).

| Unit | Symbol |
|---|---|
| `quarters` | `♩` (U+2669) |
| `seconds` | `s` |
| `samples` | `smp` |
| `ticks` | `ticks` |
| `pixels` | `px` |
| any other unit | the unit's name (`points`, `whole_note`, …) |

### 5.3 Names and labels

The name of a timeline or a conversion map is its `name`, or its `id` when
`name` is null. A region's label is its `name`; a jump's label is its
`label`, or its `control_type` when `label` is null; a break's label is its
`label`, and a break whose `label` is null has none.

## 6. Layout

### 6.1 Traversal

The **traversal** lists the timelines in pre-order: the root, then each
child in canonical order, each followed by its own descendants.

### 6.2 Constants

Distances marked "× v" are multiplied by the vertical stretch `v`
(section 1); every other size is fixed.

| Constant | Canvas units |
|---|---|
| padding `P` | 8 |
| gap between the name column and the root's start `G` | 8 |
| gap between bands `B` | 4 × v |
| child row pitch `pc` | max(14 × v, h(s)) |
| map row pitch `pm` | max(13 × v, h(s)) |
| map double-line spacing | 3 |
| wedge: base, height | 6, 13 |
| label gap (marker to label) | 2 |
| label separation (horizontal, between labels) | 2 |
| brace height | 6 |
| region row pitch `pr` | 6 + 2 + h(9) + 4 × v |
| first jump depth | 8 × v |
| jump level pitch `pj` | 10 × v + h(9) |
| break label offset | 3 |

`s` is the name font size of a band: the largest font size of the names of
its rows, displayed or not (section 6.6); the root's row is a band of its
own. Wherever `h(9)`, `a(9)` or `d(9)` appears in this section and the
next, 9 stands for the largest font size of the labels of the band in
question (9 by default).

### 6.3 First fit

Several steps below place items one at a time, in a given order, into
numbered **rows** (or tiers) 1, 2, 3, …: an item goes to the lowest row, at
or above its own minimum (1 unless stated), holding no item whose extent
**conflicts** with its own. Extents are x intervals measured from the
root's start (`x − x0`), so no row depends on `x0`; `[a1, b1]` and
`[a2, b2]` conflict when `a1 < b2` and `a2 < b1`, or when `a1 = a2`. So an
item that starts where another ends shares its row, and two items starting
at the same point never do. The extent of a label is `[left − 1, right +
1]`, so labels keep the label separation apart. Every side fills its own
rows.

### 6.4 Sides and bands

Each side of the root, above and below, is filled outwards from the root's
line in **bands**, each present only when it holds a drawn element of that
side: first the **wedge band** (the wedges whose `side` it is, with their
label tiers); then the bands of the four groups in the placement's `order`
(section 1):

- `children`: the **children band**, the children whose `side` it is;
- `maps`: the **map band**, the maps whose `side` it is;
- `regions`: the **region band**, the regions whose `side` it is;
- `flow`: the **flow band**, the jumps and breaks whose `side` it is;

and last the **break-label band**, the labels of the breaks of the *other*
side.

A distance `o` outwards from the root's line lies at `y_root − o` above and
`y_root + o` below. The first band of a side starts at `o = 0`, except a
children or map band, which starts no nearer than `h(s) / 2`, `s` the
root's row's name font size, so that its names clear the root's name. Each
following band starts at the outer edge of the one before plus `B`.

**Wedges.** The root's wedges at its start and end, each labelled with the
coordinate it marks in the root's unit: `0` and `length`. The labels of one
side are placed by first fit, start before end, into tiers centred on their
wedge's `X`. The band reaches `w / 2 + 13`, plus `2 + T × h(9)` when `T ≥
1` labels are drawn, `w` the root's stroke width.

**Children.** Every displayed child, in traversal order, is placed on its
side by first fit with extent `[x(start), x(end)]`. Its minimum row is one
more than its parent's **anchor** on that side: the root's anchor is 0 on
both sides, a placed child's anchor on its own side is its row, and every
other anchor of a child is its parent's. So a nested child lies beyond its
parent when both are on one side. Row `k` is centred at `c0 + (k − 1/2) ×
pc`, `c0` the start of the band; the band is `C × pc` wide for `C` rows.

**Maps.** The displayed maps of every timeline, in traversal order and each
timeline's maps in canonical order, are placed on their side by first fit
with the extent of their timeline. Row `k` is centred at `m0 + (k − 1/2) ×
pm`; the band is `M × pm` wide.

**Regions.** The displayed regions of every timeline, in traversal order
and each timeline's regions in canonical order, are placed on their side by
first fit with the extent from `min(xs, xe)` to `max(xs, xe)` of their
start and end, widened to the extent of their label when it is drawn. Row
`k` has its brace's arms at `r0 + (k − 1) × pr`; the band is `R × pr − 4 ×
v` wide.

**Flow.** The **flow row** of a side lies at the start of its flow band.
The displayed jumps of every timeline are listed in traversal order, each
timeline's in canonical order, sorted stably by span (the absolute exact
difference of their to and from positions), smallest first, and placed on
their side by first fit with the extent from the smaller to the larger of
`x(from)` and `x(to)`, widened to the extent of their label. Level `k`
reaches its **apex** at the distance `f0 + 8 × v + (k − 1) × pj` from the
root's line, `f0` that of the flow row, so a jump enclosing another lies
further out. The band is `8 × v + (K − 1) × pj
+ 2 + h(9)` wide for `K` levels, and 0 wide when the side has breaks but no
jumps. Jump descriptors and labels follow this placement order.

**Breaks.** A displayed break is a vertical line from the flow row of its
side across every band to the padding of the opposite side. Its label sits
at that far end: the break labels of a side are placed by first fit, in
traversal order and each timeline's breaks in canonical order, into the
tiers of the opposite side's break-label band; the band is `T × h(9)` wide.
Tier 1 lies at the padding: its baseline is at `P + a(9)` above, or at `Hc
− P − d(9)` below, and tier `k` lies `(k − 1) × h(9)` further in.

### 6.5 Heights

The root's line lies at `y_root = P + Ea`, `Ea` the outer edge of the
above side (0 when it has no band), but never less than `P + h(s) / 2`. The
content's height is `Hc = y_root + Eb + P`, `Eb` the outer edge of the
below side, never less than `h(s) / 2`. Here `s` is the root's row's name
font size.

### 6.6 Elements

Every element below is drawn only when it is displayed, with the cascaded
values of its element. `Xs`, `Xe` are `x` of an element's start and end;
`y` is its row's line; "outwards" points away from the root, up on the
above side and down below.

- **Root and children.** A line from `Xs` to `Xe` with stroke width `w`; a
  filled circle of radius `w` centred at the start. The root ends with an
  arrowhead of length `3w` and half-width `1.5w` whose tip is at `Xe`, the
  line stopping at its base; a child ends with an open diamond of
  half-length `1.5w` and half-width `1.2w` centred at `Xe` and stroked with
  width `w / 2`, the line stopping at its left corner. A child carries no
  coordinate labels. The circle and the root's arrowhead are filled and
  not stroked; the diamond is stroked and not filled.
- **Wedges.** A filled triangle, not stroked, with its tip on the root
  line's edge on its side (`y_root ± w / 2`) and its base 13 further out, 6
  wide. Its label is centred on `X`, in its tier beyond the base: tier `k`
  starts `w / 2 + 13 + 2 + (k − 1) × h(9)` out.
- **Maps.** Two lines from `Xs` to `Xe` of the map's timeline, at `y ±
  3/2`.
- **Regions.** A brace from `Xs` to `Xe`, arms at `yb`, tip 6 further out
  at `Xm`, `x` of the exact midpoint of the region's start and end, so it
  opens towards the root; its label centred on `Xm` beyond the tip, 2
  further out.
- **Jumps.** A cubic Bézier curve from `(x(from), yf)` to `(x(to), yf)`,
  `yf` the flow row, with controls `(x(from), yc)` and `(x(to), yc)`, `yc =
  yf + 4/3 × (apex − yf)`, so it reaches its apex halfway; a filled
  arrowhead of length `4w` and half-width `2w` (`w` the jump's stroke
  width), filled and not stroked, with its tip at `(x(to), yf)`, pointing
  towards the root; its label centred on `x` of the exact midpoint of from
  and to, beyond the apex, 2 further out.
- **Breaks.** The line of section 6.4 at `x` of the break; its label
  starting at `x + 3`.
- **Names.** For each row holding lines or maps (the root's row, the child
  rows, the map rows), the names (section 5.3) of its drawn lines or maps
  whose names are displayed, in traversal order, joined by `, `. When the
  `content` of the first of these names is not `none`, the row shows that
  text instead (an editor sets it to give a row its own name, and resets it
  to `none`). When the text is wider than that name's `max-width`, it is cut
  to its longest prefix that, followed by `…` (U+2026), fits, and the cut
  text is shown. It is drawn starting at `P`, vertically centred on the
  row: baseline at `y + (a(s) − d(s)) / 2`, `s` the font size of that first
  name, whose address the text carries. Name descriptors are ordered from
  the top row down.

A label "beyond" a point at ordinate `y` lies outwards from it: below, its
baseline is at `y + a(9)`; above, at `y − d(9)`, with the label gap added
where stated.

### 6.7 The box

Let `N` be the width of the widest name text as drawn (0 when none), and
`G' = 8` when a name is drawn and 0 otherwise. Every centred label `i`
(wedge, region and jump labels) has width `wi` and the proportion `ui`
(section 3.2) of the exact position it is centred on. The root's line
starts at

    x0 = max(P + N + G', max over i of (P + wi / 2 − L × ui))

so that no label crosses the padding on the left. The content's width `Wc`
is `P` plus the largest right edge of any drawn element (lines, markers,
wedges, braces, arcs, labels and names), or `P + x0` when nothing is
drawn. The box is `W =
max(Wc, width)` wide and `H = max(Hc, height)` high, a `null` request
counting as 0; the background is a rectangle filling it with corner radius
`rx`.

## 7. Writers

### 7.1 The page

A writer draws one or more drawings, each placed at a canvas position `(X,
Y)` with a zoom `z` (one drawing alone: `(0, 0)` and 1). The page is the
bounding box of the placed boxes, each `W × z` by `H × z`, plus a margin of
16 on every side: with `left` and `top` the smallest `X` and `Y` and
`right` and `bottom` the largest `X + W × z` and `Y + H × z`, the page is
`PW = right − left + 32` wide and `PH = bottom − top + 32` high, and a
drawing at `(X, Y)` lies at the page position `(X − left + 16, Y − top +
16)`, y downwards. Canvas units are pixels in SVG and points in TikZ.

### 7.2 Element descriptors

A drawing becomes a list of SVG **element descriptors**, in this order: the
background; the breaks; the maps; the regions; the jumps; the root and then
the children in traversal order; the wedges; the names, the wedge labels,
the region labels, the jump labels and the break labels. Every descriptor except the background carries `data-address`, the
address of its element. An editor renders these same descriptors on
screen; the SVG writer serializes them.

| Element | Descriptors |
|---|---|
| background | `<rect x="0" y="0" width="{W}" height="{H}" rx="{rx}" fill="{fill}"/>` |
| root | `<line>` from `(Xs, y)` to `(Xe − 3w, y)`; `<circle cx="{Xs}" cy="{y}" r="{w}">`; `<polygon points="{Xe},{y} {Xe−3w},{y−1.5w} {Xe−3w},{y+1.5w}">` |
| child | `<line>` from `(Xs, y)` to `(Xe − 1.5w, y)`; `<circle>` as the root's; `<polygon points="{Xe−1.5w},{y} {Xe},{y−1.2w} {Xe+1.5w},{y} {Xe},{y+1.2w}" fill="none">` stroked with width `w/2` and no dash |
| wedge | `<polygon points="{X},{yt} {X−3},{yb} {X+3},{yb}">`, `yt` its tip and `yb` its base (section 6.6) |
| map | two `<line>` |
| region | `<path d="{brace}">` |
| jump | `<path d="M{P0}C{C1} {C2} {P3}">`; `<polygon>` arrowhead `{X},{Y} {X−2w},{Yo} {X+2w},{Yo}`, `Yo` lying `4w` outwards of `Y` |
| break | `<line>` |
| name, label | `<text x="{x}" y="{baseline}" text-anchor="{start|middle}" font-size="{s}">` |

A line or path carries `fill="none"` (a line none at all) and `stroke`,
`stroke-width` and, unless `none`, `stroke-dasharray`; a circle, a polygon
and a text carry `fill`, and the child's diamond, the one stroked polygon,
also the stroke attributes. `opacity` is written when it is not 1. An
element without text is written self-closing (`<line …/>`); a text is written `<text …>{text}</text>`. Attributes are
written in
this order: `data-address`, the coordinates in the order shown, `text-anchor`,
`font-size`, `fill`, `stroke`, `stroke-width`, `stroke-dasharray`,
`opacity`.

**The brace** from `X1` to `X2`, arms at `Yb`, tip at `(Xm, Ya)` (section
6.6): with `Ym = (Yb + Ya) / 2` and `k = |Ya − Yb| / 2`, the path is `M X1
Yb Q X1 Ym X1+k Ym L Xm−k Ym Q Xm Ym Xm Ya Q Xm Ym Xm+k Ym L X2−k Ym Q X2 Ym
X2 Yb`. Path data is an upper-case command letter followed by its
coordinates, numbers separated by one space, no space before a command
letter (`M80 16L74 14`).

### 7.3 SVG profile

Every number either writer writes, each number of a `stroke-dasharray`
included, is formatted by one rule: take the exact value of the double,
round it to the nearest multiple of 1/10000, ties to the even multiple;
write it in decimal without exponent, without a leading `+`, with its
integer part (`0` when zero) and, when not an integer, a point and its
fractional digits without trailing zeros. A value that rounds to zero is
`0`, never `-0`.

The output is UTF-8, one element per line, no indentation, a final newline:

```
<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}" font-family="DejaVu Sans" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate({X} {Y}) scale({z})">
...
</g>
</svg>
```

with one `<g>` per drawing, `(X, Y)` its position on the page, and
` scale({z})` left out when `z` is 1. In text, `&`, `<` and `>` are written
`&amp;`, `&lt;` and `&gt;`; in attribute values, so are they, and `"` as
`&quot;`.

### 7.4 TikZ profile

Coordinates are bare numbers in points, y upwards: an SVG ordinate `y` of a
drawing of height `H` becomes `H − y`. With `standalone` (the default) the
output is a complete LuaLaTeX document:

```
\documentclass{standalone}
\usepackage{fontspec}
\setsansfont{DejaVuSans.ttf}[Path={font directory}/,Kerning=Off,Ligatures={TeXOff,NoCommon}]
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}[x=1pt,y=1pt,miter limit=4,font=\sffamily]
\definecolor{ts00CC00}{HTML}{00CC00}
...
\end{tikzpicture}
\end{document}
```

`{font directory}` is a writer option, `.` by default. Without
`standalone`, the output is the `tikzpicture` environment alone. Each
colour used is defined once, right after `\begin{tikzpicture}`, as
`\definecolor{ts<RRGGBB>}{HTML}{<RRGGBB>}`, sorted by its digits. Each
drawing is a `scope` shifted to the TikZ position of its box's bottom-left
corner, `({px},{PH − py − H × z})` for the page position `(px, py)` of
section 7.1 (`[shift={(…,…)}]`, with `,scale={z},transform shape` when `z`
is not 1).

Every descriptor of section 7.2 becomes one command, its attributes mapped
one to one:

| SVG | TikZ |
|---|---|
| `fill="#RRGGBB"` | `fill=tsRRGGBB` (`fill="none"`: no option) |
| `stroke="#RRGGBB"` | `draw=tsRRGGBB` (`stroke="none"`: no option) |
| `stroke-width="{v}"` | `line width={v}pt` |
| `stroke-dasharray="{a} {b} …"` | `dash pattern=on {a}pt off {b}pt …` (an odd list repeated once) |
| `opacity="{o}"` | `opacity={o}` |
| `rx="{r}"` | `rounded corners={r}pt` |
| `font-size="{s}"` | `font=\sffamily\fontsize{s}{h(s)}\selectfont` (TikZ's `font` key replaces the picture's font, so the family is restated) |

| Descriptor | Command |
|---|---|
| rect | `\path[{options}] (0,0) rectangle ({W},{H});` |
| line | `\path[{options}] ({x1},{y1}) -- ({x2},{y2});` |
| circle | `\path[{options}] ({cx},{cy}) circle[radius={r}];` |
| polygon | `\path[{options}] ({p1}) -- ({p2}) -- … -- cycle;` |
| path | `\path[{options}] ({P0}) .. controls ({C1}) and ({C2}) .. ({P3});`, a brace's quadratic `Q C P` from the current point `P0` written as the cubic with controls `P0 + 2/3 × (C − P0)` and `P + 2/3 × (C − P)`, an `L P` as `-- ({P})` |
| text | `\node[anchor={base west|base},inner sep=0,{options}] at ({x},{baseline}) {{text}};` with `text=tsRRGGBB` for the fill |

Options are written in the order of the attributes of section 7.2. In text,
`\` becomes `\textbackslash{}`, `~` becomes `\textasciitilde{}`, `^`
becomes `\textasciicircum{}`, each of `# $ % & _ { }` is preceded by
`\`, and a space at the start or end of a text or after another space is
written `\ `, so that TeX keeps it.
