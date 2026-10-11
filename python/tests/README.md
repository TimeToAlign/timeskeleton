# Test strategy for the `timeskeleton` Python package

This suite proves the draft public contract of schema 0.4.0.

## What the package promises

1. Every bundled fixture validates against the schema.
2. The schema rejects every shared case in `fixtures/rejections/0.4.0/` at the
   exact stored path; all 50 cases fail, including a manifest without its
   one required `timeline`. Every case declares `"0.4.0"` except two:
   `meta_schema_version_unknown` declares the unknown version `"9.9.9"`, and
   `root_missing_meta` has no `meta` to declare one
   (`test_every_0_4_0_rejection_declares_0_4_0_except_two`).
3. A manifest declaring any other version (`"0.3.0"`, `"0.1.0"`, `"1.0.0"`,
   each made from `bare.json`) is rejected through the same error, a
   `SchemaValidationError` at `meta.schema_version`.
4. Schema, fixture and font accessors resolve package data independently of
   the current working directory.
5. Validation errors expose paths as tuples of object keys and array indices
   and render them as JSON pointers.
6. Every fixture and every rejection case is reproduced byte for byte by the
   standard writer.

## One path rule for both validators

Among the diagnostic leaves of every violation, a validator reports the one
with the deepest instance path, ties going to the first reported. A
discriminated `oneOf` contributes only the candidate whose tag `const` equals
the instance's tag value (resolved through `$ref` where the candidate is a
reference), and is itself the reported error when no candidate carries that
value; the candidate is never chosen by its position. Both suites assert the
stored path of every shared rejection, so the two validators report the same
path for each. The measure-map rejections pin the rule where it matters: a
negative `actual_length` (`-1`) reports the row member itself, a negative
`qstamp` pair (`[-1, 2]`) reports its numerator (index 0), a measure map on a
`pixels` timeline reports `measure_map`, a `MetricalPositionMap` carrying the
redundant `maps` and `names` reports the map, and a row stating
`offset_within_measure: 0` or the unknown key `offset` reports the offending
row member or row.

## The canonical order

Every collection of a manifest whose order carries no meaning has one order,
so that equal values are equal text: at every depth, `children` by offset,
then id; `conversion_maps` by id; `regions` by start, then end, then name;
flow-control `breaks` by coordinate, then canonical JSON text; `jumps` by from
coordinate, then to coordinate, then canonical JSON text; `markers` by name.
Coordinates compare by exact numeric value, never by their JSON spelling;
strings by Unicode code point, never by UTF-16 code unit; the canonical JSON
text of an entry has its object keys sorted by code point and no whitespace.
Nothing else moves. What proves it, asserted in both packages with the same
expected values:

- **It is the library's order.** Every fixture is written by timetoalign
  through the fixture script, which fails unless the library's own order is
  that of the standard writer, and every fixture is reproduced byte for byte
  by `dumps`.
- **Every tie, spelled out.** The `flow_control` fixture is extended with
  entries that tie at each level of every key, in an order that is not
  canonical, and the expected sequence of ids, names and labels is stated
  literally: offsets and region bounds where numeric order and text order
  disagree (`[5, 8]` before `[2, 3]`), children tied on offset (id decides)
  with nested children (the order applies at every depth: `b`, `a`, `m`, `z`
  and inside `z` `x`, `y`), regions tied on start and on start and end (`d`,
  `c`, `a`, `b`), breaks tied on coordinate and jumps tied on both coordinates
  (canonical JSON text decides: `early`, `Fine`, `always`; `early`, `short`,
  `DaCapo`, `Repeat`), and ids and names where code point order and UTF-16
  order disagree (`"ﬀ"`, U+FB00, before `"😀"`, U+1F600, whose UTF-16 lead
  unit is 0xD83D: maps `B`, `a`, `b`, `ﬀ`, `😀`; markers `Coda`,
  `repeat-start`, `é`, `ﬀ`, `😀`). The ordered result validates.
