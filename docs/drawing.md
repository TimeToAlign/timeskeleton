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

Sections 1 to 7 specify the drawing of one timeline, called **the root**,
with all its descendants: a **member drawing**. Section 8 specifies the box
that holds member drawings. Every file is drawn as a bundle: a bundle file
as itself, a group file as an anonymous bundle holding its group, and a
timeline file as an anonymous bundle holding its top-level timeline, so the
three file kinds share one box rule. Terms in `code` are JSON members.

## 1. Inputs and output

`draw(manifest, placement, layers, metrics)` returns the manifest's drawing.

- `manifest`: a timeline, group or bundle file, read in canonical order
  (README, "Canonical order") whatever order it was written in. Its
  `graphical` block holds the manifest's own style statements; in a group or
  bundle file it also holds the member `order` (section 8).
- `placement`: chosen by whoever places the drawing, such as an editor's
  canvas or a script:
  - `length`, the **graphical length** `L` of the root, in canvas units
    (default 400): the distance from the root's start to its end;
  - `spacing`, the **vertical stretch** `v`, a positive number (default 1)
    that multiplies the vertical distances of section 6.2;
  - `width` and `height`, the requested **box size** in canvas units, or
    `null` (the default) for the content's own size;
  - `order`, the **band order**: the groups `children`, `regions` and
    `flow`, each once, in the order their bands lie outwards from the root
    on either side (default `["children", "regions", "flow"]`; section
    6.4). An editor changes it by dragging a group. Conversion maps are not
    a group: each timeline's maps lie against its own line (section 6.4).
