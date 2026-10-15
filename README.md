# timeskeleton

TimeSkeleton is the JSON Schema for the structural serialization of musical
timelines, alone or in timeline groups and alignment bundles, with fixtures
emitted by [timetoalign](https://github.com/timetoalign/timetoalign) and
validation packages for Python and TypeScript. It carries timeline
structure, not event data.

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

Every TimeSkeleton manifest has one shape, whatever it holds: one
timeline, several, a group of timelines, or an alignment bundle's
timelines and groups. The smallest manifest is

```json
{"timeskeleton": "0.7.0", "timelines": [{"id": "piece", "unit": "quarters", "length": [32, 1]}]}
```

| Member | Required | Holds |
| --- | --- | --- |
| `timeskeleton` | yes | the version marker, `"0.7.0"` |
| `timelines` | yes | the root timelines, an array that may be empty |
| `id` | no | the manifest's id |
| `name` | no | the manifest's displayed name |
| `meta` | no | an object of anything an application wants to record |
| `groups` | no | timeline groups whose members name timelines of the manifest |
| `graphical` | no | the styling and display order of the manifest's drawing |
| `$schema` | no | a string naming the schema, for editors; never read |

A single timeline is a manifest of one root, and a group is a manifest with
one group. A manifest with an `id` or a `name` is named; one with neither is
anonymous. `id` and `name` are independent: either may stand without the
other.

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
`is_segment_line`, `meta`, `children`, `conversion_maps`, `regions`,
`flow_control`, `measure_map` and `metric_hierarchy`.

- `unit` decides the timeline's domain (logical, physical or graphical)
  and modality (continuous or discrete), since each unit belongs to exactly
  one of the six combinations. A timeline writes no class.
- `number_type` is `int`, `float` or `fraction`; absent, it is the unit's
  default (section [Defaults](#defaults)).
- `length` is the timeline's length on its own axis, or `null` when it is
  not known (section [Unknown length](#unknown-length)).
- `children` is an array of timelines, each carrying its `offset` on the
  parent's axis, written in offset order with ties by id; a child shares
  its parent's `unit`, here `seconds`:

  ```json
  "children": [{"id": "perf", "offset": 4.0, "unit": "seconds", "length": 1503.2}]
  ```

  A child requires `offset`, which is never negative. Where its parent's
  length is known, a child starts at or before the parent's end and ends at
  or before it, locked or not: no child reaches past a known length. A root
  may carry an `offset` too, negative included:
  it places the root's origin on its unit's absolute axis, such as a
  recording whose origin is a moment in UNIX time. A root without `offset`
  has none.
- `locked` states whether the timeline's length is fixed; it defaults to
  `false` on every timeline. A child writes it like every other timeline,
  and may be unlocked as a root may. A locked timeline's length may still
  be unknown. An unlocked child's length may change only within its
  parent's known length; a parent's length never follows a child's.
- `is_segment_line` marks a **segment line**, a timeline containing only
  contiguous segments: its children are its segments, contiguous from 0 in
  offset order to its length, all sharing its unit as every child does,
  and all with one `is_segment_line` value. Segments that are segment lines
  themselves make a nested segment line.
- `conversion_maps`, `regions` and `flow_control` (`breaks`, `jumps` and
  `markers`) hold the timeline's conversion maps, regions and flow
  control; `metric_hierarchy` is an object without further rules.

A measure map is the
[Measure Map standard](https://github.com/measure-map/specification)'s
compressed row array: an entry equal to the preceding entry's default
successor is omitted. A row is the standard's Measure plus two extensions:
the integer `volta`, and `offset_within_measure`, where the row begins inside
its nominal measure in quarter notes. Lengths are strictly positive and
`qstamp` is non-negative; exact Fraction pairs are permitted wherever the
standard uses JSON numbers. Only a timeline whose unit is `quarters` may
carry a measure map.

### Values on a timeline's own axis

A coordinate on its timeline's own axis is written as its value alone:
`length`, a child's `offset` (on the parent's axis), a root's `offset`,
region `start` and `end`, break and marker `coordinate`, and jump
`from_coordinate` and `to_coordinate`. The value is represented as the
axis's number type selects, that is `number_type`, or the unit's default
when it is absent: a JSON integer for `int`, a JSON number for `float`, and
a `[numerator, denominator]` pair of JSON integers with a strictly positive
denominator for `fraction`, mirroring BOPP. An `int` axis also accepts an
integral JSON number, read as that integer, and a `float` axis an integer
that a float equals exactly; a `fraction` axis accepts only a pair. Writers
write each axis's own form. A child's `offset` takes the parent's number
type. The schema types these values as `Number`; both
validators then check the representation and report a mismatch such as
`length 32 of 'score' is an int on a fraction axis: write [32, 1]`, or, for
an integer no float holds exactly,
`length 9007199254740993 of 'take' is an int on a float axis: write a float`.

A coordinate on another axis, as in a conversion map's tables, keeps the
coordinate object `{unit, number_type, value}`, its value represented as its
own `number_type` selects.

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
| manifest | `id`: absent (anonymous); `name`: `null`; `meta`: `{}`; `groups`: `[]`; `graphical`: absent |
| timeline | `name`: `null`; `number_type`: the unit's default (`int` for `ticks`, `samples`, `frames` and `pixels`; `fraction` for `quarters` and `whole_note`; `float` otherwise); `offset`: absent on a root, required on a child; `locked`: `false`; `is_segment_line`: `false`; `meta`: `{}`; `children`, `conversion_maps`, `regions`: `[]`; `flow_control`: `{"breaks": [], "jumps": [], "markers": []}`; `measure_map`, `metric_hierarchy`: `null` |
| flow control | `breaks`, `jumps`, `markers`: `[]` |
| region | `name`: `null`; `meta`: `{}` |
| break | `control_type`: `"section_break"`; `condition`: `"always"`; `repeat_count`: 1; `label`, `name`: `null`; `meta`: `{}` |
| jump | `control_type`: `"repeat_end"`; `condition`: `"first_n"`; `repeat_count`: 1; `target`, `label`: `null`; `meta`: `{}` |
| marker | `name`: `null` |
| conversion map | `name`: `null` |
| group | `name`: `null`; `meta`: `{}` |
| graphical | `styles`: `{}`; `statements`: `[]`; `order`: `{}` |

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
its content reaches, and ends its line in a double chevron.

### Groups and the `graphical` block

A group is `{id, name?, meta?, members}`. `members` are the distinct ids of
the member timelines, each naming a timeline of the manifest: a root or any
descendant. Members share the same graphical start and end: every
member's 0 coincides with every other member's 0 and every member's end
with every other member's end, and positions in between convert linearly.
When only part of a timeline takes part, the member is a child of that
timeline, placed at its exact offset; a member is never placed partially.
A timeline is a member of at most one group, and no member of a group lies
inside another member of the same group, since a timeline and its
descendant in one group would give two answers for one position; a child
may belong to one group while its root belongs to another or to none. The
roots that no group names, and that contain no member, are ungrouped. A
manifest holding a group always holds its members' roots, so a member that
is a child keeps its parent.

`graphical` is `{styles?, statements?, order?}`, at the manifest's top
level only, never on a timeline. `styles` and `statements` style the
drawing ([Drawing a manifest](#drawing-a-manifest)). `order` maps a group's
id to the display order of its members, a permutation of them; writers never
reorder it, and a group without an entry is displayed in the order of
`members`. A manifest carries no MatchClaims.

### Unknown keys

Every object of the schema is open: a key the schema does not define is
valid. The free objects `meta` and `metric_hierarchy` say so explicitly;
every other object marks an unknown key with the keyword `x-unknown-key`,
which a standard JSON Schema validator ignores and both packages' validators
record. Unknown keys are warnings, never errors, since a misspelt optional
key would otherwise silently become its default. Python's
`unknown_keys(value)` and npm's `unknownKeys(value)` return the same list of
`{path, key}` entries, the path locating the object that holds the key,
sorted by path and then by key; `validate` raises only on errors. timetoalign
and TimeLineEditor keep the unknown keys of a manifest they read and write
them back. A key that a host schema declares beside its `$ref` to a
TimeSkeleton definition is reported as unknown by these validators; the
host's own validator is unaffected.

### Identity

Every timeline, group, conversion map, region, flow-control break, jump and
marker carries an `id`, which identifies it, and so may the manifest. A
`name`, where an element has one, is what is displayed, and it may repeat.
An id is a non-empty string without `/` and without control characters, and
it may contain spaces. Flow-control `markers` is a list of `{id, name,
coordinate}` objects, and a jump's `target` is the id of a marker of the same
timeline, or `null`.

Timeline ids, of roots and descendants alike, group ids and the manifest's
id are unique together across the manifest. Each root's tree is moreover one
scope: within it, an id is unique across all the element kinds above, so a
conversion map, region, break, jump or marker id is unique within the tree
of its root and may repeat in another root's tree.

One address rule holds in every manifest. A timeline, a group or the
manifest is addressed by its bare id; a conversion map, region, break, jump
or marker by the id of the root whose tree holds it, `/`, and its own id
(`score/region_1`); the parts of an element follow its address: `…/start`,
`…/end`, `…/name`, `…/label`, and a timeline's card `…/card`. These five
words are therefore reserved: no id of a manifest may be one of them. The
manifest's title, the top label of its drawing, is addressed `name`,
whether or not the manifest has an `id`, and a group's title `G/name`.

The JSON Schema cannot express these rules, nor that a member names a
timeline of the manifest, nor that no member of a group lies inside
another, nor that a child lies within its parent's known length, nor that a
segment line's segments are contiguous and alike, nor the representation of
own-axis values, so both validators check them after
the schema. Each finding is one problem, located by a path into the
manifest:

| Rule | Location | Message |
| --- | --- | --- |
| An id repeats within one root's tree | the later occurrence | `duplicate id '<id>', first at <pointer>` |
| A jump's `target` names no marker of its timeline | the `target` | `'<target>' names no marker of this timeline` |
| A child's `unit` is not its parent's | the child's `unit` | `child '<id>' has unit '<unit>', its parent '<id>' has '<unit>'` |
| A child's `offset` is negative | the child's `offset` | `offset <offset> of '<id>' is negative` |
| A child's `offset` lies beyond its parent's known length | the child's `offset` | `offset <offset> of '<id>' is beyond the length <length> of its parent '<id>'` |
| A child ends beyond its parent's known length, its own end known | the child's `length` | `child '<id>' ends at <end>, beyond the length <length> of its parent '<id>'` |
| A segment's `is_segment_line` differs from the first segment's | the segment's `is_segment_line`, or the segment when it leaves the key out | `segment '<id>' of segment line '<id>' differs from segment '<first id>' in is_segment_line` |
| A segment does not start where the one before it ends, or the first at 0 | the segment's `offset` | `segment '<id>' of segment line '<id>' does not start where the one before it ends` (`… does not start at 0`) |
| The last segment does not end at the segment line's length, both known | the segment line's `length` | `the segments of segment line '<id>' do not end at its length` |
| An id is `start`, `end`, `name`, `label` or `card` | the `id` | `id '<id>' is reserved for the parts of an address` |
| A timeline id repeats one of an earlier root's tree | the later occurrence | `duplicate id '<id>', first at <pointer>` |
| A group id equals a timeline id or an earlier group's id | the group's `id` | `duplicate id '<id>', first at <pointer>` |
| The manifest's id equals a timeline id or a group id | `id` | `duplicate id '<id>', first at <pointer>`, the pointer naming the timeline, else the first such group |
| A member names no timeline of the manifest | the member | `'<id>' names no timeline of this manifest` |
| A member is already a member of an earlier group | the later member | `duplicate member '<id>', first at <pointer>` |
| A member lies inside an earlier member of its group, or contains one | the later member | `member '<id>' lies inside member '<earlier id>' of the same group` (`… contains member …`) |
| A key of `graphical.order` names no group | the key | `'<key>' names no group of this manifest` |
| An entry of a display order is not a member of its group | the entry | `'<id>' is not a member of group '<group id>'` |
| A member of a group is missing from its display order | the order | `member '<id>' of group '<group id>' is missing` |

Within one root's tree, ids are visited in identity order (a timeline,
then its conversion maps, regions, breaks, jumps and markers, then its
children in array order); duplicates come first, then dangling targets,
then children off their parent's axis (child by child, each followed by its
own children: its unit, its negative offset, then an offset beyond its
parent's known length or else an end beyond it), then segment lines, whose
segments are visited in canonical order and compared by exact value. Across the manifest, the problems come in this
order: each root's own problems, roots in array order; then reserved words
(the manifest's id, then root by root in identity order, then the group
ids); repeated timeline ids, group ids, the manifest's id, members (member by member: dangling, repeated, nested), and
the display orders in code-point order of their keys. `<pointer>` is a JSON
pointer in URI fragment form, such as `#/timelines/0/id`, as Python's
`json_pointer(path)` and npm's `jsonPointer(path)` render a path. The
messages above quote ids as Python does; the TypeScript package quotes them
as JSON (`duplicate id "piece", first at #/timelines/0/id`), except the two
four messages about a child's unit, offset and end, which read the same in
both packages, every value spelled as the standard writer spells it (`-1`,
`[-1, 2]`, `-0.5`). A child's end, its offset plus its length, or for a
segment of unknown length its successor's offset, is compared exactly and
spelled as its parent's number type writes it, or as a `[numerator,
denominator]` pair where that type cannot write it exactly. A repeated
entry within one display order or within one group's `members` is refused by
the schema.

### The schema document

Version 0.7.0 is one document, `schema/0.7.0/timeskeleton.schema.json`,
with the identifier
`https://timetoalign.github.io/timeskeleton/0.7.0/timeskeleton.schema.json`,
so the document lies below `schema/` at the path of its identifier. Its root
is `{"$ref": "#/$defs/TimeSkeleton"}`. These definitions are public and
may be embedded by a host schema; within 0.7.x they change only by
addition:

`TimeSkeleton`, `Timeline`, `Group`, `Graphical`, `ConversionMap`,
`Coordinate`, `Number`, `Fraction`, `TimeUnit`, `NumberType`, `Id` and
`MeasureMapRow`.

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
`id` when it has no name; an anonymous manifest has none. Each group is a
frame, and each member and each ungrouped root lies in its own card; a
member that is a child timeline is drawn with the faded lines of its
ancestors. The element types are `block`,
`card`, `timeline`, `child`, `boundary` (a segment's start on its segment
line), `ancestor`, `group` (a frame), `map`, `region`, `break`, `jump`,
`wedge`, `name` and `label`. Besides `element`, a selector may name `ids`,
`domain`, `modality`, `class`, `within` (a timeline and its descendants)
and `inside` (an element type that holds the element at any depth); the
selector's `class` names the class a timeline's unit decides, such as
`ContinuousPhysicalTimeline` for `seconds`. The property `shadow` colours
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

- `timelines` by id, `groups` by id, and every group's `members` by code
  point;
- in every timeline, `children` by offset, then id;
- `conversion_maps` by id;
- `regions` by start, then end, then id;
- flow-control `breaks` and `markers` by coordinate, then id;
- flow-control `jumps` by from coordinate, then to coordinate, then id.

Ids are unique within their scope, so no two entries tie. Coordinates
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

Python validation raises `SchemaValidationError` with a tuple path to the
offending value. Read a manifest with `json.loads`, which keeps integers and
floats distinct and every integer exact, and write it with `dumps`:

```python
import json

from timeskeleton import SchemaValidationError, dumps, fixture_paths, validate

value = json.loads(fixture_paths()[0].read_text(encoding="utf-8"))
try:
    validate(value)
except SchemaValidationError as error:
    print(error.path)
else:
    text = dumps(value)
```

- `validate(value)` reads the version marker first, then checks the value
  against the schema, the representation of its own-axis values and the
  identity rules, and raises `SchemaValidationError` at the first problem.
  A value without `timeskeleton` is refused at the root; a value declaring
  another version raises `UnsupportedVersionError` naming 0.7.0. Unknown
  keys never fail it.
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
  cases.
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
      console.error(error.path);
    }
    throw error;
  }
}
```

- `parse(text)` reads and validates a manifest without losing a number or
  key order, and returns it as a `TimeSkeleton`. `parseJson(text)` reads
  any JSON text without validating it.
- `validate(value)` narrows an unknown value to `TimeSkeleton`, checking it
  as Python's `validate` does.
- `unknownKeys(value)` returns the same list as Python's `unknown_keys`.
- `complete(value)` and `minimal(value)` return the complete and the minimal
  form, as Python's functions do, keeping every number and key order
  `parseJson` read.
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
  and `Graphical`.

A number read by `parseJson` is a `JsonNumber`:

| JSON text | `JsonNumber` |
| --- | --- |
| an integer within ±(2^53 − 1), such as `480` | a `number` |
| an integer beyond that range, such as `9007199254740993` | a `bigint` |
| a float with a fractional part, such as `0.5` | a `number` |
| an integral float, such as `2.0`, `1e+16`, or `-0.0` | a `JsonFloat` |

`Lossless<T>` replaces every `number` in `T` with `JsonNumber`. A float whose
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
twin. The manifests are emitted only by `scripts/emit_fixtures.py` using
timetoalign. Do not edit them by hand.

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
