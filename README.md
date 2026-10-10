# timeskeleton

TimeSkeleton is the versioned JSON Schema for the structural serialization of musical timelines, with golden fixtures emitted by [timetoalign](https://github.com/timetoalign/timetoalign) and validation and migration packages for Python and TypeScript. It carries timeline structure, not event data.

## The document

A TimeSkeleton document is a JSON object with `meta` and `manifest`. `meta.schema_version` selects the schema and `meta.generator` is optional. `manifest.timelines` maps timeline ids to manifests matching `timetoalign`'s `Timeline.to_dict(events=False)` output: axis (`class`, `unit`, `number_type`, `length`), child timelines at exact offsets, conversion maps, regions, flow control, measure map, and metric hierarchy. Event tables travel separately, typically as Arrow or Parquet data, and are referenced rather than embedded.

Every coordinate-valued member is an object with `unit`, `number_type`, and `value`. Its number type selects the value representation: an integer is a JSON integer, a float is a JSON number, and a fraction is a `[numerator, denominator]` pair of JSON integers with a strictly positive denominator, mirroring BOPP.

Version 0.2.0 specifies conversion maps, regions, flow control, and measure maps in addition to the envelope, timeline manifests, and typed coordinates. `metric_hierarchy` remains opaque. Version 0.1.0 retains its original opaque members. The 0.2.0 schema identifier is [`https://timetoalign.github.io/timeskeleton/0.2.0/timeskeleton.schema.json`](https://timetoalign.github.io/timeskeleton/0.2.0/timeskeleton.schema.json).

In 0.2.0, a measure map is the [Measure Map standard](https://github.com/measure-map/specification)'s compressed row array: entries equal to the preceding entry's default successor are omitted. TimeSkeleton adds the integer `volta` extension and permits exact Fraction pairs for numeric values where the standard uses JSON numbers.

The schema is the source of truth for timetoalign, the TimeLineEditor browser application, and its server. timetoalign's hand-written serialization is tested for schema conformance and fixture round trips. TypeScript types are generated in this repository, never by downstream consumers.

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

Python validation raises `SchemaValidationError` with a tuple path to the offending value. `migrate()` returns a deep-copied document at the latest supported version.

```python
import json

from timeskeleton import SchemaValidationError, fixture_paths, migrate, validate

document = json.loads(fixture_paths()[0].read_text())
try:
    validate(document)
except SchemaValidationError as error:
    print(error.path)
else:
    latest = migrate(document)
```

In TypeScript, `validate()` narrows an unknown value to `TimeSkeletonDocument`; `migrate()` returns the latest document version.

```ts
import {
  migrate,
  SchemaValidationError,
  type TimeSkeletonDocument,
  validate,
} from "@timetoalign/timeskeleton";

function load(document: unknown): TimeSkeletonDocument {
  try {
    validate(document);
    const typed: TimeSkeletonDocument = document;
    return migrate(typed);
  } catch (error) {
    if (error instanceof SchemaValidationError) {
      console.error(error.path);
    }
    throw error;
  }
}
```

## Versioning and migrations

`meta.schema_version` identifies a document's contract. Every published schema version remains validatable. Both packages provide `migrate()` as an ordered sequence of pure migration functions from earlier versions to the latest, with each migration pinned by a before-and-after fixture pair.

The first migration, 0.1.0 to 0.2.0, stamps documents with 0.2.0; the newly specified members already used the library's emitted shapes.

A timeskeleton release is a schema-version event: one `vX.Y.Z` tag publishes both packages through trusted publishing without stored registry tokens. `scripts/check_versions.py` verifies that all version declarations agree before release.

## Fixtures

The [golden fixtures](fixtures/README.md) are emitted only by `scripts/emit_fixtures.py` using timetoalign and ship in both packages. Each records the timetoalign version and commit in `meta.generator`; do not edit fixture JSON by hand.

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
