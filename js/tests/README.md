# Test strategy for the `@timetoalign/timeskeleton` npm package

This suite proves the public contract of schema 0.7.0 in JavaScript: one
manifest shape, one schema document, one validator, the same answers as the
Python package. The rules and the reasoning that proves each one are stated
in the Python suite's README (`python/tests/README.md`); this suite asserts
the same cases with the same expected values, through inline documents
written in each test, and reads the same shared rejection and warning cases.
Where the two packages answer differently by design, this README says so.

## What the package promises

1. `validate` accepts exactly the manifests the Python package accepts and
   raises the first violation at the same path; `parse` is `parseJson`
   followed by `validate`.
2. `unknownKeys` returns, for every manifest, the list Python's
   `unknown_keys` returns, byte for byte once written by `dumps`.
3. `complete` and `minimal` give the values Python's functions give, from a
   `DEFAULTS` table equal to the schema's `default`s, as Python's is.
4. `dumps` writes every value as the same bytes as Python's `dumps`.
5. The generated files equal a fresh generator run, and the npm package
   ships the schema document, the drawing specification and the licence.

## The fixtures

`fixtures.test.ts`: every manifest fixture (every `*.json` below
`fixtures/0.7.0/` except the drawings), read by `parseJson`, validates, has
no unknown keys, and satisfies both round trips of `complete` and `minimal`,
as in the Python suite's "The fixture set".

## The schema document and the generated files

The schema tests (`schema.test.ts`) assert on the bundled `schema` what the
Python suite asserts on the file ("The schema document"): the document equals
the file; `$id`, the root `$ref`, local references and no `$anchor`; the
twelve public definitions and the absent ones; the members and required keys
of `TimeSkeleton`, `Timeline`, `Group` and `Graphical`; no
`additionalProperties: false`; `unevaluatedProperties: {"x-unknown-key":
true}` on exactly the object nodes outside branches and arms; every marked
node declaring what its branches declare; the defaults equal to `DEFAULTS`;
the vocabulary.

`generated.test.ts`: the committed `types.ts`, `schema.ts` and `font.ts`
equal a fresh run of `scripts/generate.ts`; `schemaSource()` is
`0.7.0/timeskeleton.schema.json`; `types.ts` exports `TimeSkeleton`,
`Timeline`, `Group`, `Graphical`, `ConversionMap`, `Coordinate`, `Number`,
`Fraction`, `TimeUnit`, `NumberType`, `Id` and `MeasureMapRow`, and none of
`TimeSkeletonManifest`, `TimeSkeletonGroupFile`, `TimeSkeletonBundleFile`,
`Bundle`, `Meta`, `TimelineClass`. The types are pinned by the compiler as
well: the suite's typecheck compiles statements that must fail, each marked
`@ts-expect-error` (a misspelt key on `Timeline`, a `Timeline` without
`length`, a child without `offset`), so a looser generation breaks the
typecheck gate; and a free `meta` and a `length: null` compile.

## The version marker, representation, identity and segment lines

`validate.test.ts`, `identity.test.ts` and `segment-lines.test.ts` assert the
cases of the Python README's sections "The version marker",
"Representation of own-axis values", "Identity", "Segment lines" and "Groups
and unknown length", with the same documents, paths and messages, except:

- **Quoting.** The representation message and the four child messages are
  the same text in both packages (`length 32 of 'score' is an int on a
  fraction axis: write [32, 1]`, `child 'take' has unit 'seconds', its parent
  'score' has 'quarters'`, `offset -1.5 of 'take' is negative`, `offset 75.0
  of 'take' is beyond the length 60.0 of its parent 'recording'`, `child
  'coda' ends at [12, 1], beyond the length [10, 1] of its parent 'score'`);
  every
  other message quotes an id as JSON (`duplicate id "m", first at …`, `id
  "start" is reserved for the parts of an address`), where Python quotes it
  as `repr` does. The `UnsupportedVersionError` message reads
  `unsupported TimeSkeleton version "9.9.9"; this package reads 0.7.0 only`.
- **Integral floats.** A value read by `parseJson` keeps `2.0` as a
  `JsonFloat`, so `length 2.0` on a fraction axis is "a float … write [2, 1]"
  as in Python; a plain JavaScript number cannot tell `2.0` from `2`, so a
  value built in code with `2` is an int. Rewritten floats are spelled as
  Python spells them (`write 2.0`, `write 0.75`, `ends at 1.0`).
- **Integers beyond 2^53.** `parseJson` reads `9007199254740993` as a
  `bigint`, so on a float axis it is "an int … write a float" as in Python;
  `9007199254740992n` and `10n ** 20n` are exactly floats and validate.

## Unknown keys

`unknown-keys.test.ts`: every shared warning case validates, its text is the
standard writer's, and `dumps(unknownKeys(manifest))` equals
`dumps(case.unknown_keys)`; `several_depths` lists its sixteen entries in the
stated order; keys inside `meta`, `metric_hierarchy`, `styles`,
`graphical.order` and unknown values are not reported; the sort (keys by
code point, `ﬀ` before `😀`, indices by number, `timelines[2]` before
`timelines[10]`); an invalid value raises before any key is listed. Ajv
records a key through the `x-unknown-key` keyword, which only the matching
branch of a discriminated `oneOf` evaluates, so a key is never reported from
a candidate the value does not match (the nested conversion map of
`several_depths` proves it).

