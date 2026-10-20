# Test strategy for the `timeskeleton` Python package

This suite proves the public contract of schema 0.7.0: one manifest shape,
described by one schema document, read by one validator. The package
supports this version only.

Every rule is proved by a document written inline in its test, never by
editing a fixture: the documents are the smallest that exercise the rule, so
a passing test cannot be a restatement of a fixture the implementation
produced. The shared rejection and warning cases (`fixtures/rejections/0.7.0/`
and `fixtures/warnings/0.7.0/`) are read by this suite and by the JavaScript
suite, so both validators are held to the same paths and the same lists.

## What the package promises

1. Every manifest is `{timeskeleton, timelines, id?, name?, meta?, groups?,
   measure_maps?, graphical?}`; `validate` accepts exactly the values the schema and the
   rules below accept, and raises the first violation with its code and
   path.
2. A value without the version marker is refused at the root, a value with
   another version raises `UnsupportedVersionError`.
3. Unknown keys are kept and listed by `unknown_keys`, never refused.
4. `complete` and `minimal` convert between the complete and the minimal
   form, both pure, from one table of defaults that agrees with the schema.
5. `canonical_order` and `dumps` write every manifest, bare own-axis values
   included, as the same bytes as the JavaScript package.
6. Schema, fixture and font accessors resolve package data independently of
   the working directory; the wheel and the sdist ship the schema document,
   `docs/drawing.md` and the licence.

## The schema document

`schema_path()` is `schema/0.7.0/timeskeleton.schema.json`; `load_schema()`
parses it. The tests hold invariants of the document, never a transcript of
its definitions; the definitions' contents are proven by the fixtures and the
rejection cases that use them (`test_schema.py`):

- **One document, one root.** `$id` is
  `https://timetoalign.github.io/timeskeleton/0.7.0/timeskeleton.schema.json`,
  `$schema` the 2020-12 dialect, the root `$ref` is `#/$defs/TimeSkeleton`,
  and `schema/` holds exactly the directory `0.7.0` with exactly that file.
  Every `$ref` is local (`#/$defs/<name>`) and names a definition; no node
  carries `$anchor`.
- **The public definitions.** The definitions include the thirteen public
  ones `TimeSkeleton`, `Timeline`, `Group`, `Graphical`, `ConversionMap`,
  `Coordinate`, `Number`, `Fraction`, `TimeUnit`, `NumberType`, `Id`,
  `MeasureMap` and `MeasureMapRow`, and none of `TimelineClass`,
  `TimelineManifest`, `Bundle`, `GroupGraphical`, `BundleGraphical`,
  `CoordinateNonnegative` and `MemberOrder`.
- **The map types.** `ConversionMap` chooses between exactly the ten types
  `ChainMap`, `CombinationMap`, `ConstantMap`, `FloatingMeasureMap`,
  `LinearMap`, `MeasureBeatMap`, `MeasureNumberMap`, `MeasureRecordMap`,
  `PiecewiseMap` and `TableMap`, and `Selector.class` names exactly the six
  timeline classes, these ten types and the five band kinds. The four
  measure views fix `source_unit` to `quarters` and `target_unit` to
  `floating_measures` (`FloatingMeasureMap`) or null (the other three).
- **The unit table.** `TimeUnit` is a string whose `oneOf` holds one
  `{const, description}` per unit and no `enum`. The consts, in order, are
  exactly the keys of `UNIT_NUMBER_TYPES`, and each description is
  `<Domain>, <modality>; default number type <t>.` with `t` that unit's
  value in the table, so the default number types the validators read
  cannot drift from the ones the schema states.
- **Shared definitions.** A shape that repeats is defined once: `Name`
  (string or null, default null) and `Meta` (a free object, default `{}`)
  are referred to by every `name` of the manifest, a timeline, a group, a
  region, a flow-control element, a measure map and a conversion map and by every
  `meta`, and no property repeats their shapes inline. `MapBase` declares
  `type`, `id`, `name`, `source_unit` and `target_unit` and requires all but
  `name`; `MeasureView` is an object whose `allOf` is exactly
  `[{"$ref": "#/$defs/MapBase"}]`, whose own `properties` are exactly
  `source_unit`, the constant `quarters`, and `measure_map`, and whose
  `required` is exactly `["measure_map"]`. Every conversion map is an
  object whose `allOf` is exactly `[{"$ref": "#/$defs/MeasureView"}]` for
  the four measure views and `[{"$ref": "#/$defs/MapBase"}]` for the six
  others, whose own `properties` declare of the bases' keys only `type`,
  its constant, and, on a measure view, `target_unit`, a constant, and
  whose `required` lists `type`, as a discriminated union needs, and none
  of the bases' other keys.
- **References are IDs, addresses are `Address`.** `Selector.within`,
  `FlowControlElement.target` and the `measure_map` of each of the four measure views
  refer to `Id`; the items of
  `Selector.ids` to `Address`, which accepts `score`, `score/regions_1`,
  `score/region_1/label` and `a b/c` and refuses `""`, `/score`, `score/`,
  `score//label` and `score/a` followed by a tab.
