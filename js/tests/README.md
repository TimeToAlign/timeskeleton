# Test strategy for the `@timetoalign/timeskeleton` npm package

This suite proves the public contract of schema 0.2.0 while retaining coverage
for every supported published version.

## What the package promises

1. Every bundled fixture for every version in `SUPPORTED_VERSIONS` validates
   against the schema declared by that fixture.
2. Conversion-map, compressed measure-map row, flow-control, and region definitions reject every
   shared case in `fixtures/rejections/0.2.0/` at the exact stored path.
3. The 0.1.0 to 0.2.0 migration is pure, reproduces the shared `after.json`
   byte for byte, yields a valid 0.2.0 document, refuses every member whose
   shape it does not know at that member's path, and copies all latest-version
   documents unchanged.
4. Generated errors expose paths as object keys and numeric array indices.
5. The checked-in generated schema and type sources equal a fresh generator
   run, and the generated schema bundle contains every supported version.
   Schema files are ordered by their parsed version, so `0.10.0` follows
   `0.2.0` and the latest version is the numerically highest one; a list
   mixing `0.10.0`, `0.2.0`, `1.0.0` and a non-schema file pins that order.

## One path rule for both validators

Among the diagnostic leaves of every violation, a validator reports the one
with the deepest instance path, ties going to the first reported. A
discriminated `oneOf` contributes only the candidate whose tag `const` equals
the instance's tag value (resolved through `$ref` where the candidate is a
reference), and is itself the reported error when no candidate carries that
value; the candidate is never chosen by its position. Both suites assert the
stored path of every shared rejection, so the two validators report the same
path for each. The rejections added with the measure-map rules pin the rule
where it matters: a negative `actual_length` (`-1`) reports the row member
itself, a negative `qstamp` pair (`[-1, 2]`) reports its numerator (index 0),
a measure map on a `pixels` timeline reports `measure_map`, a
`MetricalPositionMap` carrying the redundant `maps` and `names` reports the
map, and a row stating `offset_within_measure: 0` or the unknown key `offset`
reports the offending row member or row.

## The populated migration pair

`fixtures/migrations/0.1.0-to-0.2.0/before.json` was written by timetoalign at
the commit that emitted 0.1.0 (`meta.generator`), so it holds exactly what
0.1.0 documents hold: a tagged-measure measure map with an anacrusis (a
`MeasureConstituent` at offset 3), a repeat whose last bar names two successors
(`["m2", "m4"]`), a `MetricalPositionMap` with its redundant `maps` and
`names`, a `LinearMap` and a region. The migration must turn the map into four
compressed rows whose successors are row IDs (`["2", "4"]`) and whose first row
carries `offset_within_measure: [3, 1]`, and the position map into `meter_map`
plus `beat_map_id`, leaving every other member untouched. Serializing the result
with the language's standard JSON writer (two-space indent, final newline) must
give `after.json` byte for byte, which both packages assert, and the result must
validate. Refusal is pinned at exact paths: a measure class with no row form
(`SplitRegularMeasure`) at that measure's `class`; a `next` naming an id of no
measure at that `next`; a `MetricalPositionMap` whose `maps` are not the two
derived from `meter_map` at its `maps`; and a conversion map of an unknown type
at that conversion map, through the 0.2.0 schema.

Both packages read the same document text the same way. A `next` holding a
non-string entry (an array) is a `MigrationError` at that `next`, never a type
error, and `count: true` is refused at that `count`, because a boolean is no
integer. A JavaScript reader cannot tell `1.0` from `1`, so an integral JSON
number counts as an integer on both sides: a measure whose `qstamp` is written
`[1.0, 1]` migrates to exactly the shared `after.json`.

## Versions

The fixture helpers default to `SCHEMA_VERSION`; only the tests that pin the
published version itself spell it.

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
