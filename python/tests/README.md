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
   graphical?}`; `validate` accepts exactly the values the schema and the
   rules below accept, and raises the first violation with its path.
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
parses it. What proves its shape (`test_schema.py`):

- **One document, one root.** `$id` is
  `https://timetoalign.github.io/timeskeleton/0.7.0/timeskeleton.schema.json`,
  `$schema` the 2020-12 dialect, the root `$ref` is `#/$defs/TimeSkeleton`,
  and `schema/` holds exactly the directory `0.7.0` with exactly that file.
  Every `$ref` is local (`#/$defs/<name>`) and names a definition; no node
  carries `$anchor`. The definitions include the twelve public ones
  `TimeSkeleton`, `Timeline`, `Group`, `Graphical`, `ConversionMap`,
  `Coordinate`, `Number`, `Fraction`, `TimeUnit`, `NumberType`, `Id` and
  `MeasureMapRow`, and none of `Meta`, `TimelineClass`, `TimelineManifest`,
  `Bundle`, `GroupGraphical`, `BundleGraphical`, `CoordinateNonnegative`.
- **The manifest.** `TimeSkeleton` declares exactly `$schema` (a string),
  `timeskeleton` (`const` `"0.7.0"`), `id`, `name`, `meta`, `timelines`,
  `groups` and `graphical`, and requires exactly `timeskeleton` and
  `timelines`.
- **The timeline.** `Timeline` declares exactly `id`, `name`, `unit`,
  `number_type`, `length`, `offset`, `locked`, `is_segment_line`, `meta`,
  `children`, `conversion_maps`, `regions`, `flow_control`, `measure_map`
  and `metric_hierarchy` (no `class`), and requires exactly `id`, `unit` and
  `length`. `length` is `NumberNonnegative` or null; `offset`, region
  `start`/`end`, break and marker `coordinate` and jump
  `from_coordinate`/`to_coordinate` are `Number`; `children` items are
  `{"$ref": "#/$defs/Timeline", "required": ["offset"]}`. The description of
  `locked` is exactly "Whether the timeline's length is fixed."
- **Groups and the graphical block.** `Group` declares `id`, `name`, `meta`
  and `members` and requires `id` and `members`; `Graphical` declares
  `styles`, `statements` and `order`, and `order` is an object whose keys are
  ids and whose values are `MemberOrder`s. No definition names
  `support_policy`. Every conversion-map definition requires its own members
  but not `name`.
- **Open objects.** No node anywhere has `additionalProperties: false`;
  `meta` (on the manifest, a timeline, a region, a break, a jump, a group)
  and `metric_hierarchy` say `additionalProperties: true`. Every node with
  `type: object` and `properties` carries exactly
  `unevaluatedProperties: {"x-unknown-key": true}`, and no node inside a
  `oneOf`/`anyOf` branch or an `if`/`then`/`else` arm carries it. Every node
  that carries it declares in its own `properties` every key its branches
  and arms declare, which is what lets `unknown_keys` name the unknown keys
  from the node alone.
- **Defaults agree with the table.** For every kind of `DEFAULTS` the
  schema's corresponding definitions (`TimeSkeleton`, `Timeline`,
  `FlowControl`, `Region`, `Break`, `Jump`, `Marker`, every conversion map,
  `Group`, `Graphical`) declare `default` on exactly the keys of that kind's
  table, each equal to the table's value, and on no other key. `number_type`
  has no `default` (it depends on the unit). The JavaScript suite holds its
  table to the same schema, so the two tables are equal.
- **The vocabulary.** `TimeUnit` lists the sixteen units, `NumberType` the
  three number types, `ElementType` the fourteen element types (`block`,
  `timeline`, `child`, `map`, `region`, `break`, `jump`, `wedge`, `name`,
  `label`, `boundary`, `ancestor`, `group`, `card`), `Selector` declares
  `element`, `ids`, `domain`, `modality`, `class` (the six timeline classes
  followed by the 21 conversion-map types), `within` and `inside`;
  `Declaration` the twelve presentation properties with their bounds.

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

## Representation of own-axis values

An own-axis value (a timeline's `length` and `offset`, a region's `start` and
`end`, a break's and a marker's `coordinate`, a jump's `from_coordinate` and
`to_coordinate`) is a bare Number whose representation the axis's number type
selects: an int axis an integral JSON number, a float axis any JSON number
that a float equals exactly (an integer beyond 2^53 may have none), a
fraction axis a pair. The axis is the timeline's `number_type`, else its
unit's default (`int` for ticks, samples, frames, pixels; `fraction` for
quarters, whole_note; `float` otherwise). A child's offset lies on its
parent's axis, a root's on its own. A mismatch is reported after the schema,
at the value, as `<key> <value> of '<id>' is <found> on <axis> axis: write
<value rewritten>`, the id that of the object holding the key, the value
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
- `start`, `end`, `coordinate` (a break and a marker), `from_coordinate` and
  `to_coordinate` each reported at its own path with its holder's id.