- **Open objects.** No node anywhere has `additionalProperties: false` or
  `unevaluatedProperties`, and no key anywhere in the document begins with
  `x-`: objects are open by omission, with no custom keyword. Every object
  node with `properties` outside a branch declares, in its own `properties`
  or in those of the bases its `allOf` names, at any depth, every key its `oneOf`/`anyOf`
  branches and `if`/`then`/`else` arms declare, which is what lets
  `unknown_keys` name the unknown keys from the node alone. `meta` (on the
  manifest, a timeline, a region, a flow-control element, a group, a measure map)
  refers to `Meta`; `Meta` is the one free object: `additionalProperties:
  true` and no `properties`.
- **Discriminated unions.** Exactly two nodes carry a `discriminator`, on
  `number_type` and on `type`; each tags every branch with a distinct
  required string constant.
- **Defaults agree with the table.** For every kind of `DEFAULTS` the
  schema's corresponding definitions (`TimeSkeleton`, `Timeline`,
  `Region`, `FlowControlElement`, `MeasureMap`, `Group`, `Graphical`, every
  conversion map) declare `default` on exactly the keys
  of that kind's table, each equal to the table's value, and on no other
  key; a conversion map's kind is `conversion_map`, joined by `linear_map`
  for a `LinearMap` (`scalar` 1, `offset` 0) and by `table_map` for a
  `TableMap` (`kind` `linear`, `extrapolate` `none`); a flow-control
  element's kind is `flow_control_element`, joined by `repeat_end`
  (`repeat_count` 1), which `complete` applies to a `repeat_end` only, since
  no other element may carry a repeat count: the schema states that one
  default in the `then` arm of the `if` that tests for a `repeat_end`, and
  not on the shared `repeat_count` property, so a reader that supplies
  every default it finds on a property never writes `repeat_count` to an
  element that must not carry it. A key's default is
  stated on its property or on the definition the property refers to
  (`Name`, `Meta`), and a conversion map's keys include those of its bases,
  at any depth. `number_type`
  has no `default` (it depends on the unit). The JavaScript suite holds its
  table to the same schema, so the two tables are equal.

## The version marker

`validate` and `unknown_keys` read `timeskeleton` first (`test_validate.py`):

- a value without it, a list and a string are refused at the root with
  exactly `not a TimeSkeleton manifest`, whatever else they hold (a value
  holding the former `meta.schema_version` but no marker too);
- `"9.9.9"`, `"0.6.0"`, `"0.7"` and the number `7` raise
  `UnsupportedVersionError` with `version` that value, the message for
  `"9.9.9"` exactly `unsupported TimeSkeleton version '9.9.9'; this package
  reads 0.7.0 only`; the marker is checked before the schema, so a value with
  another version and no `timelines` raises the same error;
- the smallest file `{"timeskeleton": "0.7.0", "timelines": [{"id": "piece",
  "unit": "quarters", "length": [32, 1]}]}` and the empty manifest
  `{"timeskeleton": "0.7.0", "timelines": []}` validate.

## Reading by the declared number type

The declared number type decides how a value is read, never its lexical
form: a number written with a zero fractional part is the integer it equals
wherever an integer is read. A Fraction member written `8.0` is 8, wherever
a Fraction occurs (own-axis values, conversion-map Numbers at any depth of
nesting, measure-map rows); `2.0` on an int axis is 2; `2` on a float axis
is 2.0. So a JSON round trip that respells numbers (`JSON.parse` and
`JSON.stringify` turn `8.0` into `8`) never invalidates a manifest. What
proves it (`test_validate.py`): one inline manifest (`respellable()` in
`conftest.py`) validates, leaves `unknown_keys` empty and is unchanged by
`validate`. In quarters it holds the length `[32, 1.0]`, a child offset
`[8.0, 1]`, a region from `[0, 1.0]` to `[1.0, 2]`, a jump target at `[2.0, 1]`, a
TableMap x value `[1.0, 2]` nested in a ChainMap, a LinearMap offset
`[0, 1.0]` and, in the manifest's measure map, a row with `qstamp`
`[0, 1.0]` and `actual_length` `[4.0, 1]`; in ticks a length `480.0` with a child offset
`240.0`; in seconds a length `60` and a region starting at `0`. It also holds
numbers whose place declares no number type: the LinearMap scalar `1.0`,
the TableMap y values `0.0` and `0.5` and the row's `nominal_length` `4.0`.

Still refused, each by a shared rejection case: a non-integral value on an
int axis (`length_float_on_int_axis`, `480.5` in ticks, `representation`
at the length), a non-integral Fraction member (`length_fraction_member_not_integral`,
`[12, 1.5]`, `schema` at the member), a denominator below 1
(`length_zero_denominator`), a Fraction on an int axis
(`length_fraction_on_int_axis`) or on a float axis
(`child_offset_fraction_on_float_axis`), and a bare number on a fraction
axis (`length_int_on_fraction_axis`, `region_start_float_on_fraction_axis`).

