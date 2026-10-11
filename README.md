# timeskeleton

TimeSkeleton is the versioned JSON Schema for the structural serialization of musical timelines, with manifest fixtures emitted by [timetoalign](https://github.com/timetoalign/timetoalign) and validation and migration packages for Python and TypeScript. It carries timeline structure, not event data.

**Status: alpha.** The repository holds schema 0.4.0, a draft that no release declares yet, and keeps every published version (0.3.0, 0.2.1, 0.2.0 and 0.1.0) validatable. It offers validators in Python and TypeScript that locate a violation under one shared path rule, the canonical order of a manifest and one standard writer per language that writes the same manifest as the same bytes, a lossless JSON reader for TypeScript, the migrations from 0.1.0 up to 0.4.0 in both packages together with `split`, which divides a published envelope by its top-level timelines, and the manifest, rejection, and migration fixtures. It also specifies how a manifest is drawn: the optional `graphical` block of style rules and the [geometry specification](docs/geometry.md) of the layout and of the SVG and TikZ writers. The format may still change incompatibly in a later 0.x version; every such change ships with a migration.

## The manifest

A TimeSkeleton file at 0.4.0 is a **manifest**: a JSON object with `meta`, `timeline` and an optional `graphical` block. `meta.schema_version` selects the schema and `meta.generator` is optional. `timeline` is one timeline manifest matching `timetoalign`'s `Timeline.to_dict(events=False)` output: axis (`class`, `unit`, `number_type`, `length`), child timelines at exact offsets, conversion maps, regions, flow control, measure map, and metric hierarchy. A manifest describes exactly one top-level timeline with its subtree, and nothing about where or how often an application places it. Event tables travel separately, typically as Arrow or Parquet data, and are referenced rather than embedded. Later versions may admit `group` and `bundle` as alternatives to `timeline`.

The published versions 0.1.0 to 0.3.0 use another shape, here called an **envelope**: `{meta, manifest: {timelines: {<id>: <timeline manifest>}}, graphical?}`, which maps any number of top-level timelines, none included, to their timeline manifests. Envelopes remain validatable; `migrate` turns an envelope holding exactly one top-level timeline into a manifest, and `split` divides any envelope into envelopes of one top-level timeline each (see [Versioning and migrations](#versioning-and-migrations)).

Every coordinate-valued member is an object with `unit`, `number_type`, and `value`. Its number type selects the value representation: an integer is a JSON integer, a float is a JSON number, and a fraction is a `[numerator, denominator]` pair of JSON integers with a strictly positive denominator, mirroring BOPP.

Version 0.1.0 specifies the envelope, timeline manifests, and typed coordinates, and leaves the other members opaque. Version 0.2.0 specifies conversion maps, regions, flow control, and measure maps; `metric_hierarchy` remains opaque. Version 0.2.1 keeps every definition of 0.2.0 and fixes the order in which writers emit an envelope (see [Canonical order](#canonical-order)). Version 0.3.0 keeps every definition of 0.2.1 and adds the `graphical` block (see [Drawing a manifest](#drawing-a-manifest)). Version 0.4.0 keeps every definition of 0.3.0 and replaces the envelope's `manifest` member by the one `timeline`. The 0.4.0 schema identifier is [`https://timetoalign.github.io/timeskeleton/0.4.0/timeskeleton.schema.json`](https://timetoalign.github.io/timeskeleton/0.4.0/timeskeleton.schema.json).

Since 0.2.0, a measure map is the [Measure Map standard](https://github.com/measure-map/specification)'s compressed row array: entries equal to the preceding entry's default successor are omitted. A row is the standard's Measure plus two extensions: the integer `volta`, and `offset_within_measure`, where the row begins inside its nominal measure in quarter notes (an anacrusis, or one constituent of a split measure; absent means 0). Lengths are strictly positive and `qstamp` is non-negative; exact Fraction pairs are permitted wherever the standard uses JSON numbers. A measure map is anchored in quarter notes, so only a timeline whose unit is `quarters` may carry one.

The schema is the source of truth for timetoalign, the TimeLineEditor browser application, and its server. timetoalign's hand-written serialization is tested for schema conformance and fixture round trips. TypeScript types are generated in this repository, never by downstream consumers.

## Drawing a manifest

The optional `graphical` block holds what a user authored about the drawing of a manifest, and nothing derived: ordered lists of style rules held by containers, the manifest itself (`styles`, the outermost container) and any timeline with its subtree, the top-level timeline included (`timelines`, by timeline id).

```json
"graphical": {
  "styles": [
    {"select": {"element": "child", "domain": "logical"}, "set": {"side": "below"}}
  ],
  "timelines": {
    "performance": [{"select": {"element": "wedge"}, "set": {"colour": "#7F00FF"}}]
  }
}
```

A rule selects elements of its container (timelines, child timelines, conversion maps, regions, breaks, jumps, wedges and labels) by element type, domain, modality or a list of element ids, and sets properties from a closed set: `colour`, `line_pattern`, `visible` (`false` filters an element out), `side`, `show_length` and `show_projected_coordinates`. Each property is resolved on its own, as in CSS: a rule naming the element's id decides, then the rule of the nearest container, then a rule naming the element type over one naming only the domain or modality, then the rule naming more members, then the later rule. Every property has a written default, so a manifest without the block, or with no rules, is fully drawable. The shape of the block is being redesigned before 0.4.0 is released.

The [geometry specification](docs/geometry.md) defines the drawing completely: the layout that turns a manifest into one block of geometry (integer rows, horizontal positions as exact values on the top-level timeline's axis in the manifest's own number forms), and the SVG and TikZ writers that turn the block into text under one page transform and one number formatting rule. Two implementations that follow it draw the same manifest as the same SVG and TikZ text, byte for byte. A published envelope is drawn by splitting it first, one block per manifest. From 0.4.0 on there is no geometry schema: the JSON form of geometry is internal to an implementation, and the specification with the SVG and TikZ fixtures of a version pins the drawing (0.4.0 has none yet). The geometry schema and the geometry, SVG and TikZ fixtures of 0.3.0 remain in the repository, frozen with that release as a record of how 0.3.0 drew an envelope; they constrain nothing.

## Canonical order

Readers accept the collections of a manifest in any order. Writers emit one canonical order, so that equal manifests are equal text:

- in an envelope, `manifest.timelines` by id;
- in every timeline manifest, at every depth, starting from a manifest's `timeline` or from each of an envelope's timelines: `children` by offset, then id;
- `conversion_maps` by id;
- `regions` by start, then end, then name;
- flow-control `breaks` by coordinate, then canonical JSON text;
- flow-control `jumps` by from coordinate, then to coordinate, then canonical JSON text;
- flow-control `markers` by name.

Coordinates compare by their exact numeric value, never by their JSON spelling: `9` comes before `10`, and `[5, 8]` before `[2, 3]`. Strings compare by Unicode code point, not by UTF-16 code unit, so `"～"` (U+FF5E) comes before `"🎵"` (U+1F3B5). The canonical JSON text of an entry has its object keys sorted by code point and no whitespace. Nothing else is reordered: the members of a timeline manifest, `meta` objects, the `graphical` block, conversion-map payloads and `measure_map` rows keep their order.

## The standard writer

Each package has one writer, `dumps`. It puts a manifest or an envelope in canonical order and writes it as UTF-8 text with two-space indentation and a final newline. Every character is written unescaped except `"`, `\` and the control characters U+0000 to U+001F. A float is always written as a float, with a decimal point or an exponent, spelled exactly as Python's `repr` spells it (`2.0`, `0.0001`, `1e-05`, `1e+16`, `-0.0`); an integer is never written with a decimal point or an exponent, however large. A NaN, an infinity, or a string holding a lone surrogate (which UTF-8 cannot encode) is refused. The Python and TypeScript writers write the same value as the same bytes; the fixtures are written by it.

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

Python validation raises `SchemaValidationError` with a tuple path to the offending value. `migrate()` returns a deep copy brought to the latest version. Read manifests and envelopes with `json.loads`, which keeps integers and floats apart and every integer exact; write them with `dumps`. The example accepts a manifest or a published envelope and writes one manifest per top-level timeline:

```python
import json

from timeskeleton import (
    SCHEMA_VERSION,
    SchemaValidationError,
    declared_version,
    dumps,
    fixture_paths,
    migrate,
    split,
    validate,
)

value = json.loads(fixture_paths("0.3.0")[0].read_text(encoding="utf-8"))
try:
    validate(value)
except SchemaValidationError as error:
    print(error.path)
else:
    parts = [value] if declared_version(value) == SCHEMA_VERSION else split(value)
    texts = [dumps(migrate(part)) for part in parts]
```

- `validate(value)` checks a manifest or an envelope against the schema version it declares; a value declaring no supported version is checked against the latest schema, which rejects it at `meta.schema_version`.
- `migrate(value)` returns a deep copy of a manifest or envelope at `SCHEMA_VERSION`. It raises `UnsupportedVersionError` for an unknown version and `MigrationError`, with the path of the offending member, for a member it cannot migrate, including an envelope that does not hold exactly one top-level timeline.
- `split(envelope)` returns one 0.3.0 envelope per top-level timeline of a published envelope (a version in `ENVELOPE_VERSIONS`, 0.1.0 to 0.3.0), in id order; an envelope without timelines gives an empty list. Each envelope keeps `meta` and the envelope's own `styles`, and only those entries of `graphical.timelines` that name its timeline or one of its descendants. It raises `MigrationError` at `meta.schema_version` for a manifest or an unknown version.
- `graphical_for_subtree(graphical, root_id, manifest)` returns the part of a `graphical` block that concerns the timeline `root_id`, whose timeline manifest is `manifest`, and its descendants: a copy holding every manifest-level rule and, in `timelines`, only the entries of that subtree (absent when none remains). `split` and the 0.3.0 to 0.4.0 migration use it.
- `dumps(value)` returns the standard text of a manifest or envelope, or of any JSON value. It raises `ValueError` for a NaN, an infinity, a lone surrogate, or a collection whose entries lack the members it is ordered by. It is `json.dumps(canonical_order(value), indent=2, ensure_ascii=False)` plus a final newline.
- `canonical_order(value)` returns a deep copy with the manifest or envelope in canonical order. Only the collections listed under [Canonical order](#canonical-order), where a manifest or an envelope holds them, are reordered, so any other JSON value is copied unchanged.
- `canonical_json(value)` returns the canonical JSON text of a value: keys sorted by code point, no whitespace.
- `SCHEMA_VERSION` is the latest version, `SUPPORTED_VERSIONS` lists every validatable one and `ENVELOPE_VERSIONS` those whose shape is the envelope, oldest first; `declared_version(value)` returns `meta.schema_version` when it is a string.
- `schema_path(version)` and `load_schema(version)` return the bundled schema; `fixture_paths(version)` and `rejection_paths(version)` the manifest or envelope fixtures and the shared rejection cases of a version (each version defaults to `SCHEMA_VERSION`); `migration_paths()` the `(before, after)` pairs of every migration step; and `split_paths()` the input of the shared `split` case and its outputs, sorted by name.
- For the frozen 0.3.0 drawing record: `validate_geometry(geometry)` checks a geometry against the 0.3.0 geometry schema and raises `SchemaValidationError` with the path of the first violation; `geometry_schema_path(version)` and `load_geometry_schema(version)` return that schema, `GEOMETRY_VERSIONS` is `("0.3.0",)`, and `geometry_paths(version)` and `geometry_rejection_paths(version)` return the 0.3.0 geometry fixture directories and geometry rejection cases.

### TypeScript

`JSON.parse` loses what the format distinguishes: it reads `2.0` as the integer `2`, rounds integers beyond 2^53, and lists array-index keys such as `"10"` before every other key whatever order they were written in. The package therefore reads manifests and envelopes itself. The example accepts a manifest or a published envelope and writes one manifest per top-level timeline:

```ts
import {
  declaredVersion,
  dumps,
  migrate,
  parse,
  SCHEMA_VERSION,
  SchemaValidationError,
  split,
} from "@timetoalign/timeskeleton";

function load(text: string): string[] {
  try {
    const value = parse(text);
    const parts = declaredVersion(value) === SCHEMA_VERSION ? [value] : split(value);
    return parts.map((part) => dumps(migrate(part)));
  } catch (error) {
    if (error instanceof SchemaValidationError) {
      console.error(error.path);
    }
    throw error;
  }
}
```

- `parse(text)` reads a manifest or an envelope without losing a number or the order of a key and validates it against the schema version it declares. It returns a `Lossless<TimeSkeletonManifest>` and throws `SyntaxError` for text that is not one JSON value, `RangeError` for a float beyond the range of a double, and `SchemaValidationError` for an invalid value. The generated type describes a 0.4.0 manifest; a value declaring an earlier version is an envelope.
- `parseJson(text)` reads any JSON text the same way, without validating it, and returns a `Lossless<Json>`.
- `validate(value)` narrows an unknown value to `TimeSkeletonManifest` and accepts values read by `parseJson`, checking their numbers by value. `migrate(value)` returns the manifest at the latest version and keeps the `JsonNumber`s of such a value; it throws `MigrationError` for an envelope that does not hold exactly one top-level timeline. `split(envelope)` divides a published envelope as Python's `split` does, `graphicalForSubtree` is Python's `graphical_for_subtree`, and `ENVELOPE_VERSIONS` lists the envelope versions.
- `dumps(value)` is the standard writer. It throws `RangeError` for a non-finite number or a lone surrogate, and `TypeError` for a value that is not JSON or a collection it cannot order.
- `compactJson(value)` writes a value with no whitespace and every object's keys in their own order (the written order for a value read by `parseJson`), numbers and strings spelled as Python spells them; `parseJson` reads it back to an equal value. `canonicalJson(value)` writes the same text with keys sorted by code point, as Python's `canonical_json` does.
- `canonicalOrder(value)` returns a deep copy with the manifest or envelope in canonical order, as Python's `canonical_order` does.
- `validateGeometry(value)` checks a value against the frozen 0.3.0 geometry schema, narrowing it to `Geometry`, and throws `SchemaValidationError` at the path the Python validator reports; `geometrySchema`, `geometrySchemas` and `GEOMETRY_VERSIONS` give that schema. The generated types include `TimeSkeletonManifest`, `TimelineManifest`, the 0.3.0 geometry's `Geometry`, `Block` and `Primitive`, and the `graphical` block's `Graphical`, `StyleRule`, `StyleSelector` and `StyleProperties`.

A number read by `parseJson` is a `JsonNumber`:

| JSON text | `JsonNumber` |
| --- | --- |
| an integer within ±(2^53 − 1), such as `480` | a `number` |
| an integer beyond that range, such as `9007199254740993` | a `bigint` |
| a float with a fractional part, such as `0.5` | a `number` |
| an integral float, such as `2.0`, `1e+16` or `-0.0` | a `JsonFloat`, whose `value` is the `number` |

`-0` (without a decimal point) is the integer 0, as in Python. `Lossless<T>` is the type `T` with every `number` replaced by `JsonNumber`; `Json` is any JSON value as `JSON.parse` types it. The writers read the same representation back: a `bigint` or an integral `number` is written as an integer, a `JsonFloat` or a `number` with a fractional part (or `-0`) as a float. A float whose value is an integer must therefore be passed as `new JsonFloat(2)`, never as `2`. `isJsonFloat(value)` tells a `JsonFloat` apart, and `isJsonObject(value)` tells a JSON object from an array, a `JsonFloat` and every other value.

JavaScript code outside this package that writes manifests or envelopes must not use `JSON.stringify`, which spells every number as a JavaScript number and every object in `Object.keys` order. It must emit each object's members itself, in their intended order, and spell numbers by their `JsonNumber` representation; `dumps` and `compactJson` do both. An object built in JavaScript lists array-index keys first whatever order they were added in; objects read by `parseJson` or returned by `canonicalOrder` record their intended order, and the writers honour it.

## Versioning and migrations

`meta.schema_version` identifies the contract of a manifest or an envelope. Every published schema version remains validatable. Both packages provide `migrate()` as an ordered sequence of pure migration functions from earlier versions to the latest, with each migration pinned by a before-and-after fixture pair.

The first migration, 0.1.0 to 0.2.0, rewrites the shapes timetoalign wrote at 0.1.0 that 0.2.0 specifies differently: a tagged-measure measure map becomes compressed rows, and a `MetricalPositionMap` keeps its meter map once and names its derived beat map by `beat_map_id`. A member whose shape the migration does not know raises `MigrationError` with the member's path; a migrated envelope satisfies 0.2.0.

The second migration, 0.2.0 to 0.2.1, declares version 0.2.1, validates the envelope against it, and then puts it in canonical order; the shapes are unchanged. An envelope that does not satisfy 0.2.1 raises `MigrationError` at the path of the offending member in the input. The third, 0.2.1 to 0.3.0, does the same for 0.3.0: the `graphical` block is optional and additive, so a 0.2.1 envelope changes only in its declared version. Each migration returns its result declaring its own target version.

The fourth migration, 0.3.0 to 0.4.0, turns an envelope holding exactly one top-level timeline into a manifest: `meta` keeps its `generator`, the timeline becomes `timeline`, and the `graphical` block keeps its `styles` and those entries of `timelines` that name the timeline or one of its descendants; an entry naming no such timeline selected nothing and is dropped. Every element therefore resolves every property as before. The manifest is returned in canonical order. An envelope with no top-level timeline, or with several, raises `MigrationError` at `manifest.timelines`, naming `split`. `split` divides a published envelope into one 0.3.0 envelope per top-level timeline, in id order, so every published envelope reaches the latest version as

```python
manifests = [migrate(envelope) for envelope in split(value)]
```

and an envelope without timelines yields no manifest.

A timeskeleton release is a schema-version event: one `vX.Y.Z` tag publishes both packages through trusted publishing without stored registry tokens. `scripts/check_versions.py` verifies that all version declarations agree before release.

## Fixtures

The [fixtures](fixtures/README.md) ship in both packages. The manifest fixtures (envelope fixtures up to 0.3.0) are emitted only by `scripts/emit_fixtures.py` using timetoalign, and each records the timetoalign version and commit in `meta.generator`; never edit one by hand. At 0.4.0 there is one manifest fixture per top-level timeline of the 0.3.0 envelope fixtures: a fixture built with one top-level timeline keeps its name, and one built with several gives `<name>__<slug>.json` per timeline, where the slug is the timeline id with every character outside `[A-Za-z0-9_-]` replaced by `_` (the script refuses two timelines whose file names would coincide); this gives 34 manifest fixtures. The rejection cases, 47 at 0.4.0, the migration pairs and the `split` case under `fixtures/migrations/split/0.3.0/` are written by hand. `fixtures/0.3.0/geometry/` holds the geometry, SVG and TikZ fixtures of the 0.3.0 envelopes, seven of the geometries derived by hand (the arithmetic is in that directory's README) and the rest written by the TimeLineEditor's layout and writers; they are frozen with 0.3.0 and constrain nothing.

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

From the repository root, check that all version declarations agree:

```bash
python3 scripts/check_versions.py
```

## Releasing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the required version updates, checks, tag, and trusted-publishing configuration.

## License

[MIT](LICENSE).