## Defaults

`defaults.test.ts` asserts the Python README's section "Defaults: the
complete and the minimal form" with the same documents and values. A value
is the default only in type and value: `repeat_count: new JsonFloat(1)`, read
by `parseJson` from `1.0`, is not the default `1` and stays in the minimal
form, written back as `1.0`, as in Python; the round trips compare the texts
`dumps` writes, which tell `1.0` from `1`. The functions never hand out the
objects of `DEFAULTS` itself (two completions of one manifest hold distinct
`meta` and `flow_control` objects).

## Shared rejection cases

For each of the 86 cases (`validate.test.ts`), read by `parseJson`: its text
is the standard writer's; `version_unknown` raises `UnsupportedVersionError`
and stores `["timeskeleton"]`; every other case raises
`SchemaValidationError` at its stored path, through `validate` on the parsed
value, through `validate` on the value as `JSON.parse` reads it, and through
`parse` of its compact text. The one exception is `float_axis_int_not_exact`
as `JSON.parse` reads it: `JSON.parse` turns `9007199254740993` into
`9007199254740992`, which is exactly a float, so that reading validates, and
the test asserts that it does. The set of names is stated literally.

## One path rule for both validators

As in the Python README: the deepest diagnostic leaf, ties to the first; a
discriminated `oneOf` contributes only the candidate its tag selects (Ajv's
`discriminator`). The shared rejection cases pin the paths.

## The canonical order and the standard writer

`manifest.test.ts` asserts the Python README's sections "The canonical
order" and "The standard writer" with the same documents and expected id
sequences, including own-axis values as bare ints, floats, `JsonFloat`s and
pairs mixed, and adds:

- **Both writers, from any order.** Every fixture, rejection and warning
  case, with the keys of every object reversed and, in the fixtures, the
  items of every array the canonical order sorts (`timelines`, `groups`,
  `members`, `children`, `conversion_maps`, `regions`, `breaks`, `jumps`,
  `markers`), is written by this `dumps` and by Python's `dumps` (loaded by
  `python3` from its path) to the same bytes, equal to the file.
- **Python's `repr` itself.** 2000 doubles from a fixed pseudo-random
  sequence are spelled exactly as `python3` spells them with `repr`.
- **The shared number corpus** gives the one literal expected text.
- **Refusals.** NaN, infinity and lone surrogates are refused as a
  `RangeError`, `undefined` as a `TypeError`, a collection that cannot be
  ordered as a `TypeError`.

## Lossless reading in JavaScript

`parseJson` reads any JSON text into the smallest representation that loses
nothing: a safe integer and a float with a fractional part are plain numbers,
an integer beyond `Number.MAX_SAFE_INTEGER` is a `bigint`, an integral float
(`2.0`, `1e+16`, `-0.0`) a frozen `JsonFloat`; `-0` is the integer 0, as in
Python; objects keep the written order of their keys, array-index keys
included, which `compactJson` honours. The tests pin each case (`0.5`,
`2.0`, `123456789012345678`, `-0`, `-0.0`, `1E5`), key order surviving a
round trip, malformed text refused as a `SyntaxError`, and `1e400` refused as
a `RangeError`. `compactJson` is a fixpoint for every value nested in every
fixture and equals Python's `json.dumps(value, separators=(",", ":"),
ensure_ascii=False)` for every fixture, rejection and warning case.
`JsonFloat` is a frozen class told apart by `instanceof` or `isJsonFloat`, and
`isJsonObject` is false for it.

## Integer boundaries

`JSON.parse("9007199254740993")` gives `9007199254740992`, while `parseJson`
reads `9007199254740993n`. Lengths of `9007199254740993n` and
`9223372036854775807n` on a ticks axis validate, and are written and read
back as the same integer.

## Completing missing styles

`completeStyles` returns a new graphical block and never changes its input;
every distinct style name a statement names but `styles` lacks is added as
an empty declaration, `missing` lists them in code-point order (`ﬀ` before
`😀`), and with missing names it calls `console.warn` exactly once with the
text of Python's `MissingStyleWarning`, with none never.

## The font

`fonts/DejaVuSans.ttf` has the SHA-256 of the upstream release file
(`7da195a7…48954`) and its licence lies beside it (8816 bytes);
`package.json` exports `./fonts/*` and lists `fonts` in `files`;
`fontMetrics` has exactly `advances`, `ascender`, `descender`, `fallback`
and `units_per_em` with 5918 advances (`"9833"` 966, `"48"` 1303, `"32"`
651) and the values 1901, 483, 1229 and 2048; `dumps(fontMetrics)`
reproduces the metrics file.

## Packaging

After `scripts/copy-assets.ts`, `npm pack --dry-run --json` lists
`docs/drawing.md`, `schema/0.7.0/timeskeleton.schema.json` and `LICENSE`, each
copy byte for byte the repository's file, and `package.json` exports
`./docs/*`.

## Hermeticity

Tests read the repository fixtures and the schema through shared helpers
(`fixtures.ts`). They use no network or shared mutable input. The packaging
test refreshes the package directory's ignored copies of the repository
assets, as `pnpm build` does, and runs `npm pack` without writing a tarball.
