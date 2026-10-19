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
   followed by `validate`. A checked value is typed as the lossless form:
   one test assigns it to `LosslessTimeSkeleton` and, by a
   `@ts-expect-error` line, not to `TimeSkeleton`, and reads its lengths
   back as `9007199254740993n` and `JsonFloat(2)`.
2. `unknownKeys` returns, for every manifest, the list Python's
   `unknown_keys` returns, byte for byte once written by `dumps`.
3. `complete` and `minimal` give the values Python's functions give, from a
   `DEFAULTS` table equal to the schema's `default`s, as Python's is; their
   typed forms take and give the generated `LosslessTimeSkeleton` and
   `CompleteTimeSkeleton`.
4. `dumps` writes every value as the same bytes as Python's `dumps`.
5. The generated files are the generator's output, and the npm package
   ships the schema document, the drawing specification and the licence.

## The fixtures

`fixtures.test.ts`: every manifest fixture (every `*.json` below
`fixtures/0.7.0/` except the drawings), read by `parseJson`, validates, has
no unknown keys, and satisfies both round trips of `complete` and `minimal`,
as in the Python suite's "The fixture set".

## The schema document and the generated files

`schema.test.ts` checks invariants, not the tree's private shape, so a
refactor that keeps the accepted language stays green: the bundled `schema`
is the file; references are local and resolve; the public definitions exist
and the former ones do not; the unit table's consts are exactly the keys of
`UNIT_NUMBER_TYPES` in order, each description naming that unit's default
number type, as in the Python suite; `Name`, `Meta` and `MapBase` are the
shared definitions every `name`, every `meta` and every conversion map
refers to, the references are `Id`s and `Selector.ids` holds `Address`es
accepting and refusing the Python suite's strings; no node is closed, none
carries `unevaluatedProperties` and no key begins with `x-`; every object
declares, itself or in its `allOf` base, what its branches declare; every
discriminated union tags each branch with a distinct required constant; the
`default`s, read through references and bases, are exactly `DEFAULTS`. `generated.test.ts`: a fresh generator run exports the committed
names, which are every definition, the complete form of exactly the
definitions holding a default, and `LosslessTimeSkeleton`; the committed
text is `check:drift`'s oracle. Statements marked `@ts-expect-error` (a
misspelt key, a missing `length` or child `offset`, a complete form missing
a defaulted key, a three-member Fraction) make a looser generation break
the typecheck gate.

## The validator

`validate.test.ts`, `identity.test.ts` and `segment-lines.test.ts` prove the
rules of the Python README's sections "The version marker", "Representation
of own-axis values", "The rules and their codes" and "What proves the rules"
with the same inline documents, paths, codes and messages, in the same
order: every semantic rule by its smallest document with one problem, which
`validate` raises too, and one document breaking every step once, whose
problems and codes `identityProblems` lists in order and whose first problem
`validate` raises. The rules live in five modules of the same names and
decomposition in both packages, so a rule changes in both or the shared
cases fail. The packages differ only where JavaScript must:

`representation-schema.test.ts` derives every scalar and array member that
can hold a Number, and every scalar, array and keyed-object member that holds
a nested conversion map, from the schema's conversion-map definitions. It
asserts exact equality with the validator's two traversal tables, naming every
missing or extra entry on failure, so a schema addition cannot escape the
fraction-member rule.

