# Changelog

Release entries are written by release-please from the Conventional Commits since the previous release.

## [0.2.1](https://github.com/TimeToAlign/timeskeleton/compare/v0.2.0...v0.2.1) (2026-10-10)


### Features

* add schema 0.2.1 with a canonical order and a standard writer ([e0dbd3a](https://github.com/TimeToAlign/timeskeleton/commit/e0dbd3aae8a41fe2e302b90af3f4c81df4f6acba))


### Continuous Integration

* release through release-please and publish from the release workflow ([579e004](https://github.com/TimeToAlign/timeskeleton/commit/579e00449efb105e21e91e99892287ddabf277f2))

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