**Readers coerce, writers spell canonically.** `complete` (so `minimal`
too) and `canonical_order` (so `dumps` too) respell every value the manifest
reads by a number type: an own-axis value on an int axis as a JSON integer,
on a float axis as a float, and every member of a Fraction pair (own-axis,
conversion-map Numbers at any depth, measure-map rows) as a JSON integer.
`loads` and `validate` change nothing. A number whose place declares no
number type (a conversion map's bare Number, a measure-map row's bare
quarter value, a `repeat_count`, a free value) keeps its spelling, and a
value that has no exact respelling (an integer beyond 2^53 on a float axis,
which `validate` refuses) is left as written. What proves it
(`test_manifest.py`): for that manifest, `complete`, `minimal` and
`canonical_order` each give, compared as `canonical_json` texts (which tell
`8.0` from `8`), exactly what they give for its literal twin `respelled()`,
written canonically (`[32, 1]`, `[8, 1]`, `[0, 1]`, `[1, 2]`, `[2, 1]`,
`[1, 2]`, `[0, 1]`, `[0, 1]`, `[4, 1]`, `480`, `240`, `60.0`, `0.0`, with
`1.0`, `0.0`, `0.5` and `4.0` kept); `dumps` writes the twin's text; the twin
is its own canonical order and spelling, so that text is the canonical one;
and the input is unchanged. Each of the three equalities fails when the
respelling is left out. A seconds length `9007199254740993` stays that
integer.

`test_number_members.py` derives every scalar and array member of a
conversion map that can hold a Number (by reference or as a branch of an
`anyOf`, as `ConstantMap.value` does), and every scalar, array and
keyed-object member that holds a nested conversion map, from the schema's
conversion-map definitions. It asserts exact equality with the respelling's
two traversal tables, naming every missing or extra entry on failure, so a
schema addition cannot escape the canonical spelling.

An own-axis value (a timeline's `length` and `offset`, a region's `start` and
`end`, a flow-control element's `coordinate`) is a bare Number whose representation the axis's number type
selects: an int axis an integral JSON number, a float axis any JSON number
that a float equals exactly (an integer beyond 2^53 may have none), a
fraction axis a pair. The axis is the timeline's `number_type`, else its
unit's default (`int` for ticks, samples, frames, pixels; `fraction` for
quarters, whole_notes; `float` otherwise). A child's offset lies on its
parent's axis, a root's on its own. A mismatch is reported after the schema,
at the value, as `<key> <value> of '<id>' is <found> on <axis> axis: write
<value rewritten>`, the ID that of the object holding the key, the value
rewritten where an exact rewriting exists, else the number type named. What
proves it, one inline document per line, message stated literally:

- `length 32 of 'score' is an int on a fraction axis: write [32, 1]`;
- `length 0.5 of 'score' is a float on a fraction axis: write [1, 2]`;
- `length 0.1 of 'score' is a float on a fraction axis: write
  [3602879701896397, 36028797018963968]` (the exact value of the double);
- `length [3, 4] of 'take' is a fraction on a float axis: write 0.75`;
- `length [1, 3] of 'take' is a fraction on a float axis: write a float`;
- `length [480, 1] of 'midi' is a fraction on an int axis: write 480`;
- `length 0.5 of 'midi' is a float on an int axis: write an int`;
- `length [1, 2] of 'midi' is a fraction on an int axis: write an int`;
- `length 9007199254740993 of 'take' is an int on a float axis: write a
  float` (2^53 + 1 lies between two floats, so no float rewrites it);
- on a seconds axis declared `fraction`, `length 2.0` is `a float on a
  fraction axis: write [2, 1]`, and on quarters declared `float` a length
  `[2, 1]` is `write 2.0`;