- **Quoting.** The representation, child and finite-number messages are the
  same text in both packages; every other message quotes an id as JSON
  (`duplicate id "m", first at …`) where Python uses `repr`, and the
  version error reads `unsupported TimeSkeleton version "9.9.9"; this package
  reads 0.7.0 only`. A schema violation carries Ajv's message (`must match
  pattern …`, `must NOT have duplicate items …`).
- **Integral floats.** `parseJson` keeps `2.0` as a `JsonFloat`, so
  `length 2.0` on a fraction axis is "a float … write [2, 1]" as in Python;
  a number built in code as `2` is an int. A `JsonFloat` in either member of
  any Fraction pair is refused as `representation` at that member, including
  a timeline length, a conversion-map Number and a measure-map quarter value;
  `[8, 1]` remains accepted. Rewritten floats are spelled as Python spells
  them (`write 2.0`, `write 0.75`, `ends at 1.0`).
- **Integers beyond 2^53.** `parseJson` reads `9007199254740993` as a
  `bigint`, so on a float axis it is "an int … write a float";
  `9007199254740992n` and `10n ** 20n` are exactly floats and validate.
- **Non-finite numbers.** `parseJson` refuses them and a `JsonFloat` cannot
  hold one, so only a number built in code reaches the finite rule; the
  tests build infinity, NaN and negative infinity as Python's do.

## Shared rejection cases

Each of the 91 cases (`validate.test.ts`), read by `parseJson`, is written
as the standard writer writes it and raises `SchemaValidationError` with its
stored path and code through `validate` on the parsed value, through
`validate` on the value as `JSON.parse` reads it, and through `parse` of its
compact text; `version_unknown` raises `UnsupportedVersionError`. Each case
is read through one reader, the mirror of Python's `rejection_case`, which
puts the infinity or NaN a `finite_number` case names at its path; such a
case has one reading, the reader's value, since JSON text cannot carry it,
and a test pins the two values in place. Two `JSON.parse` readings are exempt:
`float_axis_int_not_exact`, since `9007199254740993` becomes
`9007199254740992`, exactly a float, and `length_fraction_integral_float`,
since `8.0` becomes the integer `8`; the tests assert that those lossy readings
validate. The set of names and the sixteen codes are stated literally.

The path rule is the Python README's ("One path rule for both validators");
Ajv applies a discriminated `oneOf` to the candidate its tag selects through
its `discriminator` option. The shared cases pin the paths.

## Unknown keys

`unknown-keys.test.ts`: every shared warning case validates, its text is the
standard writer's, and `dumps(unknownKeys(manifest))` equals
`dumps(case.unknown_keys)`; `several_depths` lists its sixteen entries in the
stated order; keys inside `meta`, `metric_hierarchy`, `styles`,
`graphical.order` and unknown values are not reported; the sort (keys by
code point, `ﬀ` before `😀`, indices by number, `timelines[2]` before
`timelines[10]`); an invalid value raises before any key is listed. The
validator walks the value with the in-memory closed variant of the Python
README ("One walk"); only where the variant refuses it does it walk the
document itself, which decides validity, and then reads each key from the
variant's `unevaluatedProperties` errors. A discriminated `oneOf` evaluates
only the candidate its tag selects, so a key is never reported from a
candidate the value does not match (the nested conversion map of
`several_depths` proves it). The keys belong to one run, so a refused
manifest's keys never appear in the next run's list (`validate.test.ts`).

## Defaults

`defaults.test.ts` asserts the Python README's section "Defaults: the
complete and the minimal form" with the same documents and values. A value
is the default only in type and value: `repeat_count: new JsonFloat(1)` (read
from `1.0`) is not the default `1` and stays in the minimal form; the round
trips compare `dumps` texts, which tell `1.0` from `1`. No result shares
an object with `DEFAULTS`. The typed forms' oracle is the fixtures: each
minimal twin completes to its fixture's text, keeps it in canonical order,
and strips back to its own; a literal `CompleteTimeSkeleton` compiles, and
keys whose default is absent (`id`, `graphical`, a root's `offset`) stay
optional.

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
an integer beyond `Number.MAX_SAFE_INTEGER` a `bigint`, an integral float
(`2.0`, `1e+16`, `-0.0`) a frozen `JsonFloat`; `-0` is the integer 0, as in
Python; objects keep the written order of their keys, array-index keys
included, which `compactJson` honours. The tests pin each case (`0.5`,
`2.0`, `123456789012345678`, `-0`, `-0.0`, `1E5`), key order surviving a
round trip, and `1e400` refused as a `RangeError`. Malformed text is refused
as a `JsonSyntaxError`, a `SyntaxError`, whose offset, line and column name
where the text breaks; eleven texts, each breaking in a different way and
place (an empty text, a stray comma, an unterminated string, a missing
comma on line 3), pin the message and the three numbers. `compactJson` is a
fixpoint for every value nested in every fixture and equals Python's
`json.dumps(value, separators=(",", ":"), ensure_ascii=False)` for every
fixture, rejection and warning case. `JsonFloat` is told apart by
`instanceof` or `isJsonFloat`, and `isJsonObject` is false for it.

`JSON.parse("9007199254740993")` gives `9007199254740992`, while `parseJson`
reads `9007199254740993n`; lengths of `9007199254740993n` and
`9223372036854775807n` on a ticks axis validate and are written and read
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