- **One canonical JSON text in both languages.** A literal value with nested
  objects and non-ASCII keys has one expected text in both suites, and the
  JavaScript text of every break and jump entry of every fixture (eight)
  equals the text Python's `json.dumps(entry, sort_keys=True,
  separators=(",", ":"), ensure_ascii=False)` writes for the same file.
- **Only the manifest moves.** `canonical_order` returns a copy and leaves
  its input unchanged; a value without a top-level `timeline` is copied as it
  is.

## The standard writer and lossless reading

Both packages export `dumps` (canonical order, then two-space indentation, a
final newline, characters unescaped except `"`, `\` and control characters,
every float spelled as Python's `repr`, every integer without a decimal point)
and `canonical_order` / `canonicalOrder`. They must write the same value as
the same bytes. What proves it:

- **Every standard file round-trips.** Each of the 23 fixtures and 50
  rejection cases (73 files) is reproduced byte for byte by
  `dumps(json.loads(text))` in Python and by `dumps(parseJson(text))` in
  JavaScript. `corpus_score_ms3` carries `→` and float-axis fixtures carry
  `6.0`, so neither the escaping nor the float spelling can be wrong without
  a failure.
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

## One fixture per structure

A fixture earns its place by a combination of structure no other fixture
has. The **structural signature** of a manifest is its timeline tree, where
each timeline contributes its `class`, its `locked`, the `type` of each of
its conversion maps in canonical order, the numbers of its `regions` and of
its flow-control `breaks`, `jumps` and `markers`, and the signatures of its
children in canonical order; plus the manifest's `graphical` block as
canonical JSON, or its absence. Values, ids, names, units, lengths and
offsets take no part. What proves it:

- **No two fixtures share a signature.** The test computes every fixture's
  signature from its JSON file, with its own code rather than the fixture
  script's, and requires 23 distinct signatures for the 23 fixtures. A fixture
  that repeats another's combination, as each corpus performance timeline
  repeated the audio or the sample-map fixture, fails it.
- **The fixture set is stated literally.** The exact list of the 23 file
  names; of the parangonar corpus only `corpus_parangonar_parangonada__score_dlt1`
  (a `DiscreteLogicalTimeline` with a `LinearMap`) remains.

## The graphical block

The optional `graphical` block is the one of `docs/drawing.md` section 2:
`{"styles": {name: declaration}, "statements": [statement, ...]}`, both
optional; a statement `{"select", "set"}` whose `set` is a declaration or a
style name; the selector closed over `element` (the ten element types),
`ids` (a non-empty list of unique addresses), `domain`, `modality`, `class`
(the six timeline classes and the 21 conversion-map types the schema
defines) and `within`; the declaration closed over the eleven presentation
properties `stroke`, `stroke-width`, `stroke-dasharray`, `fill`, `opacity`,
`font-size`, `rx`, `display`, `side`, `content` and `max-width`. What proves it:

- **The vocabulary is stated literally.** The members, enumerations,
  patterns and bounds of `Graphical`, `Statement`, `Selector`, `ElementType`,
  `Paint` and `Declaration`, the `class` enumeration as the timeline classes
  followed by every `type` constant of a conversion-map definition. The
  manifest's members are `meta`, `timeline` and `graphical`, the first two
  required, no other admitted.
- **The styled fixtures.** `styled__score.json` and `styled__perf.json` are
  the only manifests carrying a block, composed by the fixture script; their
  styles and statements are stated literally in the test (twenty-one and five
  statements). They exercise a named style, a statement naming it, a `class`
  selector naming a timeline class and one naming a map type, `ids`,
  `within` at depth 1 and at depth 2, `element`, `domain` and `modality`,
  two statements of one list setting the same property on the same element,
  and every presentation property with a valid value. In `styled__score`
  every drawn element (the root's line, the line of child `b`, the map, the
  brace, the jump and both wedges) and every text (both row names, both
  wedge labels, the region label and the jump label) is visible and
  resolves, under the cascade of `docs/drawing.md` with its defaults, to a
  colour no other of them has. The test resolves those thirteen colours with
  its own small implementation of the cascade's ranking over the fixture's
  statements and compares them with a literal table of distinct colours.
  Each is set by a statement of the manifest, which outranks every default,
  so the resolution needs no defaults; an item no statement of the manifest
  colours fails the test. `content` is set
  by one statement, whose selector is `ids: ["score/name"]`; no statement
  sets `stroke-width` 0, `opacity` below 0.5, or `display: none` other than
  the one hiding child `a`.
