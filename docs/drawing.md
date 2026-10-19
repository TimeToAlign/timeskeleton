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
that holds member drawings. Every manifest is drawn as one box, whether it
holds one timeline or many, groups or none: its groups as frames and its
ungrouped roots as cards. Terms in `code` are JSON members.

## 1. Inputs and output

`draw(manifest, placement, layers, metrics)` returns the manifest's drawing.

- `manifest`: a TimeSkeleton manifest, read in its complete form, every
  key the manifest leaves out taking its default (README, "Defaults"), and
  in canonical order (README, "Canonical order"), whatever form and order it
  was written in. Its `graphical` block holds the manifest's own style
  statements and its `order` (section 2).
- `placement`: chosen by whoever places the drawing, such as an editor's
  canvas or a script:
  - `length`, the **graphical length** `L` of every item of the box
    without a length of its own (section 8.6), in canvas units (default
    400): the distance from a root's start to its end;
  - `spacing`, the box's **spacing**, the gap in canvas units between its
    items that lie at their default `y` (section 8.6), a finite number ≥ 0
    (default 8). A frame's and a card's spacing are entries of `places`
    (section 8.6); none multiplies another;
  - `width` and `height`, the requested **box size** in canvas units, or
    `null` (the default) for the content's own size;
  - `places`, the **places** of the box's items and the sizes of its
    members' cards (section 8.6): an object whose keys are the ids of
    groups, of ungrouped roots and of members, each value an object with
    any of the members `x`, `y`, `length`, `scale`, `spacing`, `width` and
    `height` (default `{}`).
