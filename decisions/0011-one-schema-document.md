# 0011. One manifest shape in one schema document

Date: 2026-10-15

Status: accepted; supersedes [0010](0010-one-schema-document-per-file-kind.md)

## Context

Version 0.7.0, before its release, described three file kinds (a timeline
file, a group file and a bundle file) in four schema documents: one per kind
and a shared `core`, referring to each other by relative `$ref` (0010). Using
them showed four costs:

- A host that embeds a TimeSkeleton value in a file of its own and refers to
  our schema had to register every document; `core` cannot be resolved
  otherwise, in Python (jsonschema 4.26) or in JavaScript (Ajv 8.20).
- An editor changed the kind of a file whenever it named a timeline, extracted
  one from a bundle or merged two files, rewriting the root and every
  address.
- Styling (`graphical`) and identity had a rule per kind: a group file's
  display order was an array, a bundle's an object; a timeline file addressed
  every element by its bare id, the other kinds by `<root>/<id>`.
- The version lived in `meta.schema_version`, so `meta` could not be free.

Every real embedder also needs more than one timeline: a media axis with its
quarters axis, a score with its performances, a conversion map with the
sibling it targets.

## Considered options

- Keep three kinds in four documents (0010).
- A single timeline object as a file of its own beside a bundle file holding
  several (two shapes).
- One document whose root is a `oneOf` of a bare timeline and a manifest of
  several (one document, two root forms).
- One shape: every manifest is `{timeskeleton, timelines, id?, name?, meta?,
  groups?, graphical?}`, in one document.
- One shape with references between manifests (`timelines` items that point
  into other files).

## Decision

Every TimeSkeleton manifest has one shape, described by one document per
version, `schema/<version>/timeskeleton.schema.json`, whose root is `{"$ref":
"#/$defs/TimeSkeleton"}`. A single timeline is a manifest of one root, a group
a manifest with one group, and a manifest with an `id` or a `name` is named.
There is no file kind.

- **The version marker** is the top-level member `"timeskeleton": "0.7.0"`
  (a `const`), read before anything else: a value without it is no
  TimeSkeleton manifest, a value with another version is refused with
  `UnsupportedVersionError`. `meta` is free. `$schema` is a known optional
  string for editors and is never read.
- **Public definitions.** `TimeSkeleton`, `Timeline`, `Group`, `Graphical`,
  `ConversionMap`, `Coordinate`, `Number`, `Fraction`, `TimeUnit`,
  `NumberType`, `Id` and `MeasureMapRow` may be referred to by a host as
  `#/$defs/<name>`; within 0.7.x they change only by addition. A host may
  embed a whole manifest, marker included, or a bare `Timeline` and record the
  version itself. The document uses no `$anchor`: json-schema-to-typescript
  cannot follow one.
- **Open objects with recorded unknown keys.** No object is closed with
  `additionalProperties: false`. Every object definition with `type: object`
  and `properties` (never a `oneOf` branch or an `if`/`else` arm) carries
  `unevaluatedProperties: {"x-unknown-key": true}`. Every standard validator
  ignores the unknown keyword and accepts the key; our validators give the
  keyword a meaning (Ajv `addKeyword`, jsonschema `validators.extend`) and
  report each such key through `unknownKeys` / `unknown_keys` instead of
  refusing it, so a misspelt optional key is visible rather than silently
  taken for its default. The free objects (`meta`, `metric_hierarchy`) say
  `additionalProperties: true`.
- **Defaults.** Every key with a default declares it with `default`, and a
  reader supplies it; `complete` and `minimal` convert between the form that
  writes every such key and the form that leaves out those equal to their
  default.
- **Types.** The TypeScript types are generated from the one document with
  the generator's `additionalProperties: false`, so a misspelt key is a
  compile error while `meta` stays free; conditionals and the unknown-key
  annotation are left out of the view the generator reads.

The schema keeps only the current version; there are no migrations. Older
versions live in the git history and in their released packages.

## Rejected options

- **Three kinds in four documents**: the costs listed under Context.
- **Two shapes** (a timeline file and a bundle file): a timeline file holds
  one axis, but every embedder needs two or more; naming, extracting and
  merging still change the shape and rewrite addresses.
- **A two-form root (`oneOf`)**: a validator reports an unknown key or any
  other mistake as one opaque `oneOf` error over both forms (Ajv also
  reports a misleading missing `timelines`), and the unknown-key annotation
  cannot tell which form an object belongs to; both forms would be frozen at
  1.0.
- **References between manifests now**: validation would become
  asynchronous, browsers cannot portably resolve a relative path, and the
  semantics of a reference would be frozen with the format. Ids are
  fragment-shaped already (`op35.json#score/region_1`), so a reference form
  can join `timelines` in a later 0.x version; it must be decided before 1.0.

## Consequences

Every reader has one shape and one address rule; naming, extracting and
merging are edits of one structure. A host registers one document. A key a
host declares beside a `$ref` into this document is reported as unknown by our
validators, not by the host's own. Our validators resolve no reference between
documents, so the Python package no longer declares the direct `referencing`
dependency that 0010 introduced; `jsonschema` still brings it in. The fixtures
of a version are one set of manifests; their subdirectories sort them by
content only. Moving to references later adds an item form to `timelines`, not
a document.

## Review date

2027-10-15.
