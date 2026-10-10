# timeskeleton

TimeSkeleton is the versioned JSON Schema for the structural serialization of musical timelines, with golden fixtures emitted by [timetoalign](https://github.com/timetoalign/timetoalign) and validation and migration packages for Python and TypeScript. It carries timeline structure, not event data.

**Status: alpha.** Version 0.3.0 offers the schema (0.3.0, with 0.2.1, 0.2.0 and 0.1.0 kept validatable), validators in Python and TypeScript that locate a violation under one shared path rule, the canonical order of a document and one standard writer per language that writes the same document as the same bytes, a lossless JSON reader for TypeScript, the migrations from 0.1.0 up to 0.3.0 in both packages, and the golden, rejection, and migration fixtures. From 0.3.0 on it also specifies how a document is drawn: the optional `graphical` block of style rules, the [geometry specification](docs/geometry.md) with its geometry schema and validators, and golden geometry, SVG and TikZ figures that every implementation must reproduce byte for byte. The format may still change incompatibly in a later 0.x version; every such change ships with a migration.

## The document

A TimeSkeleton document is a JSON object with `meta`, `manifest` and, from 0.3.0 on, an optional `graphical` block. `meta.schema_version` selects the schema and `meta.generator` is optional. `manifest.timelines` maps timeline ids to manifests matching `timetoalign`'s `Timeline.to_dict(events=False)` output: axis (`class`, `unit`, `number_type`, `length`), child timelines at exact offsets, conversion maps, regions, flow control, measure map, and metric hierarchy. Event tables travel separately, typically as Arrow or Parquet data, and are referenced rather than embedded.

Every coordinate-valued member is an object with `unit`, `number_type`, and `value`. Its number type selects the value representation: an integer is a JSON integer, a float is a JSON number, and a fraction is a `[numerator, denominator]` pair of JSON integers with a strictly positive denominator, mirroring BOPP.

Version 0.2.0 specifies conversion maps, regions, flow control, and measure maps in addition to the envelope, timeline manifests, and typed coordinates. `metric_hierarchy` remains opaque. Version 0.2.1 keeps every definition of 0.2.0 and fixes the order in which writers emit a document (see [Canonical order](#canonical-order)). Version 0.3.0 keeps every definition of 0.2.1 and adds the `graphical` block (see [Drawing a document](#drawing-a-document)). Version 0.1.0 retains its original opaque members. The 0.3.0 schema identifier is [`https://timetoalign.github.io/timeskeleton/0.3.0/timeskeleton.schema.json`](https://timetoalign.github.io/timeskeleton/0.3.0/timeskeleton.schema.json).

Since 0.2.0, a measure map is the [Measure Map standard](https://github.com/measure-map/specification)'s compressed row array: entries equal to the preceding entry's default successor are omitted. A row is the standard's Measure plus two extensions: the integer `volta`, and `offset_within_measure`, where the row begins inside its nominal measure in quarter notes (an anacrusis, or one constituent of a split measure; absent means 0). Lengths are strictly positive and `qstamp` is non-negative; exact Fraction pairs are permitted wherever the standard uses JSON numbers. A measure map is anchored in quarter notes, so only a timeline whose unit is `quarters` may carry one.

The schema is the source of truth for timetoalign, the TimeLineEditor browser application, and its server. timetoalign's hand-written serialization is tested for schema conformance and fixture round trips. TypeScript types are generated in this repository, never by downstream consumers.

## Drawing a document

The optional `graphical` block holds what a user authored about the drawing of a document, and nothing derived: ordered lists of style rules held by containers, the document itself (`styles`) and any timeline with its subtree (`timelines`, by timeline id).

```json
"graphical": {
  "styles": [
    {"select": {"element": "child", "domain": "logical"}, "set": {"side": "below"}}
  ],
  "timelines": {
    "perf": [{"select": {}, "set": {"visible": false}}]
  }
}
```

A rule selects elements of its container (timelines, child timelines, conversion maps, regions, breaks, jumps, wedges and labels) by element type, domain, modality or a list of element ids, and sets properties from a closed set: `colour`, `line_pattern`, `visible` (`false` filters an element out), `side`, `show_length` and `show_projected_coordinates`. Each property is resolved on its own, as in CSS: a rule naming the element's id decides, then the rule of the nearest container, then a rule naming the element type over one naming only the domain or modality, then the rule naming more members, then the later rule. Every property has a written default, so a document without the block, or with no rules, is fully drawable.

The [geometry specification](docs/geometry.md) defines the drawing completely: the layout that turns a document into **geometry** (one block per top-level timeline, integer rows, horizontal positions as exact values on the root timeline's axis in the document's own number forms), and the SVG and TikZ writers that turn geometry into text under one page transform and one number formatting rule. Geometry validates against `schema/geometry-<version>.schema.json`, whose identifier for 0.3.0 is [`https://timetoalign.github.io/timeskeleton/0.3.0/geometry.schema.json`](https://timetoalign.github.io/timeskeleton/0.3.0/geometry.schema.json); its list of primitives is an open union, so a reader skips a primitive kind it does not know. Two implementations that follow the specification produce the same geometry and the same figures, byte for byte; the golden figures under `fixtures/<version>/geometry/` pin it.

## Canonical order

Readers accept the collections of a document in any order. Writers emit one canonical order, so that equal documents are equal text:

- `manifest.timelines` by id;
- in every timeline manifest, at every depth: `children` by offset, then id;
- `conversion_maps` by id;
- `regions` by start, then end, then name;
- flow-control `breaks` by coordinate, then canonical JSON text;
- flow-control `jumps` by from coordinate, then to coordinate, then canonical JSON text;
- flow-control `markers` by name.

Coordinates compare by their exact numeric value, never by their JSON spelling: `9` comes before `10`, and `[5, 8]` before `[2, 3]`. Strings compare by Unicode code point, not by UTF-16 code unit, so `"～"` (U+FF5E) comes before `"🎵"` (U+1F3B5). The canonical JSON text of an entry has its object keys sorted by code point and no whitespace. Nothing else is reordered: the members of a timeline manifest, `meta` objects, conversion-map payloads and `measure_map` rows keep their order.

## The standard writer

Each package has one writer, `dumps`. It puts the document in canonical order and writes it as UTF-8 text with two-space indentation and a final newline. Every character is written unescaped except `"`, `\` and the control characters U+0000 to U+001F. A float is always written as a float, with a decimal point or an exponent, spelled exactly as Python's `repr` spells it (`2.0`, `0.0001`, `1e-05`, `1e+16`, `-0.0`); an integer is never written with a decimal point or an exponent, however large. A NaN, an infinity, or a string holding a lone surrogate (which UTF-8 cannot encode) is refused. The Python and TypeScript writers write the same document as the same bytes; the golden fixtures are written by it.

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

Python validation raises `SchemaValidationError` with a tuple path to the offending value. `migrate()` returns a deep-copied document at the latest supported version. Read documents with `json.loads`, which keeps integers and floats apart and every integer exact; write them with `dumps`.

```python
import json

from timeskeleton import SchemaValidationError, dumps, fixture_paths, migrate, validate

document = json.loads(fixture_paths()[0].read_text(encoding="utf-8"))
try:
    validate(document)
except SchemaValidationError as error:
    print(error.path)
else:
    text = dumps(migrate(document))
```

- `dumps(value)` returns the standard text of a document, or of any JSON value. It raises `ValueError` for a NaN, an infinity, a lone surrogate, or a collection whose entries lack the members it is ordered by. It is `json.dumps(canonical_order(value), indent=2, ensure_ascii=False)` plus a final newline.
- `canonical_order(value)` returns a deep copy with the document in canonical order. Only the collections a document holds where a document holds them are reordered, so any other JSON value is copied unchanged.
- `canonical_json(value)` returns the canonical JSON text of a value: keys sorted by code point, no whitespace.
- `validate_geometry(geometry)` checks a geometry against the geometry schema of the version it declares and raises `SchemaValidationError` with the path of the first violation. `geometry_schema_path(version)` and `load_geometry_schema(version)` return the bundled geometry schema, `GEOMETRY_VERSIONS` lists the versions that have one, and `geometry_paths(version)` and `geometry_rejection_paths(version)` return the golden geometry directories and the shared geometry rejection cases.

### TypeScript

`JSON.parse` loses what the format distinguishes: it reads `2.0` as the integer `2`, rounds integers beyond 2^53, and lists array-index keys such as `"10"` before every other key whatever order they were written in. The package therefore reads documents itself.

```ts
import {
  dumps,
  migrate,
  parse,
  SchemaValidationError,
} from "@timetoalign/timeskeleton";

function load(text: string): string {
  try {
    const document = parse(text);
    return dumps(migrate(document));
  } catch (error) {
    if (error instanceof SchemaValidationError) {
      console.error(error.path);
    }
    throw error;
  }
}
```

- `parse(text)` reads a document without losing a number or the order of a key and validates it against the schema version it declares. It returns a `Lossless<TimeSkeletonDocument>` and throws `SyntaxError` for text that is not one JSON value, `RangeError` for a float beyond the range of a double, and `SchemaValidationError` for an invalid document.
- `parseJson(text)` reads any JSON text the same way, without validating it, and returns a `Lossless<Json>`.
- `validate(value)` narrows an unknown value to `TimeSkeletonDocument` and accepts values read by `parseJson`, checking their numbers by value. `migrate(value)` returns the document at the latest version and keeps the `JsonNumber`s of such a value.
- `dumps(value)` is the standard writer. It throws `RangeError` for a non-finite number or a lone surrogate, and `TypeError` for a value that is not JSON or a collection it cannot order.
- `compactJson(value)` writes a value with no whitespace and every object's keys in their own order (the written order for a value read by `parseJson`), numbers and strings spelled as Python spells them; `parseJson` reads it back to an equal value. `canonicalJson(value)` writes the same text with keys sorted by code point, as Python's `canonical_json` does.
- `canonicalOrder(value)` returns a deep copy with the document in canonical order, as Python's `canonical_order` does.
- `validateGeometry(value)` narrows an unknown value to `Geometry`, checked against the geometry schema of the version it declares, and throws `SchemaValidationError` at the path the Python validator reports. `geometrySchema` is the latest geometry schema, `geometrySchemas` every one by version, and `GEOMETRY_VERSIONS` their versions; the generated types include `Geometry`, `Block`, `Primitive` and the `graphical` block's `Graphical`, `StyleRule`, `StyleSelector` and `StyleProperties`.

A number read by `parseJson` is a `JsonNumber`:

| JSON text | `JsonNumber` |
| --- | --- |
| an integer within ±(2^53 − 1), such as `480` | a `number` |
| an integer beyond that range, such as `9007199254740993` | a `bigint` |
| a float with a fractional part, such as `0.5` | a `number` |
| an integral float, such as `2.0`, `1e+16` or `-0.0` | a `JsonFloat`, whose `value` is the `number` |

`-0` (without a decimal point) is the integer 0, as in Python. `Lossless<T>` is the type `T` with every `number` replaced by `JsonNumber`; `Json` is any JSON value as `JSON.parse` types it. The writers read the same representation back: a `bigint` or an integral `number` is written as an integer, a `JsonFloat` or a `number` with a fractional part (or `-0`) as a float. A float whose value is an integer must therefore be passed as `new JsonFloat(2)`, never as `2`. `isJsonFloat(value)` tells a `JsonFloat` apart, and `isJsonObject(value)` tells a JSON object from an array, a `JsonFloat` and every other value.

JavaScript code outside this package that writes these documents must not use `JSON.stringify`, which spells every number as a JavaScript number and every object in `Object.keys` order. It must emit each object's members itself, in their intended order, and spell numbers by their `JsonNumber` representation; `dumps` and `compactJson` do both. An object built in JavaScript lists array-index keys first whatever order they were added in; objects read by `parseJson` or returned by `canonicalOrder` record their intended order, and the writers honour it.

## Versioning and migrations

`meta.schema_version` identifies a document's contract. Every published schema version remains validatable. Both packages provide `migrate()` as an ordered sequence of pure migration functions from earlier versions to the latest, with each migration pinned by a before-and-after fixture pair.

The first migration, 0.1.0 to 0.2.0, rewrites the shapes timetoalign wrote at 0.1.0 that 0.2.0 specifies differently: a tagged-measure measure map becomes compressed rows, and a `MetricalPositionMap` keeps its meter map once and names its derived beat map by `beat_map_id`. A member whose shape the migration does not know raises `MigrationError` with the member's path; a migrated document satisfies 0.2.0.

The second migration, 0.2.0 to 0.2.1, declares version 0.2.1, validates the document against it, and then puts it in canonical order; the shapes are unchanged. A document that does not satisfy 0.2.1 raises `MigrationError` at the path of the offending member in the input. The third, 0.2.1 to 0.3.0, does the same for 0.3.0: the `graphical` block is optional and additive, so a 0.2.1 document changes only in its declared version. Each migration returns the document declaring its own target version.

A timeskeleton release is a schema-version event: one `vX.Y.Z` tag publishes both packages through trusted publishing without stored registry tokens. `scripts/check_versions.py` verifies that all version declarations agree before release.

## Fixtures

The [golden fixtures](fixtures/README.md) ship in both packages. The documents are emitted only by `scripts/emit_fixtures.py` using timetoalign, and each records the timetoalign version and commit in `meta.generator`. From 0.3.0 on, each document has a golden geometry, SVG and TikZ figure under `fixtures/<version>/geometry/`: seven geometries are derived by hand from the specification (the arithmetic is in that directory's README), and the other geometries and every figure are written by the TimeLineEditor's layout and writers (`app/packages/writers/scripts/emit-geometry.ts` in [TimeLineEditor](https://github.com/TimeToAlign/TimeLineEditor)), which must reproduce the seven hand-derived files first. Never edit an emitted golden fixture by hand; a hand-derived geometry changes only together with the specification and the arithmetic in that README. The rejection cases and migration pairs beside them are authored by hand.

## Development

Clone the repository, then run the package commands in their indicated directories.

```bash
git clone https://github.com/TimeToAlign/timeskeleton.git
cd timeskeleton/python
uv sync
uv run pytest
```

```bash
cd js
pnpm install
pnpm test
pnpm generate
pnpm build
```

To re-emit fixtures, use an interpreter whose environment contains the timetoalign revision being represented:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"
```

The golden geometry and figures are re-emitted from a TimeLineEditor checkout whose workspace uses this checkout's JavaScript package; from its `app/packages/writers/` directory:

```bash
node scripts/emit-geometry.ts /path/to/timeskeleton
```

From the repository root, check that all version declarations agree:

```bash
python3 scripts/check_versions.py
```

## Releasing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the required version updates, checks, tag, and trusted-publishing configuration.

## License

[MIT](LICENSE).