- `layers`: the statement lists that style the drawing, from the lowest to
  the highest precedence: the defaults of section 4, then any lists an
  application supplies below the manifest (such as an editor's settings),
  then the manifest's own `graphical` block. No layer lies above the
  manifest: a drawing's own styling is its manifest's. Section 2 defines
  them.
- `metrics`: the advance widths of the font of section 5.

The drawing is a **box** of width `W` and height `H` and a list of drawn
**elements** in box-local canvas units, origin at the box's top-left corner,
y downwards. Every element carries its **address** (section 2.2) and, where
it shows a coordinate, the exact coordinate it shows. Canvas units become
pixels in SVG and points in TikZ (section 7).

A drawing does not depend on its position on a canvas, nor on its scale: a
canvas or a writer places the box at a position and scales it uniformly by
a **scale** factor `z` (section 7.1). The three ways of resizing a drawing
change one input each:

| Resize | Input changed | Effect |
|---|---|---|
| Scale | scale `z` | everything scales, proportions kept, text included |
| Box | `width`, `height` | only the box changes; the content keeps its place at the top left; the box never becomes smaller than the content (section 8.4) |
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
    {"select": {"ids": ["region_1"]}, "set": {"display": "none"}}
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
| `card` | the raised container of a timeline drawn in its own card: a timeline file's top-level timeline, a group member, an ungrouped root (section 8) |
| `timeline` | the line of a timeline drawn in its own card (section 8) |
| `child` | a child timeline's line, at any depth |
| `boundary` | the start of a segment on its segment line, drawn as a thin vertical rule (section 6.4) |
| `ancestor` | the faded line of an ancestor of a member that is a child timeline, clipped to the member (section 8.3) |
| `group` | a group's frame (section 8) |
| `map` | a conversion map, drawn as a closed double line |
| `region` | a region, drawn as a brace |
| `break` | a flow-control break, drawn as a vertical line |
| `jump` | a flow-control jump, drawn as an arc with an arrowhead |
| `wedge` | a marker of the root's start or end; on an ancestor line, the member's start or end on the ancestor's axis (section 8.3) |
| `name` | the name of a row, in the name column, or the title of a group or bundle (section 8) |
| `label` | any other text: a coordinate, or the label of a region, jump, break or segment |

An element **belongs** to a timeline (section 2.2); the `block`, a `group`
and the titles of a group or bundle belong to none, and have no domain,
modality or class. A card belongs to the timeline it holds, and so has
its domain, modality and class. An element has the **domain** (`graphical`, `logical` or `physical`)
and the **modality** (`continuous` or `discrete`) of its timeline's
`class` (`ContinuousGraphicalTimeline` is continuous and graphical, and so
on). A map instead has the domain and modality of the map's `target_unit`,
so a map is drawn in the style of the timelines it converts to:

| Domain | Units |
|---|---|
| `logical` | `floating_measures`, `whole_note`, `quarters`, `ticks` |
| `physical` | `milliseconds`, `seconds`, `minutes`, `samples`, `frames` |
| `graphical` | `pixels`, `meters`, `centimeters`, `millimeters`, `inches`, `points` |

`ticks`, `samples`, `frames` and `pixels` are discrete, every other unit
continuous. A map whose `target_unit` is null or not in the table has no
domain and no modality, so no selector naming them matches it and it
inherits its timeline's style (section 2.5). An element's **class** is its
timeline's `class`, except that a map has the map's `type`
(`QuartersToTicks`, …).

Elements form a **tree** that carries inheritance (section 2.5): the
`block` holds the `timeline`; a `timeline` or `child` holds its maps,
regions, breaks, jumps, wedges and child timelines; a segment line holds
its segments, each holding its `boundary`, its label and its own
descendants; an element holds its own `name` and `label` where it has one
(section 5.3; a map has neither). A segment that is not a segment line is a
node of the tree although no line of its own is drawn, and has no element
type, so `inside` never names it; a segment that is a segment line is drawn
as a `child` (section 6.1), and so holds its boundary as a `child` although
the boundary lies on its segment line's line. Section 8 states the top
of the tree: the block, frames, cards and ancestor lines.

### 2.2 Addresses

Every timeline, conversion map, region, break, jump and marker of a manifest
carries an `id`, unique within the manifest across all of these kinds; an id
is a non-empty string without `/` and without control characters. An element is addressed by its own id,
and a part of an element by that element's address followed by `/` and the part's word (so a wedge's label is `T/end/label`).
An address is compared as a whole string.

| Element | Address | Belongs to |
|---|---|---|
| the root, or a child timeline with id `T` | `T` | `T` |
| a conversion map with id `M` on `T` | `M` | `T` |
| a region with id `R` of `T`'s `regions` | `R` | `T` |
| a break with id `B` of `T`'s `flow_control.breaks` | `B` | `T` |
| a jump with id `J` of `T`'s `flow_control.jumps` | `J` | `T` |
| the root's wedges at its start and end, the root's id being `T` | `T/start`, `T/end` | `T` |
| the name of an element with address `C` | `C/name` | that element's timeline |
| the label of an element with address `C` | `C/label` | that element's timeline |
| the card of a timeline with id `T` | `T/card` | `T` |
| the boundary of a segment with id `S` | `S/start` | `S` |
| the label of a segment with id `S` | `S/label` | `S` |
| the ancestor line of a timeline with id `A` | `A` | `A` |
| the marks of the start and end of a member `M` on an ancestor line | `M/start`, `M/end` | `M` |
| the frame of a group with id `G` | `G` | none |
| the title of a group with id `G`, or of the bundle with id `D` | `G/name`, `D/name` | none |

A marker is addressed by its id but is not drawn. The block has no
address.

A timeline file keeps these addresses, although it is drawn as an
anonymous bundle (section 8). In a group or bundle file, timeline ids, group ids and the bundle id are
unique across the file, but every other id is unique only within its root's
tree (README). There, a timeline, a group or the bundle is addressed by its
bare id as above, and every other element with an id of its own (a map,
region, break, jump or marker) by the id of the root of `timelines` whose
tree holds it, `/`, and its own id: a region `region_1` of a timeline in the
tree of root `score` is `score/region_1`, and its label
`score/region_1/label`, also when a member below `score` is drawn as the
root of its own member drawing. A part keeps its element's address, so a
member `M`'s wedges are `M/start` and `M/end` and its card `M/card`. Such ids may not be
`start`, `end`, `name`, `label` or `card`, so an address is read without
ambiguity. One timeline may be drawn more than once, as an ancestor line of
several members or also as a member, and a member's start and end are
marked on its own line and on each of its ancestor lines (section 8.3);
every drawing of an element carries its address.

### 2.3 Selectors

A selector is an object with any of these members:

- `element`: an element type;
- `ids`: a non-empty list of distinct addresses;
- `domain`, `modality`: a domain, a modality;
- `class`: a timeline class or a conversion-map type;
- `within`: a timeline id; it matches the elements belonging to that
  timeline or to any of its descendants;
- `inside`: an element type; it matches the elements held, at any depth,
  by an element of that type in the tree of section 2.1 (so
  `{"element": "name", "inside": "ancestor"}` matches the names of ancestor
  lines and no other name).

An element matches a selector when it matches every member present. The
empty selector `{}` matches every element.

### 2.4 Properties

Presentation properties carry SVG's names and values; the writers map them
to TikZ (section 7.4).

| Property | Values | Inherited | Read by |
|---|---|---|---|
| `stroke` | `#RRGGBB` (upper-case) or `none` | yes | every type but `block`, `wedge`, `name` and `label` |
| `stroke-width` | a number ≥ 0 | yes | as `stroke` |
| `stroke-dasharray` | `none`, or numbers separated by single spaces | yes | as `stroke` |
| `fill` | `#RRGGBB` or `none` | yes | `block`, `group`, `card`, `timeline`, `child`, `ancestor` (the circles at their start and end, the arrowhead at their end), `jump` (its arrowhead), `wedge`, `name`, `label` |
| `opacity` | a number from 0 to 1 | no | every type |
| `font-size` | a number > 0 | yes | `name`, `label` |
| `rx` | a number ≥ 0 | no | `block`, `group`, `card` (the corner radius) |
| `shadow` | `#RRGGBB` or `none` | no | `card` (the colour of its offset shadow, section 8.4) |
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
   `font-size` 9, `rx` 0, `shadow` `none`, `display` `inline`, `side`
   `below`, `content` `none`, `max-width` `none`.

The rank of a statement is, from the most to the least significant:

1. its layer: a statement of a later layer outranks every statement of an
   earlier one;
2. whether its selector names `ids`;
3. the depth of its `within`: none is 0, the root 1, its children 2, and
   so on; deeper outranks shallower;
4. whether its selector names `class`;
5. whether its selector names `element`;
6. whether its selector names `inside`;
7. how many of `domain` and `modality` its selector names;
8. its position: the later statement of one list wins.

The cascade runs on each drawing of an element at its own place in the
tree. Drawings that share an address (section 2.2) match the same `ids`,
`within` and `element`, but each inherits from its own parent and matches
`inside` by its own holders: a member's mark on an ancestor line matches
`{"inside": "ancestor"}`, its wedge on its own line does not.

## 3. Numbers

### 3.1 Positions on the root's axis

A position derived from time is a value on the **root's axis**: a
coordinate of a timeline is carried to the root by adding the offsets of
its ancestors, from the root down. The root starts at the zero of its
number type (labelled `0`, or `0.0` for a float) and ends at its length; a child of a timeline starting at `s`, with
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

in binary64, `x0` the start of the root's line (section 8.2). This is the
only step from an exact value to a double, at any depth of nesting. Labels
show the exact coordinate, never the double.

### 3.3 Canvas arithmetic

Every other number of a drawing is a double, computed in IEEE 754 binary64
in the order its formula is written, left to right, multiplications and
divisions before additions and subtractions, and a constant factor such as
`4/3`, `4w`, `2w`, `1.5w`, `1.2w` or `2.5w` formed before it multiplies
(`1.2w` is the double nearest the exact product of 6/5 and `w`, not the
binary64 product of the double `1.2` and `w`). A distance outwards is
summed whole, left to right as written and a label gap of 2 included,
before it becomes an ordinate `y_root − o` or `y_root + o`; a map's centre
is offset from its timeline's line instead, the boundaries and segment
labels of a line from that line (section 6.4), the marks of an ancestor
line and their labels from that line (section 8.3), and a break label from
the flow row (section 6.4). A label's baseline is then that ordinate plus
`a(9)` or minus `d(9)`. `max` and `min` compare exactly.

## 4. Defaults

The defaults are the lowest layer; an application may supply layers
between them and the manifest's own `graphical` block (section 1).

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
    {"select": {"element": "map", "modality": "discrete"}, "set": {"stroke-dasharray": "1 1"}},
    {"select": {"element": "wedge"}, "set": {"fill": "#000000"}},
    {"select": {"element": "region"}, "set": {"stroke": "#000000", "stroke-width": 1, "stroke-dasharray": "none"}},
    {"select": {"element": "jump"}, "set": {"stroke": "#000000", "fill": "#000000", "stroke-width": 1, "stroke-dasharray": "1 1"}},
    {"select": {"element": "break"}, "set": {"stroke": "#FF0000", "stroke-width": 1.5, "stroke-dasharray": "2 2"}},
    {"select": {"element": "boundary"}, "set": {"stroke": "#000000", "stroke-width": 1, "stroke-dasharray": "none"}},
    {"select": {"element": "ancestor"}, "set": {"stroke-width": 3, "opacity": 0.35}},
    {"select": {"element": "ancestor", "modality": "continuous"}, "set": {"stroke-dasharray": "none"}},
    {"select": {"element": "ancestor", "modality": "discrete"}, "set": {"stroke-dasharray": "3 3"}},
    {"select": {"element": "group"}, "set": {"fill": "#FFFFFF", "stroke": "#D1D5DB", "stroke-width": 1, "rx": 6}},
    {"select": {"element": "card"}, "set": {"fill": "#FFFFFF", "stroke": "#C4C9D1", "stroke-width": 0.75, "rx": 5, "shadow": "#B8BEC8"}},
    {"select": {"inside": "ancestor"}, "set": {"opacity": 0.35}},
    {"select": {"element": "label"}, "set": {"fill": "#000000", "font-size": 9}},
    {"select": {"element": "name"}, "set": {"fill": "#000000", "font-size": 11, "max-width": 160}},
    {"select": {"element": "name", "inside": "ancestor"}, "set": {"fill": "#6B7280", "font-size": 9, "opacity": 1}}
  ]
}
```

So a timeline takes the colour of its domain, dotted when discrete and
solid when continuous (dotted: dashes and gaps as long as the stroke is
wide); a conversion map takes the colour and pattern of the domain and
modality it converts to; wedges and braces are black and solid; jumps are
thin, black and dotted, and breaks dotted red. Children and maps lie above their timelines, everything
else below the root; a name longer than 160 is cut (section 6.6). Segment
boundaries are thin black rules; an ancestor line is its timeline's line,
faded, with faded marks and labels, and its name small and grey; a group's
frame is white with a light grey outline; a card is white with a grey
outline and a grey offset shadow, so that it stands out from the grey box
and from a frame alike. A card has its timeline's domain and modality, so
a statement can style the cards of one domain.

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

The name of a timeline is its `name`, or, when `name` is null, its `id`
without its scope: the part after the id's last `:` (U+003A), or the whole
id when it has none (`original_score:dgt_1` is named `dgt_1`). A
conversion map has no name or label in the drawing. A region's label is its `name`, and a region whose `name` is null has none; a jump's label is its
`label`, or its `control_type` when `label` is null; a break's label is its
`label`, and a break whose `label` is null has none; a segment's label is
its `name`, and a segment whose `name` is null has none. The title of a
group or bundle is its `name`, or, when `name` is null, its `id` without its
scope.

## 6. Layout

### 6.1 Traversal

The **traversal** lists the timelines in pre-order: the root, then each
child in canonical order (by offset, compared by exact value, then by id,
compared by Unicode code point, whatever the order of the `children` keys), each followed by its own descendants.

A timeline whose `is_segment_line` is true is a **segment line**; its
children are its **segments**, contiguous from its start to its end. Every
segment lies on its segment line's line, which shows where it starts by a
**boundary** and its name by a label (section 6.4). A segment that is not a
segment line has no line of its own: wherever this section speaks of its
line, it is its segment line's line. The boundaries and segment labels on
a line that is not displayed are not drawn and take no room, as its maps.
A segment that is itself a segment line is drawn as a child line (section 6.4, children), in the row beyond
its segment line, and its own segments lie on that line; neighbouring
segments drawn so meet end to start, the start circle of one inside the
open diamond of the other (section 6.6).

### 6.2 Constants

Distances marked "× v" are multiplied by the vertical stretch `v`
(section 1); every other size is fixed.

| Constant | Canvas units |
|---|---|
| padding `P` | 8 (above and below the content: P × v, section 6.5) |
| gap between the name column and the root's start `G` | 8 |
| gap between bands `B` | 4 × v |
| row pitch `p` | max(14 × v, h(s)) |
| map double-line spacing `d` | 2 |
| map gap `g` (1.5 × d) | 3 |
| wedge: base, height | 6, 13 |
| label gap (marker to label) | 2 |
| label separation (horizontal, between labels) | 2 |
| brace height | 6 |
| region row pitch `pr` | 6 + 2 + h(9) + 4 × v |
| first jump depth | 8 × v |
| jump level pitch `pj` | 10 × v + h(9) |
| break label offset | 3 |
| boundary half-height `k` | 8 |
| group frame padding `Q` | 8 |
| card padding `K` | 8 |
| gap between frames and cards `F` | 8 |
| gap after a frame's title | 4 |
| card shadow offset | 2 |

`s` is the name font size of a band: the largest font size of the names of
its rows, displayed or not (section 6.6); a child whose line is not
displayed has no row. A row whose lines contribute no name (a row of
segment lines, section 6.6) counts the font size the `name` of its first
line has under the cascade. The root's row is a band of its own, so `p0` (section
6.4) takes the root's name size alone and a children band its own rows'. Wherever `h(9)`, `a(9)` or `d(9)` appears in section 3.3, anywhere
in section 6 or in section 8, 9 stands for the largest font size of the labels of the band in
question (9 by default). The labels of a flow band are its drawn jump labels
and break labels together, so its jump levels and break-label tiers share one
size.

### 6.3 First fit

Several steps below place items one at a time, in a given order, into
numbered **rows** (or tiers) 1, 2, 3, …: an item goes to the lowest row, at
or above its own minimum (1 unless stated), holding no item whose extent
**conflicts** with its own. Extents are x intervals measured from the
root's start, each end computed as `L × u` (section 3.2) and never as a
difference `x − x0`, so no row depends on `x0`; an extent named by
positions below runs from `L × u` of the one to `L × u` of the other.
`[a1, b1]` and `[a2, b2]` conflict when `a1 < b2` and `a2 < b1`, or when
`a1 = a2`. So an item that starts where another ends shares its row, and
two items starting at the same point never do. The extent of a label is
`[left − 1, right + 1]`, so labels keep the label separation apart: for a
label of width `wi` centred on a position of proportion `u`, `[L × u − wi /
2 − 1, L × u + wi / 2 + 1]`, and for a break label, `[L × u + 3 − 1, L × u
+ 3 + wi + 1]`, each end computed left to right. Every side fills its own
rows.

### 6.4 Sides and bands

Each side of the root, above and below, is filled outwards from the root's
line in **bands**, each present only when it holds a drawn element of that
side: first the **root band** (the root's map stack and the wedges of that
side, with their label tiers); then the bands of the three groups in the
placement's `order` (section 1):

- `children`: the **children band**, the children whose `side` it is;
- `regions`: the **region band**, the regions whose `side` it is;
- `flow`: the **flow band**, the jumps and breaks whose `side` it is,
  with the breaks' labels.

A distance `o` outwards from the root's line lies at `y_root − o` above and
`y_root + o` below. The first band of a side starts at `o = 0`, except a
children band, which starts no nearer than `p0 / 2` wherever it lies in the
order, `p0` the row pitch of the root's row, so that the rows of a side, the root's included, lie one
pitch apart when no map stack widens them. Each following band starts at
the outer edge of the one before plus `B`. A band's outer edge is its start
plus its width, the width summed first; the root band starts at 0, so its
outer edge is its reach.

**Map stacks.** A timeline's maps lie against its own line. Its **map
stack** on a side is its displayed maps whose `side` it is, in canonical
order; for a map, `above` is up and `below` is down, whichever side of the
root its timeline lies on. With `w` the timeline's stroke width, map `j`
(from 1) is centred `w / 2 + j × (g + d) − d / 2` from the timeline's line
on that side, so the gap between the line and the first map, and between
two maps, is `g`; a stack of `J` maps **reaches** `e = w / 2 + J × (g + d)`
from the line (0 when `J = 0`). A map spans its timeline, from `Xs` to
`Xe`. A map is drawn only when its timeline's line is drawn: the maps of a
timeline that is not displayed are not drawn and take no room. The maps of
a segment that is not a segment line join its segment line's stack, after
the segment line's own maps, in traversal order, each spanning its
segment.

**Segment lines.** Every segment of a segment line except its first (in
canonical order) has a **boundary**: a thin vertical rule at `x` of the
segment's start, `k` to either side of the segment line's line. A line's
boundaries are those of its own segments, drawn on it; the boundary of a
segment that is itself a segment line lies on its segment line's line, not
on its own. The labels
(section 5.3) of the segments of one segment line, in canonical order, are
placed by one first fit into **segment-label tiers** above its line, each
centred on `x` of the exact midpoint of its segment's start and end. Tier
`n` has its baseline at `y − (m + 2 + (n − 1) × h(9)) − d(9)`, `y` the
line's ordinate and `m` the larger of the reach `e` of the line's stack
above and, when the line has a drawn boundary, `k`. A segment
that is not a segment line has no row, no name in the name column, and no
element type: a selector naming `element` never matches it, only its
boundary or label. A line therefore **reaches** above the larger of `e`
and, when it has a drawn boundary, `k`, plus `2 + T × h(9)` when its labels
fill `T ≥ 1` tiers; and below the larger of its stack's reach below and,
when it has a drawn boundary, `k`. "Above" is up whichever side of the
root the line lies on, as for maps. Wherever this section uses a stack's
reach on a side, it uses the line's reach instead.

**The root band.** The root's map stack on the side, and the root's wedges
whose `side` it is, each wedge labelled with the coordinate it marks in the
root's unit: `0` and `length`. The labels of one side are placed by first
fit, start before end, into tiers centred on their wedge's `X`. Only wedge labels fill these tiers. When
the root is a segment line, its boundaries and segment labels belong to
the root band too, and the band reaches at least the root line's reach on
that side. The
wedges reach `w / 2 + 13`, or `w / 2 + 13 + 2 + T × h(9)` (left to right)
when the labels fill `T ≥ 1` tiers, `w` the root's stroke width; the band reaches the larger of that reach (when a
wedge is drawn) and the root's stack's reach `e`. Wedges are drawn over the
stack.

**Children.** Every displayed child that is not a segment, and every
displayed segment that is a segment line, in traversal order, is placed on
its side by first fit with the extent from its start to its end. Its minimum row is
one more than its parent's **anchor** on that side: the root's anchor is 0
on both sides, a placed child's anchor on its own side is its row, and
every other anchor of a child is its parent's; the anchors of a segment
that is not a segment line are its parent's. Since an item that starts
where another ends shares its row (section 6.3), the segment lines among
one segment line's segments lie in one row. So a nested child lies beyond its
parent when both are on one side. Row `k` has an **inner** half (towards
the root) and an **outer** half: each is `p / 2`, or the largest reach of
the row's children's lines on that half's side when it is larger. The outer half's side is the row's own side and the inner half's
the opposite one, so a child above the root has its `above` maps in its
outer half. With `ik` and `ok` the inner and outer halves of row `k`, row 1's
line lies at `l1 = c0 + i1` outwards, `c0` the start of the band, and row
`k + 1`'s at `l(k+1) = lk + (ok + i(k+1))`; the band is `i1 + o1 + i2 + o2
+ … + iC + oC` wide for `C` rows, summed left to right.

**Regions.** The displayed regions of every timeline, in traversal order
and each timeline's regions in canonical order, are placed on their side by
first fit with the extent from the smaller to the larger of their start
and end, widened to the extent of their label when it is drawn. Row
`k` has its brace's arms at `r0 + (k − 1) × pr`, `r0` the start of the
band; the band is `R × pr − 4 ×
v` wide.

**Flow.** A flow band holds first the **break-label tiers** of its side,
`T × h(9)` wide for `T` tiers (0 when it has no drawn break label), and
then the **flow row**, where jumps leave and arrive and breaks end: the
flow row lies `T × h(9)` beyond the start of the band. The displayed jumps of every timeline are listed in traversal order, each
timeline's in canonical order, sorted stably by span (the absolute exact
difference of their to and from positions), smallest first, and placed on
their side by first fit with the extent from the smaller to the larger of
their from and to, widened to the extent of their label. Level `k`
reaches its **apex** at the distance `f0 + 8 × v + (k − 1) × pj` from the
root's line, `f0` that of the flow row, so a jump enclosing another lies
further out. The band is `T × h(9) + 8 × v + (K − 1) × pj + 2 + h(9)` wide
for `K ≥ 1` levels, and `T × h(9)` wide for none. Jump descriptors and
labels follow this placement order.

**Breaks.** A displayed break is a vertical line from the flow row of its
side across every band to the padding of the opposite side: from `(x, yf)`
to `(x, P × v)` below the root and to `(x, Hc − P × v)` above it (section 6.5),
ordinates of the member drawing counted from its top (section 8.4). Its label sits
at the line's end on the flow row, alongside the line on the root's side of
the flow row: the break labels of a side are placed by first fit, in
traversal order and each timeline's breaks in canonical order, into the
break-label tiers of the side. Tier 1 touches the flow row: its baseline is
at `yf − d(9)` below the root and at `yf + a(9)` above it, `yf` the flow
row's ordinate, and tier `k` lies `(k − 1) × h(9)` further in, towards the
root.

### 6.5 Heights

The root's line lies at `y_root = max(P × v + Ea, P × v + h(s) / 2)`, `Ea`
the outer edge of the above side (0 when it has no band). The content's
height is `Hc = y_root + max(Eb, h(s) / 2) + P × v`, `Eb` the outer edge of
the below side. Here `s` is the root's row's name font size. The padding
above and below is stretched by `v` so that the vertical stretch also works
on a single timeline, by growing the room above and below it; with `v = 1`
it is `P`.

### 6.6 Elements

Every element below is drawn only when it is displayed, with the cascaded
values of its element. `Xs`, `Xe` are `x` of an element's start and end;
`y` is its row's line; "outwards" points away from the root, up on the
above side and down below.

- **Root and children.** A line with stroke width `w` from `Xs`; a filled
  circle of radius `w` centred at the start. The end tells what the
  timeline is:
  - a top-level timeline (a root of the file) whose `locked` is false ends
    with an **arrowhead** of length `3w` and half-width `1.5w` whose base is
    at `Xe` and whose tip is at `Xe + 3w`, the line ending at `Xe`, so that
    the drawn timeline is longer than its length; when it is a segment line,
    the arrowhead is **open**: the same triangle, stroked with width `w / 2`
    and not filled, since prolonging it appends a segment;
  - a top-level timeline whose `locked` is true ends with a filled circle of
    radius `w` centred at `Xe`, like its start, the line ending at `Xe`;
  - a child timeline, at any depth, ends with an **open diamond** of
    half-length `1.5w` and half-width `1.2w` centred at `Xe` and stroked with
    width `w / 2`, the line stopping at its left corner: a child is locked by
    its embedding, whatever its `locked` says. A member that is a child
    timeline ends so too, although its line is a `timeline` element.

  A child carries no coordinate labels. The circles and the arrowhead are
  filled and not stroked; the open arrowhead and the diamond are stroked
  and not filled, with no dash. Every arrow of a drawing follows one rule:
  its shaft ends at its head's base, and the head continues the shaft's
  direction at that point.
- **Boundaries.** A line from `(X, y − k)` to `(X, y + k)`, `X` the
  segment's start and `y` its segment line's ordinate (section 6.4), drawn
  over the line.
- **Segment labels.** Centred on `x` of the exact midpoint of the segment,
  in its tier (section 6.4).
- **Wedges.** A filled triangle, not stroked, with its tip on the root
  line's edge on its side (`y_root ± w / 2`) and its base 13 further out
  (`y_root ± (w / 2 + 13)`), 6 wide. Its label is centred on `X`, in its
  tier beyond the base: tier `k` starts `w / 2 + 13 + 2 + (k − 1) × h(9)`
  out, the label gap included, and its baseline lies beyond that start.
- **Maps.** A closed double line: the outline of the rectangle from `Xs`
  to `Xe` of the map's timeline between the ordinates `yc − d / 2` and `yc
  + d / 2`, `yc` the map's centre (section 6.4), stroked and not filled.
- **Regions.** A brace from `Xs` to `Xe`, arms at `yb`, tip 6 further out
  at `Xm`, `x` of the exact midpoint of the region's start and end, so it
  opens towards the root; its label centred on `Xm` beyond the tip, 2
  further out.
- **Jumps.** An arrow from `(Xf, yf)` to `(Xt, yf)`, `Xf = x(from)`, `Xt =
  x(to)`, `yf` the flow row, `w` the jump's stroke width. Its **curve** is
  the cubic Bézier curve from `P0 = (Xf, yf)` to `P3 = (Xt, yf)` with
  controls `C1 = (Xf + q, yc)` and `C2 = (Xt − q, yc)`, `q = (Xt − Xf) / 4`
  and `yc = yf + 4/3 × (ya − yf)`, `ya` the ordinate of its level's apex:
  the controls lie a quarter of the span inwards, so the curve reaches its
  apex halfway, and a short jump arrives steeply and a long one flatly. The
  arrow is placed as TikZ places an arrow tip on a curve: the head points
  along the curve's direction at its end, the unit vector `u = (ux, uy)`
  from `C2 = (Cx, yc)` to `P3`, `ux = (Xt − Cx) / ℓ` and `uy = (yf − yc) /
  ℓ`, `ℓ = sqrt((Xt − Cx) × (Xt − Cx) + (yf − yc) × (yf − yc))` (the
  correctly rounded square root); the head is a filled triangle, not stroked, of length `4w` and
  half-width `2w`, its tip at `P3` and its base centred at `Bh = (Xt − 4w ×
  ux, yf − 4w × uy)`, its corners `Bh − 2w × n` and `Bh + 2w × n`, `n = (−uy, ux)`; the **shaft** is
  the curve with its end moved from `P3` to `Bh` and its controls kept, so
  it meets the head's base at a right angle. The label is centred on `x` of
  the exact midpoint of from and to, beyond the apex, 2 further out.
- **Breaks.** The line of section 6.4 at `x` of the break; its label
  starting at `x + 3`, in its tier (section 6.4).
- **Names.** For each row holding lines (the root's row and the child
  rows), the names (section 5.3) of its drawn lines whose names are
  displayed, in traversal order, joined by `, `; the line of a segment
  contributes no name, since its name is its label, so a row of segment
  lines alone has no name. When the
  `content` of the first of these names is not `none`, the row shows that
  text instead (an editor sets it to give a row its own name, and resets it
  to `none`). When the text is wider than that name's `max-width`, it is cut
  to its longest prefix that, followed by `…` (U+2026), fits, and the cut
  text is shown. It is drawn starting at `x = xn` (section 8.2), vertically
  centred on the row: baseline at `y + (a(s) − d(s)) / 2`, `s` the font size of that first
  name, whose address the text carries. Name descriptors are ordered from
  the top row down.

A label "beyond" a point at ordinate `y` lies outwards from it: below, its
baseline is at `y + a(9)`; above, at `y − d(9)`, with the label gap added
where stated.

### 6.7 Extents

A member drawing has no box of its own; section 8 places it. Its **names**
are the name texts it draws, its ancestor names included, and every
centred label `i` it draws (wedge, segment, region and jump labels, the
labels of the marks on its ancestor lines included) has width `wi` and the
proportion `ui` (section 3.2) of the exact position it is centred on; a
mark on an ancestor line is centred at the member's start (`ui = 0`) or end
(`ui = 1`). A centred label at `X` ends at `X + wi / 2`. Its **right edge** is the largest right edge of any element it
draws (lines, markers, wedges, braces, arcs, labels and names). Right
edges are geometric, no stroke width counted: a timeline's start circle
`Xs + w`, its arrowhead's tip `Xe + 3w`, its end circle `Xe + w` or its
diamond's corner `Xe + 1.5w`, an ancestor's outer chevron tip (section
8.3), a map's `Xe`, a boundary's `X`, a wedge's `X + 3`, the largest x of
the points written in a brace's or a jump's descriptors (control points and
a jump's arrowhead corners included), and a text's end from its advance
widths.

## 7. Writers

### 7.1 The page

A writer draws one or more drawings, each placed at a canvas position `(X,
Y)` with a scale `z` (one drawing alone: `(0, 0)` and 1). The page is the
bounding box of the placed boxes, each `W × z` by `H × z`, plus a margin of
16 on every side: with `left` and `top` the smallest `X` and `Y` and
`right` and `bottom` the largest `X + W × z` and `Y + H × z`, the page is
`PW = right − left + 32` wide and `PH = bottom − top + 32` high, and a
drawing at `(X, Y)` lies at the page position `(X − left + 16, Y − top +
16)`, y downwards. Canvas units are pixels in SVG and points in TikZ.

### 7.2 Element descriptors

A member drawing becomes a list of SVG **element descriptors**, in this
order: the breaks; the maps (in traversal order, each timeline's in
canonical order, whatever their side); the regions; the jumps; the root and
then the children in traversal order; the boundaries, in the traversal order
of their segments (a nested segment line's boundaries thus follow its own
boundary, not its siblings'); the wedges, start before end; the names, the
wedge labels, start before end, the segment labels, in the traversal order
of their segments, the region labels, the jump labels and the break labels. Section
8.5 places them among the background, the titles, frames and cards, and
the ancestor lines. Every
descriptor except the background carries `data-address`, the address of its
element; the several descriptors of one element carry the same address. An editor renders these same descriptors on
screen; the SVG writer serializes them.

| Element | Descriptors |
|---|---|
| background | `<rect x="0" y="0" width="{W}" height="{H}" rx="{rx}" fill="{fill}"/>` |
| group frame | `<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}">` filled and stroked (section 8) |
| card | when its `shadow` is not `none`, `<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" rx="{rx}" fill="{shadow}">`, not stroked; then `<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}">` filled and stroked (section 8.4) |
| a line's start | `<line x1="{Xs}" y1="{y}" x2="{Xl}" y2="{y}">`, `Xl` where the line stops; `<circle cx="{Xs}" cy="{y}" r="{w}">`, except where an ancestor line runs on |
| arrowhead | the line stops at `Xe`; `<polygon points="{Xe+3w},{y} {Xe},{y−1.5w} {Xe},{y+1.5w}">` |
| open arrowhead | the line stops at `Xe`; the same `<polygon>` with `fill="none"`, stroked in the line's `stroke` with width `w/2` and no dash |
| end circle | the line stops at `Xe`; `<circle cx="{Xe}" cy="{y}" r="{w}">` |
| diamond | the line stops at `Xe − 1.5w`; `<polygon points="{Xe−1.5w},{y} {Xe},{y−1.2w} {Xe+1.5w},{y} {Xe},{y+1.2w}" fill="none">` stroked in the line's `stroke` with width `w/2` and no dash |
| chevrons | two `<polyline points="{p1} {p2} {p3}" fill="none">`, inner one first, stroked in the line's `stroke` with width `w/2` and no dash (section 8.3) |
| wedge | `<polygon points="{X},{yt} {X−3},{yb} {X+3},{yb}">`, `yt` its tip and `yb` its base (section 6.6) |
| map | `<polygon points="{Xs},{yc−d/2} {Xe},{yc−d/2} {Xe},{yc+d/2} {Xs},{yc+d/2}" fill="none">` stroked |
| region | `<path d="{brace}">` |
| jump | `<path d="M{P0}C{C1} {C2} {Bh}">`, the shaft; `<polygon>` arrowhead `{P3} {Bh − 2w × n} {Bh + 2w × n}`, `n = (−uy, ux)` (section 6.6) |
| break | `<line x1="{x}" y1="{yf}" x2="{x}" y2="{y2}">` (section 6.4) |
| boundary | `<line x1="{X}" y1="{y−k}" x2="{X}" y2="{y+k}">` (section 6.6) |
| name, label | `<text x="{x}" y="{baseline}" text-anchor="{a}" font-size="{s}">`, `a` `start` for names and break labels, `middle` for the centred labels |

