# timeskeleton

TimeSkeleton is an exchange format for the structures of musical
timelines: their axes, extents, nesting, groups, conversion maps, regions,
flow control and measure maps, without their events. Music-research
software trades these structures in it like a currency. The format
expresses the TimeToAlign! model
([TISMIR](https://doi.org/10.5334/tismir.296)); the Python library
[timetoalign](https://github.com/timetoalign/timetoalign) is one
implementation of it, and emits the shared fixtures, but does not define
the format. This repository holds the format as a JSON Schema, with
validation packages for Python and TypeScript.

**Status: alpha.** The repository holds one schema version, 0.7.0, the
current version, as one JSON Schema document describing one manifest shape.
It provides validators for Python and TypeScript that locate a violation
under one shared path rule and list unknown keys as warnings, the complete
and the minimal form of a manifest, a canonical order, standard writers
that produce the same bytes in Python and TypeScript, a lossless JSON reader
for TypeScript, generated TypeScript types, and shared fixtures. It also
specifies how a manifest is drawn, and both packages ship that
specification.

## The manifest

Every TimeSkeleton manifest has one shape and is an alignment bundle,
whatever it holds: one timeline, several, a group of timelines, or several
groups beside ungrouped timelines. The smallest manifest is

```json
{"timeskeleton": "0.7.0", "timelines": [{"id": "piece", "unit": "quarters", "length": [32, 1]}]}
```

| Member | Required | Holds |
| --- | --- | --- |
| `timeskeleton` | yes | the version marker, `"0.7.0"` |
| `timelines` | yes | the root timelines, an array that may be empty |
| `id` | no | the manifest's ID |
| `name` | no | the manifest's displayed name |
| `meta` | no | an object of anything an application wants to record |
| `groups` | no | timeline groups whose members name timelines of the manifest |
| `measure_maps` | no | the measure maps the conversion maps read, each with an ID; they belong to no timeline |
| `graphical` | no | the styling of the manifest's drawing, its groups' display orders and its timelines' band orders |
| `$schema` | no | a string naming the schema, for editors; never read |

A single timeline is a bundle of one root, and a group is a bundle of one
group. A manifest with an `id` or a `name` is a named bundle; one with
neither is an anonymous bundle. `id` and `name` are independent: either may
stand without the other.

**The version marker.** Both validators read `timeskeleton` first. A value
without it is refused at the root as `not a TimeSkeleton manifest`; a value
declaring any other version raises `UnsupportedVersionError` naming 0.7.0.

A manifest describes timelines and all their descendants. No manifest says
where or how often an application places it. Event tables travel
separately, typically as Arrow or Parquet data, and are referenced rather
than embedded.

### The timeline

A timeline (`$defs/Timeline`) requires `id`, `unit` and `length`. Its
optional keys are `name`, `number_type`, `offset`, `locked`,
`is_segment_line`, `meta`, `children`, `conversion_maps`, `regions` and
`flow_control`.

- `unit` decides the timeline's domain (logical, physical or graphical)
  and modality (continuous or discrete), since each unit belongs to exactly
  one of the six combinations, and the default of its number type:

  | Unit | Domain | Modality | Default number type |
  | --- | --- | --- | --- |
  | `number`, `floating_measures` | logical | continuous | `float` |
  | `whole_notes`, `quarters` | logical | continuous | `fraction` |
  | `ticks` | logical | discrete | `int` |
  | `milliseconds`, `seconds`, `minutes` | physical | continuous | `float` |
  | `samples`, `frames` | physical | discrete | `int` |
  | `pixels` | graphical | discrete | `int` |
  | `meters`, `centimeters`, `millimeters`, `inches`, `points` | graphical | continuous | `float` |

  The domain and modality decide the timeline's class (`seconds` makes a
  `ContinuousPhysicalTimeline`), which a timeline never writes.
- `number_type` is `int`, `float` or `fraction`; absent, it is the unit's
  default number type above.
- `length` is the timeline's length on its own axis, or `null` when it is
  not known (section [Unknown length](#unknown-length)).
- `children` is an array of timelines, each carrying its `offset` on the
  parent's axis, written in offset order with ties by ID; a child shares
  its parent's `unit`, here `seconds`:

  ```json
  "children": [{"id": "perf", "offset": 4.0, "unit": "seconds", "length": 1503.2}]
  ```

  A child requires `offset`. The schema and both validators accept a
  negative offset, a child starting before its parent's 0; timetoalign and
  TimeLineEditor do not support it yet and refuse it (`A negative child
  offset is not supported yet: …`). Where its
  parent's length is known, a child starts at or before the parent's end
  and ends at or before it, locked or not: no child reaches past a known
  length. A root may carry an `offset` too, negative included:
  it places the root's origin on its unit's absolute axis, such as a
  recording whose origin is a moment in UNIX time. A root without `offset`
  has none.
- `locked` states whether the timeline's length is fixed; it defaults to
  `false` on every timeline. A child writes it like every other timeline,
  and may be unlocked as a root may. A locked timeline's length may still
  be unknown. An unlocked child's length may change only within its
  parent's known length; a parent's length never follows a child's.
  A segment is never locked, since its segment line's lock governs it:
  writers write `false` for a segment, and timetoalign and TimeLineEditor
  read a segment's `locked` as `false` whatever it states. A segment line
  that is a child, a segment or a group member is the exception, locked by
  default when it is built. That default belongs to construction, not to the table of
  [Defaults](#defaults), so writers write its `true` explicitly, in the
  minimal form as well. timetoalign and TimeLineEditor do not support
  lifting it yet.
- `is_segment_line` marks a **segment line**, a timeline containing only
  contiguous segments: its children are its segments, contiguous from 0 in
  offset order to its length, all sharing its unit as every child does,
  and all with one `is_segment_line` value. Segments that are segment lines
  themselves make a nested segment line.
- `conversion_maps`, `regions` and `flow_control` hold the timeline's
  conversion maps ([Conversion maps and measure
  maps](#conversion-maps-and-measure-maps)), regions (`{id, name?, start,
  end, meta?}`) and flow-control elements ([Flow control](#flow-control)).

### Conversion maps and measure maps

A conversion map is a function from a position on its timeline's axis to a
value, discriminated by its `type`. Every map carries `type`, `id`, `name`,
`source_unit` and `target_unit`, a unit being null where that side is not
a time axis. A map is an abstract type, independent of any number type: each
of its numbers is an int, a float or a Fraction pair, whatever the
implementation computes in. Its domain and modality, which the drawing
styles it by, are those of its `target_unit`. There are ten types:

| Type | Maps x to | Own keys |
| --- | --- | --- |
| `LinearMap` | `scalar` · x + `offset` | `scalar` (default 1), `offset` (default 0) |
| `TableMap` | an interpolation between anchor pairs | `x_values`, `y_values` (equal length, at least two, x strictly increasing); `kind` `linear` (default) or `previous`; `extrapolate` `none` (default), `constant` or `linear` |
| `ConstantMap` | one value for every x | `value`, a number or a string |
| `PiecewiseMap` | the value of the map of the interval `[breaks[i], breaks[i+1])` holding x | `breaks` (strictly increasing), `maps` (one fewer than `breaks`) |
| `ChainMap` | the value of its maps applied in turn, the first first | `maps` (at least one) |
| `CombinationMap` | several named outputs, each one map's value | `maps`, an object from output name to map |
| `MeasureRecordMap` | the row of the measure holding x | `measure_map` |
| `MeasureNumberMap` | that row's `number` | `measure_map` |
| `FloatingMeasureMap` | floating measures | `measure_map` |
| `MeasureBeatMap` | the measure number and the beat | `measure_map` |

Scaling, shifting and every conversion between two units of fixed ratio
(quarters to ticks at a resolution, samples to seconds at a sample rate)
are linear maps. The last four are the **measure views**: each reads the
measure map its `measure_map` names, from `quarters` (its constant
`source_unit`) to `floating_measures` (`FloatingMeasureMap`) or to null
(the other three, whose outputs are not positions on a time axis).

A map attached to a timeline converts from the timeline's axis: its
`source_unit`, where not null, is the timeline's unit. A map that another
map holds reads its holder's input: every map of a `PiecewiseMap` or a
`CombinationMap`, and the first map of a `ChainMap`, has its holder's
`source_unit` wherever both are stated. A timeline in ticks or
`whole_notes` therefore reaches a measure view through a `ChainMap` whose
first map is a `LinearMap` to quarters. The schema states the exact
reading of every type.

`measure_maps` holds the manifest's measure maps, each `{id, name?, meta?,
rows}`. A measure map belongs to no timeline and is not drawn; its
positions are quarters by definition, so it fits every timeline. `rows` is
the [Measure Map standard](https://github.com/measure-map/specification)'s
compressed row array, at least one row: an entry equal to the preceding
entry's default successor is omitted. A row is the standard's Measure plus
two extensions: the integer `volta`, and `offset_within_measure`, where the
row begins inside its nominal measure in quarter notes. Lengths are
strictly positive and `qstamp` is non-negative; exact Fraction pairs are
permitted wherever the standard uses JSON numbers. A measure view's
`measure_map` must name an entry of `measure_maps`, which both validators
check after the schema.

### Flow control

A timeline's `flow_control` is one array of elements `{id, type,
manifestation, coordinate, target?, repeat_count?, name?, label?, meta?}`,
each at a `coordinate` on the timeline's own axis. Its `type` decides the
manifestations it may take and whether it carries a `target`:

| `type` | Manifestations | `target` |
| --- | --- | --- |
| `jump_from`, a jump origin | `repeat_end`, `da_capo`, `da_capo_al_fine`, `da_capo_al_coda`, `dal_segno`, `dal_segno_al_fine`, `dal_segno_al_coda`, `to_coda` | the ID of a `jump_to` of the same timeline; required on the `dal_segno` manifestations and `to_coda`, optional on the `da_capo` manifestations and `repeat_end`, whose jump without one goes to the timeline's start |
| `jump_to`, a jump target | `repeat_start`, `segno`, `coda` | none |
| `flow_marker`, a flow marker | `fine`, `section_break`, `double_barline`, `final_barline` | none |

Only a `repeat_end` carries `repeat_count`, an integer of at least 1. When
a jump origin acts follows from its manifestation: a `repeat_end` on its
first `repeat_count` passes, a `to_coda` only after a `da_capo_al_coda` or
a `dal_segno_al_coda`, every other jump origin always. A flow marker is
not a coordinate marker: the markers band of a drawing holds the
coordinate markers, the wedges at a root's start and end, never an element
of `flow_control`.

### Values on a timeline's own axis

A coordinate on its timeline's own axis is written as its value alone:
`length`, a child's `offset` (on the parent's axis), a root's `offset`,
region `start` and `end`, and the `coordinate` of every flow-control
element. The value is represented as the axis's number type selects, that
is `number_type`, or the unit's default when it is absent: a JSON integer
for `int`, a JSON number for `float`, and a `[numerator, denominator]` pair
of integers with a strictly positive denominator for `fraction`, mirroring
BOPP. A child's `offset` takes the parent's number type.

The declared number type decides how a value is read, never its spelling,
and a reader coerces: `2.0` on an `int` axis is the integer 2, `2` on a
`float` axis the float 2.0, and `[1, 8.0]` the Fraction 1/8. A JSON round
trip that respells numbers therefore never invalidates a manifest. Writers
spell every value canonically: an int as a JSON integer, a float as
Python's `repr` spells it, Fraction members as JSON integers. What a value
cannot be read as stays refused: a number with a fractional part on an
`int` axis, an integer that no float equals exactly on a `float` axis, a
Fraction pair on an `int` or `float` axis and a bare number on a
`fraction` axis, each with the code `representation`; and a Fraction
member with a fractional part or a denominator below 1, which the schema
refuses. The schema types own-axis values as `Number`; both validators then
check the representation and report a mismatch such as
`length 32 of 'score' is an int on a fraction axis: write [32, 1]`, or, for
an integer no float holds exactly,
`length 9007199254740993 of 'take' is an int on a float axis: write a float`.
Every number of a manifest is finite: JSON spells no NaN or infinity, but a
value built in memory, or read by a lenient reader, may hold one, and both
validators refuse it at its path.

A conversion map's numbers and a measure-map row's lengths are numbers of
the same kind, each a JSON number or a Fraction pair. The self-describing
coordinate object `{unit, number_type, value}` (`$defs/Coordinate`) serves
a position outside such a container, as hosts exchange single positions;
inside a manifest every position lies on an axis its container declares.

### Defaults

Every key of this table is optional, and readers supply its default when it
is absent. Writers write the **complete form**: every key of the table,
its default included (`null`, `{}`, `[]`), except the keys whose default is
"absent", which are written only with a value. Asked for the **minimal
form**, they omit exactly the keys whose value is the default, equal to it
in JSON type and value: `repeat_count: 1.0` is a float, not the integer
default `1`, and stays. Either form
reads to the same objects, and each writes back to itself. `length` is
required in both forms.

| Object | Key: default |
| --- | --- |
| manifest | `id`: absent (without a `name` too, an anonymous bundle); `name`: `null`; `meta`: `{}`; `groups`, `measure_maps`: `[]`; `graphical`: absent |
| timeline | `name`: `null`; `number_type`: the unit's default (the unit table of [The timeline](#the-timeline)); `offset`: absent on a root, required on a child; `locked`: `false`; `is_segment_line`: `false`; `meta`: `{}`; `children`, `conversion_maps`, `regions`, `flow_control`: `[]` |
| region | `name`: `null`; `meta`: `{}` |
| flow-control element (`flow_control_element`) | `name`, `label`: `null`; `meta`: `{}` |
| a `repeat_end` besides (`repeat_end`) | `repeat_count`: 1 |
| conversion map (`conversion_map`) | `name`: `null` |
| a `LinearMap` besides (`linear_map`) | `scalar`: 1; `offset`: 0 |
| a `TableMap` besides (`table_map`) | `kind`: `"linear"`; `extrapolate`: `"none"` |
| measure map (`measure_map`) | `name`: `null`; `meta`: `{}` |
| group | `name`: `null`; `meta`: `{}` |
| graphical | `styles`: `{}`; `statements`: `[]`; `order`: `{}` |

A row marked "besides" adds its keys to those of the general row it
follows: a `repeat_end` has the keys of every flow-control element plus
`repeat_count`, which no other element carries, and a `LinearMap` or a
`TableMap` the keys of every conversion map plus its own, at any depth of
nesting. The names in
parentheses are the kinds of the packages' `DEFAULTS` table.
Python's `complete(value)` and npm's `complete(value)` return a copy of a
manifest in the complete form, and `minimal(value)` in both packages a copy
in the minimal form; both are pure and read the one table above.
timetoalign's `to_dict()` writes the complete form, and
`to_dict(minimal=True)` the minimal one.

### Unknown length

`length: null` means that the length is not known, on any timeline: a root,
a child, a segment, a locked timeline or a group member. It is a fact
stated by the manifest, never inferred and never a violation; content
added to such a timeline leaves its length unknown. A rule that needs an
end applies where the end is known and is skipped where it is not. Segment
lines are checked between known values: a segment of unknown length ends
where the next segment starts, and the last segment of a segment line
whose length is known ends at that length. The segments of a segment line
of known length keep ending at its length: a segment's length changes only
where its neighbours allow, never moving the line's end. The
[drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
scales a timeline of unknown length to its reach, the farthest coordinate
its content reaches, and ends its line in three chevrons.

### Groups and the `graphical` block

A group is `{id, name?, meta?, members}`. `members` are the distinct IDs of
the member timelines, each naming a timeline of the manifest: a root or any
descendant. Members share the same graphical start and end: every
member's 0 coincides with every other member's 0 and every member's end
with every other member's end, and positions in between convert linearly.
When only part of a timeline takes part, the member is a child of that
timeline, placed at its exact offset; a member is never placed partially.
A timeline may be a member of several groups, and no member of a group
lies inside another member of the same group, since a timeline and its
descendant in one group would give two answers for one position; a child
may belong to one group while its root belongs to another or to none. The
roots that no group names, and that contain no member, are ungrouped. A
manifest holding a group always holds its members' roots, so a member that
is a child keeps its parent.

`graphical` is `{styles?, statements?, order?}`, at the manifest's top
level only, never on a timeline: a timeline holds time, and what is
graphical lies in this block. `styles` and `statements` style the drawing
([Drawing a manifest](#drawing-a-manifest)). `order` maps the ID of a group
or of a timeline to the order of what it stacks, top to bottom, and
writers never reorder it:

- a group's ID to the **display order** of its members, a permutation of
  them; a group without an entry is displayed in the order of `members`;
- a timeline's ID `T`, of a root or a descendant, to its **band order**, a
  permutation of its five bands `T/markers_1`, `T/conversion_maps_1`,
  `T/children_1`, `T/regions_1` and `T/flow_control_1`
  ([Identity](#identity)) and of `T` itself: the bands before `T` lie
  above its line, the nearest last, and those after it below, the nearest
  first. Every timeline, root or child, has these bands at its own line. A
  timeline without an entry follows its parent's band order, band by band
  ID (the parent's `P/regions_1` becomes `T/regions_1`), a member that is
  a child included, and a root without one the default
  `["T/children_1", "T/conversion_maps_1", "T", "T/markers_1",
  "T/regions_1", "T/flow_control_1"]`; changing a timeline's band order so
  changes that of every descendant without an entry of its own.

```json
"order": {"score": ["score/children_1", "score/markers_1", "score", "score/conversion_maps_1", "score/regions_1", "score/flow_control_1"]}
```

draws the start and end marks of `score` against its line above it, its
children beyond them, and its conversion maps against its line below it;
its descendants follow it, so their conversion maps lie below their lines
too. A manifest carries no MatchClaims.

### Unknown keys

Every object of the schema is open: the schema closes none and carries no
custom keyword, so a key an object does not declare is valid. Both
packages' validators find such keys themselves and report them as
**unknown keys**, except inside `meta`, the one free object. Unknown keys
are warnings, never errors, since a misspelt optional
key would otherwise silently become its default. Python's
`unknown_keys(value)` and npm's `unknownKeys(value)` return the same list of
`{path, key}` entries, the path locating the object that holds the key,
sorted by path and then by key; `validate` raises only on errors. timetoalign
and TimeLineEditor keep the unknown keys of a manifest they read and write
them back. A key that a host schema declares beside its `$ref` to a
TimeSkeleton definition is reported as unknown by these validators; the
host's own validator is unaffected.

### Identity

Every timeline, group, measure map, conversion map, region and
flow-control element carries an `id`, which identifies it, and so may the
manifest. A `name`, where an element has one, is what is displayed, and it
may repeat. An ID is a non-empty string without `/` and without control
characters, and it may contain spaces. A reference is an ID: a jump
origin's `target` names a jump target of the same timeline, and a measure
view's `measure_map` an entry of `measure_maps`.

Timeline IDs, of roots and descendants alike, group IDs, measure-map IDs
and the manifest's ID are unique together across the manifest. Each root's
tree is moreover one scope: within it, an ID is unique across all the
element kinds above, so a conversion map, region or flow-control element ID
is unique within the tree of its root and may repeat in another root's
tree.

One address rule holds in every manifest. A timeline, a group, a measure
map or the manifest is addressed by its bare ID; a conversion map, region
or flow-control element by the ID of the root whose tree holds it, `/`,
and its own ID
(`score/region_1`); the parts of an element follow its address: `…/start`,
`…/end`, `…/name` and `…/label`. A card follows the timeline it holds:
an ungrouped root's card is `T/card`, and a member's card `G/T/card`, one
for each group `G` that has the timeline `T` as a member; every other
element keeps one address however often it is drawn. The five
**bands** every timeline has, root or child, follow the timeline's ID
too, each by its kind and number: `…/markers_1`, `…/conversion_maps_1`,
`…/children_1`, `…/regions_1` and `…/flow_control_1`, which hold its
coordinate markers, conversion maps, children, regions and flow control in
its drawing. The words `start`, `end`, `name`, `label` and `card` are
therefore reserved, and so is every ID
that matches `^(markers|conversion_maps|children|regions|flow_control)_[1-9][0-9]*$`,
whatever its number: no ID of a manifest may be one of them or match the
pattern. The manifest's title, the top label of its drawing, is addressed
`name`, whether or not the manifest has an `id`, and a group's title
`G/name`.

The JSON Schema cannot express these rules, nor that a reference names an
element, nor that a map converts from its timeline's unit or its
holder's, nor that a map's arrays agree, nor that a member names a timeline
of the manifest, nor that no member of a group lies inside another, nor
that a child lies within its parent's known length, nor that a segment
line's segments are contiguous and alike, nor the representation of
own-axis values, so both validators check them after the schema. Each
finding is one problem, located by a path into the manifest and named by a
stable code:

| Rule | Code | Location | Message |
| --- | --- | --- | --- |
| An ID repeats within one root's tree | `duplicate_id` | the later occurrence | `duplicate id '<id>', first at <pointer>` |
| A jump origin's `target` names no jump target of its timeline | `dangling_target` | the `target` | `'<target>' names no jump_to of this timeline` |
| A measure view's `measure_map` names no entry of `measure_maps` | `dangling_target` | the `measure_map` | `'<id>' names no measure map of this manifest` |
| A map's non-null `source_unit` is not its timeline's unit, or, for a map a `PiecewiseMap` or `CombinationMap` holds or a `ChainMap`'s first map, not its holder's non-null `source_unit` | `conversion_map` | the `source_unit` | `<type> '<id>' has source unit '<unit>', its timeline '<id>' has '<unit>'` (`… its <holder type> '<id>' has '<unit>'`) |
| A `TableMap`'s `x_values` and `y_values` differ in length | `conversion_map` | the `y_values` | `TableMap '<id>' has <n> x values and <m> y values` |
| An x value of a `TableMap`, or a break of a `PiecewiseMap`, does not exceed the one before it | `conversion_map` | the value | `x value <value> of TableMap '<id>' does not exceed the one before it` (`break <value> of PiecewiseMap …`) |
| A `PiecewiseMap` does not have one map fewer than breaks | `conversion_map` | the `maps` | `PiecewiseMap '<id>' has <n> maps for <m> breaks; it needs <m − 1> maps` |
| A child's `unit` is not its parent's | `child_unit` | the child's `unit` | `child '<id>' has unit '<unit>', its parent '<id>' has '<unit>'` |
| A child's `offset` lies beyond its parent's known length | `child_offset` | the child's `offset` | `offset <offset> of '<id>' is beyond the length <length> of its parent '<id>'` |
| A child ends beyond its parent's known length, its own end known | `child_end` | the child's `length` | `child '<id>' ends at <end>, beyond the length <length> of its parent '<id>'` |
| A segment's `is_segment_line` differs from the first segment's | `segment_line` | the segment's `is_segment_line`, or the segment when it leaves the key out | `segment '<id>' of segment line '<id>' differs from segment '<first id>' in is_segment_line` |
| A segment does not start where the one before it ends, or the first at 0 | `segment_line` | the segment's `offset` | `segment '<id>' of segment line '<id>' does not start where the one before it ends` (`… does not start at 0`) |
| The last segment does not end at the segment line's length, both known | `segment_line` | the segment line's `length` | `the segments of segment line '<id>' do not end at its length` |
| An ID is `start`, `end`, `name`, `label` or `card`, or matches the band pattern above | `reserved_id` | the `id` | `id '<id>' is reserved for the parts of an address` (`id '<id>' is reserved for the bands of a timeline`) |
| A timeline ID repeats one of an earlier root's tree | `duplicate_id` | the later occurrence | `duplicate id '<id>', first at <pointer>` |
| A group ID equals a timeline ID or an earlier group's ID | `duplicate_id` | the group's `id` | `duplicate id '<id>', first at <pointer>` |
| A measure-map ID equals a timeline ID, a group ID or an earlier measure map's ID | `duplicate_id` | the measure map's `id` | `duplicate id '<id>', first at <pointer>` |
| The manifest's ID equals a timeline ID, a group ID or a measure-map ID | `manifest_id` | `id` | `duplicate id '<id>', first at <pointer>`, the pointer naming the timeline, else the first such group, else the first such measure map |
| A member names no timeline of the manifest | `group_member` | the member | `'<id>' names no timeline of this manifest` |
| A member repeats an earlier member of its group | `group_member` | the later member | `duplicate member '<id>', first at <pointer>` |
| A member lies inside an earlier member of its group, or contains one | `group_member` | the later member | `member '<id>' lies inside member '<earlier id>' of the same group` (`… contains member …`) |
| A key of `graphical.order` names no group and no timeline | `order_key` | the key | `'<key>' names no group or timeline of this manifest` |
| An entry of a display order is not a member of its group | `display_order` | the entry | `'<id>' is not a member of group '<group id>'` |
| A member of a group is missing from its display order | `display_order` | the order | `member '<id>' of group '<group id>' is missing` |
| An entry of a band order is neither its timeline's ID nor one of its bands | `band_order` | the entry | `'<entry>' is not '<id>' or one of its bands` |
| A band, or the timeline's own ID, is missing from its band order | `band_order` | the order | `'<address>' is missing from the band order of '<id>'` |

Within one root's tree, IDs are visited in identity order (a timeline,
then its conversion maps, regions and flow-control elements, then its
children in array order), and after them the IDs of the maps a
`ChainMap`, `PiecewiseMap` or `CombinationMap` holds, timeline by timeline
in the same order, each map before the maps it holds; duplicates come first, then dangling targets
(timeline by timeline, its jump origins' targets before its measure views),
then the conversion-map rules (a timeline's maps in array order, each
before the maps it holds, the outputs of a `CombinationMap` in code-point
order of their names, then its children's), then children off their
parent's axis (child by child, each followed by its
own children: its unit, then an offset beyond its parent's known length
or else an end beyond it), then segment lines, whose
segments are visited in canonical order and compared by exact value. Across the manifest, the problems come in this
order: each root's own problems, roots in array order; then reserved IDs
(the manifest's ID, then root by root in identity order followed by the
IDs of the maps other maps hold, then the group IDs, then the measure-map
IDs); repeated timeline IDs, group IDs,
measure-map IDs, the manifest's ID, members (member by member: dangling, repeated, nested), and
the entries of `graphical.order` in code-point order of their keys: an
order's strangers first, in its order, then its missing entries, in the
order of the group's `members` or of the default band order. `<pointer>`
is a JSON pointer in URI fragment form, such as `#/timelines/0/id`, as Python's
`json_pointer(path)` and npm's `jsonPointer(path)` render a path. The
messages above quote IDs as Python does; the TypeScript package quotes them
as JSON (`duplicate id "piece", first at #/timelines/0/id`), except the
three messages about a child's unit, offset and end, which read the same in
both packages, every value spelled as the standard writer spells it (`720`,
`[19, 2]`, `75.0`). A child's end, its offset plus its length, or for a
segment of unknown length its successor's offset, is compared exactly and
spelled as its parent's number type writes it, or as a `[numerator,
denominator]` pair where that type cannot write it exactly. A repeated
entry within one display or band order or within one group's `members` is
refused by the schema, and so is, at the entry, an entry of an order that
is neither an ID nor an ID followed by `/` and a band's ID, its kind, `_`
and its number (`score/foo`, `score/region_1`); an entry of that shape in
the band order of `score` that is neither `score` nor one of its bands,
such as `score/regions_2` or `other`, is refused by the table's band-order
row above.

### The schema document

Version 0.7.0 is one document, `schema/0.7.0/timeskeleton.schema.json`,
with the identifier
`https://timetoalign.github.io/timeskeleton/0.7.0/timeskeleton.schema.json`,
so the document lies below `schema/` at the path of its identifier. Its root
is `{"$ref": "#/$defs/TimeSkeleton"}`. These definitions are public and
may be embedded by a host schema; within 0.7.x they change only by
addition:

`TimeSkeleton`, `Timeline`, `Group`, `Graphical`, `ConversionMap`,
`Coordinate`, `Number`, `Fraction`, `TimeUnit`, `NumberType`, `Id`,
`MeasureMap` and `MeasureMapRow`.

A host refers to the document, or to one definition as
`timeskeleton.schema.json#/$defs/<Name>`, never through an `$anchor`. It
embeds either a whole manifest, version marker included, or a bare
`Timeline`, in which case the host records the TimeSkeleton version itself.

The schema is the source of truth for timetoalign and TimeLineEditor.
timetoalign's hand-written serialization is tested for schema conformance and
fixture round trips. TypeScript types are generated in this repository from
the one document.

## Drawing a manifest

The optional `graphical` block of a manifest contains named declarations
in `styles` and an ordered list of `statements`:

```json
"graphical": {
  "styles": {
    "highlight": {"stroke": "#7F00FF", "fill": "#7F00FF"}
  },
  "statements": [
    {"select": {"element": "label"}, "set": {"fill": "#404040"}},
    {"select": {"element": "wedge", "within": "performance"}, "set": "highlight"}
  ]
}
```

Each statement has a selector in `select` and either a declaration or a style
name in `set`. Statement order matters. The complete selectors, presentation
properties, cascade, defaults, element addresses, layout, and writer profiles
are defined by the
[drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md).

Every manifest is drawn as one box, opened by its title: its `name`, or its
`id` when it has no name; an anonymous bundle has none. Each group is a
frame; each ungrouped root lies in a card of its own, and each member in
one card in the frame of each group that has it as a member; a
member that is a child timeline is drawn with the faded lines of its
ancestors. The element types are `block`,
`card`, `timeline`, `child`, `band` (one of a timeline's five bands, which
its band order places above or below its own line; a band that is not
displayed hides everything it holds, and by default the markers, regions
and flow control bands are hidden on every timeline but the one a card
holds),
`boundary` (a segment's start on its segment line), `ancestor`, `group` (a
frame), `map`, `region`, `flow_marker` (a flow marker), `jump_from` (a
jump origin, drawn as an arc to its target or to the start; a jump target
draws nothing), `wedge` (a coordinate marker, never an element of
`flow_control`), `name` and `label`.
Besides `element`, a selector may name `ids`, `domain`, `modality`,
`class`, `within` (a timeline and its descendants) and `inside` (an element
type that holds the element at any depth); the selector's `class` names
the class a timeline's unit decides, such as `ContinuousPhysicalTimeline`
for `seconds`, a conversion map's type, or a band's kind, such as
`regions`. The property `shadow` colours
a card's offset shadow. The group fixture `group_styled` frames its group in violet, fills the group's title violet,
and gives every card in a frame a light violet shadow:

```json
"graphical": {
  "order": {"group_1": ["score", "page", "performance"]},
  "statements": [
    {"select": {"element": "group"}, "set": "frame-highlight"},
    {"select": {"element": "name", "ids": ["group_1/name"]}, "set": {"fill": "#7F00FF"}},
    {"select": {"element": "card", "inside": "group"}, "set": {"rx": 2, "shadow": "#C4B5FD"}}
  ],
  "styles": {
    "frame-highlight": {"stroke": "#7F00FF"}
  }
}
```

A statement may name a style missing from its block's `styles`. Python's
`complete_styles(graphical)` and npm's `completeStyles(graphical)` return a
copied block with every such name added as an empty declaration, together with
the sorted missing names. Python issues one `MissingStyleWarning` and npm one
`console.warn` call, each naming all missing styles. The completed block is
valid, and a statement that names one of those empty declarations sets nothing.

A drawing is derived and is not exchanged as JSON. The drawing specification
pins the drawing, and both packages contain it: the wheel as
`timeskeleton/docs/drawing.md`, the npm package as
`@timetoalign/timeskeleton/docs/drawing.md`.

Every text is measured and drawn with the bundled DejaVu Sans 2.37 release
file, `fonts/DejaVuSans.ttf`. `fonts/LICENSE` contains its licence, and
`fonts/dejavu-sans-2.37.metrics.json` contains its advance-width metrics.
Python exposes the files through `font_path()` and `font_metrics()`. The npm
package exports `fontMetrics` and exposes the files through the
`@timetoalign/timeskeleton/fonts/*` subpath. Run
`scripts/extract_font_metrics.py` to regenerate the metrics from the font.

## Canonical order

Readers accept a manifest's collections in any order. Writers emit one
canonical order, so equal manifests have equal text. The keys of every
object, at every depth, are sorted by Unicode code point. The arrays whose
order keys cannot express are put in this order:

- `timelines`, `groups` and `measure_maps` by ID, and every group's
  `members` by code point;
- in every timeline, `children` by offset, then ID;
- `conversion_maps` by ID;
- `regions` by start, then end, then ID;
- `flow_control` by coordinate, then ID.

IDs are unique within their scope, so no two entries tie. Coordinates
compare by exact numeric value, never by JSON spelling. Strings compare by
Unicode code point. No other array is reordered: `graphical` statements,
display orders, conversion-map payloads, and measure-map rows keep their
order.

## The standard writer

Each package has one writer, `dumps`. It puts a manifest in canonical
order, sorts the keys of every object by code point, and writes UTF-8 text
with two-space indentation and a final newline. It writes any other JSON
value, such as an application's file embedding manifests, under the same
rules. It writes the form it is given: pass a manifest through `complete`
or `minimal` first to choose its form. Every
character is unescaped except `"`, `\`, and control characters U+0000 to
U+001F. A float remains a float and is spelled as Python's `repr` spells it
(`2.0`, `0.0001`, `1e-05`, `1e+16`, `-0.0`); an integer never has a decimal
point or exponent. A NaN, an infinity, or a string containing a lone surrogate
is refused. The fixtures use this writer.

## Install

```bash
pip install timeskeleton
```

```bash
pnpm add @timetoalign/timeskeleton
# or
npm install @timetoalign/timeskeleton
```

## Usage

### Python

Python validation raises `SchemaValidationError` with the `code` of the
rule broken, a tuple `path` to the offending value and a `message`. Read a
manifest with `loads` and write it with `dumps`:

```python
from timeskeleton import SchemaValidationError, dumps, fixture_paths, loads, validate

value = loads(fixture_paths()[0].read_text(encoding="utf-8"))
try:
    validate(value)
except SchemaValidationError as error:
    print(error.code, error.path)
else:
    text = dumps(value)
```

- `validate(value)` reads the version marker first, then checks the value
  against the schema, the representation of its own-axis values and the
  identity rules, and raises `SchemaValidationError` at the first problem.
  A value without `timeskeleton` is refused at the root; a value declaring
  another version raises `UnsupportedVersionError` naming 0.7.0. Unknown
  keys never fail it.
- `loads(text)` reads JSON text as the TypeScript package's `parseJson`
  does: integers stay exact at any size and floats stay floats, and `NaN`,
  `Infinity` and a float beyond a double are refused with `ValueError`.
- `unknown_keys(value)` returns the unknown keys of a manifest as a list of
  `{path, key}` entries, sorted by path and then by key.
- `complete(value)` and `minimal(value)` return a copy of a manifest in the
  complete or the minimal form; the input is not changed.
- `dumps(value)` returns the standard text of a manifest or any JSON value.
- `canonical_order(value)` returns a deep copy with the manifest's arrays in
  canonical order. `canonical_json(value)` returns compact JSON with object
  keys sorted by code point.
- `identity_problems(value)` returns every violation of the identity rules in
  a schema-valid manifest, in the order described above; `validate` raises
  the first.
- `complete_styles(graphical)` returns `(completed, missing)` and warns with
  `MissingStyleWarning` when `missing` is non-empty.
- `SCHEMA_VERSION` is `"0.7.0"`, the one version the package reads.
- `schema_path()` and `load_schema()` return the schema document,
  `fixture_paths()` the bundled accepted fixtures, `rejection_paths()`
  the bundled rejection cases and `warning_paths()` the bundled warning
  cases. `rejection_case(path)` reads one rejection case as a
  `RejectionCase` (`manifest`, `path`, `code`, `error`, `reason`), with the
  non-finite number a finite-rule case names put in place.
- `font_path()` returns the bundled TrueType file, and `font_metrics()` returns
  its metrics.

### TypeScript

`JSON.parse` cannot preserve every distinction in the format: it reads `2.0`
as the integer `2`, rounds integers beyond 2^53, and changes the enumeration
order of array-index keys. Use the package's lossless reader:

```ts
import {
  dumps,
  parse,
  SchemaValidationError,
} from "@timetoalign/timeskeleton";

function load(text: string): string {
  try {
    return dumps(parse(text));
  } catch (error) {
    if (error instanceof SchemaValidationError) {
      console.error(error.code, error.path);
    }
    throw error;
  }
}
```

- `parse(text)` reads and validates a manifest without losing a number or
  key order, and returns it as a `LosslessTimeSkeleton`. `parseJson(text)`
  reads any JSON text without validating it, and throws `JsonSyntaxError`,
  a `SyntaxError` with the `offset` (in UTF-16 code units), `line` and
  `column` (from 1) of the fault.
- `validate(value)` asserts that an unknown value is a
  `LosslessTimeSkeleton` (its numbers may be bigints and `JsonFloat`s),
  checking it as Python's `validate` does; its `SchemaValidationError` carries the same
  `code` (typed `ValidationCode`), a `path` and a `detail`.
- `unknownKeys(value)` returns the same list as Python's `unknown_keys`.
- `complete(value)` and `minimal(value)` return the complete and the minimal
  form, as Python's functions do, keeping every number and key order
  `parseJson` read. The typed forms say which form a value is in:
  `completeManifest(value: LosslessTimeSkeleton): CompleteTimeSkeleton`,
  `minimalManifest(value): LosslessTimeSkeleton` and
  `canonicalManifest(value)`, which returns its argument's type in canonical
  order.
- `dumps(value)` is the standard writer. `compactJson(value)` writes without
  whitespace, and `canonicalJson(value)` also sorts object keys by code point.
- `canonicalOrder(value)` returns a deep copy with the manifest's arrays in
  canonical order.
- `identityProblems(value)` returns the same identity problems as Python's
  `identity_problems`.
- `completeStyles(graphical)` returns `{graphical: completed, missing}`.
- `fontMetrics` contains the bundled font's advance-width metrics.
- `SCHEMA_VERSION` is `"0.7.0"`, and `schema` holds the schema document.
  The generated types are generated from it, with the root type
  `TimeSkeleton` and one type per definition, such as `Timeline`, `Group`
  and `Graphical`. Beside each definition with defaults a complete form is
  generated, `CompleteTimeSkeleton`, `CompleteTimeline`, `CompleteGroup` and
  so on, in which every key with a default is required at every depth and
  every number is a `JsonNumber`; keys whose default is their absence (the
  manifest's `id` and `graphical`, a root's `offset`) stay optional.
  `LosslessTimeSkeleton` is `Lossless<TimeSkeleton>`.

A number read by `parseJson` is a `JsonNumber`:

| JSON text | `JsonNumber` |
| --- | --- |
| an integer within ±(2^53 − 1), such as `480` | a `number` |
| an integer beyond that range, such as `9007199254740993` | a `bigint` |
| a float with a fractional part, such as `0.5` | a `number` |
| an integral float, such as `2.0`, `1e+16`, or `-0.0` | a `JsonFloat` |

`Lossless<T>` replaces every `number` in `T` with `JsonNumber` and keeps
tuples, so a Fraction is `[JsonNumber, JsonNumber]`. A float whose
value is an integer must be passed as `new JsonFloat(2)`, not as `2`, if it is
to be written as a float. JavaScript code that writes files must use
`dumps` or `compactJson`, not `JSON.stringify`.

## Versioning

The packages read the current version only. A value declaring any other
version raises `UnsupportedVersionError`, and neither package migrates a
value from one version to another. Older versions live in the git history
of this repository and in the packages released with them.

A timeskeleton release is a schema-version event: one `vX.Y.Z` tag publishes
both packages through trusted publishing. `scripts/check_versions.py` checks
that all version declarations agree.

## Fixtures

The [fixture guide](fixtures/README.md) describes the generated manifests
and the drawings, the hand-authored rejection cases, and the warning cases.
Every accepted fixture is written in the complete form beside its minimal
twin. The manifests are emitted only by timetoalign through the catalogue of
builders in `scripts/fixtures/`, whose CLI is `scripts/emit_fixtures.py`. Do
not edit them by hand.

## Development

Clone the repository, then run the package commands in their directories:

```bash
cd python
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv build
```

```bash
cd ../js
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm generate
pnpm build
```

To regenerate the font metrics, run this from `python/`:

```bash
uv run python ../scripts/extract_font_metrics.py
```

To re-emit the fixtures, use an interpreter containing the timetoalign
revision being represented:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"
```

From the repository root, check version declarations with:

```bash
python3 scripts/check_versions.py
```

## Releasing

See the
[contribution guide](https://github.com/TimeToAlign/timeskeleton/blob/main/CONTRIBUTING.md)
for the required version updates, checks, tag, and trusted-publishing
configuration.

## License

[MIT](https://github.com/TimeToAlign/timeskeleton/blob/main/LICENSE).
