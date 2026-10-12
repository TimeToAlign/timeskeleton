# timeskeleton

TimeSkeleton is the JSON Schema for the structural serialization of musical
timelines, timeline groups and alignment bundles, with fixtures emitted by
[timetoalign](https://github.com/timetoalign/timetoalign) and validation
packages for Python and TypeScript. It carries timeline structure, not event
data.

**Status: alpha.** The repository contains schema versions 0.5.0, 0.6.0 and
0.7.0; 0.7.0 is the current version. It provides validators for three file
kinds (timeline, group and bundle files) that locate a violation under one
shared path rule, a canonical order, standard writers that produce the same
bytes in Python and TypeScript, a lossless JSON reader for TypeScript,
generated TypeScript types, migrations from 0.5.0 to 0.6.0 and from 0.6.0 to
0.7.0, and shared fixtures. It also specifies how a timeline manifest is
drawn, and both packages ship that specification.

## The files

A TimeSkeleton file is a JSON object holding `meta` and exactly one of
`timeline`, `group` or `bundle`, the member that names its kind.
`meta.schema_version` is `"0.7.0"`, and `meta.generator` is optional. Every
file is self-contained. Versions 0.5.0 and 0.6.0 know the timeline file only.

- **Timeline file** `{meta, timeline, graphical?}`. `timeline` is one
  timeline manifest matching timetoalign's `Timeline.to_dict(events=False)`
  output: its axis (`class`, `unit`, `number_type`, and `length`), child
  timelines at exact offsets, conversion maps, regions, flow control, measure
  map, and metric hierarchy. The optional `graphical` block styles its
  drawing ([Drawing a timeline manifest](#drawing-a-timeline-manifest)).
  From 0.7.0 on every timeline, at every depth, also carries the boolean
  `is_segment_line`. A segment line is a timeline containing only contiguous
  segments. It is written with one of the six classes, its segments' class,
  plus `is_segment_line: true`, and its children are its segments: contiguous
  from 0 in offset order to its length, all of one class, all with one
  `is_segment_line` value. Segments that are segment lines themselves make a
  nested segment line. Every other timeline has `is_segment_line: false`.
- **Group file** `{meta, timelines, group, graphical?}`, one timeline group
  with the timelines it names. A group is an array of member timelines that
  share the same graphical start and end: every member's 0 coincides with
  every other member's 0 and every member's length with every other member's
  length, and positions in between convert linearly. When only part of a
  timeline takes part, the member is a child of that timeline, placed at its
  exact offset; a member is never placed partially. `group` is `{id, name,
  meta, members}`, and `members` are the ids of the member timelines, each
  naming a timeline of `timelines`: a root or any descendant. `timelines`
  holds root timeline manifests, and every root contains a member.
- **Bundle file** `{meta, timelines, bundle, graphical?}`, one alignment
  bundle. `timelines` holds every root timeline of the bundle, so each
  timeline occurs once in the file. `bundle` is `{id, name, meta,
  support_policy, groups}`: `support_policy` is `"omit"`, `"clamp"` or
  `"extrapolate"`, and `groups` holds groups of the same form as a group
  file's, whose members name timelines of the one `timelines` array. A
  timeline is a member of at most one group; a child may belong to one group
  while its root belongs to another or to none. The roots that no group names
  are the bundle's ungrouped timelines. A 0.7.0 bundle file carries no
  MatchClaims.

A group or bundle file's `graphical` block holds one member, `order`: the
display order of a group's members, a permutation of them. In a group file
it is an array; in a bundle file it is an object mapping a group id to such
an array. Writers never reorder it. Without it, a group's members are
displayed in the order of `members`.

A timeline manifest describes one timeline and all its descendants. No file
says where or how often an application places its object. Event tables
travel separately, typically as Arrow or Parquet data, and are referenced
rather than embedded.

Every coordinate-valued member is an object with `unit`, `number_type`, and
`value`. Its number type selects the representation: an integer is a JSON
integer, a float is a JSON number, and a fraction is a `[numerator,
denominator]` pair of JSON integers with a strictly positive denominator,
mirroring BOPP.

A measure map is the
[Measure Map standard](https://github.com/measure-map/specification)'s
compressed row array: an entry equal to the preceding entry's default
successor is omitted. A row is the standard's Measure plus two extensions:
the integer `volta`, and `offset_within_measure`, where the row begins inside
its nominal measure in quarter notes. Lengths are strictly positive and
`qstamp` is non-negative; exact Fraction pairs are permitted wherever the
standard uses JSON numbers. Only a timeline whose unit is `quarters` may
carry a measure map.

### Identity

Every timeline, conversion map, region, flow-control break, jump and marker
carries an `id`, which identifies it; so does every group and every bundle. A
`name`, where an element has one, is what is displayed, and it may repeat.
An id is a non-empty string without `/` and without control characters, and
it may contain spaces. Flow-control `markers` is a list of `{id, name,
coordinate}` objects, and a jump's `target` is the id of a marker of the same
timeline, or `null`.

Ids are unique within nested scopes. Each timeline manifest is one scope: an
id is unique within it across all the element kinds above. In a group or
bundle file, each root of `timelines` is such a scope; timeline ids, of roots
and descendants alike, are moreover unique across the file, and group ids are
unique among the groups and differ from every timeline id.

The JSON Schema cannot express these rules, nor that a member names a
timeline of the file, nor that no member of a group lies inside another, nor
that a segment line's segments are contiguous and alike, so both validators
check them after the schema. Members share their start and end, but a child
sits at its offset inside its parent, so a timeline and its descendant in one
group would give two answers for one position; in different groups of a
bundle they are allowed. Each finding is one
problem, located by a path into the file:

| Rule | Location | Message |
| --- | --- | --- |
| An id repeats within one timeline manifest | the later occurrence | `duplicate id '<id>', first at <pointer>` |
| A jump's `target` names no marker of its timeline | the `target` | `'<target>' names no marker of this timeline` |
| A segment's `class` is not its segment line's | the segment's `timeline/class` | `segment '<key>' of segment line '<id>' is no <class>` |
| A segment's `is_segment_line` differs from the first segment's | the segment's `timeline/is_segment_line` | `segment '<key>' of segment line '<id>' differs from segment '<first key>' in is_segment_line` |
| A segment does not start where the one before it ends, or the first at 0 | the segment's `offset` | `segment '<key>' of segment line '<id>' does not start where the one before it ends` (`… does not start at 0`) |
| The last segment does not end at the segment line's length | the segment line's `length` | `the segments of segment line '<id>' do not end at its length` |
| A timeline id repeats one of an earlier root | the later occurrence | `duplicate id '<id>', first at <pointer>` |
| A group id equals a timeline id, or, in a bundle, an earlier group's id | the group's `id` | `duplicate id '<id>', first at <pointer>` |
| A member names no timeline of the file | the member | `'<id>' names no timeline of this file` |
| In a bundle, a member is already a member of an earlier group | the later member | `duplicate member '<id>', first at <pointer>` |
| A member lies inside an earlier member of its group, or contains one | the later member | `member '<id>' lies inside member '<earlier id>' of the same group` (`… contains member …`) |
| In a group file, a root contains no member | the root, `timelines/<i>` | `timeline '<id>' contains no member of the group` |
| In a bundle, a key of `graphical.order` names no group | the key | `'<key>' names no group of this bundle` |
| An entry of a display order is not a member of its group | the entry | `'<id>' is not a member of group '<group id>'` |
| A member of a group is missing from its display order | the order | `member '<id>' of group '<group id>' is missing` |

Within one timeline manifest, ids are visited in identity order (a timeline,
then its conversion maps, regions, breaks, jumps and markers, then its
children in code-point order of their keys); duplicates come first, then
dangling targets, then segment lines, whose segments are visited in offset
order (ties by key in code-point order) and compared by exact value. In a
group or bundle file, the problems come in this order: each root's own
problems, roots in array order; then repeated timeline ids, group ids, members
(member by member: dangling, repeated, nested), roots without a member, and
the display orders (a bundle's in code-point order of their keys). `<pointer>`
is a JSON pointer in URI fragment form, such as `#/timelines/0/id`. The
messages above quote ids as Python does; the TypeScript package quotes them as
JSON (`duplicate id "piece", first at #/timelines/0/id`). A repeated entry
within one display order or within one group's `members` is refused by the
schema.

### Schema documents

Version 0.7.0 has four schema documents in `schema/0.7.0/`, one per file
kind and one for what they share:

| Document | Holds |
| --- | --- |
| `core.schema.json` | the shared definitions: `Fraction` and its variants, the number and coordinate forms, `TimeUnit`, `NumberType`, the id rule `Id` and the file metadata `Meta` |
| `timeline.schema.json` | the timeline definitions and the timeline file |
| `group.schema.json` | `Group`, the display order `MemberOrder` and the group file |
| `bundle.schema.json` | the bundle file |

Each identifier is
`https://timetoalign.github.io/timeskeleton/0.7.0/<name>.schema.json`, so a
document lies below `schema/` at the path of its identifier, and the
documents refer to each other by relative `$ref`
(`core.schema.json#/$defs/Id`, `timeline.schema.json#/$defs/TimelineManifest`,
`group.schema.json#/$defs/Group`). A validator registers all four documents
of the version and checks a file against the document of its kind. Versions
0.5.0 and 0.6.0 each have one document,
`schema/timeskeleton-<version>.schema.json`.

The schema is the source of truth for timetoalign and TimeLineEditor.
timetoalign's hand-written serialization is tested for schema conformance and
fixture round trips. TypeScript types are generated in this repository.

## Drawing a timeline manifest

The optional `graphical` block of a timeline file contains named
declarations in `styles` and an ordered list of `statements`:

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

Readers accept a file's collections in any order. Writers emit one
canonical order, so equal files have equal text. The keys of every object,
at every depth, are sorted by Unicode code point. The arrays whose order keys
cannot express are put in this order:

- in every timeline manifest, `conversion_maps` by id;
- `regions` by start, then end, then id;
- flow-control `breaks` and `markers` by coordinate, then id;
- flow-control `jumps` by from coordinate, then to coordinate, then id;
- in a group or bundle file, `timelines` by id, a bundle's `groups` by id,
  and every group's `members` by code point.

Ids are unique within their scope, so no two entries tie.

`children` is an object keyed by id, so its text is sorted by id; its
canonical order, the one a reader that traverses the tree follows, is by
offset, then id. Coordinates compare by exact numeric value, never by JSON
spelling. Strings compare by Unicode code point. No other
array is reordered: `graphical` statements, display orders, conversion-map
payloads, and measure-map rows keep their order.

## The standard writer

Each package has one writer, `dumps`. It puts a file in canonical order,
sorts the keys of every object by code point, and writes UTF-8 text with
two-space indentation and a final newline. It writes any other JSON value, such
as an application's file embedding manifests, under the same rules. Every
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
offending value. Read a file with `json.loads`, which keeps integers and
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

- `validate(value)` checks a file against the schema of the version and kind
  it declares: a 0.5.0 or 0.6.0 timeline file against that version's schema,
  a 0.7.0 file against the document of its kind. A 0.7.0 value holding none
  or several of `timeline`, `group` and `bundle` is rejected at the root
  (`exactly one of 'timeline', 'group' or 'bundle' is required; found none`).
  A value that declares no supported version, or none, is refused on its
  `meta` alone, checked against the latest version's: at
  `meta.schema_version`, or at the root when `meta` is missing.
- `file_kind(value)` returns `"timeline"`, `"group"` or `"bundle"` for a value
  holding exactly that member, and `None` otherwise; `FILE_KINDS` is
  `("timeline", "group", "bundle")`.
- `migrate(value)` returns a copy of a file of any supported version
  rewritten to 0.7.0, through one step per later version; the input is not
  changed and the result is not validated. From 0.5.0 only
  `meta.schema_version` changes; from 0.6.0 every timeline, the root and
  every descendant, also gains `is_segment_line: false`, since 0.6.0 knows no
  segment lines. A 0.7.0 file is copied. A value that declares no supported
  version raises `UnsupportedVersionError`, as do the version-taking
  accessors below.
- `dumps(value)` returns the standard text of a file or any JSON value.
- `canonical_order(value)` returns a deep copy with the file's arrays in
  canonical order. `canonical_json(value)` returns compact JSON with object
  keys sorted by code point.
- `identity_problems(value)` returns every violation of the identity rules in
  a schema-valid file of any kind, in the order described above; `validate`
  raises the first.
- `complete_styles(graphical)` returns `(completed, missing)` and warns with
  `MissingStyleWarning` when `missing` is non-empty.
- `SCHEMA_VERSION` is `"0.7.0"`, and `SUPPORTED_VERSIONS` is
  `("0.5.0", "0.6.0", "0.7.0")`.
  `declared_version(value)` returns `meta.schema_version` when it is a string.
- `schema_documents(version)` returns the names of a version's schema
  documents: `("timeline",)` for 0.5.0 and 0.6.0, and `SCHEMA_DOCUMENTS`,
  `("core", "timeline", "group", "bundle")`, for 0.7.0.
  `schema_path(version, document)` and `load_schema(version, document)` return
  one document, the timeline document by default.
  `fixture_paths(version, kind)` returns the bundled fixtures of one file
  kind, timeline files by default, and `rejection_paths(version)` the bundled
  rejection cases. Each takes a version, 0.7.0 by default.
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

- `parse(text)` reads and validates a file of any kind without losing a
  number or key order, and returns it as a `TimeSkeletonFile`.
  `parseJson(text)` reads any JSON text without validating it.
- `validate(value)` narrows an unknown value to `TimeSkeletonFile`, checking
  it against the schema of the version and kind it declares, as Python's
  `validate` does. `TimeSkeletonFile` is the union of `TimeSkeletonManifest`
  (the timeline file), `TimeSkeletonGroupFile` and `TimeSkeletonBundleFile`.
- `fileKind(value)` returns the kind of a file, or `null`, as Python's
  `file_kind` does; `FILE_KINDS` lists the kinds and `FileKind` is their type.
- `migrate(value)` returns a copy rewritten to 0.7.0, as Python's `migrate`
  does, keeping every number and key order `parseJson` read.
- `dumps(value)` is the standard writer. `compactJson(value)` writes without
  whitespace, and `canonicalJson(value)` also sorts object keys by code point.
- `canonicalOrder(value)` returns a deep copy with the file's arrays in
  canonical order.
- `identityProblems(value)` returns the same identity problems as Python's
  `identity_problems`.
- `completeStyles(graphical)` returns `{graphical: completed, missing}`.
- `fontMetrics` contains the bundled font's advance-width metrics.
- `SCHEMA_VERSION` and `SUPPORTED_VERSIONS` name the bundled versions.
  `schemaDocuments` holds every bundled schema document, keyed by version and
  then by document name; `schemas` holds each version's timeline document,
  and `schema` the latest one. The generated types include
  `TimeSkeletonManifest`, `TimeSkeletonGroupFile`, `TimeSkeletonBundleFile`,
  `TimelineManifest`, `Group`, `Bundle`, `Meta`, `Id`, `MemberOrder`,
  `Graphical`, `Statement`, `Selector`, and `Declaration`.

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

Schema 0.5.0 is the earliest version this repository validates, and every
schema version from 0.5.0 onward remains validatable. Each later version has
a pure, ordered migration from the version before it in both packages,
pinned by a before-and-after fixture pair under `fixtures/migrations/`.
0.6.0 keeps the manifest format of 0.5.0 and revises the drawing
specification; its migration rewrites `meta.schema_version` alone. 0.7.0 adds
the group and bundle files, splits the schema into four documents, and adds
`is_segment_line` to every timeline; its migration also writes
`is_segment_line: false` on every timeline of a 0.6.0 file.

A timeskeleton release is a schema-version event: one `vX.Y.Z` tag publishes
both packages through trusted publishing. `scripts/check_versions.py` checks
that all version declarations agree.

## Fixtures

The [fixture guide](fixtures/README.md) describes the generated timeline,
group and bundle files and the drawings of each version, the hand-authored
rejection cases, and the migration pairs. The files of every kind are emitted
only by `scripts/emit_fixtures.py` using timetoalign and record its version
and commit in `meta.generator`. Do not edit them by hand.

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

`--kinds` followed by one or more of `timeline`, `group` and `bundle` emits
those kinds alone and leaves the files of the others as they are.

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
