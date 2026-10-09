# Test strategy for the `@timetoalign/timeskeleton` npm package

This file states what would prove the package works. The tests follow it; a
test that cannot be traced to a point below does not belong here. The
strategy mirrors the Python package's (`python/tests/README.md`): the same
fixtures, the same rejection cases, the same expected paths. Where the two
suites differ it is because the npm package carries generated files and the
Python package does not.

## What the package promises

1. It bundles exactly the schema it claims: the exported `schema` object
   carries the `$id`, `$schema` and `meta.schema_version` constant of
   `SCHEMA_VERSION`, which is the last entry of `SUPPORTED_VERSIONS`, and it
   is byte-for-byte the schema file at the repository root.
2. The schema's vocabulary is the library's: the `TimelineClass`, `TimeUnit`
   and `NumberType` enumerations and the fourteen required keys of a timeline
   manifest are pinned verbatim in the tests.
3. `validate` accepts every document timetoalign emits: every fixture at the
   repository root passes, and the set is exactly the nine documents listed
   in `fixtures/README.md`.
4. Acceptance is not leniency: `validate` rejects each class of defect at the
   exact location of the offending value, and narrows the document's type on
   success.
5. `migrate` brings a document of any supported version to the latest one,
   returns a copy that shares nothing with its input, and refuses unknown
   versions with a typed error.
6. Errors are typed and machine-readable: `SchemaValidationError.path` is an
   array of object keys and numeric array indices, its `message` starts with
   the JSON pointer of that path in fragment form, and
   `UnsupportedVersionError.version` names the offending version (or `null`).
7. The generated files are what the generator produces: `src/generated/types.ts`
   and `src/generated/schema.ts` equal a fresh run of `scripts/generate.ts`
   on the schema at the repository root. A schema change without
   regeneration, or a hand edit of a generated file, fails this test.

## How each promise is proven

**Promises 1 and 2** are identity checks against literals in the test file,
plus `toEqual` between the exported `schema` and the parsed schema file.

**Promise 3** reads `fixtures/<SCHEMA_VERSION>/` from the repository root
(the only copy; the package's own `fixtures/` directory is a build-time copy),
asserts the sorted file names against the literal list of nine, then
validates each document.

**Promise 4** uses the one-mutation method: each case parses a fixture afresh,
applies exactly one change, and expects `SchemaValidationError` whose `path`
equals the full expected array. The timeline id in the path is read from the
fixture; everything else is literal. The cases and expected paths are the
Python table, repeated here so this file stands alone:

| Case | Mutation | Expected path |
|---|---|---|
| unknown root key | add `extra` at the root | `[]` |
| missing `meta` | delete `meta` | `[]` |
| missing required key | delete `locked` from the timeline | `[manifest, timelines, id]` |
| `name` neither string nor null | set `name` to `1` | `[…, name]` |
| `class` outside the enum | set `class` to `Timeline` | `[…, class]` |
| `unit` outside the enum | set `unit` to `beats` | `[…, unit]` |
| `number_type` outside the enum | set `number_type` to `decimal` | `[…, number_type]` |
| float numerator | set `length.numerator` to `1.5` | `[…, length, numerator]` |
| one-sided ratio | set `length.denominator` to `null`, numerator stays | `[…, length]` |
| denominator 0 | set `length.denominator` to `0` | `[…, length, denominator]` |
| string numerator `"12a"` | set `length.numerator` to `"12a"` | `[…, length, numerator]` |
| child offset with float numerator | set the first child's `offset.numerator` to `0.5` | `[…, children, child id, offset, numerator]` |
| region that is not an object | set `regions` to `[1]` | `[…, regions, 0]` |
| `schema_version` `0.2.0` | set `meta.schema_version` | `[meta, schema_version]` |

The one-sided ratio is reported at the rational object: each member is
well-formed on its own; it is their pairing that fails. The rule that picks
the reported error is stated in `src/validate.ts` (`select`); it is the same
rule the Python package applies, which is why both sides name the same path.
The type narrowing of promise 4 is a compile-time check: after `validate`
returns, the test reads `document.manifest.timelines` without a cast, so
`tsc --noEmit` fails if the assertion signature is lost.

**Promise 5**: for every fixture, `migrate` returns a document deeply equal to
its input, not the same object, and a deep enough copy that changing a nested
value of the result leaves the input untouched. For every supported version,
every fixture migrates to a document that declares `SCHEMA_VERSION` and
passes `validate`; this harness is what a future migration extends with its
before/after fixture pair. With a single version, `MIGRATIONS` is asserted
empty. A document with an unknown, missing or non-string version throws
`UnsupportedVersionError` carrying that version (`null` when absent).

**Promise 6**: the pointer renderer is checked on the root (`#`), on nested
keys with the `~` and `/` escapes, and on a numeric index; a caught error's
`message` starts with the renderer applied to its path followed by `: `, and
the remainder is not empty.

**Promise 7**: the test imports `generate()` from `scripts/generate.ts`,
runs it, and compares each rendered file with the committed one using exact
string equality. CI additionally runs the script and `git diff --exit-code`.

## Hermeticity

Fixtures and the schema file are read from the repository root through paths
derived from `import.meta.url`, never from the working directory. No network,
no temporary files, no shared mutable state: documents are parsed fresh per
test and mutated locally. The Ajv instance is created once per process and
only ever read.
