# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Schema 0.2.1 and both packages at 0.2.1.

### Added

- Schema 0.2.1 keeps every definition of 0.2.0 and fixes the canonical order in which writers emit a document: `manifest.timelines` by id; at every depth `children` by offset, then id; `conversion_maps` by id; `regions` by start, end, name; `breaks` by coordinate and `jumps` by from and to coordinate, each then by canonical JSON text; `markers` by name. Coordinates compare by exact value, strings by Unicode code point. Readers accept any order.
- One standard writer per package, `dumps`: canonical order, two-space indentation, a final newline, UTF-8 with characters unescaped except `"`, `\` and control characters, every float spelled as Python's `repr` and every integer without a decimal point or exponent. Both packages write the same document as the same bytes. Python adds `canonical_order` and `canonical_json`; the npm package adds `canonicalOrder`, `canonicalJson` and `compactJson`.
- A lossless JSON reader in the npm package: `parseJson` keeps integers beyond 2^53 as `bigint`, integral floats as `JsonFloat`, and the written order of array-index keys; `parse` reads and validates a document. Types `Json`, `JsonNumber`, `Lossless` and guards `isJsonFloat`, `isJsonObject`.
- The 0.2.0 to 0.2.1 migration in both packages, which validates the document at 0.2.1 and puts it in canonical order, pinned by a fixture pair.
- Golden fixtures for 0.2.1 written in canonical order by the standard writer, and the 34 rejection cases at 0.2.1.

### Changed

- Each migration returns the document declaring its own target version; `migrate` no longer stamps the version after each step.
- The npm `validate` and `migrate` accept values read by `parseJson`.

## [0.2.0] - 2026-10-10

### Added

- Schema 0.2.0 specifies conversion maps, regions, flow control, and measure maps while retaining an opaque metric hierarchy.
- A measure map is the Measure Map standard's compressed row array. A row is the standard's Measure plus two TimeSkeleton extensions: the integer `volta`, which carries no structural constraint, and `offset_within_measure`, the strictly positive position in quarter notes at which a row begins inside its nominal measure (an anacrusis, or one constituent of a split measure). An absent `offset_within_measure` means 0; a row never states 0.
- Row numbers are bounded: `actual_length` and a non-null `nominal_length` are strictly positive (`NumberPositive`), `qstamp` is non-negative (`NumberNonnegative`); each is a JSON number or an exact Fraction pair.
- A measure map is admitted only on a timeline whose `unit` is `quarters`; any other timeline states `measure_map: null`.
- A `MetricalPositionMap` holds its meter map once, as `meter_map`, and names the beat map derived from it by `beat_map_id`; it carries no `maps` or `names`.
- The 0.1.0 to 0.2.0 migration rewrites the members 0.1.0 left opaque in the shapes timetoalign wrote at 0.1.0: a tagged-measure `measure_map` becomes compressed rows whose `next` holds row IDs, and a `MetricalPositionMap` at any depth of the conversion maps takes the 0.2.0 form. A member whose shape the migration does not know raises `MigrationError` (exported by both packages) at that member's path, and a migrated document satisfies 0.2.0.
- Both validators report a violation under one path rule: among the diagnostic leaves of every violation, the one with the deepest instance path, ties going to the first reported; a discriminated `oneOf` contributes only the candidate whose tag `const` equals the instance's tag. The shared rejection fixtures pin the path of every case in both packages.
- Golden map, flow-control, and corpus fixtures, 34 shared rejection cases, and a populated 0.1.0 to 0.2.0 migration fixture pair.
- Version-aware validators and migration support in both packages.
- The release workflow runs the Python lint, format check, and tests before building, as it already did for the npm package.
- The 0.1.0 TimeSkeleton JSON Schema for eventless structural musical timelines.
- Nine golden fixtures emitted by timetoalign, including all six timeline classes, nested timelines, regions, and an empty document.
- The `timeskeleton` Python package with schema resources, validation, migrations, and fixture helpers.
- The `@timetoalign/timeskeleton` npm package with generated TypeScript types, validation, and migrations.
- Continuous integration, version consistency checks, fixture emission, and OIDC trusted publishing for both packages.
- MADR decision records for format, tooling, packaging, validation, generation, and release choices.
