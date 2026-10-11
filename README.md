# timeskeleton

TimeSkeleton is the JSON Schema for the structural serialization of musical
timelines, with manifest fixtures emitted by
[timetoalign](https://github.com/timetoalign/timetoalign) and validation
packages for Python and TypeScript. It carries timeline structure, not event
data.

**Status: alpha.** The repository contains schema version 0.4.0. It provides
validators that locate a violation under one shared path rule, a canonical
manifest order, standard writers that produce the same bytes in Python and
TypeScript, a lossless JSON reader for TypeScript, generated TypeScript types,
and shared fixtures. It also specifies how a manifest is drawn.

## The manifest

A TimeSkeleton file is one manifest: a JSON object with `meta`, `timeline`,
and an optional `graphical` block. `meta.schema_version` is `"0.4.0"`, and
`meta.generator` is optional. `timeline` is one timeline manifest matching
timetoalign's `Timeline.to_dict(events=False)` output: its axis (`class`,
`unit`, `number_type`, and `length`), child timelines at exact offsets,
conversion maps, regions, flow control, measure map, and metric hierarchy.
The schema identifier is
[`https://timetoalign.github.io/timeskeleton/0.4.0/timeskeleton.schema.json`](https://timetoalign.github.io/timeskeleton/0.4.0/timeskeleton.schema.json).

A manifest describes exactly one top-level timeline and all its descendants.
It says nothing about where or how often an application places that timeline.
Event tables travel separately, typically as Arrow or Parquet data, and are
referenced rather than embedded.

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

The schema is the source of truth for timetoalign and TimeLineEditor.
timetoalign's hand-written serialization is tested for schema conformance and
fixture round trips. TypeScript types are generated in this repository.

## Drawing a manifest

The optional `graphical` block contains named declarations in `styles` and an
ordered list of `statements`:

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
pins the drawing.

Every text is measured and drawn with the bundled DejaVu Sans 2.37 release
file, `fonts/DejaVuSans.ttf`. `fonts/LICENSE` contains its licence, and
`fonts/dejavu-sans-2.37.metrics.json` contains its advance-width metrics.
Python exposes the files through `font_path()` and `font_metrics()`. The npm
package exports `fontMetrics` and exposes the files through the
`@timetoalign/timeskeleton/fonts/*` subpath. Run
`scripts/extract_font_metrics.py` to regenerate the metrics from the font.

## Canonical order

Readers accept a manifest's collections in any order. Writers emit one
canonical order, so equal manifests have equal text:

- at every depth, `children` by offset, then id;
- `conversion_maps` by id;
- `regions` by start, then end, then name;
- flow-control `breaks` by coordinate, then canonical JSON text;
- flow-control `jumps` by from coordinate, then to coordinate, then canonical
  JSON text;
- flow-control `markers` by name.

Coordinates compare by exact numeric value, never by JSON spelling. Strings
compare by Unicode code point. The canonical JSON text of an entry has its
object keys sorted by code point and no whitespace. Nothing else is reordered:
the members of a timeline manifest, `meta`, `graphical`, conversion-map
payloads, and measure-map rows keep their order.

## The standard writer

Each package has one writer, `dumps`. It puts a manifest in canonical order
and writes UTF-8 text with two-space indentation and a final newline. Every
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

- `validate(value)` checks a manifest against the version it declares. A value
  that does not declare the supported version is checked against 0.4.0 and is
  rejected at `meta.schema_version`.
- `dumps(value)` returns the standard text of a manifest or any JSON value.
- `canonical_order(value)` returns a deep copy with the manifest collections
  in canonical order. `canonical_json(value)` returns compact JSON with object
  keys sorted by code point.
- `complete_styles(graphical)` returns `(completed, missing)` and warns with
  `MissingStyleWarning` when `missing` is non-empty.
- `SCHEMA_VERSION` is `"0.4.0"`, and `SUPPORTED_VERSIONS` is `("0.4.0",)`.
  `declared_version(value)` returns `meta.schema_version` when it is a string.
- `schema_path()` and `load_schema()` return the bundled schema;
  `fixture_paths()` and `rejection_paths()` return the bundled manifest and
  rejection fixtures.
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

- `parse(text)` reads and validates a manifest without losing a number or key
  order. `parseJson(text)` reads any JSON text without validating it.
- `validate(value)` narrows an unknown value to `TimeSkeletonManifest`.
- `dumps(value)` is the standard writer. `compactJson(value)` writes without
  whitespace, and `canonicalJson(value)` also sorts object keys by code point.
- `canonicalOrder(value)` returns a deep copy with the manifest collections in
  canonical order.
- `completeStyles(graphical)` returns `{graphical: completed, missing}`.
- `fontMetrics` contains the bundled font's advance-width metrics.
- `schema`, `schemas`, `SCHEMA_VERSION`, and `SUPPORTED_VERSIONS` expose the
  bundled 0.4.0 contract. The generated types include
  `TimeSkeletonManifest`, `TimelineManifest`, `Graphical`, `Statement`,
  `Selector`, and `Declaration`.

A number read by `parseJson` is a `JsonNumber`:

| JSON text | `JsonNumber` |
| --- | --- |
| an integer within ±(2^53 − 1), such as `480` | a `number` |
| an integer beyond that range, such as `9007199254740993` | a `bigint` |
| a float with a fractional part, such as `0.5` | a `number` |
| an integral float, such as `2.0`, `1e+16`, or `-0.0` | a `JsonFloat` |

`Lossless<T>` replaces every `number` in `T` with `JsonNumber`. A float whose
value is an integer must be passed as `new JsonFloat(2)`, not as `2`, if it is
to be written as a float. JavaScript code that writes manifests must use
`dumps` or `compactJson`, not `JSON.stringify`.

## Versioning

Schema 0.4.0 is the earliest version this repository validates. Every schema
version from 0.4.0 onward remains validatable. A later schema version adds
pure, ordered migrations in both packages, with each step pinned by a
before-and-after fixture pair.

A timeskeleton release is a schema-version event: one `vX.Y.Z` tag publishes
both packages through trusted publishing. `scripts/check_versions.py` checks
that all version declarations agree.

## Fixtures

The [fixture guide](fixtures/README.md) describes the generated 0.4.0
manifests and the hand-authored rejection cases. Manifest fixtures are emitted
only by `scripts/emit_fixtures.py` using timetoalign and record its version and
commit in `meta.generator`. Do not edit them by hand.

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

To re-emit manifests, use an interpreter containing the timetoalign revision
being represented:

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
