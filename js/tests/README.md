# Test strategy for the `@timetoalign/timeskeleton` npm package

This suite proves the draft public contract of schema 0.7.0, its three file
kinds (timeline, group and bundle files), and of the schema versions it still
validates (0.5.0 and 0.6.0, timeline files only).

## What the package promises

1. Every bundled fixture of every supported version and every file kind
   validates against the schema of the version and kind it declares, read
   and validated by `parse` and as `JSON.parse` reads it.
2. `validate` rejects every shared case in `fixtures/rejections/0.5.0/`,
   `fixtures/rejections/0.6.0/` and `fixtures/rejections/0.7.0/` at the exact
   stored path, in both readings; all 203 cases fail, including a manifest
   without its one required `timeline`; `parse` rejects the 93 cases of the
   latest version. Every case
   of a version's directory declares that version except two:
   `meta_schema_version_unknown` declares the unknown version `"9.9.9"`, and
   `root_missing_meta` has no `meta` to declare one (the test "has every
   rejection declare its version except the two without a declaration").
3. A manifest declaring any other version (`"0.3.0"`, `"0.1.0"`, `"0.4.0"`,
   `"1.0.0"`, each made from `bare.json`) is rejected through the same error,
   a `SchemaValidationError` at `["meta", "schema_version"]`.
4. Generated errors expose paths as object keys and numeric array indices.
5. The checked-in generated files (`types.ts`, `schema.ts`, `font.ts`) equal a
   fresh generator run, and the generated schema bundle is the schema files:
   `schemaDocuments` holds every document keyed by version and name
   (`{"0.5.0": {timeline}, "0.6.0": {timeline}, "0.7.0": {core, timeline,
   group, bundle}}`), `schemas` every version's timeline document and
   `schema` the 0.7.0 one, each equal to its file. Schema files and version
   directories are ordered by their parsed version, so `0.10.0` follows
   `0.9.0` and the latest version is the numerically highest one; a list
   mixing `0.10.0`, `0.9.0`, `1.0.0` and a non-schema file pins that order,
   and a list mixing `0.10.0`, `timeskeleton-0.6.0.schema.json`, `0.7.0`,
   `0.7` and `README.md` gives the single file, `0.7.0`, `0.10.0`. The
   generator finds exactly the three versions of the repository, and
   `types.ts` exports `TimeSkeletonManifest`, `TimeSkeletonGroupFile`,
   `TimeSkeletonBundleFile`, `Group`, `Bundle`, `Meta` and `MemberOrder`.
6. The schema's graphical definitions (`Graphical`, `Statement`, `Selector`,
   `ElementType`, `Paint`, `Declaration`) state the vocabulary listed in the
   Python suite's README, literally, as in Python; the manifest's members are
   `meta`, `timeline` and `graphical`, the first two required, no other
   admitted, and a styled fixture's members are written `graphical`, `meta`,
   `timeline` (keys sorted). The styled blocks are stated literally, as in Python (twenty-one
   and five statements); the Python suite alone resolves their colours,
   since both suites read the same files. Exact validation
   cases accept every boundary stated there and reject values outside them at
   the property path. Timeline names with control characters still validate.
7. The timeline fixture set of 0.6.0 and of 0.7.0 is the exact list of 23
   file names the Python suite states, and the group (3) and bundle (7)
   fixture sets of 0.7.0 are the exact lists it states; the Python suite
   alone proves that no two fixtures of a kind share a structural signature,
   since both suites read the same files.
8. The npm package ships `docs/drawing.md` and the four 0.7.0 schema
   documents: after `scripts/copy-assets.ts`, `npm pack --dry-run --json`
   lists `docs/drawing.md` and `schema/0.7.0/<name>.schema.json` for `core`,
   `timeline`, `group` and `bundle`, each copy equals the repository's file
   byte for byte, and `package.json` exports `./docs/*`.
9. The npm package ships the repository's MIT licence: after
   `scripts/copy-assets.ts`, `npm pack --dry-run --json` lists `LICENSE` at
   the package root (not only `fonts/LICENSE`), and the copy equals the root
   `LICENSE` byte for byte.

## Versions and migration

