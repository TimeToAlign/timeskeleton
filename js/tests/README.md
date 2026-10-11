# Test strategy for the `@timetoalign/timeskeleton` npm package

This suite proves the draft public contract of schema 0.4.0.

## What the package promises

1. Every bundled fixture validates against the schema, read and validated by
   `parse` and as `JSON.parse` reads it.
2. The schema rejects every shared case in `fixtures/rejections/0.4.0/` at the
   exact stored path, in both readings and through `parse`; all 50 cases
   fail, including a manifest without its one required `timeline`. Every case
   declares `"0.4.0"` except two: `meta_schema_version_unknown` declares the
   unknown version `"9.9.9"`, and `root_missing_meta` has no `meta` to
   declare one (the test "has every 0.4.0 rejection declare 0.4.0 except the
   two without a declaration").
3. A manifest declaring any other version (`"0.3.0"`, `"0.1.0"`, `"1.0.0"`,
   each made from `bare.json`) is rejected through the same error, a
   `SchemaValidationError` at `["meta", "schema_version"]`.
4. Generated errors expose paths as object keys and numeric array indices.
5. The checked-in generated files (`types.ts`, `schema.ts`, `font.ts`) equal a
   fresh generator run, and the generated schema bundle is the schema file.
   Schema files are ordered by their parsed version, so `0.10.0` follows
   `0.9.0` and the latest version is the numerically highest one; a list
   mixing `0.10.0`, `0.9.0`, `1.0.0` and a non-schema file pins that order.
6. The schema's graphical definitions (`Graphical`, `Statement`, `Selector`,
   `ElementType`, `Paint`, `Declaration`) state the vocabulary listed in the
   Python suite's README, literally, as in Python; the manifest's members are
   `meta`, `timeline` and `graphical`, the first two required, no other
   admitted. The styled fixtures pin a style map, a style-name `set`, a
   `class` selector and valid numeric and dash properties. Exact validation
   cases accept every boundary stated there and reject values outside them at
   the property path. Every `id` member and `children` key carries the literal
   control-character exclusion, while timeline names with control characters
   still validate.

## The font

The package bundles the metrics of DejaVu Sans 2.37 (`fontMetrics`, typed
`FontMetrics`, generated into `src/generated/font.ts` from
`fonts/dejavu-sans-2.37.metrics.json`) and ships the TrueType file and its
licence as the subpath `@timetoalign/timeskeleton/fonts/*`. What proves it:
the repository's `fonts/DejaVuSans.ttf` has the SHA-256 of the upstream
release file (`7da195a7…48954`) and its licence lies beside it (8816 bytes);
`package.json` exports `./fonts/*` and lists `fonts` in `files`;
`fontMetrics` has exactly the members `units_per_em`, `ascender`,
`descender`, `fallback`, `advances` with the values 2048, 1901, 483, 1229 and
5918 advances, among them `"9833"` 966, `"48"` 1303 and `"32"` 651 (the same
values the Python suite states); the metrics file is the standard writer's
text, and `dumps(fontMetrics)` reproduces it, so the bundled constant is that
file. The generated module is covered by the drift test of item 5.

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

The order and its proofs are stated in the Python suite's README ("The
canonical order"); this suite asserts the same expected values: the extended
`flow_control` fixture with a tie at every key level is put in the literally
stated order by `canonicalOrder` and still validates; a literal value has one
canonical JSON text; and the text of every break and jump entry of every
fixture (eight) equals Python's `json.dumps(entry, sort_keys=True,
separators=(",", ":"), ensure_ascii=False)` for the same file (the suite runs
`python3` on the fixture files). Marker names that are array-index keys
(`"10"`, `"2"`) are written in code-point order and read back so.
`canonicalOrder` returns a copy, and copies a value without a top-level
`timeline` as it is; a collection it cannot order is refused with a
`TypeError`.

## The standard writer and lossless reading

Both packages export `dumps` (canonical order, then two-space indentation, a
final newline, characters unescaped except `"`, `\` and control characters,
every float spelled as Python's `repr`, every integer without a decimal point)
and `canonical_order` / `canonicalOrder`. They must write the same value as
the same bytes. What proves it:

- **Every standard file round-trips.** Each of the 34 fixtures and 50
  rejection cases (84 files) is reproduced byte for byte by
  `dumps(parseJson(text))`. `corpus_score_ms3` carries `→` and float-axis
  fixtures carry `6.0`, so neither the escaping nor the float spelling can be
  wrong without a failure.
- **A shared corpus.** One literal JSON text, identical in both suites, holds
  `0.1`, `2.0`, `1e-07`, `1e+16`, `123456789012345678`, `-0.0`, `5e-324`,
  `1.7976931348623157e+308`, `1E5`, `1.50`, `-0`, `100`, the fixed and
  exponent boundaries `0.0001`, `1e-05` and `1000000000000000.0`, `é`, an
  astral character, `ﬀ` and a string with a quote, a backslash and control
  characters; both writers must give one literal expected text (`1E5` becomes
  `100000.0`, `1.50` becomes `1.5`, `-0` the integer `0`).
- **Python's `repr` itself.** The suite spells 2000 doubles from a fixed
  pseudo-random sequence (half raw bit patterns, covering every exponent and
  subnormals; half scattered around the switch between fixed and exponent
  notation) and requires exactly the strings `python3` gives with `repr` for
  the same bit patterns. Moving either notation threshold by one fails it.
- **Refusals.** The writer refuses a NaN or an infinity and a string or key
  with a lone surrogate (UTF-8 cannot encode one), as a `RangeError`, and a
  value that is no JSON value (`undefined`) as a `TypeError`.

## Integer boundaries

The library bounds integers to signed int64, but the JSON Schema does not
repeat that bound because it cannot express it portably. There is no
decimal-string representation. `JSON.parse("9007199254740993")` produces
`9007199254740992`; the suite pins that, and pins that `parseJson` reads the
exact `9007199254740993n`. Values whose integer length is `9007199254740993`
or `9223372036854775807` validate and are written back by `dumps`, and read
back by `parseJson`, as the same integer.

## Lossless reading in JavaScript

`parseJson` reads any JSON text into the smallest representation that loses
nothing; `parse` is `parseJson` followed by `validate`. A safe integer and a
float with a fractional part are plain numbers, as `JSON.parse` gives them;
only what a number cannot hold is marked: an integer beyond
`Number.MAX_SAFE_INTEGER` is a `bigint`, and an integral float (`2.0`, `1e+16`,
`-0.0`) is a frozen `JsonFloat` holding its value. The text `-0` is the integer
0, as in Python. Objects keep the written order of their keys, which
`JSON.parse` cannot for array-index keys (`"10"`, `"2"`), and `dumps` honours
it. The generated types are untouched: `Lossless<T>` maps them, and
`validate` accepts either form. The tests pin each case (`0.5`, `2.0`,
`123456789012345678`, `-0`, `-0.0`, `1E5`), key order surviving a round trip,
malformed text refused as a `SyntaxError`, and `1e400` (beyond a double)
refused as a `RangeError`, where Python reads an infinity it cannot write.
`parse` reads `continuous_physical.json` with its child offsets `0.5` and the
`JsonFloat` 6. `JsonFloat` is a frozen class, told apart by `instanceof` or
`isJsonFloat`, and `isJsonObject` is false for it.

`compactJson` writes a value without whitespace in its own key order (the
written order of array-index keys included), for storing single values: for
every value nested anywhere in every fixture, writing, reading back and
writing again gives the same text, and for every fixture and rejection case
its text equals Python's `json.dumps(value, separators=(",", ":"),
ensure_ascii=False)` (the suite runs `python3`).

## Completing missing styles

`completeStyles` returns a new graphical block and never changes its input.
Every distinct style name named by a statement but absent from `styles` is
added as an empty declaration, and `missing` lists those names in Unicode
code-point order. With missing names it calls `console.warn` exactly once with
a message naming all of them, the text of Python's `MissingStyleWarning`; with
none it writes nothing to the console. Tests pin an absent `styles` member,
duplicate references, code-point ordering (`ﬀ` before `😀`), preservation of
existing declarations and input independence. When a block has some styles and
lacks others, the completed `styles` holds the existing declarations and an
empty one for each missing name, while the input's `styles` keeps exactly its
existing declarations.

## Hermeticity

Tests read the repository fixtures and schemas through shared helpers. They use
no network or shared mutable input.