Accepted: `8` and `8.0` on an int axis (an integral number is an int, as in
JSON Schema), `8`, `0.5`, `9007199254740992` (2^53) and `10**20` on a float
axis (each exactly a float), `[8, 1]` on a fraction axis,
`length: null` anywhere, a root's negative offset in its own number type.
The checks visit a timeline's offset, length, regions, breaks, jumps,
markers, then its children in array order; the first problem is raised.

## Open objects and unknown keys

`unknown_keys(value)` validates the value and returns every key the schema
does not declare on the object holding it, as `{"path": [...], "key": ...}`,
sorted by path (segment by segment, indices by number, keys by code point,
an object before its descendants) and then by key (`test_unknown_keys.py`):

- **The shared warning cases.** For every case of
  `fixtures/warnings/0.7.0/`, `validate` accepts the manifest and
  `unknown_keys` returns exactly its `unknown_keys` list; the JavaScript suite
  asserts the same lists. `several_depths` holds unknown keys on the
  manifest, a timeline, a child, a region, the flow control, a break, a
  jump, a marker, a conversion map and the map nested in it, a measure-map
  row, a group, the graphical block, a statement, a selector and a
  declaration (sixteen entries). The other cases are the rules the closed
  0.7.0 draft enforced and the open one reports: a former timeline `class`,
  a manifest `support_policy`, a group's `order`, `arrangement` in
  `graphical`, a selector's `kind`, a declaration's `colour` and
  `show-projections`, a measure-map row's `tempo` and `offset`, and a
  `MetricalPositionMap`'s `maps` and `names`.
- **What is not reported.** Keys inside `meta` and `metric_hierarchy` (free
  objects), keys inside the value of an unknown key, keys of `styles` and of
  `graphical.order` (maps keyed by data), and a known key whose value is
  its default: a manifest with none of these and a key in each lists
  nothing.
- **Sorting.** Keys `zz`, `aa`, `ﬀ`, `😀` on one object come out `aa`, `zz`,
  `ﬀ`, `😀`; an unknown key on `timelines[10]` follows one on
  `timelines[2]`; the manifest's own keys come first.
- **An invalid value** raises the error `validate` raises, before any key
  is listed.

## Defaults: the complete and the minimal form

`DEFAULTS` is the one table (`test_defaults.py`). What proves `complete` and
`minimal`:

- **Literal forms.** The smallest file completes to the literal complete
  manifest (`name` null, `meta` `{}`, `groups` `[]`, and on the timeline
  `name` null, `number_type` `fraction`, `locked` false, `is_segment_line`
  false, `meta` `{}`, `children`, `conversion_maps`, `regions` `[]`,
  `flow_control` with three empty arrays, `measure_map` and
  `metric_hierarchy` null), and that minimizes back to the smallest file.
  A region, a break, a jump, a marker, a group, a conversion map (and the map
  nested in a `ChainMap`, a `CombinationMap` and a `BeatInMeasureMap`'s
  `meter_map`) and a graphical block each gain exactly their table's keys.
  The unit default of `number_type` is stated for ticks (`int`), seconds
  (`float`) and whole_note (`fraction`).
- **Never added, never removed.** `id`, `graphical` and a root's `offset`
  are absent from the completion of a manifest without them; a present
  `graphical: {}` completes to its three keys and minimizes to `{}`; a
  child's `offset` stays in the minimal form.
- **Values that differ from the default stay.** `locked: true`,
  `number_type` `float` on quarters, `repeat_count` 2 and a flow control
  with one break survive `minimal` (the break keeps only its own non-default
  keys, the empty `jumps` and `markers` go). A value is the default only in
  type and value: `repeat_count: 1.0` is a float, not the default `1`, and
  survives `minimal` as `1.0`; were it stripped, `complete` would restore it
  as `1` and change the document.
- **Unknown keys pass through** both functions, at every depth, untouched.
- **`length` survives** both, `null` included.
- **The round trips.** For each of these documents (a break with
  `repeat_count: 1.0` among them) and for every fixture,
  `minimal(complete(x)) == minimal(x)`, `complete(minimal(x)) == complete(x)`
  and both results validate; both functions return new objects and leave
  their input unchanged. The equalities compare the texts `dumps` writes,
  since Python's `==` takes `1.0` for `1`.

## Identity

The identity rules hold after the schema and the representation check
(`test_identity.py`). Timeline ids (of roots and descendants), group ids and
the manifest id are unique together; every other id is unique within its
root's tree; the part words are no id anywhere. `identity_problems` returns,
in this order, one problem per finding (Python quotes ids as `repr`):