The rules and their proofs are stated in the Python suite's README
("Versions and migration"); this suite asserts the same cases with the same
expected values: `SCHEMA_VERSION` `"0.7.0"` and `SUPPORTED_VERSIONS`
`["0.5.0", "0.6.0", "0.7.0"]`; the 0.5.0 and 0.6.0 schemas equal once `$id`,
the top-level `description` and the version constant are removed; the 0.6.0
manifests equal to the 0.5.0 ones and the 0.7.0 timeline manifests to the
0.6.0 ones, once migrated and without `meta.generator` (`corpus_score_ms3`
once its store-built children `notes`, `controls` are renamed `clt_2`, `clt_3`
with the store names as names); the 0.6.0 rejection
cases equal to the 0.5.0 cases and the 0.7.0 directory holding the 0.6.0
cases, their manifests equal once migrated (the two cases `migrate` refuses
equal to the 0.6.0 ones with `is_segment_line: false` on their timeline; the reason of
`root_missing_timeline` restated for 0.7.0); both pinned pairs (`before.json`
byte for byte the source version's `bare.json`, the first `after.json` the
same text with the target version, the second also with the root's
`"is_segment_line": false`, `dumps(migrate(parseJson(before)))` byte for byte
the second `after.json`, the result validating); only the declaration and the
flag on every timeline changing for every 0.5.0 and 0.6.0 fixture (compared
as text written by `dumps`); every
0.7.0 fixture of every kind copied, not returned; the input never changed or
shared; the chain reaching the latest version; and the refusals
(`UnsupportedVersionError` with `version` `"9.9.9"`, `"0.4.0"`, `null` and
`null`, and the message for `"9.9.9"` exactly `unsupported schema_version
"9.9.9"; this package supports 0.5.0, 0.6.0, 0.7.0`).

`migrate` copies what `parseJson` read. What proves it beyond the fixtures'
`6.0` floats, which the text comparison above already covers:

- **Exact numbers and key order survive.** The text
  `{"meta":{"schema_version":"0.5.0"},"timeline":{"children":{"10":1.0,"2":123456789012345678}}}`
  read by `parseJson` and migrated is written by `compactJson` as the same
  text with `"0.7.0"` and the timeline's `"is_segment_line":false` appended: the array-index keys keep their written order (`"10"`
  before `"2"`), `1.0` stays a `JsonFloat` and the integer stays a `bigint`.
  The value is not a manifest, which `migrate` does not require.

## File kinds and schema documents

The rules and their proofs are stated in the Python suite's README ("File
kinds and schema documents"); this suite asserts the same cases on the
bundled `schemaDocuments["0.7.0"]`: four documents, each `$id` the base plus
`<name>.schema.json`; every reference local or relative to another document
of the version and naming an existing definition; definition names unique,
`core` holding the twelve shared definitions; the union of the `core` and
`timeline` definitions, references made local, the id rule written inline
and `is_segment_line` removed from `TimelineManifest`, equal to 0.6.0's
definitions, the root members and `Meta` as stated there; thirty-two references to `Id` (27, 3 and 2 in the timeline, group and
bundle documents); the group and bundle documents literally; `FILE_KINDS`
and `fileKind` on the same ten values; the two test documents (built from
the 0.7.0 `bare` manifest as the Python suite builds them) validating, also
through `parse` of their `dumps` text; a 0.7.0 value with none or two kinds
rejected at the root with `exactly one of "timeline", "group" or "bundle" is
required; found none` and `… found "timeline", "group"`; `"9.9.9"` rejected
at `meta.schema_version` with a group and with no kind; a 0.6.0 value
holding a group rejected at the root, not with the kind message; and a
bundle checked against the bundle document. `validate` asserts the union
`TimeSkeletonFile` of the three root types, and `parse` returns it.

## Segment lines

The rules, their order, locations and messages, and the cases that prove
them are stated in the Python suite's README ("Segment lines"); this suite
asserts the same cases with the messages quoted as JSON (`segment "b" of
segment line "bare" is no ContinuousLogicalTimeline`, `… differs from segment
"a" in is_segment_line`, `… does not start at 0`, `… does not start where the
one before it ends`, `the segments of segment line "bare" do not end at its
length`). Exact values are compared as rationals (`exact`, the coordinate
reader of the canonical order), never as JavaScript numbers summed, so
`0.1 + 0.2` does not meet `0.3` here either. `TimelineManifest` requires
`is_segment_line`, and the shared rejection cases pin the paths.

## Identity in group and bundle files

The rules, their order, locations and messages are stated in the Python
suite's README ("Identity in group and bundle files").
`identityProblems` returns the same problems, with the same paths, in the
same order, as Python's `identity_problems`, and this suite asserts the same
cases with each message quoted as JSON (`duplicate id "piece", first at
#/timelines/0/id`, `"tempo" names no timeline of this file`, `duplicate
member "score", first at …`, `timeline "recording" contains no member of the
group`, `member "second-half" lies inside member "piece" of the same group`,
`member "recording" contains member "excerpt" of the same group`, `"piece" is
not a member of group "group_1"`, `member "recording" of group "group_1" is
missing`, `"group_9" names no group of this bundle`). No member of a group
lies inside or contains another member of the same group, but a parent and
its child in different groups of one bundle are no problem. The
93 shared 0.7.0 rejection cases pin the paths of both validators for every
rule.

