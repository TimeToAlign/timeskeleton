# Test strategy for the `@timetoalign/timeskeleton` npm package

This suite proves the public contract of schema 0.2.0 while retaining coverage
for every supported published version.

## What the package promises

1. Every bundled fixture for every version in `SUPPORTED_VERSIONS` validates
   against the schema declared by that fixture.
2. Conversion-map, compressed measure-map row, flow-control, and region definitions reject every
   shared case in `fixtures/rejections/0.2.0/` at the exact stored path.
3. The 0.1.0 to 0.2.0 migration is pure, reproduces the shared `after.json`,
   and all latest-version documents migrate to independent equal copies.
4. Generated errors expose paths as object keys and numeric array indices.
5. The checked-in generated schema and type sources equal a fresh generator
   run, and the generated schema bundle contains every supported version.

## Integer boundaries

The library bounds integers to signed int64, but the JSON Schema does not
repeat that bound because it cannot express it portably. There is no
decimal-string representation. JavaScript consumers have a known limitation:
`JSON.parse("9007199254740993")` produces `9007199254740992`, so consumers that
need exact integers above 2^53 must parse documents with a BigInt-aware parser.
The suite pins that native `JSON.parse` behavior explicitly.

## Hermeticity

Tests read the repository fixtures and schemas through shared helpers. They use
no network or shared mutable input.