- `offset [1, 2] of 'take' is a fraction on a float axis: write 0.5` for a
  child in seconds of a root in seconds, and a child in quarters of a root in
  seconds with offset `[1, 2]` is reported the same way (the parent's axis),
  while its own length `[4, 1]` is fine; a root's own `offset 3` in quarters
  is `write [3, 1]`;
- `start`, `end` and the `coordinate` of a flow marker, a jump origin and a
  jump target each reported at its own path with its holder's ID.

Accepted: `8` and `8.0` on an int axis (an integral number is an int),
`8`, `0.5`, `9007199254740992` (2^53) and `10**20` on a float axis (each
exactly a float), `[8, 1]` and `[8.0, 1]` on a fraction axis, `length:
null` anywhere, a root's negative offset in its own number type. The checks
visit a timeline's offset, length, regions and flow-control elements, then
its children in array order; the first problem is raised.

## Open objects and unknown keys

`unknown_keys(value)` validates the value and returns every key the schema
does not declare on the object holding it, as `{"path": [...], "key": ...}`,
sorted by path (segment by segment, indices by number, keys by code point,
an object before its descendants) and then by key (`test_unknown_keys.py`):

- **The shared warning cases.** For every case of
  `fixtures/warnings/0.7.0/`, `validate` accepts the manifest and
  `unknown_keys` returns exactly its `unknown_keys` list; the JavaScript suite
  asserts the same lists. `several_depths` holds unknown keys on the
  manifest, a timeline, a child, a region, a flow marker, a jump origin, a
  jump target, a conversion map and the map nested in it, a measure map and
  one of its rows, a group, the graphical block, a statement, a selector and a
  declaration (sixteen entries). The other cases are the rules the closed
  0.7.0 draft enforced and the open one reports: a former timeline `class`,
  a manifest `support_policy`, a group's `order`, `arrangement` in
  `graphical`, a selector's `kind`, a declaration's `colour` and
  `show-projections`, a measure-map row's `tempo` and `offset`, and a
  `CombinationMap`'s former `names`.
- **A former property.** `side` is not a property: a manifest whose statement
  sets `{"fill": "#000000", "side": "above"}` on maps and whose style
  `below` is `{"side": "below"}` validates, and `unknown_keys` lists exactly
  `{"path": ["graphical", "statements", 0, "set"], "key": "side"}` and
  `{"path": ["graphical", "styles", "below"], "key": "side"}`.
- **A base of a base.** A measure view's base is `MeasureView`, whose own
  base is `MapBase`: a `MeasureNumberMap` carrying the unknown key
  `colour` lists exactly `{"path": ["timelines", 0, "conversion_maps",
  0], "key": "colour"}`, its `id`, `name` and units counting as declared.
- **What is not reported.** Keys inside `meta` (a free object), keys inside the value of an unknown key, keys of `styles` and of
  `graphical.order` (maps keyed by data), and a known key whose value is
  its default: a manifest with none of these and a key in each lists
  nothing.
- **Sorting.** Keys `zz`, `aa`, `ﬀ`, `😀` on one object come out `aa`, `zz`,
  `ﬀ`, `😀`; an unknown key on `timelines[10]` follows one on
  `timelines[2]`; the manifest's own keys come first.
- **An invalid value** raises the error `validate` raises, before any key
  is listed.
- **One walk.** The keys come from the schema walk `validate` runs. It
  walks an in-memory variant of the document that closes every object the
  document leaves open (`unevaluatedProperties: false` on each object node
  with `properties` outside a branch, except the base an `allOf` shares), and
  a failure that only an undeclared key causes is a key to list, not a
  violation. Listing them walks the manifest with the schema once, as a
  counting validator proves.

## Defaults: the complete and the minimal form

`DEFAULTS` is the one table (`test_defaults.py`). What proves `complete` and
`minimal`:

- **Literal forms.** The smallest file completes to the literal complete
  manifest (`name` null, `meta` `{}`, `groups` and `measure_maps` `[]`, and
  on the timeline `name` null, `number_type` `fraction`, `locked` false,
  `is_segment_line` false, `meta` `{}`, `children`, `conversion_maps`,
  `regions` and `flow_control` `[]`), and that minimizes back to the
  smallest file. A region, a flow-control element (a `repeat_end` gains
  `repeat_count` 1 besides, no other element does), a group, a measure map, a conversion map (and the maps nested in a
  `ChainMap`, a `CombinationMap` and a `PiecewiseMap`), a `LinearMap`, a
  `TableMap` and a graphical block each gain exactly their table's keys.
  The unit default of `number_type` is stated for ticks (`int`), seconds
  (`float`) and whole_notes (`fraction`).
- **Never added, never removed.** `id`, `graphical` and a root's `offset`
  are absent from the completion of a manifest without them; a present
  `graphical: {}` completes to its three keys and minimizes to `{}`; a
  child's `offset` stays in the minimal form.
- **Values that differ from the default stay.** `locked: true`,
  `number_type` `float` on quarters and a `repeat_end` with `repeat_count` 2
  survive `minimal`, the element keeping only its own non-default keys. A
  value is the default only in
  type and value: `repeat_count: 1.0` is a float, not the default `1`, and
  survives `minimal` as `1.0`; were it stripped, `complete` would restore it
  as `1` and change the document. So do a `LinearMap`'s `scalar` `[1, 1]`
  and `offset` `0.0`, which equal but are not the defaults 1 and 0.
- **Unknown keys pass through** both functions, at every depth, untouched.
- **`length` survives** both, `null` included.
- **The round trips.** For each of these documents (a `repeat_end` with
  `repeat_count: 1.0` among them) and for every fixture,
  `minimal(complete(x)) == minimal(x)`, `complete(minimal(x)) == complete(x)`
  and both results validate; both functions return new objects and leave
  their input unchanged. The equalities compare the texts `dumps` writes,
  since Python's `==` takes `1.0` for `1`.

## The rules and their codes

`validate` checks in this order and raises the first violation as a
`SchemaValidationError` carrying `code`, `path` and `message`: the version
marker; `finite_number`; the schema, in one walk that also collects the
unknown keys; `representation`; then the semantic rules in the order of the
table, root by root for the first six (a root's duplicates, then its
targets, then its conversion maps, then child by child, each followed by its
own children, the containment rules, then its segment lines), the rest over
the whole manifest. A timeline's maps are read in array order, each before
the maps it holds, a `CombinationMap`'s by output name in code-point order,
and a map's source unit before its arrays.
`identity_problems` returns every semantic problem in that order; `validate`
stops at the first. Python quotes IDs as `repr` does.

| Code | Rule | Reported at | Message |
| --- | --- | --- | --- |
| `not_a_manifest` | an object holding `timeskeleton` | the root | `not a TimeSkeleton manifest` |
| `finite_number` | every number finite | the leaf | `length of 'take' is not a finite number`, or `#/graphical/styles/s/opacity is not a finite number` with no ID above it |
| `schema` | the schema document | the path rule below | the schema library's |
| `representation` | own-axis values in the axis's number type | the value | `length 32 of 'score' is an int on a fraction axis: write [32, 1]` |
| `duplicate_id` | IDs unique within a root's tree, the maps a `ChainMap`, `PiecewiseMap` or `CombinationMap` holds included after the tree's other IDs | the later ID | `duplicate id 'm', first at #/…` |
| `dangling_target` | a jump origin's `target` names a jump target of its timeline; then, map by map, a measure view's `measure_map` names an entry of `measure_maps` | the target, the `measure_map` | `'there' names no jump_to of this timeline`, `'ghost' names no measure map of this manifest` |
| `conversion_map` | a non-null `source_unit` of a map attached to a timeline is the timeline's unit, and that of every map a `PiecewiseMap` or `CombinationMap` holds, and of a `ChainMap`'s first map, is its holder's non-null `source_unit`; a `TableMap`'s x and y values of equal length, its x values strictly increasing; a `PiecewiseMap`'s maps one fewer than its breaks, its breaks strictly increasing | the `source_unit`, the `y_values`, the value, the `maps`, the break | `MeasureRecordMap 'bars' has source unit 'quarters', its timeline 'score' has 'ticks'`, `LinearMap 'scale' has source unit 'ticks', its ChainMap 'chain' has 'quarters'`, `TableMap 'tempo' has 3 x values and 2 y values`, `x value [0, 1] of TableMap 'tempo' does not exceed the one before it`, `PiecewiseMap 'sections' has 1 map for 3 breaks; it needs 2 maps`, `break [4, 1] of PiecewiseMap 'sections' does not exceed the one before it` |
| `child_unit` | a child has its parent's unit | its `unit` | `child 'take' has unit 'seconds', its parent 'score' has 'quarters'` |
| `child_offset` | a child starts within the parent's known length | its `offset` | `offset 75.0 of 'take' is beyond the length 60.0 of its parent 'recording'` |
| `child_end` | else, it ends within it | its `length` | `child 'coda' ends at [12, 1], beyond the length [10, 1] of its parent 'score'` |
| `segment_line` | segments contiguous from 0 to the length, one flag | the segment's flag or offset, the line's `length` | `segment 'b' of segment line 'line' does not start where the one before it ends` |
| `reserved_id` | part words and band IDs are not IDs: the manifest's, then each root's tree, the maps a `ChainMap`, `PiecewiseMap` or `CombinationMap` holds after the tree's other IDs, then the groups', then the measure maps' | the ID | `id 'start' is reserved for the parts of an address`, `id 'regions_1' is reserved for the bands of a timeline` |
| `duplicate_id` | timeline IDs unique across roots, group IDs unique among themselves and the timelines', measure-map IDs unique among themselves and the timelines' and groups' | the later ID | as above |
| `manifest_id` | the manifest ID is not a timeline, group or measure-map ID | `id` | `duplicate id 'g2', first at #/groups/1/id` |
| `group_member` | a member names a timeline and neither contains nor lies inside another member of its group | the member | `'ghost' names no timeline of this manifest`, `member 'b' lies inside member 'a' of the same group` |
| `order_key` | a `graphical.order` key names a group or a timeline | the key | `'g9' names no group or timeline of this manifest` |
| `display_order` | a group's order permutes its members | the entry, then the order | `'x' is not a member of group 'g'`, `member 'b' of group 'g' is missing` |
| `band_order` | a timeline's order permutes its ID and its five bands | the entry, then the order | `'score/regions_2' is not 'score' or one of its bands`, `'score/flow_control_1' is missing from the band order of 'score'` |

The keys of `graphical.order` are read in code-point order, each order's
strangers before its missing entries, missing members in the order of
`members`, missing bands in the default band order (`T/children_1`,
`T/conversion_maps_1`, `T`, `T/markers_1`, `T/regions_1`, `T/flow_control_1`).
A key naming a group and a timeline never reaches `validate` (the duplicate
ID comes first); `identity_problems` reads it as the group's.

## What proves the rules

**The shared rejection cases are the oracle the two packages share.** Each of
the 105 cases of `fixtures/rejections/0.7.0/` breaks one rule and stores the
path and the code (`test_validate.py`); `validate` raises
`SchemaValidationError` with exactly both, and the codes of the cases are
exactly the seventeen of the table, so every code is reached by a case both
suites read. `version_unknown` raises `UnsupportedVersionError` and stores
`["timeskeleton"]` and the code `null`. Every case is read through the
package's one reader, `rejection_case`, which every consumer uses too; it
puts the infinity or NaN a `finite_number` case names at the stored path.
Three tests pin the reader: `nan_offset` and `infinite_length` hold the
value in place and are reported at their path with the exact message, a
case without one (`id_empty`) reads as written, and an unknown name is
refused with `ValueError`. Each case's text is the
standard writer's, and the set of names is stated literally, so a case cannot
disappear unnoticed. Seven cases pin their message too (`test_identity.py`):
`child_unit_differs`, `child_offset_beyond_parent`, `child_end_beyond_parent`,
`band_id_region`, `band_order_unknown_entry`, `band_order_missing_band` and
`order_unknown_group`.

**Each semantic rule has the smallest inline document with exactly one
problem** (`test_identity.py`, `test_segment_lines.py`), whose path and
message are stated literally, and `validate` raises that same problem. The
documents that bound each rule from the other side:

- **Scopes.** A jump target `m` in two roots, and a region `perf` beside a child
  timeline `perf` of another root, are no problem; a timeline ID repeated
  inside one root is reported once. Nested map IDs share their root's
  scope: two maps `l` held by one `ChainMap`, a map `l` held by a
  `PiecewiseMap` beside a region `l`, and a map `cmap_1` held by the
  `CombinationMap` `cmap_1` are each one `duplicate_id` at the nested
  `id`, the tree's own IDs counting first; the same nested ID in two roots
  is no problem.
- **Reserved IDs.** Every part word (`start`, `end`, `name`, `label`,
  `card`) and band ID (the five kinds numbered 1, `regions_12`,
  `flow_control_907`) is refused as the ID of a timeline, a map, a map held
  by a `ChainMap`, by a `PiecewiseMap` and by a `CombinationMap` (reported
  at the nested `id`), a region, a flow marker, a jump origin, a jump
  target, a group, a measure map and the manifest, in a manifest of one
  root; `starts`, `Start`, the bare kind words, `regions_0`, `regions_01`,
  `region_1`, `Regions_1` and `regions_1a` are accepted, since the pattern
  names a whole ID.
- **Containment.** A child's end is its offset plus its length, or, for a
  segment of unknown length, its successor's offset; values compare exactly
  and the end is spelled in the parent's number type, a fraction pair where
  that type has no exact spelling: `0.2` at `0.1` in `0.3` seconds ends at
  `[10808639105689191, 36028797018963968]`, `0.5` at `0.5` in `0.75` at
  `1.0`, `240` ticks at `480` in `480` at `720`, a quarters child declared
  `float`, `2.5` at `[7, 1]` in `[8, 1]`, at `[19, 2]`; `0.25` at `0.5` in
  `0.75` and `[2, 1]` at `[8, 1]` in `[10, 1]` end at the length and pass.
  An offset beyond the length is its child's one problem; a child of another
  unit gets only the unit problem, also between two continuous logical units
  (`number` under `quarters`); a parent of unknown length checks no
  containment. Unknown lengths pass wherever they stand: a root, a locked
  root, a child in a parent of known length and the reverse
  (`test_validate.py`). Negative offsets pass, on a root (`-1700000000.25` seconds,
  `[-3, 2]` quarters) and on a child (`-1.5`, `-0.0` seconds,
  `[-1, 1000000]`, `[-3, 2]` quarters, a grandchild at `[-1, 2]`), while a
  child at `[-3, 2]` of length `[40, 1]` in `[32, 1]` ends at `[77, 2]` and is
  reported. A grandchild is reported at its own path, naming its parent.
- **Segment lines.** Offset order decides, not array order (`b`, `a` at 3
  and 0 are contiguous); exact comparison (`0.1 + 0.2` does not meet `0.3`,
  `0.5 + 0.25` meets `0.75`); a segment of unknown length ends where its
  successor starts; the end check is skipped where the last segment's or the
  line's length is unknown, contiguity is not; a line without segments has
  one problem at a length of 8, none at 0 or null; a flag differing from the
  first segment's is reported at its `is_segment_line`, or at the segment
  where the key is absent; a descendant segment line is checked at its own
  path, a timeline whose `is_segment_line` is false never.
- **Conversion maps.** A `TableMap` with three x values and two y values is
  one problem at its `y_values`, with x values `[0, 1]`, `[2, 1]`, `2.0` one
  at the third (values compare exactly, `2.0` equals `[2, 1]`), and with
  `[0, 1]`, `0.5`, `[3, 4]` none; a `PiecewiseMap` with three breaks and one
  map is one problem at its `maps`, with breaks `[0, 1]`, `[8, 1]`, `[4, 1]`
  one at the third. A map nested in a `ChainMap`, a `PiecewiseMap` or a
  `CombinationMap` is checked at its own path (`…/maps/0`, `…/maps/beat`),
  the outputs `b` and `a` of a `CombinationMap` in the order `a`, `b`, and a
  map of a child at the child's path.
- **Source units.** A map converts from its timeline's axis, and a map
  another holds reads its holder's input. A `MeasureRecordMap` (source
  `quarters`) attached to a ticks timeline `score` is one problem at its
  `source_unit`, `MeasureRecordMap 'bars' has source unit 'quarters', its
  timeline 'score' has 'ticks'`, also on a child in ticks, at the child's
  path; the same view held second by a `ChainMap` from ticks whose first
  map is a `LinearMap` from ticks to quarters passes, as does a map whose
  `source_unit` is null and a map held by a holder whose `source_unit` is
  null. A `ChainMap` from quarters whose first map, the `LinearMap`
  `scale`, is from ticks is one problem at `…/maps/0/source_unit`,
  `LinearMap 'scale' has source unit 'ticks', its ChainMap 'chain' has
  'quarters'`; a measure view held by a `CombinationMap` from ticks is one
  at `…/maps/bar/source_unit`, and a `LinearMap` from seconds held by a
  `PiecewiseMap` from quarters one at `…/maps/0/source_unit`. Every
  emitted fixture passes (`test_fixtures.py`).
