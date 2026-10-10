# Test strategy for the `@timetoalign/timeskeleton` npm package

This suite proves the public contract of schema 0.3.0 and of its geometry
schema, while retaining coverage for every supported published version.

## What the package promises

1. Every bundled fixture for every version in `SUPPORTED_VERSIONS` validates
   against the schema declared by that fixture.
2. Conversion-map, compressed measure-map row, flow-control, and region definitions reject every
   shared case in `fixtures/rejections/<version>/` at the exact stored path
   (the 0.2.1 cases are the 0.2.0 cases, each change applied to the 0.2.1
   fixture it was made on; the 0.3.0 cases are the 0.2.1 cases declaring
   0.3.0 plus eleven cases of the graphical block, listed in the Python suite's
   README).
3. Each migration step reproduces the shared `after.json` of its pair byte for
   byte and yields a valid document at its target version; the 0.1.0 to 0.2.0
   step refuses every member whose shape it does not know at that member's
   path; the 0.2.0 to 0.2.1 step writes the canonical order; `migrate` copies
   all latest-version documents unchanged.
4. Generated errors expose paths as object keys and numeric array indices.
5. The checked-in generated schema and type sources equal a fresh generator
   run, and the generated schema bundle contains every supported version.
   Schema files are ordered by their parsed version, so `0.10.0` follows
   `0.2.0` and the latest version is the numerically highest one; a list
   mixing `0.10.0`, `0.2.0`, `1.0.0` and a non-schema file pins that order.
   The bundle also holds every geometry schema (`geometrySchemas`, keyed by
   version, `geometrySchema` the latest), and the generated types include the
   geometry's (`Geometry`, `Block`, `Primitive` as the union of the eight
   primitive types, ...), generated with the document's in one file.
6. `validateGeometry` accepts every golden geometry
   (`fixtures/<version>/geometry/<name>/geometry.json`, read with
   `parseJson`), whose text `dumps` reproduces byte for byte; it rejects every
   shared case of `fixtures/<version>/geometry-rejections/` at the stored
   path, the same path the Python validator reports, including a case whose
   violation lies inside a definition of the document schema the geometry
   schema refers to (a frame extent's offset, a `Number`); and it accepts a
   primitive of an unknown kind, since the union of primitives is open.
7. The 0.2.1 to 0.3.0 migration declares 0.3.0 and changes nothing else: its
   `after.json` is `before.json` with the one version line substituted, and a
   0.2.1 document with an unknown break `control_type` is refused at that
   member's path with `no 0.3.0 shape: `.

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

## The 0.2.0 to 0.2.1 migration: canonical order

0.2.1 has the definitions of 0.2.0 and fixes the order of every collection
whose order carries no meaning, so that equal documents are equal text:
`manifest.timelines` by id; at every depth, `children` by offset, then id;
`conversion_maps` by id; `regions` by start, then end, then name; flow-control
`breaks` by coordinate, then canonical JSON text; `jumps` by from coordinate,
then to coordinate, then canonical JSON text; `markers` by name. Coordinates
compare by exact numeric value, never by their JSON spelling; strings by
Unicode code point, never by UTF-16 code unit; the canonical JSON text of an
entry has its object keys sorted by code point and no whitespace. Nothing else
moves. The migration is proven correct by four independent arguments, each
asserted in both packages with the same expected values:

- **It is the library's order.** Every 0.2.0 fixture, migrated and written by
  the standard writer, is byte-equal to the 0.2.1 fixture of the same name
  that timetoalign emitted, `meta.generator` aside; the fixture script fails
  unless the library's own order is that of the standard writer. Three of
  the sixteen 0.2.0 documents were not canonical (`conversion_maps`:
  timelines and maps; `corpus_parangonar_parangonada`: timelines;
  `corpus_score_ms3`: children and markers), so the equality is not vacuous.
- **The pair.** `fixtures/migrations/0.2.0-to-0.2.1/before.json` was written
  by timetoalign at 0.2.0 (`meta.generator`), when the library still wrote
  insertion order, from a construction that leaves every collection out of
  canonical order: timelines `score`, `perf`; children `z`, `m` (both at 1),
  `b` (5/8), `a` (2/3), and inside `z` the children `y` (1), `x` (0); maps
  `shift`, `scale`, `label`; regions `verse` (2 to 6), `intro` (2 to 4),
  `alpha` (2 to 6), `coda` (5/8 to 2/3); breaks `early` (5/8), `section`,
  `fine` (both at 12); jumps `first` (5/8 to 0), `repeat` (8 to 2), `inner`
  (8 to 2/3), `segno` (8 to 2, a `dal_segno`); markers `segno`, `coda`,
  `Fine`; and on the `ticks` timeline regions `late` (10 to 20), `early`
  (9 to 10). The step must give `after.json` byte for byte, and the expected
  sequences are stated literally: `perf`, `score`; `b`, `a`, `m`, `z`; `x`,
  `y`; `label`, `scale`, `shift`; `coda`, `intro`, `alpha`, `verse`; `early`,
  `fine`, `section`; `first`, `inner`, `segno`, `repeat`; `Fine`, `coda`,
  `segno`; `early`, `late`. No frozen 0.2.0 fixture misorders every
  collection (`conversion_maps` misorders timelines and maps,
  `corpus_score_ms3` children and markers, `corpus_parangonar_parangonada`
  timelines only), and those three are pinned by the first argument anyway.
- **Every tie, spelled out.** A loaded 0.2.0 fixture is extended with entries
  that tie at each level of every key, in an order that is not canonical,
  and the expected sequence of ids, names and labels is stated literally:
  offsets and region bounds where numeric order and text order disagree
  (`[5, 8]` before `[2, 3]`), children tied on offset (id decides) with nested
  children (the order applies at every depth), regions tied on start and on
  start and end, breaks tied on coordinate and jumps tied on both coordinates
  (canonical JSON text decides), and ids and names where code point order and
  UTF-16 order disagree (`"ﬀ"`, U+FB00, before `"😀"`, U+1F600, whose UTF-16
  lead unit is 0xD83D).
- **One canonical JSON text in both languages.** A literal value with nested
  objects and non-ASCII keys has one expected text in both suites, and the
  JavaScript text of every break and jump entry of every 0.2.1 fixture equals
  the text Python's `json.dumps(entry, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False)` writes for the same file (the JavaScript suite runs
  `python3` on the fixture files).