## Identity

The rules and their proofs are stated in the Python suite's README
("Identity"). `identityProblems` returns the same problems, with the same
paths, in the same order, as Python's `identity_problems`, and this suite
asserts the same cases: the schema's literal `Region`, `Break`, `Jump`,
`Marker` and `markers` definitions and the id pattern `^[^/\u0000-\u001f]+$`
on all twenty-six `id` members and on `children` keys; no problem in any
fixture; three repeated ids reported at their later occurrences, the first
one by `validate`; children visited in code-point order of their keys
(`😀` before `ﬀ` would be UTF-16 order, `ﬀ` before `😀` is code-point order,
so the `😀` child repeats); targets resolved within their own timeline; and
duplicates listed before dangling targets. A JavaScript message quotes the id
as JSON (`duplicate id "m", first at …`, `"there" names no marker of this
timeline`), where Python's quotes it as `repr` does; the paths are equal.

## The font

The package bundles the metrics of DejaVu Sans 2.37 (`fontMetrics`, typed
`FontMetrics`, generated into `src/generated/font.ts` from
`fonts/dejavu-sans-2.37.metrics.json`) and ships the TrueType file and its
licence as the subpath `@timetoalign/timeskeleton/fonts/*`. What proves it:
the repository's `fonts/DejaVuSans.ttf` has the SHA-256 of the upstream
release file (`7da195a7…48954`) and its licence lies beside it (8816 bytes);
`package.json` exports `./fonts/*` and lists `fonts` in `files`;
`fontMetrics` has exactly the members `advances`, `ascender`, `descender`,
`fallback` and `units_per_em` (keys sorted), with 5918 advances, among them
`"9833"` 966, `"48"` 1303 and `"32"` 651, and the values 1901, 483, 1229 and
2048 (the same values the Python suite states); the metrics file is the standard writer's
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
`bare` fixture with a tie at every key level is put in the literally stated
order by `canonicalOrder` and still validates, and `dumps` writes its
children by key; a literal value is written with its keys sorted, array-index
keys (`"10"`, `"2"`) included, in one literal text; a literal value has one
canonical JSON text; and the text of every break and jump entry of every
fixture equals Python's `json.dumps(entry, sort_keys=True, separators=(",",
":"), ensure_ascii=False)` for the same file (the suite runs `python3` on the
fixture files). The group and bundle documents are put in the order the
Python suite states (roots, groups and members sorted, display orders as
given, the regions of a root sorted), members `😀`, `ﬀ`, `b` become `b`, `ﬀ`,
`😀`, and a member that is no string is refused with a `TypeError`.
`canonicalOrder` returns a copy, and copies a value without a top-level
`timeline`, `timelines`, `group` or `bundle` as it is; a collection it cannot
order is refused with a `TypeError`.

## The standard writer and lossless reading

Both packages export `dumps` (canonical order, then keys sorted by code
point, two-space indentation, a final newline, characters unescaped except `"`, `\` and control characters,
every float spelled as Python's `repr`, every integer without a decimal point)
and `canonical_order` / `canonicalOrder`. They must write the same value as
the same bytes. What proves it:

- **Every standard file round-trips.** Each of the 23 timeline, 3 group and
  7 bundle fixtures and the 93 rejection cases of the latest version (126
  files) is reproduced byte for byte by `dumps(parseJson(text))`. `corpus_score_ms3` carries `→` and float-axis
  fixtures carry `6.0`, so neither the escaping nor the float spelling can be
  wrong without a failure.
- **Both writers, from any order.** Every standard file with the keys of
  every object reversed, and in the fixtures the items of every array the
  canonical order sorts (`timelines`, `members` and `groups` included), is
  written by this `dumps` and by Python's `dumps`
  (`python/src/timeskeleton/manifest.py`, loaded by `python3` from its path)
  to the same bytes, equal to the file. The group and bundle test documents
  with `timelines`, `members` and `groups` reversed are written by both to the
  same bytes, equal to `dumps` of the documents as built.
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
`JSON.parse` cannot for array-index keys (`"10"`, `"2"`), and `compactJson`
honours it (`dumps` sorts every object's keys). The generated types are untouched: `Lossless<T>` maps them, and
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
no network or shared mutable input. The packaging test refreshes the
package directory's ignored copies of the repository assets, as `pnpm build`
does, and runs `npm pack` without writing a tarball.
