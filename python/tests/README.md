# Test strategy for the `timeskeleton` Python package

This suite proves the public contract of schema 0.2.0 while retaining coverage
for every supported published version.

## What the package promises

1. Every bundled fixture for every version in `SUPPORTED_VERSIONS` validates
   against the schema declared by that fixture.
2. Conversion-map, compressed measure-map row, flow-control, and region definitions reject every
   shared case in `fixtures/rejections/0.2.0/` at the exact stored path.
3. The 0.1.0 to 0.2.0 migration is pure, reproduces the shared `after.json`,
   and all latest-version documents migrate to independent equal copies.
4. Schema and fixture accessors resolve package data independently of the
   current working directory, including migration and rejection paths.
5. Generated validation errors expose paths as tuples of object keys and array
   indices and render them as JSON pointers.

## Integer boundaries

The library bounds integers to signed int64, but the JSON Schema does not
repeat that bound because it cannot express it portably. There is no
decimal-string representation. Python preserves integers exactly: documents
whose integer length is `9007199254740993` (2^53 + 1) or
`9223372036854775807` (2^63 - 1) validate, migrate, and serialize back to the
same integer.

## Generated artifacts

The package tests load the checked-in schemas and fixtures that the build
bundles. JavaScript separately proves its generated TypeScript files do not
drift from a fresh generator run.

## Hermeticity

Tests obtain fixtures through package accessors, never relative paths. They use
no network, temporary files, or shared mutable input.