- **Flow control.** The schema ties each element type to its
  manifestations, its `target` and its `repeat_count`: the three `da_capo`
  manifestations and a `repeat_end` without a target validate
  (`test_validate.py`), a `dal_segno` without one is refused at the element; a jump origin whose target names a flow marker, or a jump target
  of its child, is one `dangling_target` at that `target`, naming the target
  (`'fine' names no jump_to of this timeline`).
- **Measure maps.** A measure view naming `ghost` while `measure_maps` holds
  only `measures` is one problem at its `measure_map`, also when nested in a
  `CombinationMap`; a measure map in a manifest of a timeline in seconds
  is no problem, as no unit constraint remains. A measure-map ID equal to
  a timeline ID, a group ID or an earlier measure-map ID is one
  `duplicate_id` at the later ID, and a manifest ID equal to a measure-map ID
  one `manifest_id`.
- **Groups and orders.** A child in one group with its root in another or in
  none, a group without members and members of unknown length pass. A
  timeline that is a member of two groups (`t` in `g1` beside `u` and in
  `g2` beside `v`) is no problem for `identity_problems` and validates. A
  member listed twice in one group (`a`, `a`) is the schema's rule, not an
  identity rule: `validate` refuses it at `members` (the shared case
  `group_members_repeated`). A band order passes at a root and at a descendant (for the child `b` the reverse
  of the default); each stranger (`score/regions_2`, `regions_1`,
  `b/regions_1`, `b`, `ghost`) is one problem at its entry, a missing band
  one at the order, an empty order its six missing addresses in the default
  band order; a child's order is held to its own bands.

