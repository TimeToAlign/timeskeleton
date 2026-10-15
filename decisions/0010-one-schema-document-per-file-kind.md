# 0010. One schema document per file kind, with a shared core

Date: 2026-10-12

Status: superseded by [0011](0011-one-schema-document.md)

## Context

Up to 0.6.0 a TimeSkeleton version is one schema file describing one file
kind, the timeline file `{meta, timeline, graphical?}`. Version 0.7.0 adds
two kinds: a group file `{meta, timelines, group, graphical?}`, one timeline
group with the timelines it names, and a bundle file `{meta, timelines,
bundle, graphical?}`, one alignment bundle with all its timelines and its
groups. Both files embed complete timeline manifests, a bundle embeds groups,
and all three share the number, coordinate, unit, id and metadata
definitions. The timeline definitions alone are some 2,200 lines.

## Considered options

- One schema file per version holding all three file kinds, dispatched by a
  top-level `oneOf`.
- One schema document per file kind, each repeating the definitions it uses.
- One schema document per file kind plus one shared `core` document, the
  documents referring to each other by relative `$ref`.
- A finer split (numbers, coordinates, conversion maps, flow control,
  graphical block each in a document of its own).

## Decision

Each version from 0.7.0 on has four documents in `schema/<version>/`:
`core.schema.json` (the shared definitions: `Fraction` and its variants, the
number and coordinate forms, `TimeUnit`, `NumberType`, the id rule `Id` and
the file metadata `Meta`), `timeline.schema.json` (the timeline definitions
and the timeline file), `group.schema.json` (`Group`, the display order and
the group file) and `bundle.schema.json` (the bundle file). Each `$id` is
`https://timetoalign.github.io/timeskeleton/<version>/<name>.schema.json`, so
the documents lie below `schema/` at the paths of their identifiers, and
every reference between them is relative (`core.schema.json#/$defs/Id`,
`timeline.schema.json#/$defs/TimelineManifest`,
`group.schema.json#/$defs/Group`); a reader resolves them against the `$id`
or against the file's directory alike. The four documents share one version
and are released together. Definition names are unique across a version's
documents.

A file names its kind by the one member it holds beside `meta`: `timeline`,
`group` or `bundle`. The validators read that member and check the file
against its kind's document; a file holding none or several is refused at
the root. A top-level `oneOf` was declined because a failure inside it would
be reported against every kind at once, which the shared path rule of both
validators cannot attribute to the file's actual kind. Repeating the shared
definitions in each document was declined because the copies would drift. A
finer split was declined: the timeline definitions refer to each other
densely, and readers of the schema read them together.

The timeline definitions are 0.6.0's, moved, plus one member: the shared
ones moved to `core`, the id pattern written once as `Id` and referred to,
the version constant set to 0.7.0, and every timeline manifest gains the
required boolean `is_segment_line` (whether the timeline is a segment line of
contiguous segments), which the migration from 0.6.0 writes as `false` on
every timeline. Versions 0.5.0 and 0.6.0 keep their single files.

Both packages register all four documents of a version with their validator:
Python through a `referencing.Registry` handed to `jsonschema`'s
`Draft202012Validator`, TypeScript by adding every document to Ajv before
compiling the kind's document. `referencing` is the reference-resolution
library `jsonschema` itself depends on and documents for exactly this use;
the Python package now declares it directly (`referencing>=0.37.0,<1`).

- **Maintenance of `referencing`.** Maintained by the maintainer of
  `jsonschema` in the same organisation, released together with it; licence
  MIT (https://github.com/python-jsonschema/referencing/blob/main/COPYING);
  its dependencies, `attrs`, `rpds-py` and, before Python 3.13,
  `typing-extensions`, are already installed with `jsonschema`
  (https://pypi.org/project/referencing/0.37.0/). It adds no package to an
  environment that has `jsonschema`.
- **Writing it ourselves.** Resolving relative references across documents
  by hand would mean pre-bundling the documents into one schema, which
  rewrites every reference and makes the reported schema locations differ
  from the published documents.
- **Audited version.** 0.37.0, released 2025-10-13, the version locked in
  `python/uv.lock`.

The generated TypeScript types are compiled from the documents of the latest
version as one schema whose references are made local, so every definition
is one exported type: `TimeSkeletonManifest`, `TimeSkeletonGroupFile` and
`TimeSkeletonBundleFile` for the three file kinds.

## Consequences

A schema change touches the document it concerns; `core` changes ripple to
all three kinds within one version. The fixtures of a version are kept per
kind: timeline files in `fixtures/<version>/`, group files in its `groups/`
and bundle files in its `bundles/` directory. Moving back to one file per
version would cost a bundling step and a rewrite of every reference; moving
to a finer split would only add documents and references.

## Review date

2027-10-12.