- **Rejections.** Fourteen cases of `fixtures/rejections/0.4.0/`, eight of them
  one change to `styled__score.json`, six one change to `bare.json`, with the path both validators report: an unknown
  selector member `kind` (the selector), the element type `segment` (the
  `element`), an empty `ids` list (the list), an unknown property `colour`
  (the `set`), a lower-case `stroke` (the `stroke`), the dash array `"3,3"`
  (the `stroke-dasharray`), `opacity` 1.5 (the `opacity`) and a `set` that is
  the number 5 (the `set`); plus a removed `projection` element and
  `show-projections` property, zero `max-width`, non-string `content`, an id
  holding a tab and a `children` key holding a newline.
- **Property bounds.** Exact validation tests accept `stroke-width` and `rx`
  at zero, `opacity` at both endpoints, positive `font-size` and `max-width`,
  `content` text and both forms of `stroke-dasharray`; they reject a negative
  width and radius, opacity outside either endpoint, zero font size and maximum
  width, non-text content and malformed dash text at the exact property path.
- **Identifiers.** Every schema member named `id` and every `children` key has
  the control-character exclusion literally. Shared cases reject a tab in an
  id and a newline in a child key, while names remain unrestricted.

## Completing missing styles

`complete_styles` returns a new graphical block and never changes its input.
Every distinct style name named by a statement but absent from `styles` is
added as an empty declaration, and the returned missing names are sorted by
Unicode code point. With missing names it emits exactly one
`MissingStyleWarning` whose exact text names all of them; with none it emits no
warning. Tests pin an absent `styles` member, duplicate references, code-point
ordering (`ﬀ` before `😀`), preservation of existing declarations and input
independence. When a block has some styles and lacks others, the completed
`styles` holds the existing declarations and an empty one for each missing
name, while the input's `styles` keeps exactly its existing declarations.

## The font

`docs/drawing.md` measures every text from the advance widths of DejaVu Sans
2.37, the file `ttf/DejaVuSans.ttf` of the upstream release zip
`dejavu-fonts-ttf-2.37.zip`. What proves the bundled copy and its metrics:

- **The file is the release's.** The SHA-256 of `font_path()` is
  `7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954`, and
  the licence file lies beside it.
- **The metrics are that file's.** `font_metrics()` has exactly the members
  `units_per_em`, `ascender`, `descender`, `fallback` and `advances`, with
  the values 2048, 1901, 483 (the `hhea` descender as a positive depth) and
  1229 (the advance of glyph 0); `advances` holds 5918 code points, keyed in
  ascending numeric order, among them `"9833"` (♩) 966, `"48"` ("0") 1303
  and `"32"` (space) 651. These values were read with fontTools from the
  release file; the metrics file is written by `dumps`, so `dumps` of the
  parsed file reproduces its text.
- **The extraction refuses another file.** The extraction script's
  `metrics()` raises `SystemExit` naming both digests for a file whose
  SHA-256 differs (a copy of the font with one byte appended, in a temporary
  directory), and reproduces the shipped metrics file byte for byte from the
  bundled font. This test runs where the development dependency fontTools
  is installed.
- **Access is independent of the working directory.** After changing to an
  unrelated temporary directory, `font_path()` still names the bundled font
  and `font_metrics()` still returns the pinned metrics.

## Integer boundaries

The library bounds integers to signed int64, but the JSON Schema does not
repeat that bound because it cannot express it portably. There is no
decimal-string representation. Python preserves integers exactly: values
whose integer length is `9007199254740993` (2^53 + 1) or
`9223372036854775807` (2^63 - 1) validate and serialize back to the same
integer.

## Generated artifacts

The package tests load the checked-in schema and fixtures that the build
bundles. JavaScript separately proves its generated TypeScript files do not
drift from a fresh generator run.

## Hermeticity

Tests obtain fixtures through package accessors, never relative paths. They use
no network and no shared mutable input; the one file a test writes lies in
its own temporary directory.
