# Test strategy for the `timeskeleton` Python package

This suite proves the public contract of schema 0.3.0, and of the geometry
schema of 0.3.0, while retaining coverage for every supported published
version.

## What the package promises

1. Every bundled fixture for every version in `SUPPORTED_VERSIONS` validates
   against the schema declared by that fixture.
2. Conversion-map, compressed measure-map row, flow-control, region and
   graphical-block definitions reject every shared case in
   `fixtures/rejections/<version>/` at the exact stored path (the 0.2.1 cases
   are the 0.2.0 cases, each change applied to the 0.2.1 fixture it was made
   on; the 0.3.0 cases are the 0.2.1 cases declaring 0.3.0, plus the cases of
   the graphical block).
3. Each migration step reproduces the shared `after.json` of its pair byte for
   byte and yields a valid document at its target version; the 0.1.0 to 0.2.0
   step refuses every member whose shape it does not know at that member's
   path; the 0.2.0 to 0.2.1 step writes the canonical order; `migrate` copies
   all latest-version documents unchanged.
4. Schema and fixture accessors resolve package data independently of the
   current working directory, including migration and rejection paths.
5. Every golden geometry validates against the geometry schema of its
   version, is written by the standard writer, and its frames are
   consistent; the geometry schema rejects every shared
   case in `fixtures/<version>/geometry-rejections/` at the stored path.
6. Generated validation errors expose paths as tuples of object keys and array
   indices and render them as JSON pointers.

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

## Schema 0.3.0: the graphical block and the geometry

0.3.0 keeps every definition of 0.2.1 and adds the optional `graphical`
member, the style rules of containers: `{"styles": [rule, ...],
"timelines": {"<timeline id>": [rule, ...]}}`, both optional; a rule
`{"select", "set"}`; the selector closed over `element` (eight element
types), `domain`, `modality` and a non-empty `ids` list (no `kind`, no
`timeline`: a timeline is selected by its container); the properties closed
over `colour` (`#RRGGBB`, upper case), `line_pattern`, `visible`, `side`,
`show_length` and `show_projected_coordinates`, with at least one property
per rule. What proves it:

- **The schema is 0.2.1 plus the block.** Deleting the `graphical` member and
  the six definitions it introduces (`Graphical`, `StyleRules`, `StyleRule`,
  `StyleSelector`, `ElementType`, `StyleProperties`, and nothing else) and
  restoring the 0.2.1 identifier, version constant and description gives the
  0.2.1 schema exactly. The members and enumerations of the block are stated
  literally.
- **The fixtures are the library's.** `fixtures/0.3.0/` holds the sixteen
  documents of 0.2.1, each byte-equal to its 0.2.1 counterpart but for the
  declared version and `meta.generator` (proven by comparing the texts with
  those two lines substituted), plus `bare`, `contiguous`, `map` and `styled`:
  twenty documents. `styled` is the only one carrying a `graphical` block, and
  its rules (four of the document, five of the `score` container, one of
  `b`, one of `perf`) are stated literally.
- **Rejections.** The 45 cases of `fixtures/rejections/0.3.0/` are the 34 of
  0.2.1 declaring 0.3.0 and eleven cases of the block, each one change to
  `styled.json`: an unknown member of the block (`#/graphical`), a timeline
  container that is no list (that container), a rule without `set` (the
  rule), an unknown property `color` (the `set` object), an empty `set` (the
  `set` object), the element type `segment` (the `element`), a selector with
  the removed member `kind` (the selector), a selector with the removed member
  `timeline` (the selector), an empty `ids` list (the list), a lower-case
  colour in a timeline container (the `colour`) and the side `left` (the
  `side`). Both validators report each stored path.
- **The migration declares 0.3.0 and nothing else.**
  `fixtures/migrations/0.2.1-to-0.3.0/before.json` is the 0.2.1 document of the
  0.2.0 to 0.2.1 pair (`after.json` there); `after.json` differs from it in
  the one line `"schema_version": "0.3.0"`, which the test states by building
  the expected text from `before.json` with that substitution. The step
  validates against 0.3.0, so a 0.2.1 document carrying a member 0.3.0 does
  not know (an unknown break `control_type`) is refused at that member's path
  with `no 0.3.0 shape: `.

The geometry schema (`schema/geometry-0.3.0.schema.json`, specified in
`docs/geometry.md`) refers to the document schema of its version for
`LinearMap`, `Number` and `Fraction`. What proves it:

- **Every golden geometry validates**, and its text is the standard writer's
  (`dumps(json.loads(text)) == text`).
- **The frames are consistent.** Each block's `frame` holds the name
  column at offset 0 and the plot area at the offset equal to the name
  column's length, and its length is the sum of the two lengths (exactly; for
  a float frame, as the float sum); the placement maps into `number`.
- **Rejections.** `fixtures/0.3.0/geometry-rejections/` holds cases written by
  hand, each one change to a golden geometry, with the path both validators
  report: a frame carrying a timeline member (`unit`), a frame extent whose
  offset is a string, a known primitive with an unknown member, a label
  anchor TikZ does not have, a vertical position written as a float, and a
  block whose `rows.max` is negative. A primitive of an unknown kind is not rejected: the union of
  primitives is open.
- **The figures are well formed.** Every golden `figure.svg` parses with the
  standard library's `xml.etree.ElementTree` and its root is the SVG element
  (the figures' bytes are pinned by the TimeLineEditor writers, which emit
  them, and their TikZ compiles there under LuaLaTeX).
- **The specimens are the documents.** The golden geometry directories are
  named exactly as the twenty document fixtures of 0.3.0.

## Versions

The fixture helpers default to `SCHEMA_VERSION`; only the tests that pin the
published version itself spell it.

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
