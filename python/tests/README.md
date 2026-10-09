# Test strategy for the `timeskeleton` Python package

This file states the validation logic the tests prove. The npm suite follows
the same fixture set, rejection cases, and paths.

## What the package promises

1. It bundles the schema named by `SCHEMA_VERSION`, including its identifier,
   version constant, enumerations, and closed fourteen-key timeline manifest.
2. `validate` accepts all nine timetoalign fixtures and rejects malformed
   documents at a deterministic JSON-pointer path.
3. `migrate` returns a separate equal copy for every supported fixture and
   refuses unsupported versions with `UnsupportedVersionError`.
4. Generated errors expose paths as tuples of object keys and array indices.

## Validation logic

Every rejection begins with `continuous_logical.json`; the tests apply one
mutation and require the listed complete `SchemaValidationError.path`. The
timeline id is read from that fixture.

| Case | Mutation | Expected path |
|---|---|---|
| unknown root key | add `extra` at the root | `()` |
| missing required key | delete `locked` from the timeline | `(manifest, timelines, id)` |
| `class` outside the enum | set `class` to `Timeline` | `(…, class)` |
| `unit` outside the enum | set `unit` to `beats` | `(…, unit)` |
| fraction coordinate with a bare integer | set `length.value` to `12` | `(…, length, value)` |
| zero denominator | set `length.value` to `[12, 0]` | `(…, length, value, 1)` |
| negative length | set `length.value` to `[-12, 1]` | `(…, length, value, 0)` |
| three-element fraction | set `length.value` to `[1, 2, 3]` | `(…, length, value)` |
| string fraction | set `length.value` to `"12/1"` | `(…, length, value)` |
| coordinate without `unit` | delete `length.unit` | `(…, length)` |
| `int` number type with a fraction value | set `length.number_type` to `int` | `(…, length, value)` |
| `schema_version` `0.2.0` | set `meta.schema_version` | `(meta, schema_version)` |

The discriminated `oneOf` reports the closest bad member or array index; those
stable paths are shared with the npm validator. Schema tests also pin the
bundled fixture names and vocabulary.

## Hermeticity

Tests obtain fixtures through `fixture_paths()`, never a relative path. They
use no network, temporary files, or shared mutable input.
