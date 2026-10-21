# Changelog

Release entries are written by release-please from the Conventional Commits since the previous release.

## [0.7.0](https://github.com/TimeToAlign/timeskeleton/compare/v0.6.0...v0.7.0) (2026-10-21)


### ⚠ BREAKING CHANGES

* **schema:** rename the unit whole_note to whole_notes
* **schema:** model flow control as jump origins, jump targets and flow markers
* **schema:** reduce conversion maps to abstract types over top-level measure maps
* **schema:** read every value by its declared number type
* validate asserts and parse returns the union TimeSkeletonFile instead of TimeSkeletonManifest; schema_path and load_schema take a document name; a value declaring no supported schema version is refused on its meta alone; timeline manifests require is_segment_line.

### Features

* accept a negative child offset, never lock a segment, end unknown length in three chevrons ([0d09322](https://github.com/TimeToAlign/timeskeleton/commit/0d0932217a8d0d0bee939ce23b5a9d71c7af3ddb))
* allow a measure map on a whole_note timeline as on a quarters one ([751bd5d](https://github.com/TimeToAlign/timeskeleton/commit/751bd5df4871f47c3a3ab7b5115cb7e8ad7432ac))
* allow a timeline to be a member of several groups ([28ed36c](https://github.com/TimeToAlign/timeskeleton/commit/28ed36c17c73cf5668de099cc0ee9d7b77029a1f))
* bands as elements of every timeline, ordered in graphical.order ([dbd5fdd](https://github.com/TimeToAlign/timeskeleton/commit/dbd5fdd373122d2c728755616b70e55778d46cc8))
* describe timeline groups and alignment bundles as their own files ([18127fa](https://github.com/TimeToAlign/timeskeleton/commit/18127fa3f71137795345826adc6a284d8c723e71))
* draw groups and bundles, with cards, ancestor lines and segment lines ([2dfbe2f](https://github.com/TimeToAlign/timeskeleton/commit/2dfbe2fc1a9b0a68df134ee663b9586082d2910f))
* give the bundle and group fixtures maps, regions, flow control and segment lines ([0a9d270](https://github.com/TimeToAlign/timeskeleton/commit/0a9d270ff4251a0f4159c8148f06f6821f81bf3f))
* keep requested margins in proportion on a stretch, stretch frames and cards vertically ([3ecece8](https://github.com/TimeToAlign/timeskeleton/commit/3ecece8930c6f5c7d3c0195085ddc175e0f345b4))
* make a container's spacing the gap between its direct contents ([7d9b370](https://github.com/TimeToAlign/timeskeleton/commit/7d9b370ac2fa8f548557a83a567c8db7cc089d7f))
* name flow-control ids by element type; add a shared-member bundle ([9c7daba](https://github.com/TimeToAlign/timeskeleton/commit/9c7daba16cd81a0e9553bb3f6012b5bc79e0f595))
* one manifest shape with complete and minimal forms, open objects and unknown length ([36d0bd3](https://github.com/TimeToAlign/timeskeleton/commit/36d0bd3fce43e0f1efcaef17fb11b7b9f4e695c9))
* place each box item on its own and cascade band orders in drawings ([73f9490](https://github.com/TimeToAlign/timeskeleton/commit/73f949007dc6735601e5cdbfe8ebf268238bafcf))
* refuse a conversion map whose source unit differs from its timeline's unit ([3e455df](https://github.com/TimeToAlign/timeskeleton/commit/3e455dfc5d67b0cca82dd0907f51f7dc6a0c3a9b))
* **schema:** model flow control as jump origins, jump targets and flow markers ([ba2eb92](https://github.com/TimeToAlign/timeskeleton/commit/ba2eb92007e03692f6b8c0250e667787ada128bb))
* **schema:** read every value by its declared number type ([4e484a5](https://github.com/TimeToAlign/timeskeleton/commit/4e484a552cafb5f1ca554040de475e8184e331a9))
* **schema:** reduce conversion maps to abstract types over top-level measure maps ([7e59cf7](https://github.com/TimeToAlign/timeskeleton/commit/7e59cf731dea845f465f35f5a62664f57a6835b1))
* **schema:** rename the unit whole_note to whole_notes ([44e1c95](https://github.com/TimeToAlign/timeskeleton/commit/44e1c95fc3f473cffe5ad9fb739c7dbbd1898dfa))
* share one horizontal layout per box, scale items, size member cards ([21e76ad](https://github.com/TimeToAlign/timeskeleton/commit/21e76ad6ddb6ea9f691198fee2c0086c3435ecee))


### Bug Fixes

* leave a member repeated in one group to the schema ([697d018](https://github.com/TimeToAlign/timeskeleton/commit/697d01867419e3bd24c3c3a278c3062f680f4979))
* refuse a fraction pair written with a float member ([678e315](https://github.com/TimeToAlign/timeskeleton/commit/678e315be93c022627da46bcff13af258bd5dd9c))
* refuse a nested conversion-map ID repeated within its root's tree ([7865aeb](https://github.com/TimeToAlign/timeskeleton/commit/7865aeb3a20f4be61f6eeb9166dbeeef05dea496))
* refuse reserved words as nested conversion-map IDs ([8419468](https://github.com/TimeToAlign/timeskeleton/commit/841946844c510dd568b6c047fad153ac28d38f31))
* **schema:** put the repeat count default on the repeat end only and share the measure-view definition ([584ed83](https://github.com/TimeToAlign/timeskeleton/commit/584ed8311b6352dbc3a9241a90054fa24e7c23b3))

## [0.6.0](https://github.com/TimeToAlign/timeskeleton/compare/v0.5.0...v0.6.0) (2026-10-12)


### Features

* pad vertically stretched drawings and pin text rendering ([ec4ff22](https://github.com/TimeToAlign/timeskeleton/commit/ec4ff22f5a7ff73d9b6642be444def8ff417fad8))


### Bug Fixes

* ship the MIT licence in the npm and Python packages ([63a54b9](https://github.com/TimeToAlign/timeskeleton/commit/63a54b9c038408aefe252e072024a3f2b59d437e))

## [0.5.0](https://github.com/TimeToAlign/timeskeleton/compare/v0.4.0...v0.5.0) (2026-10-11)


### ⚠ BREAKING CHANGES

* manifests declare schema 0.5.0 and carry the ids above; 0.4.0 manifests are not accepted.

### Features

* identify every manifest element and write keys in sorted order ([da8669e](https://github.com/TimeToAlign/timeskeleton/commit/da8669e8bf38a99f5943d7774d6ef2fe5b9b7410))

## [0.4.0](https://github.com/TimeToAlign/timeskeleton/compare/v0.3.0...v0.4.0) (2026-10-11)


### ⚠ BREAKING CHANGES

* specify the drawing and keep only schema 0.4.0
* hold one timeline manifest per file and add split

### Features

* hold one timeline manifest per file and add split ([3b7d6dc](https://github.com/TimeToAlign/timeskeleton/commit/3b7d6dc4ceff6eabf69cddc43d1819d5b73f0f69))
* publish the drawing fixtures and declare version 0.4.0 ([7995bdd](https://github.com/TimeToAlign/timeskeleton/commit/7995bddfba81ae2972a441b2e29a355322a0c9f4))
* specify the drawing and keep only schema 0.4.0 ([cea5130](https://github.com/TimeToAlign/timeskeleton/commit/cea5130549bf5bf11bd7e7dad303625a2809d20e))


### Bug Fixes

* draw C-Map stacks per timeline and place arrow tips as TikZ does ([ab8976f](https://github.com/TimeToAlign/timeskeleton/commit/ab8976f3a9659b9390a53f10b267e31d1a468f39))

## [0.3.0](https://github.com/TimeToAlign/timeskeleton/compare/v0.2.1...v0.3.0) (2026-10-10)


### Features

* add schema 0.3.0 with the graphical block and the geometry specification ([c92e874](https://github.com/TimeToAlign/timeskeleton/commit/c92e87499a14d73118d1c19107412ba395d21426))

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