**One document breaks every step once** (`test_every_step_in_order` and its
JavaScript twin): `identity_problems` returns exactly the stated problems, in
the stated order, with the stated codes, and `validate` raises the first.

**The finite rule runs before everything else.** Infinity as a length, NaN
in a fraction pair of a region and negative infinity in a style, each in a
manifest whose repeated root also breaks the identity rules, raise
`finite_number` at the leaf with the message of the table.

**Reading JSON.** `loads` reads text as the JavaScript package's `parseJson`
does, with the same cases as its tests: `0.5`, `2.0`,
`123456789012345678`, `-0` (the integer 0), `-0.0` (a negative float zero)
and `1E5` (a float) keep their kinds, an integer beyond 64 bits stays exact,
and `""`, `[1,]`, `{1: 2}`, `01`, `[1] 2`, `nul`, `1e400`, `NaN` and
`-Infinity` raise `ValueError`.

## One path rule for both validators

Among the diagnostic leaves of every violation, a validator reports the one
with the deepest instance path, ties going to the first reported. A
discriminated `oneOf` contributes only the candidate whose tag `const` equals
the instance's tag value (resolved through `$ref`), and is itself the
reported error when no candidate carries that value. The shared rejections
pin it where it matters: a negative fraction length reports its numerator
(`length/0`), a zero denominator the denominator (`length/1`), a negative
`actual_length` the row member, a negative `qstamp` pair its numerator, an
unknown conversion-map type the map, a missing `x_values` the `TableMap`, a
measure view's `source_unit` other than `quarters` the unit, a `target` on a
jump target or a `repeat_count` on a `to_coda` the member, a `dal_segno`
without a `target` the element.