- `layers`: the statement lists that style the drawing, from the lowest to
  the highest precedence: the defaults of section 4, then any lists an
  application supplies below the manifest (such as an editor's settings),
  then the manifest's own `graphical` block. No layer lies above the
  manifest: a drawing's own styling is its manifest's. Section 2 defines
  them.
- `metrics`: the advance widths of the font of section 5.

The drawing is a **box** of width `W` and height `H` and a list of drawn
**elements** in box-local canvas units, origin at the box's top-left corner,
y downwards, and the box-local position `(Ox, Oy)` of the **place origin**,
from which places are measured (section 8.6). Every element carries its
**address** (section 2.2) and, where it shows a coordinate, the exact
coordinate it shows. Canvas units become
pixels in SVG and points in TikZ (section 7).

A drawing does not depend on its position on a canvas, nor on its scale: a
canvas or a writer places the box at a position and scales it uniformly by
a **scale** factor `z` (section 7.1). The three ways of resizing a drawing
change one input each:

| Resize | Input changed | Effect |
|---|---|---|
| Scale | scale `z` | everything scales, proportions kept, text included |
| Box | `width`, `height` | only the box changes; the content keeps its place at the top left; the box never becomes smaller than the content (section 8.4) |
| Stretch | `length` (horizontal), `spacing` (vertical), both (a corner); `width`, `height` where a box size is requested | horizontally, distances along time stretch; vertically, the gaps between the container's contents grow or shrink; markers, line widths and text keep their size; the box follows the content (below) |

On a stretch, a requested box size larger than the content keeps its
proportion to the content, so the box follows the stretched content and
every margin it adds stretches with it: `width` (or `height`) becomes the
request times the stretched content's size divided by the content's size
before the stretch, multiplied first, in binary64 (an editor may round the
result to the grid it stores numbers on). A request no larger than the
content before the stretch becomes `null`, and `null` stays `null`. A
horizontal Stretch of the box scales every `x`, `length` and `width` that
`places` states by the ratio of the lengths, and keeps every `scale`; a
vertical Stretch changes the box's `spacing` alone, so it moves the items
at their default `y` and keeps every stated `y` and `height`.

Every frame and card of the box is resized in the same three ways,
changing entries of `places` only (section 8.6). An item, a group's frame
or an ungrouped root's card: Scale changes its `scale`, Box its `width`
and `height`, Stretch its `length` (horizontal), its `spacing` (vertical)
or both (a corner), its `width` and `height` following the stretched
content as the box's do. A member's card: Scale and the horizontal Stretch
change its group's `scale` and `length`, since the members of a group
share them; the vertical Stretch changes the card's own `spacing`; Box
changes the card's own `width` and `height`. An item's or card's content,
for this rule, is its frame or card without its own request (for a
member's card, without its frame's request too, since the frame's width
widens its cards), in item coordinates: for `width` its right edge less its left (section 8.2), for
`height` its height of section 8.4. Every requested `width` or `height`
of a frame or card whose content a Stretch of an item or a member's card
changes keeps its proportion to
that content by the rule above: a horizontal Stretch of a group, from its
frame or a member's card, rescales every requested width of the frame and
of its members' cards, so the members' lines keep one length and every
margin stretches with them; a vertical Stretch of a frame, which changes
only the gaps between its cards, rescales its own requested height, and of
a card its own and its frame's.

## 2. The `graphical` block

```json
"graphical": {
  "styles": {
    "highlight": {"stroke": "#7F00FF", "fill": "#7F00FF"}
  },
  "statements": [
    {"select": {"element": "label"}, "set": {"fill": "#404040"}},
    {"select": {"element": "wedge", "within": "performance"}, "set": "highlight"},
    {"select": {"ids": ["score/region_1"]}, "set": {"display": "none"}}
  ]
}
```

The block is optional; an absent block draws with the other layers alone.
`styles` maps a style name to a **declaration**, an object of properties
(section 2.4) and their values. `statements` is a list of **statements**,
each a selector (`select`, section 2.3) and either a declaration or the name
of a style in the same layer's `styles` (`set`). The order of the
statements matters, so writers never reorder them. Every layer of section 1
has this shape. The manifest's own block also holds `order`, which no other
layer holds: it maps a group's id to the display order of the group's
members (section 8.1) and a timeline's id to the timeline's band order
(section 6.4).

A reader that meets statements naming styles its `styles` does not hold
issues one warning naming every missing style, and adds each to `styles` as
an empty declaration; such a statement then sets nothing, and the block is
valid.

### 2.1 Elements

Every drawn thing is an **element** of one **type**, and so is every band
of a timeline, which draws nothing of its own:

| Type | What it is |
|---|---|
| `block` | the box's background |
| `card` | the raised container of a timeline drawn in its own card: a group member or an ungrouped root (section 8) |
| `timeline` | the line of a timeline drawn in its own card (section 8) |
| `child` | a child timeline's line, at any depth |
| `band` | one of the five bands of a timeline, holding its markers, conversion maps, children, regions or flow control (below; section 6.4) |
| `boundary` | the start of a segment on its segment line, drawn as a thin vertical rule (section 6.4) |
| `ancestor` | the faded line of an ancestor of a member that is a child timeline, clipped to the member (section 8.3) |
| `group` | a group's frame (section 8) |
| `map` | a conversion map, drawn as a closed double line |
| `region` | a region, drawn as a brace |
| `break` | a flow-control break, drawn as a vertical line |
| `jump` | a flow-control jump, drawn as an arc with an arrowhead |
| `wedge` | a marker of the root's start or end; on an ancestor line, the member's start or end on the ancestor's axis (section 8.3) |
| `name` | the name of a row, in the name column, or the title of a group or of the manifest (section 8) |
| `label` | any other text: a coordinate, or the label of a region, jump, break or segment |

An element **belongs** to a timeline (section 2.2); the `block`, a `group`
and the titles of a group or of the manifest belong to none, and have no
domain, modality or class. A card belongs to the timeline it holds, and so
has its domain, modality and class. A band belongs to its timeline but has
no domain and no modality, so no selector naming them matches it, and what
it holds inherits through it its timeline's values unless a statement
matches the band itself (section 2.5). An element has the **domain**
(`graphical`, `logical` or `physical`) and the **modality** (`continuous`
or `discrete`) of its timeline's `unit`. A map instead has the domain and
modality of the map's `target_unit`, so a map is drawn in the style of the
timelines it converts to:

| Domain | Units |
|---|---|
| `logical` | `number`, `floating_measures`, `whole_note`, `quarters`, `ticks` |
| `physical` | `milliseconds`, `seconds`, `minutes`, `samples`, `frames` |
| `graphical` | `pixels`, `meters`, `centimeters`, `millimeters`, `inches`, `points` |

`ticks`, `samples`, `frames` and `pixels` are discrete, every other unit
continuous. A map whose `target_unit` is null has no domain and no
modality, so no selector naming them matches it and it inherits its style
through its band (section 2.5). An element's **class** is the timeline
class its timeline's unit decides: `Continuous` or `Discrete` for the
modality, then `Logical`, `Physical` or `Graphical` for the domain, then
`Timeline` (`seconds` decides `ContinuousPhysicalTimeline`, `ticks`
`DiscreteLogicalTimeline`). A manifest writes no class; the unit decides
it. A map instead has the map's `type` (`QuartersToTicks`, …), and a band
its **kind**: `markers`, `conversion_maps`, `children`, `regions` or
`flow_control`.

Elements form a **tree** that carries inheritance (section 2.5): the
`block` holds the `timeline`; a `timeline` or `child` holds its five
bands, and each band what it holds: the markers band the timeline's
wedges, the conversion maps band its maps, the children band its child
timelines, the regions band its regions, and the flow control band its
breaks and jumps; an element holds its own `name` and `label` where it has
one (section 5.3; a map and a band have neither), except that a segment's
label and its `boundary` are held by its segment line, directly and in no
band, as parts of that line (section 6.4). A segment is a child timeline of
its segment line, held by its children band. One that is not a segment
line is a node of the tree although no line of its own is drawn, holding
its five bands as a line does, whose content is drawn at its segment
line's line (section 6.4), and has no element type, so `inside` never names
it; one that is a segment line is drawn as a `child` (section 6.1).
Section 8 states the top of the tree: the block, frames, cards and
ancestor lines.

### 2.2 Addresses

Every timeline, group, conversion map, region, break, jump and marker of a
manifest carries an `id`, and so may the manifest itself; an id is a
non-empty string without `/` and without control characters. Timeline ids
(of roots and descendants alike), group ids and the manifest's id are
unique together across the manifest; every other id is unique within the
tree of the root that holds it (README, "Identity"). One rule addresses
every element of every manifest, one timeline or many:

- a timeline, a group or the manifest is addressed by its bare id;
- every other element with an id of its own (a conversion map, region,
  break, jump or marker) is addressed by the id of the root of `timelines`
  whose tree holds it, `/`, and its own id;
- a part of an element is addressed by that element's address, `/`, and
  the part's word: `start`, `end`, `name`, `label` or `card`;
- a band of a timeline, root or child, is addressed by the timeline's id,
  `/`, and the band's id: its kind (section 2.1), `_` and its number.
  Every timeline has five bands, one of each kind, each numbered 1.

The five part words are reserved, and so is every id that matches
`^(markers|conversion_maps|children|regions|flow_control)_[1-9][0-9]*$`,
whatever its number: no id of a manifest may be one of them or match the
pattern, so an address is read without ambiguity.

An address is compared as a whole string. In this table `T` is a
timeline's id, `r` the id of the root whose tree holds the element, and `C`
an element's address:

| Element | Address | Belongs to |
|---|---|---|
| the root, or a child timeline with id `T` | `T` | `T` |
| the bands of a timeline with id `T` | `T/markers_1`, `T/conversion_maps_1`, `T/children_1`, `T/regions_1`, `T/flow_control_1` | `T` |
| a conversion map with id `M` on `T` | `r/M` | `T` |
| a region with id `R` of `T`'s `regions` | `r/R` | `T` |
| a break with id `B` of `T`'s `flow_control.breaks` | `r/B` | `T` |
| a jump with id `J` of `T`'s `flow_control.jumps` | `r/J` | `T` |
| the root's wedges at its start and end, the root's id being `T` | `T/start`, `T/end` | `T` |
| the name of an element with address `C` | `C/name` | that element's timeline |
| the label of an element with address `C` | `C/label` | that element's timeline |
| the card of a timeline with id `T` | `T/card` | `T` |
| the boundary of a segment with id `S` | `S/start` | `S` |
| the label of a segment with id `S` | `S/label` | `S` |
| the ancestor line of a timeline with id `A` | `A` | `A` |
| the marks of the start and end of a member `M` on an ancestor line | `M/start`, `M/end` | `M` |
| the frame of a group with id `G` | `G` | none |
| the title of a group with id `G` | `G/name` | none |
| the title of the manifest | `name` | none |

So a region `region_1` of a timeline in the tree of root `score` is
`score/region_1` and its label `score/region_1/label`, whether the manifest
holds `score` alone or many roots, and also when a member below `score` is
drawn as the root of its own member drawing; a jump `jump_1` of the root
`score` itself is `score/jump_1`, its label `score/jump_1/label`. A band
follows its timeline's own address, as a card does: the regions band of a
child `b` of `score` is `b/regions_1`. The
manifest's title is addressed `name` whether or not the manifest has an
`id`, so naming a manifest, or giving it an id, changes no address. The
manifest's own id addresses the manifest, which draws no element of its
own: the block has no address. A marker is addressed like a region but is
not drawn.

One timeline may be drawn more than once, as an ancestor line of several
members or also as a member, and a member's start and end are marked on its
own line and on each of its ancestor lines (section 8.3); every drawing of
an element carries its address.

### 2.3 Selectors

A selector is an object with any of these members:

- `element`: an element type;
- `ids`: a non-empty list of distinct addresses;
- `domain`, `modality`: a domain, a modality;
- `class`: a timeline class (section 2.1), a conversion-map type or a
  band's kind;
- `within`: a timeline id; it matches the elements belonging to that
  timeline or to any of its descendants;
- `inside`: an element type; it matches the elements held, at any depth,
  by an element of that type in the tree of section 2.1 (so
  `{"element": "name", "inside": "ancestor"}` matches the names of ancestor
  lines and no other name).

An element matches a selector when it matches every member present. The
empty selector `{}` matches every element. A band is selected as every
element is: `{"element": "band"}` matches every band, `{"element": "band",
"class": "regions"}` every regions band, `{"ids": ["score/regions_1"]}` the
regions band of `score`, and `{"inside": "band"}` everything that bands
hold, the bands of every timeline but a member drawing's root included,
since a child is held by its parent's children band.

### 2.4 Properties

Presentation properties carry SVG's names and values; the writers map them
to TikZ (section 7.4).

| Property | Values | Inherited | Read by |
|---|---|---|---|
| `stroke` | `#RRGGBB` (upper-case) or `none` | yes | every type but `block`, `band`, `wedge`, `name` and `label` |
| `stroke-width` | a number ≥ 0 | yes | as `stroke` |
| `stroke-dasharray` | `none`, or numbers separated by single spaces | yes | as `stroke` |
| `fill` | `#RRGGBB` or `none` | yes | `block`, `group`, `card`, `timeline`, `child`, `ancestor` (the circles at their start and end, the arrowhead at their end), `jump` (its arrowhead), `wedge`, `name`, `label` |
| `opacity` | a number from 0 to 1 | no | every type but `band` |
| `font-size` | a number > 0 | yes | `name`, `label` |
| `rx` | a number ≥ 0 | no | `block`, `group`, `card` (the corner radius) |
| `shadow` | `#RRGGBB` or `none` | no | `card` (the colour of its offset shadow, section 8.4) |
| `display` | `inline` or `none` | no | every type but `block` |
| `content` | a text, or `none` | no | `name` (a row's own name, section 6.6) |
| `max-width` | a number > 0, or `none` | no | `name` (section 6.6) |

A statement may set any property on any element; an element ignores the
properties its type does not read. `display: none` is the filter: an element
that is not displayed is not drawn and takes no room. An element is
**displayed** when its `display` is `inline` and no rule of this list hides
it. The list holds every way in which one element hides another, and the
other sections refer to it:

- **A band hides everything it holds.** A band that is not displayed hides
  every element it holds, at any depth of the tree of section 2.1.
- **An element hides its label.** The label of a wedge, region, jump or
  break is displayed only when that element is displayed.
- **A line hides its timeline's whole drawing.** A line that is not
  displayed, the root's and a child's alike, hides its name, the maps,
  boundaries and segment labels on it (section 6.4), and its five bands
  with everything they hold, at any depth, its children and its segments
  with everything of theirs included. It takes no room, its stroke
  included: a child whose line is not displayed is not placed and has no
  row (section 6.4, Children), and section 6.5 states what a member
  drawing whose root's line is not displayed still draws.
- **A segment without a line hides its bands.** A segment that is not a
  segment line has no line of its own (section 6.1); when it is not
  displayed, its five bands and everything they hold are not displayed
  either, so it adds nothing to its segment line's bands (section 6.4,
  Segments without a line). The boundary and the label of a segment, of
  either kind, are parts of its segment line's line (section 2.1): that
  line hides them, the segment never does.
- **An ancestor line hides its name and its marks.** An ancestor line
  (section 8.3) that is not displayed hides its name and its marks of the
  member's start and end, with their labels, and has no row.

No other element hides another. A frame or card that is not displayed
keeps everything drawn in it (section 8.4); a member's line keeps its
ancestor lines, which are no part of its timeline's drawing; and no band
takes its `display` from another: hiding `score/regions_1` hides the
regions of `score` alone, and the regions of a child of `score` are drawn,
at the child's own line, only when the child's own regions band is
displayed. The defaults hide some bands (section 4).

### 2.5 The cascade

The value of a property on an element is found per property:

1. Of the statements matching the element that set this property, the
   highest-ranking sets it.
2. When none sets it and the property is inherited, the element takes its
   parent's value in the tree of section 2.1.
3. Otherwise the property's initial value applies: `stroke` `none`,
   `stroke-width` 1, `stroke-dasharray` `none`, `fill` `none`, `opacity` 1,
   `font-size` 9, `rx` 0, `shadow` `none`, `display` `inline`, `content`
   `none`, `max-width` `none`.

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
coordinate. Where a length is `null`, section 3.4 says where the timeline
ends.

A coordinate's value is read as its number type selects: a `float` value is
a float, an `int` or `fraction` value is exact. Values combine as Python's
numeric tower combines them: the sum of two exact values is exact; a sum
involving a float converts each exact operand to the nearest double (ties
to even) and adds in IEEE 754 binary64 arithmetic, rounding to nearest,
ties to even.

The **midpoint** of two positions `a` and `b`, on which section 6 centres
a segment label, a region's brace tip and label and a jump's label, is
`(a + b) / 2` in the same arithmetic: the sum `a + b` combined as above,
then halved, exactly when the sum is exact and as a binary64 division by 2
when it is a float. On a float axis it is therefore the double sum halved,
not the exact midpoint of the two doubles rounded once.

The format and both validators accept a child whose offset is negative,
which starts before its parent's zero. The readers of timetoalign and
TimeLineEditor refuse such a child as not supported yet, and this version
of the specification does not draw it.

### 3.2 From the axis to the canvas

A position `t` on the root's axis, with `λ` the root's length, or its reach
when its length is `null` (section 3.4), becomes the **proportion** `u = t
/ λ`: an exact quotient when both are exact, then
rounded once to the nearest double; a binary64 division when either is a
float; 0 when `λ` is 0. Its x in item coordinates (section 8.2) is

    x(t) = x0 + L × u

in binary64, `x0` the start of the root's line (section 8.2). This is the
only step from an exact value to a double, at any depth of nesting. Labels
show the exact coordinate, never the double.

### 3.3 Canvas arithmetic

Every other number of a drawing is a double, computed in IEEE 754 binary64
in the order its formula is written, left to right, multiplications and
divisions before additions and subtractions, and a constant factor such as
`4/3`, `9.5w`, `8w`, `5.5w`, `4w`, `2w`, `1.5w`, `1.2w` or `2.5w` formed before it multiplies
(`1.2w` is the double nearest the exact product of 6/5 and `w`, not the
binary64 product of the double `1.2` and `w`). A distance outwards is
summed whole, left to right as written and a label gap of 2 included,
before it becomes an ordinate `yl − o` or `yl + o`, `yl` the ordinate of
the line of the timeline whose band it lies in (section 6.4); the
boundaries and segment labels of a line are offset from that line (section
6.4), the marks of an ancestor
line and their labels from that line (section 8.3), and a break label from
the flow row (section 6.4). A label's baseline is then that ordinate plus
`a(9)` or minus `d(9)`. `max` and `min` compare exactly.

### 3.4 Timelines of unknown length

A timeline whose `length` is `null` has an unknown length: the manifest
does not say where it ends, and the drawing never invents an end for it.
A root of unknown length is scaled to its reach; the end of a timeline of
unknown length is found by the rules below, and is marked as open where
they say so.

**The reach** of a timeline `T` is a value on `T`'s own axis: the largest
of the zero of `T`'s number type and of every coordinate its content
reaches on that axis, which is

- for each child at offset `o`, `o` plus the child's length, or, when the
  child's length is `null`, `o` plus the child's own reach, recursively;
- the `start` and the `end` of each region;
- the `coordinate` of each break and of each marker;
- the `from_coordinate` and the `to_coordinate` of each jump;
- for each row of the `measure_map` that holds both `qstamp` and
  `actual_length`, `qstamp + actual_length`.

Sums combine as section 3.1 combines values. The values compare exactly;
of several equal largest values, an exact one (`int` or `fraction`) is
taken before a float. Content counts whether or not it is displayed, so a
style never changes a scale. Conversion maps are not content. A timeline
without content, or whose content reaches no further than its start, has
the reach 0. The reach is a coordinate on an axis; the distances that
sections 6 and 8 call the reach of a map stack, a line, a band or a mark
are canvas distances outwards from a line, and have nothing to do with it.

**The end.** Every drawn timeline `T` starting at `S` (section 3.1) ends
at a position on the root's axis, and its end is either **known** or
**open**. The first of these rules that applies gives it:

1. `T`'s length is a value: `T` ends at `S` plus its length; known.
2. `T` is the root of its member drawing: it ends at `λ`, its reach;
   open.
3. `T` is a segment followed by another segment, in canonical order: it
   ends where the next segment starts; known, since the segment line fixes
   it.
4. `T` is the last segment of its segment line: it ends where its segment
   line ends; known or open as that end is.
5. Otherwise: `T` ends at `S` plus its reach; open.

The reach does not follow these rules. A segment of unknown length that is
followed by another counts towards its segment line's reach as every child
of unknown length does, with its offset plus its own reach, never with the
end rule 3 gives it; so when its content runs past the next segment's
start, that content counts towards the reach all the same, and is drawn
where it lies, past the segment's end.

`Xe`, `x` of the end, is `x` of the end's position (section 3.2), except
for an end that is the root's under rule 2, directly or through rule 4,
where `Xe = x0 + L` whatever the reach. So the reach of a
root of unknown length lies at the end of the graphical length, and a root
whose reach is 0 is still drawn `L` long, every position of it at `u = 0`
(section 3.2). A line whose end is open ends in three chevrons (section
6.6), never in a mark that would assert a position.

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
    {"select": {"element": "map"}, "set": {"stroke-width": 1}},
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
    {"select": {"element": "name", "inside": "ancestor"}, "set": {"fill": "#6B7280", "font-size": 9, "opacity": 1}},
    {"select": {"element": "band", "class": "markers", "inside": "band"}, "set": {"display": "none"}},
    {"select": {"element": "band", "class": "regions", "inside": "band"}, "set": {"display": "none"}},
    {"select": {"element": "band", "class": "flow_control", "inside": "band"}, "set": {"display": "none"}}
  ]
}
```

So a timeline takes the colour of its domain, dotted when discrete and
solid when continuous (dotted: dashes and gaps as long as the stroke is
wide); a conversion map takes the colour and pattern of the domain and
modality it converts to; wedges and braces are black and solid; jumps are
thin, black and dotted, and breaks dotted red; a name longer than 160 is
cut (section 6.6). Segment
boundaries are thin black rules; an ancestor line is its timeline's line,
faded, with faded marks and labels, and its name small and grey; a group's
frame is white with a light grey outline; a card is white with a grey
outline and a grey offset shadow, so that it stands out from the grey box
and from a frame alike. A card has its timeline's domain and modality, so
a statement can style the cards of one domain. The last three statements
hide the markers, regions and flow control bands of every timeline that is
held by a band, which is every timeline of a member drawing but its root
(a child is held by its parent's children band, a segment without a line
of its own too); every conversion maps band and every children band is
shown, so the nesting of a member drawing and every timeline's maps stay
visible.

The **default band order** of a root of `timelines` with the id `T`, when
`graphical.order` has no entry for it (section 6.4), is

```json
["T/children_1", "T/conversion_maps_1", "T", "T/markers_1", "T/regions_1", "T/flow_control_1"]
```

So by default a root's conversion maps lie against its line above it and
its children beyond them, its start and end wedges against its line below
it, then its regions and its flow control; its descendants follow it, so
every child's maps lie against the child's line above it and its own
children beyond them.

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
group, or of the manifest, is its `name`, or, when `name` is null, its `id`
without its scope. A manifest with neither a `name` nor an `id`, an
anonymous bundle, has no title.

## 6. Layout

### 6.1 Traversal

The **traversal** lists the timelines in pre-order: the root, then each
child in canonical order (by offset, compared by exact value, then by id,
compared by Unicode code point, whatever the order of the `children` keys), each followed by its own descendants.

A timeline whose `is_segment_line` is true is a **segment line**; its
children are its **segments**, contiguous from its start to its end. Every
segment lies on its segment line's line, which shows where it starts by a
**boundary** and its name by a label (section 6.4), both hidden with that
line (section 2.4). A segment that is not a
segment line has no line of its own: wherever this section speaks of its
line, it is its segment line's line.
A segment that is itself a segment line is drawn as a child line in its
segment line's children band (section 6.4, Children), and its own segments
lie on that line; neighbouring
segments drawn so meet end to start, the start circle of one inside the
open diamond of the other (section 6.6).

### 6.2 Constants

Distances marked with `S` depend on the card spacing `S` of the member
drawing (section 8.6), the gap between its rows and between its bands;
every other size is fixed. With the default `S = 4` every distance is the
number it has always had.

| Constant | Canvas units |
|---|---|
| padding `P` | 8 |
| gap between the name column and the root's start `G` | 8 |
| gap between bands | `S` |
| row pitch `p` | max(10 + S, h(s)) |
| map double-line spacing `d` | 2 |
| map gap `g` (1.5 × d) | 3 |
| wedge: base, height | 6, 13 |
| label gap (marker to label) | 2 |
| label separation (horizontal, between labels) | 2 |
| brace height | 6 |
| region row pitch `pr` | 6 + 2 + h(9) + S |
| first jump depth | 4 + S |
| jump row pitch `pj` | 6 + S + h(9) |
| break label offset | 3 |
| boundary half-height `k` | 8 |
| group frame padding `Q` | 8 |
| card padding `K` | 8 |
| gap after the manifest's title `F` | 8 |
| gap after a frame's title | 4 |
| card shadow offset | 2 |

`s` is the name font size of children bands laid out together (section
6.4, Children): the largest font size of the names of the lines in their
rows, displayed or not (section 6.6); a child whose line is not displayed
has no row. A row whose lines contribute
no name (a row of segment lines, section 6.6) counts the font size the
`name` of its first line has under the cascade. The root's row counts on
its own: its pitch `p0` takes the root's name size alone. A row's **name
size** and **pitch** are the `s` and `p` of the children bands laid out
together whose row it is, at any depth, and the root's name size and `p0`
for the root's row; so all rows of children bands laid out together have
one pitch. Wherever `h(9)`, `a(9)` or `d(9)`
appears in section 3.3, anywhere in section 6 or in section 8, 9 stands
for the largest font size of the drawn labels of the band in question, and
is 9 when the band draws no label; every line at level 0 (section 6.4)
counts as a band of its own, whose labels are its segment labels. So a
regions band whose regions have no drawn label still keeps the label room
`2 + h(9)` in its row pitch `pr`, and is as wide as one with labels of size
9. The labels of a flow
control band are its drawn jump labels and break labels together, so its
jump rows and break-label tiers share one size.

### 6.3 First fit

Several steps below place items one at a time, in a given order, into
numbered **rows** (or tiers) 1, 2, 3, …: an item goes to the lowest row
holding no item whose extent **conflicts** with its own. Extents are x
intervals measured from the root's start, at any depth of the member
drawing, each end computed as `L × u` (section 3.2) and never as a
difference `x − x0`, so no row depends on `x0`; an extent named by
positions below runs from `L × u` of the one to `L × u` of the other.
`[a1, b1]` and `[a2, b2]` conflict when `a1 < b2` and `a2 < b1`, or when
`a1 = a2`. So an item that starts where another ends shares its row, and
two items starting at the same point never do. The extent of a label is
`[left − 1, right + 1]`, so labels keep the label separation apart: for a
label of width `wi` centred on a position of proportion `u`, `[L × u − wi /
2 − 1, L × u + wi / 2 + 1]`, and for a break label, `[L × u + 3 − 1, L × u
+ 3 + wi + 1]`, each end computed left to right. Every band fills its own
rows.

### 6.4 Levels and bands

**Every timeline's bands.** Every timeline drawn with a line of its own,
the root and every child at any depth alike, has its five bands (section
2.2) at its own line, and this section lays them out for each such
timeline whose line is displayed (section 2.4) as for the root: a band's **timeline** is the timeline it belongs
to, and "its line", "above" and "below" are that timeline's. `yl` is the
ordinate of a timeline's line: `y_root` for the root (section 6.5), and for
a child the ordinate its row gives it (Children). A segment that is not a
segment line has its bands at its segment line's line (Segments without a
line).

**The band order.** The **band order** of a timeline with the id `T` lists
its five bands and `T` itself, from top to bottom: the entry of the
manifest's `graphical.order` under `T` (section 2; README, "Groups and the
`graphical` block"); without one, its parent's band order with each of the
parent's bands replaced by `T`'s band of the same id (the parent's
`P/regions_1` by `T/regions_1`) and the parent's id by `T`; and for a root
of `timelines` without one, the default band order of section 4. A member
that is a child timeline follows its parent so too. Changing a timeline's
band order therefore changes that of every descendant without an entry of
its own. The bands listed before `T` lie **above** its line, those after
it **below**: up and down, whichever side of its parent's line it lies on.

**What a band holds.** A band draws what its own timeline holds of its
kind (section 2.1), and what another timeline holds only where a segment
without a line of its own joins its segment line's bands (below):

- the **markers band** the wedges of the root's start and end (Markers);
  no other timeline's start or end is marked and no marker of
  `flow_control` is drawn (section 2.2), so the markers band of every
  other timeline draws nothing;
- the **conversion maps band** its maps (Conversion maps);
- the **children band** its children (Children);
- the **regions band** its regions (Regions);
- the **flow control band** its jumps and breaks, with the breaks' labels
  (Flow control, Breaks).

An element that is not displayed (section 2.4) is drawn in no band and
takes no room.

**Levels.** A timeline's line lies at **level** 0. A band is **present**
when it draws an element; the present bands above the line are the levels
1, 2, … outwards, level 1 being the present band listed nearest before the
timeline's id in its band order, and those below it the levels −1, −2, …,
level −1 being the present band listed nearest after it. An absent band
has no level and takes no room. A distance `o` outwards from a timeline's
line lies at `yl − o` above and `yl + o` below.

**Where a band lies.** Each band is laid out from its **start** `c`, a
distance outwards from its timeline's line, so that a band starting at `c
= 0` lies against the line; the paragraphs below place its content from
`c`. A band's **width** is the distance its content reaches outwards from
`c`, and its **outer edge** is `c` plus its width, the width summed first.
The band at level 1, and the one at level −1, starts

- at `c = 0` when it is the markers band or the conversion maps band, each
  of which lies against the line and shares its room with the line's own
  reach (Level 0, below): its outer edge is then the larger of `c` plus its
  width and the line's reach on that side;
- otherwise at `S` beyond the larger of the line's reach on that side and
  `w / 2`, `w` the line's stroke width, so that its content keeps the gap
  `S` from the line's stroke even where the line reaches nothing.

Each further band starts at the outer edge of the band at the level before
it plus `S`. A children band's **own start** is instead the larger of the
start these rules give it and `pl / 2`, wherever it lies, `pl` the **row
pitch** of its timeline, the pitch of the row its line lies in (section
6.2; `p0` for the root), so that the rows of a side, its timeline's
included, lie one pitch apart when nothing widens them; the band starts
as Children lays it out, together with the children bands of the other
lines of that row. The markers band
and the conversion maps band are two bands, never over each other: on one
side they lie at two levels, the outer starting at least `S` beyond the
outer edge of the inner. The **outer edge of a side** of a timeline is
that of its outermost band there, or, when no band is present there, the
line's reach on that side.

**Level 0.** A timeline's line reaches out on each side as every line does
(Segment lines, below): by its map stack (Conversion maps) and, when it is
a segment line, by its boundaries, `k` both ways, and above by its segment
labels, which belong to the line and to no band, so its segment labels lie
beyond the maps against it. A drawn boundary spans `k` to either side of
the line, so a line with a drawn boundary reaches at least `k` on both
sides. A markers or conversion maps band at level 1 or −1 thus lies over
the line's boundaries, and every other band beyond them and its segment
labels.

**Conversion maps.** The conversion maps band of a timeline holds its
displayed maps (section 2.4), in canonical order. With `w` the stroke width of the
timeline's line and `c` the start of the band, map `j` (from 1) is centred
`c + w / 2 + j × (g + d) − d / 2` from that line on the band's side, so
that the first map lies `g` beyond `c + w / 2`, the line's edge when `c`
is 0, and each next one `g` beyond the one before. `J` maps are `e = w / 2
+ J × (g + d)` wide (0 when `J = 0`). At level 1 or −1 the band is the
line's **map stack** on that side, which **reaches** `e` from the line; on
every other side the line's map stack is empty. A map spans its timeline,
from `Xs` to `Xe`.

**Segment lines.** Every segment of a segment line except its first (in
canonical order) has a **boundary**: a thin vertical rule at `x` of the
segment's start, `k` to either side of the segment line's line. A line's
boundaries are those of its own segments, drawn on it; the boundary of a
segment that is itself a segment line lies on its segment line's line, not
on its own. The labels
(section 5.3) of the segments of one segment line, in canonical order, are
placed by one first fit into **segment-label tiers** above its line, each
centred on `x` of the midpoint (section 3.1) of its segment's start and end (the
end of section 3.4, so a segment of unknown length ends where the next
segment starts, and the last where its segment line ends). Tier
`n` has its baseline at `y − (m + 2 + (n − 1) × h(9)) − d(9)`, `y` the
line's ordinate and `m` the largest of the reach `e` of the line's stack
above, the width of its markers band when that band lies at level 1, and,
when the line has a drawn boundary, `k`, so that the segment labels lie
beyond the band against the line above, whichever of the two it is. A segment
that is not a segment line has no row, no name in the name column, and no
element type: a selector naming `element` never matches it, only its
boundary or label. A line therefore **reaches** above `m` plus `2 + T ×
h(9)` when its labels fill `T ≥ 1` tiers, and `m` when they fill none; and below the larger of its stack's reach below and,
when it has a drawn boundary, `k`. "Above" is up whichever side of its
parent's line the line lies on, as for every band.

**Segments without a line.** A segment that is not a segment line has no
line of its own, and its bands lie at its segment line's line: what each of
its displayed bands holds joins its segment line's band with the same kind
and number, after the segment line's own content, segment after segment in
traversal order, and that band draws it and lays it out as it lays out its
own. So the segment's maps lie in its segment line's conversion maps band,
each spanning the segment, its children in the children band, its regions
in the regions band, and its jumps and breaks in the flow control band;
its own band order places nothing, and its markers band draws nothing.
Section 2.4 states when a segment adds nothing. A band of a segment line
is present when it draws anything, of its own or of its segments, also
when its own `display` is `none`, since each segment's bands are displayed
or hidden on their own (section 2.4).

**Markers.** The root's markers band draws its wedges, each labelled with
the coordinate it marks in the root's unit (section 5.2): the zero of its
number type, which is `0`, or `0.0` on a float axis (section 3.1), and
`length`. A root whose end is open (section 3.4) has its start wedge and
that zero's label only (`0 ♩` in quarters, `0.0 s` in seconds). The labels
are placed by first fit, start before end, into tiers centred on their
wedge's `X`; only wedge labels fill these tiers. The band is `w / 2 + 13`
wide, or `w / 2 + 13 + 2 + T × h(9)` (left to right) when the labels fill
`T ≥ 1` tiers, `w` the root's stroke width; section 6.6 places the wedges
and their labels from the band's start.

**Children.** The children band of a timeline places its displayed
children that have a line of their own, every child that is not a segment
and every segment that is a segment line, in canonical order, by first
fit. Each is placed **as a whole**: its line together with everything its
own bands draw, at any depth, laid out from its line by this section. The
**extent** of a child is the smallest interval that holds the extent of its
line, the extent of every item that a first fit of its own drawing places
at any depth (its segment labels, the regions, jumps and break labels of
its bands, and its own children, each with its extent by this rule), and
the position `L × u` of every break it draws. The extent of a line runs
from its start to its end; when its end is open (section 3.4), it runs on
to `L × u + 9.5w`, `u` the proportion of its end and `w`
its stroke width, so that its three chevrons (section 6.6) take room in its
row: `9.5w` is the distance from the end to the outer chevron's tip. This
end of the extent is summed as written, `L × u` plus the constant `9.5w`
(section 3.3), measured from the root's start like every extent and only
compared, never computed from `Xr`; the drawn tip, and the right edge of
section 6.7, is `Xr + 5.5w`. So a child takes the room of its whole
drawing, also where that reaches beyond its span, as a label wider than the child
does, or the content of a segment of unknown length that runs on past the
next segment's start (section 3.4). Since an item that starts where
another ends shares its row (section 6.3), the segment lines among one
segment line's segments lie in one row when nothing of theirs reaches
beyond their spans.

A child's **edge** on a side is the outer edge of that side of its own
drawing (Where a band lies). The lines of a **row** lie at one ordinate:
the root's row holds the root, and every other row is a row of children
bands laid out together. The present children bands of the lines of one
row that lie on one side of those lines, above or below, are laid out
**together**, also when there is only one:

- They start at one distance `c0` outwards from their timelines' lines,
  the largest of their own starts (Where a band lies).
- Each places its own children by its own first fit, and their rows are
  numbered together: row `k` holds every child that any of them places in
  its row `k`, and lies at one distance `lk` outwards from their
  timelines' lines.
- Row `k` has an **inner** half (towards their timelines' lines) and an
  **outer** half: each is `p / 2`, `p` their row pitch (section 6.2), or
  the largest edge of row `k`'s children on that half's side, whichever
  band places them, when it is larger. The outer half's side is the bands'
  own side and the inner half's the opposite one, so a child in a band
  above its parent's line has its own above side in its row's outer half.
- With `ik` and `ok` the inner and outer halves of row `k`, row 1 lies at
  `l1 = c0 + i1` and row `k + 1` at `l(k+1) = lk + (ok + i(k+1))`. A band
  whose children fill `C` rows is `i1 + o1 + i2 + o2 + … + iC + oC` wide,
  summed left to right: its own rows, with the halves they have together.

A child in row `k` has its line at `yl − lk`, `yl` its parent's, when its
band lies above its parent's line and at `yl + lk` when it lies below, and
its own bands lie outwards from its line. The lines of a row lay out their
own children bands together in turn, at every depth, so the sections of a
row of movements share their rows whichever movement holds them.

The layout takes three passes. First every first fit, which uses extents
alone (section 6.3), so that which row holds which line, and every row's
name size and pitch (section 6.2), are known before any distance is. Then
the distances, from the deepest rows up: once every row of the children
bands of a row's lines has its halves, each of those lines has the starts
and widths of its bands and so its edges, and the row its halves (the
root's row the outer edges of the root's sides, section 6.5). Last the
ordinates, from the root's line (section 6.5) down.

No two children's drawings overlap, and no two names of rows (section 6.6)
do. The extents of two lines of a row never overlap, and meet at most
where one ends and the other starts: one band places both by one first
fit, or the bands of two lines of one row place them within those lines'
extents; and each row takes on each side the room that its children's
drawings take there. Rows laid out together lie at least a pitch apart,
since every half is at least half the pitch, and the rows of the children
bands of a row's lines lie within that row's room on their side (its half,
or the root's side) and at least half that row's pitch beyond its
ordinate; so any two rows lie at least half the sum of their pitches
apart, and a row's name is at most its row's pitch high (section 6.2).

A child that is not displayed is not placed; section 2.4 states what it
hides.

**Regions.** The regions band of a timeline places its displayed regions,
in canonical order, by first fit with the extent from the smaller to the
larger of their start and end, widened to the extent of their label when
it is drawn. Row `k` has its brace's arms at `r0 + (k − 1) × pr` from the
timeline's line, `r0` the start of the band; the band is `R × pr − S`
wide.

**Flow control.** The flow control band of a timeline holds first the
**break-label tiers**, `T × h(9)` wide for `T` tiers (0 when it has no
drawn break label), and then the **flow row**, where jumps leave and
arrive and breaks end: the flow row lies `T × h(9)` beyond the start of
the band. The timeline's displayed jumps, in canonical order, are sorted
stably by span (the absolute exact difference of their to and from
positions), smallest first, and placed by first fit with the extent from
the smaller to the larger of their from and to, widened to the extent of
their label, into **jump rows**. Row `k` reaches its **apex** at the
distance `f0 + (4 + S) + (k − 1) × pj` from the timeline's line, `f0` that
of the flow row and `4 + S` the first jump depth, so a jump enclosing
another lies further out. The band is `T × h(9) + (4 + S) + (K − 1) × pj +
2 + h(9)` wide for `K ≥ 1` jump rows,
and `T × h(9)` wide for none. Its jump descriptors and labels follow this
order of first fit (section 7.2).

**Breaks.** A displayed break is a vertical line at `x` of the break, from
the flow row across the line of the band's timeline to the far side of
that timeline's own drawing. For the root it runs across every band to the
padding of the opposite side: from `(x, yf)` to `(x, P)` when the flow
control band lies below the root's line and to `(x, Hc − P)` when it
lies above it (section 6.5), ordinates of the member drawing counted from
its top (section 8.4). For every other timeline it runs from `(x, yf)` to
`(x, yl − mb)` when the band lies below the timeline's line and to `(x, yl +
mb)` when it lies above it, `mb = max(E, h(s) / 2)`, `E` the outer edge of
the timeline's opposite side and `s` the name size of the row its line
lies in (section 6.2): the distance at which the root's
padding lies beyond the root's line, `s` there the root's name size
(section 6.5). So a break crosses its own timeline's drawing from its flow
row to the far side, as the root's crosses the member drawing, and stays
inside the room the timeline's row takes (Children): of other timelines'
drawings it crosses only those of its own descendants that lie in its way. Its label sits at the line's end on the flow row, alongside the
line on the timeline's side of the flow row: the break labels are placed
by first fit, in canonical order, into the break-label tiers. Tier 1
touches the flow row: its baseline is at `yf − d(9)` when the band lies
below the line and at `yf + a(9)` when it lies above it, `yf` the flow
row's ordinate, and tier `k` lies `(k − 1) × h(9)` further in, towards the
timeline's line.

### 6.5 Heights

The root's line lies at `y_root = max(P + Ea, P + h(s) / 2)`, `Ea`
the outer edge of the root's above side (section 6.4), its descendants'
drawings included in its children band. The content's height is
`Hc = y_root + max(Eb, h(s) / 2) + P`, `Eb` the outer edge of the below
side. Here `s` is the root's row's name font size.

**A root whose line is not displayed** hides its whole drawing (section
2.4): none of its bands is present and its line reaches nothing, so the
outer edges of both its sides are 0. Its row remains, with the name size
`s` and the pitch `p0` of section 6.2, which count its name although the
name is hidden. The formulas above then hold with `Eb = 0` and with `Ea`
the outer edge of its ancestor band (section 8.3), or 0 when it has none:
`y_root = max(P + Ea, P + h(s) / 2)` and `Hc = y_root + h(s) / 2 +
P`. Its ancestor band, when it has one, starts at `max(p0 / 2, S)`, the
start of section 8.3 with `Ea` and `wm` 0. Such a member
drawing draws its displayed ancestor lines, with their displayed names,
marks and mark labels, and nothing else, and lies in its card, `Hm = Hc`
high, as every member drawing does (section 8.4). One without a displayed
ancestor line draws nothing: `y_root = P + h(s) / 2` and `Hc = y_root
+ h(s) / 2 + P`, and it gives section 8.2 no name, no centred label
and no right edge.

### 6.6 Elements

Every element below is drawn only when it is displayed, with the cascaded
values of its element. `Xs`, `Xe` are `x` of an element's start and end;
`y` is the ordinate of its line (section 6.4); "outwards" points away from
the line of the band's timeline, up in a band above that line and down in
one below it.

- **Root and children.** A line with stroke width `w` from `Xs`; a filled
  circle of radius `w` centred at the start. The end tells what the
  timeline is; the first of these that applies draws it:
  - a timeline whose end is open (section 3.4) ends with **three
    chevrons**: the line runs on past `Xe` to `Xr = Xe + 4w` and stops
    there, and three chevrons pointing right follow it, each `1.5w` long
    and `3w` high, each `1.5w` further right than the one before, so
    that the inner and the middle chevron each have their tip at the x of
    the next one's arms:
    - the inner chevron through `(Xr + w, y − 1.5w)`, `(Xr + 2.5w, y)`
      and `(Xr + w, y + 1.5w)`;
    - the middle chevron through `(Xr + 2.5w, y − 1.5w)`, `(Xr + 4w, y)`
      and `(Xr + 2.5w, y + 1.5w)`;
    - the outer chevron through `(Xr + 4w, y − 1.5w)`, `(Xr + 5.5w, y)`
      and `(Xr + 4w, y + 1.5w)`, so its tip is at `Xr + 5.5w`.

    Each x is `Xr` plus its own constant multiple of `w`, each ordinate
    `y` minus or plus `1.5w`, or `y` itself, and `Xr` is `Xe` plus `4w`
    (section 3.3); no point is computed from another chevron's.
    The line runs on `4w` past its end and the glyph ends `9.5w` past it,
    12 and 28.5 with the default stroke width 3 of a `timeline` or `child`
    line; these are distances, and the tip is written, and is the right
    edge (section 6.7), as `Xr + 5.5w`. Relative to `Xr`, the inner and middle chevrons lie where an
    ancestor line that runs on to the right draws its two (section 8.3),
    and the outer chevron is what tells the marks apart: **three
    chevrons** say that a timeline's length is unknown, **two** that an
    ancestor line runs on beyond the member it is clipped to. An ancestor line never ends in
    three chevrons, whatever its length or the member's, and an open end
    never in two. The three chevrons stand for a root, a child, a segment
    line or a member alike, locked or not: an end that is not known has no
    position for a circle, an arrowhead or a diamond to mark. Such a root
    has no end wedge and no end label (section 6.4);
  - a top-level timeline (a root of the manifest) whose end is known and
    whose `locked` is false ends with an **arrowhead** of length `3w` and half-width `1.5w` whose base is
    at `Xe` and whose tip is at `Xe + 3w`, the line ending at `Xe`, so that
    the drawn timeline is longer than its length; when it is a segment line,
    the arrowhead is **open**: the same triangle, stroked with width `w / 2`
    and not filled, since prolonging it appends a segment;
  - a top-level timeline whose end is known and whose `locked` is true ends
    with a filled circle of radius `w` centred at `Xe`, like its start, the
    line ending at `Xe`;
  - a child timeline whose end is known, at any depth, ends with an **open
    diamond** of half-length `1.5w` and half-width `1.2w` centred at `Xe`
    and stroked with width `w / 2`, the line stopping at its left corner:
    the diamond marks where the child ends on its parent's axis, and is the
    same whether the child's `locked` is true or false. A member that is a
    child timeline ends so too, although its line is a `timeline` element.

  A child carries no coordinate labels. The circles and the arrowhead are
  filled and not stroked; the open arrowhead, the diamond and the chevrons
  are stroked and not filled, with no dash. Every arrow of a drawing follows one rule:
  its shaft ends at its head's base, and the head continues the shaft's
  direction at that point.
- **Boundaries.** A line from `(X, y − k)` to `(X, y + k)`, `X` the
  segment's start and `y` its segment line's ordinate (section 6.4), drawn
  over the line.
- **Segment labels.** Centred on `x` of the midpoint of the segment's start and end,
  in its tier (section 6.4).
- **Wedges.** A filled triangle, not stroked, 6 wide, with its tip at the
  distance `c + w / 2` outwards from the root's line and its base 13
  further out, at `c + w / 2 + 13`, `c` the start of the markers band
  (section 6.4) and `w` the root's stroke width, so that with `c = 0` the
  tip lies on the line's edge. Its label is
  centred on `X`, in its tier beyond the base: tier `k` starts `c + w / 2 +
  13 + 2 + (k − 1) × h(9)` out, the label gap included, and its baseline
  lies beyond that start.
- **Maps.** A closed double line: the outline of the rectangle from `Xs`
  to `Xe` of the map's timeline between the ordinates `yc − d / 2` and `yc
  + d / 2`, `yc` the map's centre (section 6.4), stroked and not filled.
- **Regions.** A brace from `Xs` to `Xe`, arms at `yb`, tip 6 further out
  at `Xm`, `x` of the midpoint (section 3.1) of the region's start and end, so it
  opens towards its timeline's line; its label centred on `Xm` beyond the
  tip, 2 further out. The arms lie at the distance `r0 + (k − 1) × pr` of their
  row (section 6.4), the tip at that distance plus 6, and the label's
  ordinate at that distance plus 6 plus 2, each distance summed whole
  before it becomes an ordinate (section 3.3), never computed from `yb`.
- **Jumps.** An arrow from `(Xf, yf)` to `(Xt, yf)`, `Xf = x(from)`, `Xt =
  x(to)`, `yf` the flow row, `w` the jump's stroke width. Its **curve** is
  the cubic Bézier curve from `P0 = (Xf, yf)` to `P3 = (Xt, yf)` with
  controls `C1 = (Xf + q, yc)` and `C2 = (Xt − q, yc)`, `q = (Xt − Xf) / 4`
  and `yc = yf + 4/3 × (ya − yf)`, `ya` the ordinate of its jump row's apex:
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
  the midpoint of from and to, beyond the apex, 2 further out.
- **Breaks.** The line of section 6.4 at `x` of the break; its label
  starting at `x + 3`, in its tier (section 6.4).
- **Names.** For each **row** of lines (section 6.4, Children: the root's
  row and every row of children bands laid out together, at any depth, so
  that all lines at one ordinate form one row), the names (section 5.3) of
  its drawn lines whose names are displayed, in traversal order, joined by
  `, `; the line of a segment
  contributes no name, since its name is its label, so a row of segment
  lines alone has no name. When the
  `content` of the first of these names is not `none`, the row shows that
  text instead (an editor sets it to give a row its own name, and resets it
  to `none`). When the text is wider than that name's `max-width`, it is cut
  to its longest prefix that, followed by `…` (U+2026), fits, and the cut
  text is shown. It is drawn starting at `x = n` (section 8.2), vertically
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
diamond's corner `Xe + 1.5w`, the outer chevron's tip of an open end's
three chevrons `Xr + 5.5w`, with `Xr = Xe + 4w` computed first (section
6.6; `9.5w` past `Xe` only as a distance, never as the sum `Xe + 9.5w`),
the outer chevron's tip of the two chevrons of an ancestor line that runs
on to the right `Xr + 4w`, with `Xr = x0 + L + 4w` computed first (section
8.3; `8w` past `x0 + L` only as a distance), a map's `Xe`, a boundary's `X`, a wedge's `X + 3`, the largest x of
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
order: the breaks; the maps; the regions; the jumps, each of these four
band by band in the traversal order of the bands' timelines, and each
band's in the order it places them (section 6.4); the root and
then the children in traversal order; the boundaries, in the traversal order
of their segments (a nested segment line's boundaries thus follow its own
boundary, not its siblings'); the wedges, start before end; the names, the
wedge labels, start before end, the segment labels, in the traversal order
of their segments, the region labels, the jump labels and the break labels. Section
8.5 places them among the background, the titles, frames and cards, and
the ancestor lines. Every
descriptor except the background carries `data-address`, the address of its
element; the several descriptors of one element carry the same address. An editor renders these same descriptors on
screen; the SVG writer serializes them. An element's hit area is the
painted geometry of its descriptors, each standing for the element whose
address it carries; this specification gives no element a hit area beyond
them. So the three chevrons of an open end, part of their line like an
arrowhead, carry the line's address `T` and hit the timeline, and an open end, which
draws no end wedge and no end label, has no descriptor with `T/end` or
`T/end/label` and nothing there to hit.

A point in a template (`{p1}`, `{P0}`, `{P3}`, `{Bh − 2w × n}`, …) is
written by where it stands. In a `points` attribute it is `{x},{y}`, its
two numbers formatted by section 7.3 and joined by a comma without a
space, and the points are separated by one space, as the polygon templates
spell out; this holds for the chevrons' polylines and the jump's arrowhead
too. In path data (`d`) it is its two numbers separated by one space, as
the brace below writes them, so a jump's shaft `M{P0}C{C1} {C2} {Bh}`
opens like `M290.9775 63.8555C253.4775 74.5221`.

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
| three chevrons | an open end (section 6.6): the line stops at `Xr`; three `<polyline points="{p1} {p2} {p3}" fill="none">`, the inner one, the middle one, then the outer one, each through its three points in the order section 6.6 lists them, stroked in the line's `stroke` with width `w/2` and no dash |
| two chevrons | an ancestor line running on (section 8.3): the line stops at `Xr` (to the right) or starts at `Xa` (to the left); two `<polyline points="{p1} {p2} {p3}" fill="none">`, inner one first, each through its three points in the order section 8.3 lists them, stroked as three chevrons are |
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

## 8. The box: frames and cards

Every manifest is an alignment bundle and is drawn as one **box**, the
bundle box, whatever it holds: a manifest of one root as a box holding that
root as an ungrouped root, a manifest of one group as a box holding that
group's frame, and every other manifest alike. The box opens with the
manifest's title (section 5.3), which an anonymous bundle, with neither a
`name` nor an `id`, does not have.
Every timeline drawn as a root (a member or an ungrouped root) is drawn as
sections 3 to 6 draw a root, in its own **card**. The box's **items** are
its frames and its ungrouped roots' cards; each lies at its own place
(section 8.6) and has its own graphical length `L`. The member drawings of
one item share its `L` and one start `x0`, so that the members of a group
by definition start and end at the same points. The **shared end** is
`x0 + L`, found
from `x0` and `L` alone and never from a length: a member or ungrouped
root of unknown length is drawn with its reach at the shared end (section
3.4), and its line runs on past it into its three chevrons (section 6.6).

### 8.1 What is drawn

- **Groups.** A box draws the manifest's groups in canonical order (by id), and
  then every **ungrouped root**, a root of `timelines` that no group names
  as a member and that contains no member, in canonical order (by id). A
  root that contains a member is drawn only as an ancestor line of that
  member.
- **Frames.** Each group is a **frame**, a `group` element: a rounded
  rectangle holding the group's title and then its members' cards, one
  under the other, in the group's display order: the entry of
  `graphical.order` under the group's id, or `members` when `order` has no
  entry for it. An ungrouped root has no frame.
- **Cards.** Each member and each ungrouped root `M` lies in a **card**, a
  `card` element with the address `M/card`: a raised rounded rectangle
  around `M`'s member drawing (in the tree below, a card holds nothing). The card is the same whether it lies on the
  grey box or in a frame.
- **Member drawings.** A **member drawing** is the drawing of sections 3
  to 6 of one timeline `M` taken as the root: its line is a `timeline`
  element, its wedges mark its own `0` and `length` (its `0` alone when
  its length is `null`), and positions are on `M`'s axis (section 3.1). A
  member that is a child timeline in `timelines` is still a `timeline`
  element in its member drawing, so statements selecting `child` do not
  reach its line, and it ends with the diamond, or with three chevrons
  when its length is `null` (section 6.6). Such a member's drawing also has an
  **ancestor band** (section 8.3).
- **Titles.** A group's title, a `name` element with the address `G/name`,
  opens its frame. The manifest's title, a `name` element with the
  address `name`, opens the box.

The tree of section 2.1: the `block` holds the manifest's title, the frames,
and the cards and `timeline` elements of the ungrouped roots; a frame holds
its title and its members' cards and `timeline` elements; a card holds
nothing; a member's `timeline` element holds what a root holds (section
2.1) and its ancestor lines; an ancestor line holds its `name` and its
marks of the member's start and end, each mark holding its `label`.
`within` names a timeline at any depth of `timelines`; a timeline's depth
(section 2.5) is its depth in its root's tree, the roots being 1.

### 8.2 Horizontal

The box has **one horizontal layout**, which every item applies at its own
place: the name column, the line's start and the right margin are found
once over all items, so that items of one length are equally wide wherever
they lie. Each quantity below is computed in **item coordinates**, measured
from the item's left edge, before the item's scale (section 8.6); `Li` is
the graphical length of item `i`.

The **name column** starts at `n = Q + K` when the box holds a frame and at
`n = K` otherwise: inside the cards, at the same offset for every card of
every item. Every row name of every member drawing, ancestor names
included, is drawn at `x = n`. `N` is the width of the widest name of any
member drawing of the box (section 6.7), and `G' = 8` when any such name is
drawn and 0 otherwise; titles are not names of rows and count for neither.
The **start** is

    s0 = max(n + N + G', max over i, j of (n + wj / 2 − Li × uj), max over a of (n + N + G' + 8 × wa))