The **stroke attributes** are `stroke`, `stroke-width` and, unless it is
`none`, `stroke-dasharray`. A path carries `fill="none"` and a line no
`fill`; both carry the stroke attributes; a circle, a polygon
and a text carry `fill`, and the open arrowhead, the diamond and the map's
outline, the stroked polygons, also the stroke attributes (the map's dash
included); a polyline carries `fill="none"` and the stroke attributes; a
group frame and a card carry `fill` and the stroke attributes, a card's
shadow `fill` alone. A line's descriptors are, in this order, its `<line>`,
its start circle or left chevrons, and its end or right chevrons. Every
descriptor of an element, a card's shadow included, carries the element's
`opacity`, written when it is not 1. An
element without text is written self-closing (`<line …/>`); a text is written `<text …>{text}</text>`. Attributes are
written in this order, except the background's, which follow its template
and then `opacity`: `data-address`, the template's geometric attributes
(`x`, `y`, `width`, `height`, `x1` to `y2`, `cx`, `cy`, `r`, `points`, `d`)
in the order shown, `rx`, `text-anchor`,
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
<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}" font-family="DejaVu Sans" text-rendering="geometricPrecision" style="font-kerning:none;font-variant-ligatures:none">
<g transform="translate({X} {Y}) scale({z})">
...
</g>
</svg>
```

with one `<g>` per drawing, `(X, Y)` its position on the page, and
` scale({z})` left out when `z` is 1. `text-rendering="geometricPrecision"`
keeps a renderer from hinting small text, which would move its glyphs off
the advance widths the layout measured. In text, `&`, `<` and `>` are written
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
| rect | `\path[{options}] ({x},{H − y − h}) rectangle ({x + w},{H − y});`, the background with `x = y = 0`, `w = W`, `h = H` |
| line | `\path[{options}] ({x1},{y1}) -- ({x2},{y2});` |
| circle | `\path[{options}] ({cx},{cy}) circle[radius={r}];` |
| polygon | `\path[{options}] ({p1}) -- ({p2}) -- … -- cycle;` |
| polyline | `\path[{options}] ({p1}) -- ({p2}) -- ({p3});` |
| path | `\path[{options}] ({P0}) .. controls ({C1}) and ({C2}) .. ({P3});`, a brace's quadratic `Q C P` from the current point `P0` written as the cubic with controls `P0 + 2/3 × (C − P0)` and `P + 2/3 × (C − P)`, computed as section 3.3 states (the factor `2/3` formed first), an `L P` as `-- ({P})` |
| text | `\node[anchor={base west|base},inner sep=0,{options}] at ({x},{baseline}) {{text}};` with `text=tsRRGGBB` for the fill |

Options are written in the order of the attributes of section 7.2. In text,
`\` becomes `\textbackslash{}`, `~` becomes `\textasciitilde{}`, `^`
becomes `\textasciicircum{}`, each of `# $ % & _ { }` is preceded by
`\`, and a space at the start or end of a text or after another space is
written `\ `, so that TeX keeps it.

## 8. The box: bundles, frames and cards

Every file is drawn as a **bundle**: a bundle file as itself; a group file
as an **anonymous bundle** holding its group; a timeline file as an
anonymous bundle holding its top-level timeline as an ungrouped root. An
anonymous bundle has no title, and is one naming step from a bundle file.
Every timeline drawn as a root (a member or an ungrouped root) is drawn as
sections 3 to 6 draw a root, in its own **card**, and all of them share
one graphical length `L` and one start `x0`, so that by definition they
start and end at the same points.

### 8.1 What is drawn

- **Groups.** A bundle draws its groups in canonical order (by id), and
  then every **ungrouped root**, a root of `timelines` that no group names
  as a member and that contains no member, in canonical order (by id). A
  root that contains a member is drawn only as an ancestor line of that
  member.
- **Frames.** Each group is a **frame**, a `group` element: a rounded
  rectangle holding the group's title and then its members' cards, one
  under the other, in the group's display order: `graphical.order` (in a
  bundle file, `graphical.order` under the group's id), or `members` when
  absent. An ungrouped root has no frame.
- **Cards.** Each member and each ungrouped root `M` lies in a **card**, a
  `card` element with the address `M/card`: a raised rounded rectangle
  around `M`'s member drawing (in the tree below, a card holds nothing). The card is the same whether it lies on the
  grey box or in a frame.
- **Member drawings.** A **member drawing** is the drawing of sections 3
  to 6 of one timeline `M` taken as the root: its line is a `timeline`
  element, its wedges mark its own `0` and `length`, and positions are on
  `M`'s axis (section 3.1). A member that is a child timeline in
  `timelines` is still a `timeline` element in its member drawing, so
  statements selecting `child` do not reach its line, and it ends with the
  diamond (section 6.6). Such a member's drawing also has an **ancestor
  band** (section 8.3).
- **Titles.** A group's title, a `name` element with the address `G/name`,
  opens its frame. A bundle file opens with the bundle's title, a `name`
  element with the address `D/name`; an anonymous bundle has none.

The tree of section 2.1: the `block` holds the bundle's title, the frames,
and the cards and `timeline` elements of the ungrouped roots; a frame holds
its title and its members' cards and `timeline` elements; a card holds
nothing; a member's `timeline` element holds what a root holds (section
2.1) and its ancestor lines; an ancestor line holds its `name` and its
marks of the member's start and end, each mark holding its `label`.
`within` names a timeline at any depth of `timelines`; a timeline's depth
(section 2.5) is its depth in its root's tree, the roots being 1.

### 8.2 Horizontal

The **name column** of the whole box starts at `xn = P + Q + K` when the
box holds a frame and at `xn = P + K` otherwise: inside the cards, at the
same x for every card. Every row name of every member drawing, ancestor
names included, is drawn at `x = xn`. `N` is the width of the widest name
of any member drawing (section 6.7), and `G' = 8` when any such name is
drawn and 0 otherwise; titles are not names of rows and count for neither.
The shared start is

    x0 = max(xn + N + G', max over i of (xn + wi / 2 − L × ui), max over a of (xn + N + G' + 8 × wa))