## The standard writer and lossless reading

Both packages export `dumps` (canonical order, then two-space indentation, a
final newline, characters unescaped except `"`, `\` and control characters,
every float spelled as Python's `repr`, every integer without a decimal point)
and `canonical_order` / `canonicalOrder`. They must write the same document as
the same bytes. What proves it:

- **Every standard file round-trips.** Each of the 16 fixtures and 34
  rejections of 0.2.1 and the 0.2.0 to 0.2.1 `after.json` (51 files) is
  reproduced byte for byte by `dumps(json.loads(text))` in Python and by
  `dumps(parse(text))` in JavaScript. `corpus_score_ms3` carries `→` and
  float-axis fixtures carry `6.0`, so neither the escaping nor the float
  spelling can be wrong without a failure.
- **A shared corpus.** One literal JSON text, identical in both suites, holds
  `0.1`, `2.0`, `1e-07`, `1e+16`, `123456789012345678`, `-0.0`, `5e-324`,
  `1.7976931348623157e+308`, `1E5`, `1.50`, `-0`, `100`, the fixed and
  exponent boundaries `0.0001`, `1e-05` and `1000000000000000.0`, `é`, an
  astral character, `ﬀ` and a string with a quote, a backslash and control
  characters; both writers must give one literal expected text (`1E5` becomes
  `100000.0`, `1.50` becomes `1.5`, `-0` the integer `0`).
- **Python's `repr` itself.** The JavaScript suite spells 2000 doubles from a
  fixed pseudo-random sequence (half raw bit patterns, covering every exponent
  and subnormals; half scattered around the switch between fixed and exponent
  notation) and requires exactly the strings `python3` gives with `repr` for
  the same bit patterns. Moving either notation threshold by one fails it.
- **Refusals.** Both writers and both canonical JSON texts refuse a NaN or an
  infinity and a string or key with a lone surrogate (UTF-8 cannot encode
  one); a collection whose ordering members are missing is refused rather
  than written in some order.

The step validates its input against 0.2.1 before it reorders, since order
does not affect validity: a 0.2.0 document with an unknown break
`control_type` is refused as a `MigrationError` at that member's path in the
input. A migration step returns the document declaring its target version;
each pair is asserted against the one step it pins, and the whole chain from
every supported version must give a valid latest document.

## Versions

The fixture helpers default to `SCHEMA_VERSION`; only the tests that pin the
published version itself spell it.

## Integer boundaries

The library bounds integers to signed int64, but the JSON Schema does not
repeat that bound because it cannot express it portably. There is no
decimal-string representation. `JSON.parse("9007199254740993")` produces
`9007199254740992`; the suite pins that, and pins that `parseJson` reads the exact
`9007199254740993n`. Documents whose integer length is `9007199254740993` or
`9223372036854775807` validate, migrate and are written back by `dumps` with
the same integer.

## Lossless reading in JavaScript

`parseJson` reads any JSON text into the smallest representation that loses nothing; `parse` is `parseJson` followed by `validate`. A safe
integer and a float with a fractional part are plain numbers, as `JSON.parse`
gives them; only what a number cannot hold is marked: an integer beyond
`Number.MAX_SAFE_INTEGER` is a `bigint`, and an integral float (`2.0`, `1e+16`,
`-0.0`) is a frozen `JsonFloat` holding its value. The text `-0` is the integer
0, as in Python. Objects keep the written order of their keys, which
`JSON.parse` cannot for array-index keys (`"10"`, `"2"`), and `dumps` honours
it; a canonical-order object holding such keys is written in code-point order.
The generated types are untouched: `Lossless<T>` maps them, and `validate` and
`migrate` accept either form. The tests pin each case (`0.5`, `2.0`,
`123456789012345678`, `-0`, `-0.0`, `1E5`), key order surviving a round trip,
malformed text refused as a `SyntaxError`, and `1e400` (beyond a double)
refused as a `RangeError`, where Python reads an infinity it cannot write.
Every fixture is also validated as `JSON.parse` reads it, and every rejection
is refused at the same path in both readings and by `parse`. `JsonFloat` is a
frozen class, told apart by `instanceof` or `isJsonFloat`, and `isJsonObject`
is false for it.

`compactJson` writes a value without whitespace in its own key order (the
written order of array-index keys included), for storing single values: for
every value nested anywhere in every 0.2.1 fixture, writing, reading back and
writing again gives the same text, and for every 0.2.1 fixture and rejection
its text equals Python's `json.dumps(value, separators=(",", ":"),
ensure_ascii=False)` (the suite runs `python3`). A document read by `parse`,
migrated by `migrate` and written by `dumps` must be byte-identical to the
Python migration's output: the shared `after.json` for the pair, and for every
0.2.0 fixture the 0.2.1 fixture of the same name (generator aside), which the
Python suite asserts its own migration writes.

## Hermeticity

Tests read the repository fixtures and schemas through shared helpers. They use
no network or shared mutable input.
