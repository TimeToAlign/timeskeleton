# Test strategy for the `timeskeleton` Python package

This file states what would prove the package works. The tests follow it; a
test that cannot be traced to a point below does not belong here. The same
strategy governs the npm package (`js/tests/README.md`), with the same
fixtures, the same rejection cases and the same expected paths.

## What the package promises

1. It bundles exactly the schema it claims: `schema_path()` names the file of
   `SCHEMA_VERSION`, `load_schema()` returns a document whose `$id`, `$schema`
   and `meta.schema_version` constant carry that version, and
   `SCHEMA_VERSION` is the last entry of `SUPPORTED_VERSIONS`.
2. The schema's vocabulary is the library's: the `TimelineClass`, `TimeUnit`
   and `NumberType` enumerations and the fourteen required keys of a timeline
   manifest are pinned verbatim in the tests. A change on either side fails a
   test instead of drifting silently.
3. `validate` accepts every document timetoalign emits: every bundled fixture
   passes, and the bundled set is exactly the nine documents listed in
   `fixtures/README.md`.
4. Acceptance is not leniency: `validate` rejects each class of defect at the
   exact location of the offending value.
5. `migrate` brings a document of any supported version to the latest one,
   returns a copy that shares nothing with its input, and refuses unknown
   versions with a typed error.
6. Errors are typed and machine-readable: `SchemaValidationError.path` is a
   tuple of object keys and integer array indices, `str()` renders it as a
   JSON pointer in fragment form, and `UnsupportedVersionError.version` names
   the offending version (or `None` when there is none).

## How each promise is proven

**Promises 1 and 2** are identity checks against literals written in the test
file: the `$id`, the enumeration arrays in order, the required-key list in
order, `additionalProperties: false` on the manifest.

**Promise 3** is a parametrized pass over `fixture_paths()`; the list of file
names is asserted against the literal list of nine before any document is
validated, so a missing or extra fixture fails on its own.

**Promise 4** uses the one-mutation method: each case loads a fixture that
promise 3 accepts, applies exactly one change, and expects
`SchemaValidationError` whose `path` equals the full expected tuple. The
timeline id in the path is read from the fixture (ids are assigned by the
library), everything else is literal. One change per case keeps the path
unambiguous. The cases and their expected paths:

| Case | Mutation | Expected path |
|---|---|---|
| unknown root key | add `extra` at the root | `()` |
| missing `meta` | delete `meta` | `()` |
| missing required key | delete `locked` from the timeline | `(manifest, timelines, id)` |
| `name` neither string nor null | set `name` to `1` | `(…, name)` |
| `class` outside the enum | set `class` to `Timeline` | `(…, class)` |
| `unit` outside the enum | set `unit` to `beats` | `(…, unit)` |
| `number_type` outside the enum | set `number_type` to `decimal` | `(…, number_type)` |
| float numerator | set `length.numerator` to `1.5` | `(…, length, numerator)` |
| one-sided ratio | set `length.denominator` to `null`, numerator stays | `(…, length)` |
| denominator 0 | set `length.denominator` to `0` | `(…, length, denominator)` |
| string numerator `"12a"` | set `length.numerator` to `"12a"` | `(…, length, numerator)` |
| child offset with float numerator | set the first child's `offset.numerator` to `0.5` | `(…, children, child id, offset, numerator)` |
| region that is not an object | set `regions` to `[1]` | `(…, regions, 0)` |
| `schema_version` `0.2.0` | set `meta.schema_version` | `(meta, schema_version)` |

The one-sided ratio is reported at the rational object, not at a member: each
member is well-formed on its own; it is their pairing that fails. The rule
that picks the reported error is stated in `validate.py` (`_select`) and the
npm package applies the same rule, so both sides name the same path.

Why these cases: they cover the root envelope (two), the required-key rule,
each enumeration, every constraint of the rational value (type, pairing,
minimum, pattern), recursion into children, an integer array index, and the
version constant.

**Promise 5**: for every fixture, `migrate` returns a document equal to its
input, not identical to it, and deep enough a copy that changing a nested
value of the result leaves the input untouched. For every supported version,
every fixture migrates to a document that declares `SCHEMA_VERSION` and
passes `validate`; this harness is what a future migration extends with its
before/after fixture pair. With a single version, `MIGRATIONS` is asserted
empty, so the identity is by construction, not by accident. A document with
an unknown, missing or non-string version raises `UnsupportedVersionError`
carrying that version.

**Promise 6**: the pointer renderer is checked on the root (`#`), on nested
keys with the `~` and `/` escapes, and on an integer index; `str()` of a
caught error equals the renderer applied to its path followed by its message.

## Hermeticity

Tests read fixtures through `fixture_paths()` only, never through a relative
path, so they pass from an installed wheel and from a checkout. No network, no
temporary files, no shared mutable state: documents are loaded fresh per test
and mutated locally.