1. root by root: a repeated id within the root's tree (any two of timeline,
   map, region, break, jump, marker), at the later occurrence in identity
   order (a timeline, its maps, regions, breaks, jumps, markers, then its
   children in array order), `duplicate id 'm', first at <pointer>`; then
   a jump target naming no marker of its own timeline, `'there' names no
   marker of this timeline`; then, child by child in array order, each
   followed by its own children, a child whose unit is not its parent's, at
   its `unit`, `child 'take' has unit 'seconds', its parent 'score' has
   'quarters'`, and, where the parent's length is known, a child whose
   offset lies beyond it, at its `offset`, `offset 75.0 of 'take' is beyond
   the length 60.0 of its parent 'recording'`, or else a child whose end
   lies beyond it, at its `length`, `child 'coda' ends at [12, 1], beyond
   the length [10, 1] of its parent 'score'` (the three messages the same
   text in the JavaScript package); a negative offset is no problem, on a
   child as on a root; then the segment lines;
2. part words: the manifest's `id`, then every id of every root's tree, then
   each group id, `id 'start' is reserved for the parts of an address`;
3. a timeline id repeating one of an earlier root;
4. a group id equal to a timeline id or an earlier group's id;
5. the manifest id equal to a timeline id or a group id (first at the
   timeline);
6. members: naming no timeline (`'tempo' names no timeline of this
   manifest`), already in an earlier group (`duplicate member`), nested with
   an earlier member of the same group (`lies inside` / `contains`);
7. `graphical.order` keys in code-point order: naming no group (`'g9' names
   no group of this manifest`), entries that are no member, members missing.

What proves it: each rule has an inline document with exactly that one
problem, path and message stated; a marker `m` in two roots is no problem
(scopes are per root), while a region `perf` in root `score` beside a child
timeline `perf` of root `take` is no problem either; a timeline id repeated
inside one root is reported once (step 1); every part word is refused as the
id of a timeline, a map, a region, a break, a jump, a marker, a group and the
manifest, in a one-root manifest, while `starts` and `Start` are accepted;
a child sharing its parent's unit at offset 0 is no problem, and a negative
offset is none either, on a root (`-1700000000.25` seconds, `[-3, 2]`
quarters), where it places the origin, or on a child, which then starts
before its parent's origin: children at `-1.5` seconds, `[-1, 1000000]`,
`[0, 1]` and `[-3, 2]` quarters (the last of length `[4, 1]` in a parent of
`[32, 1]`), at `-0.0` seconds and a grandchild at `[-1, 2]` quarters all
validate, the same documents in both packages; yet a child at `[-3, 2]` of
length `[40, 1]` in that parent ends at `[77, 2]`, beyond its length, and is
reported at its `length`, so the end rule still applies to a child that
starts before the origin; a child in
`number` under a parent in `quarters`, both continuous logical, is still
reported, since the rule compares units, not classes; the unit rule reaches
a grandchild at its own path; one manifest carrying a finding of every step
yields exactly the problems in the stated order, with paths and messages; a child of one group with its root
in another, or ungrouped, is no problem; a group without members stays valid;
every shared rejection pins its path, `child_unit_differs`,
`child_offset_beyond_parent` and `child_end_beyond_parent` with their
messages too.

**A child lies within its parent's known length.** A child's end is its
offset plus its length where both are known; a segment of unknown length ends
where its successor in offset order starts (as for contiguity); any other
child of unknown length has no known end, and a child of another unit has
none either (its length lies on another axis, and its unit is reported).
Values compare exactly; the end is spelled as the parent's number type writes
it, as a fraction pair where that type cannot write it exactly. An offset
beyond the length is the one problem of its child, whatever its length. What
proves it, one inline document each: a child of unknown length at `75.0` in a
`60.0` s parent is reported at its offset, at `60.0` it is not; a child
`[2, 1]` at `[9, 1]` in `[8, 1]` gives the offset problem alone; a child
`[4, 1]` at `[8, 1]` in `[10, 1]` ends at `[12, 1]`, one of `[2, 1]` there
ends exactly at the length and is no problem; on a seconds axis `0.5` at
`0.5` in `0.75` ends at `1.0`, `0.25` at `0.5` meets `0.75`, and `0.2` at
`0.1` in `0.3` ends at `[10808639105689191, 36028797018963968]` (the exact
sum, which no float equals); `240` ticks at `480` in `480` ends at `720`; a
quarters child declared `float`, `2.5` at `[7, 1]` in `[8, 1]`, ends at
`[19, 2]`; a child in seconds of length `100.0` under `[8, 1]` quarters
yields only its unit problem; a grandchild `[2, 1]` at `[3, 1]` in a child of
length `[4, 1]` is reported at its own path, naming that child; any child
under a parent of unknown length is no problem; on a segment line of length
`[8, 1]`, segments `a` (0, null) and `b` (`[10, 1]`, `[1, 1]`) yield `a`'s
end `[10, 1]`, `b`'s offset and the segment line's length, in that order.