where `j` runs over every centred label of every member drawing of item
`i` (section 6.7, with the member's own proportions and the item's length
`Li`) and `a` over every ancestor line of the box that runs on to the left
(section 8.3), `wa` its stroke width. So no label crosses the name column's
left edge, and no chevron crosses the gap after the names. Every member
drawing of item `i` starts at `s0`, its shared end is `s0 + Li`, and the
`x0` of sections 3 and 8.3 is `s0` in item coordinates.

The **right margin** `Mr` is the largest of `e − (s0 + Li)` over every
member drawing of every item `i` that draws anything, `e` its right edge
(section 6.7); it may be negative. Item `i`'s right edge is `Ri =
max(s0 + Li + Mr, t)`, `t` the right edge of its group's title, which
starts at `Q` (none for an ungrouped root's card), or `Ri = max(s0, t)`
when no member drawing of the box draws anything; section 8.6 widens it on
request. A box of one item so has the right edge of its widest content. A card
inside a frame spans `Q` to `Ri + K`, so that every card of a frame ends
at one x, unless its own request widens it (section 8.6); a frame spans `0`
to `Ri + K + Q`; an ungrouped root's card spans `0` to `Ri + K + Q` when
the box holds a frame and to `Ri + K` otherwise, so that the frames and
ungrouped cards of one length end at one x.

### 8.3 Ancestor lines

For a member `M` that is a child timeline, let `A1, …, Ak` be its
ancestors from its root `A1` down to its parent `Ak`. Each `Aj` has an
**ancestor line**, an `ancestor` element with `Aj`'s address, drawn at
`M`'s scale and clipped to `M`. On `M`'s axis `Aj` starts at `ts = −(o(j+1)
+ … + o(k) + oM)`, the negated sum of the offsets from `Aj` down to `M`
(`oM` being `M`'s own offset in `Ak`, `o(j+1)` that of `A(j+1)` in `Aj`), and
ends at `te = ts + ` `Aj`'s `length`, combined as section 3.1 combines
values, when that length is a value; `λ` is `M`'s length, or its reach when
its length is `null` (section 3.4). `ts ≤ 0`, and `te ≥ λ` wherever every
length involved is a value, since a child lies within its parent. With `w`
the line's stroke width and `y` its ordinate:

- **On the left**, when `ts < 0` (compared exactly) the line **runs on**:
  it starts at `Xa = x0 − 4w` and ends in a double chevron pointing left,
  the inner one through `(Xa − w, y − 1.5w)`, `(Xa − 2.5w, y)` and `(Xa −
  w, y + 1.5w)`, the outer one the same `1.5w` further left, through `(Xa −
  2.5w, y − 1.5w)`, `(Xa − 4w, y)` and `(Xa − 2.5w, y + 1.5w)`, so its tip
  is at `x0 − 8w`. When `ts = 0` the line starts at `x0` with its circle.
- **On the right**, when `Aj`'s length or `M`'s length is `null`, or `te
  > λ`, the line runs on to `Xr = x0 + L + 4w`
  and ends in a double chevron pointing right, mirrored: the inner one
  through `(Xr + w, y − 1.5w)`, `(Xr + 2.5w, y)` and `(Xr + w, y + 1.5w)`,
  the outer one `1.5w` further right, through `(Xr + 2.5w, y − 1.5w)`, `(Xr
  + 4w, y)` and `(Xr + 2.5w, y + 1.5w)`, its tip at `Xr + 4w`, `8w` past
  `x0 + L` (section 6.7): where
  either end is not known, the drawing does not claim that the ancestor
  ends with the member. A running-on ancestor line has two chevrons on
  either side, also when its own length or `M`'s is `null`: the three
  chevrons of an open end (section 6.6) mark a line's own unknown length
  and are never drawn on an ancestor line. When `te =
  λ` the line ends at `x0 + L` with `Aj`'s own end (section 6.6): the
  arrowhead, open arrowhead or circle of a top-level timeline, the diamond
  of a child. When `te < λ`, which a manifest allows only where a timeline
  between `Aj` and `M` has a length of `null`, the line ends at `x(te)`
  (section 3.2), inside the member's span, with `Aj`'s own end.
- **Marks.** Two wedges mark `M`'s start and end on `Aj`'s axis: `wedge`
  elements with the addresses `M/start` and `M/end`; when `M`'s length is
  `null`, its end is not known and only `M/start` and its label are drawn.
  The marks lie always above the line, outside every band, each with its
  tip on the line's edge (`y − w / 2`) and its base 13 further up, at `x0`
  and `x0 + L`. Each is labelled with the coordinate it
  marks in `Aj`'s unit: `−ts` and `−ts + λ`, combined as section 3.1
  combines values. The labels are placed by first fit, start before
  end, into tiers above the base, as the markers band places its wedge
  labels (section 6.4).
- **Nothing else** of `Aj` is drawn: no maps, regions, flow control,
  boundaries or other descendants. Its name is drawn in the name column on its row
  (section 6.6, names).

The **ancestor band** is the outermost band of the member drawing's above
side, beyond the root's bands and outside every band order; it is not an
element and has no address. It starts at the larger of `p0 / 2` and `S`
beyond the larger of the outer edge `Ea` of the above side (section 6.4)
and half the stroke width `wm` of the member's line, `wm` being 0 when
that line is not displayed (section 6.5): at `max(p0 / 2, max(Ea, wm / 2)
+ S)`, so that the band keeps the gap `S` from the line's stroke, as a
band at level 1 does.
It holds one row per ancestor, `Ak` nearest the member's line and `A1`
outermost; an ancestor line that is not displayed has no row (section 2.4
states what it hides), and a member drawing without a displayed ancestor
line has no ancestor band. Row `j` (counted from `Ak`) has the row pitch `qj` of its name's
font size (`p` of section 6.2), an inner half `ij = qj / 2` and an outer half `oj`, the larger of
`qj / 2` and the reach of its marks, `w / 2 + 13`, or `w / 2 + 13 + 2 + T ×
h(9)` (left to right) when their labels fill `T ≥ 1` tiers (9 standing for
its labels' largest font size), or `qj / 2` alone when no mark is drawn.
The line of the first row lies at `c0 + i1`, `c0` the start of the band,
and that of row `j + 1` at `oj + i(j + 1)` beyond the row before. The
band is `i1 + o1 + … + ik + ok` wide, summed in that order.

### 8.4 Vertical

Every member drawing has its own height `Hm`, its content height `Hc` of
section 6.5 with its ancestor band included in `Ea`; its card is `Hm` high,
and the drawing's top is the card's top. The card padding `K` is
horizontal only: above and below, the member drawing's own padding `P`
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
  not displayed), and each further one the frame's spacing `Sf` below the
  previous one's bottom (section 8.6). The frame is `Q + h(s) + 4 + Hm1 +
  Sf + Hm2 + … + Sf + Hmn + Q` high, summed in that order, without `h(s) +
  4` when the title is not displayed.
- **The box.** The manifest's title, when there is one, lies at the box's
  top left corner: drawn at `x = Xl + P`, with its baseline at `Yt + P +
  a(s)`, both in place coordinates (below), so in the box at `P` and `P +
  a(s)` wherever the box grows. Its slot, `h(s)` high, is the top border
  of the items: no item rises into it, and an item placed higher pushes it
  up with the box's top. Every frame and ungrouped card lies at its place
  (section 8.6).

Within a member drawing, the root's line lies at the drawing's top plus the
`y_root` of section 6.5, computed in that order; every other ordinate
follows from that line as section 3.3 states.

The box grows in every direction to hold its content, with the padding `P`
on every side. Every position is first computed in **place coordinates**,
measured from the place origin, as sections 6 and 8 write it (an item's
positions through its item coordinates and its place, section 8.6). In place
coordinates the content runs from `Xl`, the smaller of 0 and the smallest
left edge of any frame or card minus `P`, to `Xr`, `P` plus the largest
right edge of any frame or card, a card's shadow included, or of the
manifest's displayed title, whose right edge is `Xl + P` plus its width;
and from `Yt`, the smaller of 0 and the smallest top of any frame or card
minus `Pt`, to `Yb`, `P` plus the largest bottom edge of any frame or card,
a card's shadow included, or of the manifest's displayed title, whose slot
ends at `Yt + P + h(s)` (`Xr = 2P + K` and `Yb = P` when the box holds none
of these). `Pt` is `P + h(s) + F` when the manifest's title is displayed,
`s` its font size, and `P` otherwise, so that an item never rises above
`F` below the title's slot.
The content is `Wb = Xr − Xl` wide and `Hb = Yb − Yt` high, the sum with
`P` taken first: `Wb = (P + max(b + 2, …)) − Xl`, and `Hb` likewise. The place origin lies at
`(Ox, Oy) = (0 − Xl, 0 − Yt)` in the box, so an origin of 0 is `+0`; it is
`(0, 0)` unless an item reaches left of or above the padding. Each finished
position is then drawn in the box with `Ox` added to its x and `Oy` to its
y, the last sum of each: the manifest's title is drawn at `(Xl + P) + Ox`
with its baseline at `((Yt + P) + a(s)) + Oy`. A frame's or card's width and height are
taken in item coordinates (section 8.6); the box's `Wb` and `Hb` in place
coordinates, as above. A frame or card that is not displayed is not drawn but keeps
its place, since member drawings lie in it: the layout, `n`, `Wb` and `Hb`
are as when it is displayed, except that a hidden card's shadow is not
drawn and does not count. The
box is `W = max(Wb, width)` wide and `H = max(Hb, height)` high (`W = Wb`
when `width` is `null`, `H = Hb` when `height` is); the
background is a rectangle filling it with corner radius `rx`.

### 8.5 Descriptors

A manifest becomes element descriptors in this order: the background; the
manifest's title; then, for each frame in drawing order, the frame, its
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

### 8.6 Places

Every item of the box, a group's frame or an ungrouped root's card, lies at
a **place**: its left edge `x` and its top `y`, measured from the place
origin in canvas units, its graphical length `length`, its **scale**
`scale` (positive), its `spacing` (finite, ≥ 0), and its
requested size `width` and `height` (positive, or left out for its
content's own size). `places` (section 1) states any of
these members for the item whose id is its key; a key naming nothing drawn
is not used, and so is any of a value's members that this section gives
no use for (a member's card uses only `width`, `height` and `spacing`). A member that is not stated takes its default:

- `length`: the placement's `length`;
- `scale`: 1;
- `spacing`: 8 for a frame, 4 for a card;
- `width` and `height`: none, the content's own size;
- `x`: `P`;
- `y`: for the first item in drawing order (section 8.5), `P + h(s) + F`
  below the manifest's title, `s` its font size, or `P` when there is no
  title or it is not displayed; for every further item, the box's spacing
  below the largest bottom edge `d` of the items before it. That edge is
  the frame's or card's `d` of section 8.4, its place `y` plus `scale` times its
  height, summed in place coordinates before any shift; a card's shadow does not count, and
  an item that a `height` request makes higher ends at its requested
  bottom.

So with `places` empty the items lie one under the other, as an editor
first shows them.

An item is laid out by sections 8.2 and 8.4 with its own `length` as `L`,
in item coordinates, its left edge and top at 0, every sum written as those
sections write it. Its frame or card is wider when `width` asks for more:
for a frame, `Ri` is taken as the larger of its `Ri` and `width − K − Q`,
so its cards still end at one x inside it; for an ungrouped root's card,
as the larger of its `Ri` and `width − K − Q` when the box holds a frame
and `width − K` otherwise. It is higher when `height` asks for more: the
frame or card is the larger of its own height and `height` high, every card
and member drawing keeping its top. `width` and `height` are in item
coordinates, before the scale.

The **card spacing** `S` of a member drawing (sections 6.2 to 6.5 and
8.3) is its card's `spacing`: the entry of `places` under the member's
id, or under the ungrouped root's id. A group's entry states its frame's
spacing `Sf`, the gap between its member cards (section 8.4); the
placement's `spacing` is the gap between the box's items at their default
`y`. Each container's spacing spaces only its own contents: no spacing
multiplies another, and a frame's padding `Q`, its title's slot, the box's
padding `P` and the card's padding `P` above and below do not change with
any of them.

A **member's card** may request a size and a spacing of its own:
the entry of `places` under the member's id states its `width` and
`height`, in item coordinates, before its group's scale, and its
`spacing`, and nothing else of it is used. The card is then the larger of its own width and `width` wide,
spanning `Q` to `max(Ri + K, Q + width)`, and the larger of `Hm` and
`height` high; its member drawing keeps its place at the card's top left,
so the request adds a margin to its right and below. The frame holding it
grows with it: the frame spans `0` to the largest right edge of its cards
plus `Q`, and its height sums its cards' heights.

The item is then drawn at its place: every position of its elements, its
frame's or card's included, is the item-coordinate position `(px, py)`
taken to `(x + scale × px, y + scale × py)`, and every length of them, a
width or height, a radius (a frame's or card's corner radius `rx`
included), a stroke width, every dash of a dash array, a font size, a
text's `max-width` and the size of every marker, is multiplied by `scale`;
a frame's or card's `width` and `height` are `scale` times its
item-coordinate `b − a` and `d − c`; a card's shadow is written at its
card's written `x` and `y` plus `scale × 2`, with the card's `width` and
`height`, its right and bottom edges for the box being `x + scale × (b +
2)` and `y + scale × (d + 2)`; with
`scale` 1 that is `(x + px, y + py)` and every length unchanged. So an item's
scale scales everything in it, proportions kept, text included, about its
top left corner, as the box's scale `z` scales the box (section 1). Its
edges for the box (section 8.4) and for the default `y` above are its
drawn edges, after the scale.

The members of a group are never placed: they lie one under the other in
their frame, in the group's display order (section 8.1), and only that order
changes; their cards may only request a size and a spacing. The bands of every timeline likewise lie outwards from its own line
in its band order (section 6.4).