where `i` runs over every centred label of every member drawing (section
6.7, with the member's own proportions) and `a` over every ancestor line
that runs on to the left (section 8.3), `wa` its stroke width. So no label
crosses the name column's left edge, and no chevron crosses the gap after
the names.

Let `R` be the largest right edge of every member drawing (section 6.7)
and of every title, a group's title starting at `P + Q` and the bundle's at
`P`, or `x0` when none of them draws anything. A card inside a frame spans `x = P + Q` to `R + K`; a frame spans `x =
P` to `R + K + Q`; an ungrouped root's card spans `x = P` to `R + K + Q`
when the box holds a frame and to `R + K` otherwise, so that every frame
and every ungrouped card of a box ends at one x.

### 8.3 Ancestor lines

For a member `M` that is a child timeline, let `A1, …, Ak` be its
ancestors from its root `A1` down to its parent `Ak`. Each `Aj` has an
**ancestor line**, an `ancestor` element with `Aj`'s address, drawn at
`M`'s scale and clipped to `M`. On `M`'s axis `Aj` starts at `ts = −(o(j+1)
+ … + o(k) + oM)`, the negated sum of the offsets from `Aj` down to `M`
(`oM` being `M`'s own offset in `Ak`, `o(j+1)` that of `A(j+1)` in `Aj`), and
ends at `te = ts + ` `Aj`'s `length`, combined as section 3.1 combines
values; `ts ≤ 0` and `te ≥ λ`, `λ` being `M`'s length, since a child lies
within its parent. With `w` the line's stroke width and `y` its ordinate:

- **On the left**, when `ts < 0` (compared exactly) the line **runs on**:
  it starts at `Xa = x0 − 4w` and ends in a double chevron pointing left,
  the inner one through `(Xa − w, y − 1.5w)`, `(Xa − 2.5w, y)` and `(Xa −
  w, y + 1.5w)`, the outer one the same `1.5w` further left, through `(Xa −
  2.5w, y − 1.5w)`, `(Xa − 4w, y)` and `(Xa − 2.5w, y + 1.5w)`, so its tip
  is at `x0 − 8w`. When `ts = 0` the line starts at `x0` with its circle.
- **On the right**, when `te > λ` the line runs on to `Xr = x0 + L + 4w`
  and ends in a double chevron pointing right, mirrored: the inner one
  through `(Xr + w, y − 1.5w)`, `(Xr + 2.5w, y)` and `(Xr + w, y + 1.5w)`,
  the outer one `1.5w` further right, through `(Xr + 2.5w, y − 1.5w)`, `(Xr
  + 4w, y)` and `(Xr + 2.5w, y + 1.5w)`, its tip at `x0 + L + 8w`. When `te =
  λ` the line ends at `x0 + L` with `Aj`'s own end (section 6.6): the
  arrowhead, open arrowhead or circle of a top-level timeline, the diamond
  of a child.
- **Marks.** Two wedges mark `M`'s start and end on `Aj`'s axis: `wedge`
  elements with the addresses `M/start` and `M/end`, always on the line's
  above side, whatever their `side`, each with its tip on the line's edge (`y − w / 2`) and its base 13
  further up, at `x0` and `x0 + L`. Each is labelled with the coordinate it
  marks in `Aj`'s unit: `−ts` and `−ts + λ`, combined as section 3.1
  combines values. The two labels are placed by first fit, start before
  end, into tiers above the base, as the root band places its wedge
  labels (section 6.4).
- **Nothing else** of `Aj` is drawn: no maps, regions, flow, boundaries or
  other descendants. Its name is drawn in the name column on its row
  (section 6.6, names).

The **ancestor band** is the outermost band of the member drawing's above
side, after the bands of section 6.4. It starts at the larger of `p0 / 2`
and, when a band precedes it on that side, that band's outer edge plus `B`.
It holds one row per ancestor, `Ak` nearest the member's line and `A1`
outermost. Row `j` (counted from `Ak`) has the row pitch `qj` of its name's
font size (`p` of section 6.2), an inner half `ij = qj / 2` and an outer half `oj`, the larger of
`qj / 2` and the reach of its marks, `w / 2 + 13`, or `w / 2 + 13 + 2 + T ×
h(9)` (left to right) when their labels fill `T ≥ 1` tiers (9 standing for
its labels' largest font size), or `qj / 2` alone when no mark is drawn. An
ancestor line that is not displayed draws neither its name nor its marks
and has no row, as the maps of an undisplayed timeline take no room. Its line lies at `c0 + i1` for the first row,
`c0` the start of the band, and `oj + i(j + 1)` beyond the row before. The
band is `i1 + o1 + … + ik + ok` wide, summed in that order.

### 8.4 Vertical

Every member drawing has its own height `Hm`, its content height `Hc` of
section 6.5 with its ancestor band included in `Ea`; its card is `Hm` high,
and the drawing's top is the card's top. The card padding `K` is
horizontal only: above and below, the member drawing's own padding `P × v`
(section 6.5) lies inside the card. A card's shadow lies 2 to the
right of and 2 below the card.

A frame or card spanning `x = a` to `b` and `y = c` to `d` is written with
`x` `a`, `y` `c`, `width` `b − a` and `height` `d − c`, its right and bottom
edges being `b` and `d`: a card's `b` is the end of its span (section 8.2)
and its `d` its top plus `Hm`, a frame's `d` its top plus its height below.
A card's shadow is written at `x + 2` and `y + 2` with the card's `width`
and `height`, and its right and bottom edges are `b + 2` and `d + 2`.

- **A frame** is laid out from its top: the title's baseline lies at `top +
  Q + a(s)`, `s` the title's font size, so the title sits at the top of a
  slot `h(s)` high, unlike a row name, which is centred on its row. The
  first card starts at `top + Q + h(s) + 4` (at `top + Q` when the title is
  not displayed), and each further one `F` below the previous one's bottom.
  The frame is `Q + h(s) + 4 + Hm1 + F + Hm2 + … + F + Hmn + Q` high,
  summed in that order, without `h(s) + 4` when the title is not displayed.
- **The box.** The bundle's title, when there is one, is drawn at `x = P`,
  with its baseline at `P + a(s)`; the first frame or ungrouped card starts
  at `P + h(s) + F` (at `P` when there is no title or it is not
  displayed), and each further one `F` below the previous one's bottom.

Within a member drawing, the root's line lies at the drawing's top plus the
`y_root` of section 6.5, computed in that order; every other ordinate
follows from that line as section 3.3 states. The box's padding `P` is
not stretched by `v`. The box's content is `Wb = P` plus
the largest right edge of any frame or card, a card's shadow included, or
of the bundle's displayed title, wide, and `Hb = P` plus the largest bottom
edge of any frame or card, a card's shadow included, or of the bundle's
displayed title, whose slot ends at `P + h(s)`, high (`P + x0` and `P` when
the box holds none of these). A frame or card that is not displayed is not drawn but keeps
its place, since member drawings lie in it: the layout, `xn`, `Wb` and `Hb`
are as when it is displayed, except that a hidden card's shadow is not
drawn and does not count. The
box is `W = max(Wb, width)` wide and `H = max(Hb, height)` high (`W = Wb`
when `width` is `null`, `H = Hb` when `height` is); the
background is a rectangle filling it with corner radius `rx`.

### 8.5 Descriptors

A file becomes element descriptors in this order: the background; the
bundle's title; then, for each frame in drawing order, the frame, its
title, and for each of its members in display order, the member's card and
the descriptors of its member drawing; then, for each ungrouped root, its
card and the descriptors of its member drawing. The descriptors of a member
drawing follow section 7.2, with its ancestor lines, from `A1` to `Ak`,
each with its chevrons, just before its root; their marks, from `A1` to
`Ak`, each ancestor's start mark before its end mark, first among its
wedges; their names, from `A1` to `Ak`, first among its names; and their
mark labels, from `A1` to `Ak`, each ancestor's start label before its end
label, first among its wedge labels. A title is a text descriptor of section 7.2, anchored at `start`;
its `content` and `max-width` apply as section 6.6 applies them to a row's
name.