## Segment lines

A segment line (`is_segment_line` true) holds only its segments, contiguous
from 0 in offset order (ties by id) to its length, all with one
`is_segment_line` value (absent is false). A segment is a child, so it
shares the segment line's unit (Identity, step 1); a segment in another unit
is reported by that rule alone, at its `unit`. The problems, after the
duplicates, targets and children of their root (`test_segment_lines.py`),
per segment: a flag
different from the first segment's, at its `is_segment_line` (at the segment
where the key is absent), `… differs from segment 'a' in is_segment_line`; an
offset other than the previous end, at its `offset`, `… does not start at 0`
or `… does not start where the one before it ends`; then one problem at the
segment line's `length` when the last end misses it, `the segments of segment
line 'line' do not end at its length`. Values compare exactly: on a seconds
axis `0.1 + 0.2` does not meet `0.3`, `0.5 + 0.25` meets `0.75`.

**Unknown length.** A segment of unknown length ends where its successor
starts: segments `a` (0, null) and `b` (5, 3) on a line of length 8 have no
problem, nor with `b` at 7 and length 1. The end check is skipped where the
last segment's length or the line's is unknown: a last segment of null
length, and a line of null length with segments `a` (0, 3), `b` (3, 5), have
no problem; but a line of null length still checks contiguity (`b` at 4 after
`a` ending at 3 is reported). A segment line without segments and length 0
has no problem, with length 8 one problem at its length, with length null
none. Offset order, not array order, decides: segments given `b`, `a` with
offsets 3, 0 are contiguous. A segment line among the descendants is checked
at its own path, a timeline with `is_segment_line` false never.

## Groups and unknown length

A group may hold members of unknown length, roots and children alike; a
locked timeline may have an unknown length; a child of unknown length may sit
in a parent of known length and the reverse; all validate (`test_identity.py`
for groups, `test_validate.py` for lengths). The containment rules (Identity,
step 1) need the parent's length and are skipped where it is unknown.

## Shared rejection cases

`fixtures/rejections/0.7.0/` holds 85 cases `{manifest, path, reason}`, one
rule each, written by `dumps`; `version_unknown` adds `"error":
"UnsupportedVersionError"` and its `path` is `["timeskeleton"]`. For every
other case `validate` raises `SchemaValidationError` at exactly the stored
path; for that one it raises `UnsupportedVersionError` (`test_validate.py`).
The set is stated literally by name, so a case cannot disappear unnoticed.

## One path rule for both validators

Among the diagnostic leaves of every violation, a validator reports the one
with the deepest instance path, ties going to the first reported. A
discriminated `oneOf` contributes only the candidate whose tag `const` equals
the instance's tag value (resolved through `$ref`), and is itself the
reported error when no candidate carries that value. The shared rejections
pin it where it matters: a negative fraction length reports its numerator
(`length/0`), a zero denominator the denominator (`length/1`), a negative
`actual_length` the row member, a negative `qstamp` pair its numerator, an
unknown conversion-map type the map, a missing `scalar` the `LinearMap`.

## The canonical order

Every array whose order carries no meaning has one order: `timelines` by id;
in every timeline `children` by offset then id, `conversion_maps` by id,
`regions` by start, end, id, `breaks` and `markers` by coordinate then id,
`jumps` by from and to coordinate then id; `groups` by id and `members` by
code point. Values compare exactly; strings by code point. What proves it
(`test_manifest.py`): an inline manifest with ties at every level, own-axis
values given as bare ints, floats and pairs mixed (`[5, 8]` before `[2, 1]`,
`0.625` equal to `[5, 8]` and tied by id), ids where code-point and UTF-16
order disagree (`ﬀ` before `😀`), yields the literally stated id sequences
and validates; children `z` (1), `m` (1), `b` (`[5, 8]`), `a` (`[2, 3]`) come
out `b`, `a`, `m`, `z`; roots, groups and members sorted while
`graphical.order` keeps its order; the input is unchanged; a value without a
`timelines` array is copied as it is; a member that is no string and two
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
stated `graphical` blocks (21 and 5 statements), the score's element
addresses in the one address rule (`score/intro/label`,
`score/da-capo/label`); the thirteen drawn items of the score resolve, by the
cascade ranking of `docs/drawing.md`, to thirteen distinct colours, and no
statement hides anything but child `a`.

## The graphical block

`docs/drawing.md` section 4's defaults block (three styles, 28 statements),
read from the file, validates as the `graphical` of the smallest file; the
statements naming `card`, `inside: ancestor` and `shadow` validate; property
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