## The canonical order

Every array whose order carries no meaning has one order: `timelines` by ID;
in every timeline `children` by offset then ID, `conversion_maps` by ID,
`regions` by start, end, ID, `flow_control` by coordinate then ID; `groups`
by ID and `members` by code point; `measure_maps` by ID. Values compare
exactly; strings by code point. What proves it
(`test_manifest.py`): an inline manifest with ties at every level, own-axis
values given as bare ints, floats and pairs mixed (`[5, 8]` before `[2, 1]`,
`0.625` equal to `[5, 8]` and tied by ID), IDs where code-point and UTF-16
order disagree (`ﬀ` before `😀`), yields the literally stated ID sequences
and validates; children `z` (1), `m` (1), `b` (`[5, 8]`), `a` (`[2, 3]`) come
out `b`, `a`, `m`, `z`; roots, groups, members and measure maps (`mﬀ`,
`mb`, `ma` come out `ma`, `mb`, `mﬀ`) sorted while
`graphical.order` keeps its order; the input is unchanged; a value without a
`timelines` array is copied as it is; a member that is not a string and two
regions without `start` are refused (`cannot put … in canonical order`).

## The standard writer

`dumps` writes the canonical order with keys sorted by code point, two-space
indentation, a final newline, characters unescaped except `"`, `\` and the
control characters, floats as `repr` spells them, integers without a point.
What proves it: every fixture, rejection case and warning case is reproduced
byte for byte by `dumps(json.loads(text))`; a literal key-sorting text; the
shared number corpus (identical in the JavaScript suite) with its one
expected text; the refusals of NaN, infinity and lone surrogates.

## The fixture set

The fixtures under `fixtures/0.7.0/` are emitted by timetoalign, never
written by hand (`test_fixtures.py`). For every fixture: `validate` accepts
it, `unknown_keys` lists nothing, `dumps` reproduces it, and the two round
trips of `complete` and `minimal` hold. `fixture_paths()` lists every
`*.json` under `fixtures/0.7.0/` except the drawings. The styled fixtures
`styled__score.json` and `styled__performance.json` carry the literally
stated `graphical` blocks (20 and 3 statements, and the score's band order
with its start and end wedges above its line and its map below), the
score's element addresses in the one address rule (`score/intro/label`,
`score/da-capo/label`); the thirteen drawn items of the score resolve, by the
cascade ranking of `docs/drawing.md`, to thirteen distinct colours, and no
statement hides anything but child `a`.

Two properties of the emitted set are pinned because a hand-written document
cannot prove that the emitter produces them:

- **A timeline in several groups.** `bundles/bundle_shared_member.json` and
  its twin hold the groups `g1` with the members `t`, `u` and `g2` with `t`,
  `v`; besides passing the checks above, `identity_problems` finds nothing
  in either form, so a member shared between groups, as the emitter writes
  it, passes both the schema and the identity rules.
- **Flow-control IDs by type.** Across the complete fixtures, every
  flow-control element whose ID has the generated form `<prefix>_<N>`
  carries its own `type` as the prefix: exactly `flow_marker_1` (three
  elements), `jump_from_1` to `jump_from_4` (six, two, one and one) and
  `jump_to_1` to `jump_to_3` (three, two and one). Every other flow-control
  ID is one a builder names (`fine`, `da-capo`, `da_capo_al_fine`,
  `dal_segno`, `repeat`, `segno`). A prefix taken from another type (a flow
  marker `break_1`, a jump target `marker_1`, a jump origin `jump_1`) fails
  the test.

## The graphical block

`docs/drawing.md` section 4's defaults block (three styles, 30 statements),
read from the file, validates as the `graphical` of the smallest file; the
statements naming `card`, `inside: ancestor` and `shadow` validate; so do
the band selectors of section 2.3, `{"element": "band"}`, `{"element":
"band", "class": <kind>}` for each of the five kinds `markers`,
`conversion_maps`, `children`, `regions` and `flow_control`, `{"ids":
["score/regions_1"]}` and `{"inside": "band"}`, each setting `display:
none`, while the class `band` is refused at the selector's `class`. In
the manifest whose groups `g1` and `g2` share the member `t`, a selector
`{"ids": ["g1/t/card"]}`, the card `t` has in `g1`, validates. The
schema shapes each entry of an order, an ID or an ID followed by `/` and a
band's ID: `score/foo`, `score/regions_0` and, after two valid entries,
`score/region_1` are refused at the entry, and a repeated entry
(`score`, `score/markers_1`, `score`) at the order, before any identity
rule is read; property
bounds accept `stroke-width` and `rx` 0, `opacity` 0 and 1, positive
`font-size` and `max-width`, both forms of `stroke-dasharray`, and reject a
negative width and radius, opacity outside [0, 1], zero font size and maximum
width, non-text content and malformed dash text at the property path. A
timeline name holding control characters validates.

## Completing missing styles

`complete_styles` returns a new graphical block and never changes its input.
Every distinct style name named by a statement but absent from `styles` is
added as an empty declaration, and the returned missing names are sorted by
code point. With missing names it emits exactly one `MissingStyleWarning`
whose exact text names all of them; with none no warning. Tests pin an absent
`styles` member, duplicate references, code-point ordering (`ﬀ` before `😀`),
preservation of existing declarations and input independence.

## The font

`font_path()` has the SHA-256
`7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954` with its
licence beside it; `font_metrics()` has exactly `advances`, `ascender`,
`descender`, `fallback`, `units_per_em` with 2048, 1901, 483 and 1229 and 5918
advances (`"9833"` 966, `"48"` 1303, `"32"` 651); `dumps` reproduces the
metrics file; the extraction script reproduces it from the bundled font and
refuses another file naming both digests; access works from any working
directory.

## Integer boundaries

Values whose integer length is `9007199254740993` (2^53 + 1) or
`9223372036854775807` (2^63 - 1) on a ticks axis validate and serialize back
to the same integer.

## Packaging

The test builds the sdist and the wheel with `uv build` twice (the wheel
from the checkout, and from the sdist as the release does) and requires
`timeskeleton/docs/drawing.md` and
`timeskeleton/schema/0.7.0/timeskeleton.schema.json` in the wheel, the same
under `src/timeskeleton/` in the sdist, each byte for byte the repository's
file, and the root `LICENSE` in the wheel's `.dist-info/licenses/` and at the
sdist root.

## Hermeticity

Tests obtain fixtures through package accessors, never relative paths. They
use no shared mutable input; the files a test writes lie in its own
temporary directory. Building the distributions needs `uv`, and the network
unless uv's cache already holds the build backend.
