# Test strategy for the `timeskeleton` Python package

This suite proves the draft public contract of schema 0.7.0, its three file
kinds (timeline, group and bundle files), and of the schema versions it still
validates (0.5.0 and 0.6.0, timeline files only).

## What the package promises

1. Every bundled fixture of every supported version and every file kind
   validates against the schema of the version and kind it declares.
2. `validate` rejects every shared case in `fixtures/rejections/0.5.0/`,
   `fixtures/rejections/0.6.0/` and `fixtures/rejections/0.7.0/` at the exact
   stored path; all 210 cases (55, 55 and 100) fail, including a manifest
   without its one required `timeline`. Every case of a version's directory
   declares that version except two:
   `meta_schema_version_unknown` declares the unknown version `"9.9.9"`, and
   `root_missing_meta` has no `meta` to declare one
   (`test_every_rejection_declares_its_version_except_two`).
3. A manifest declaring any other version (`"0.3.0"`, `"0.1.0"`, `"0.4.0"`,
   `"1.0.0"`, each made from `bare.json`) is rejected through the same error,
   a `SchemaValidationError` at `meta.schema_version`: it is refused for its
   declaration alone, its `meta` checked against the latest version's `Meta`,
   whose version constant it fails; a value without `meta` is refused at the
   root (`root_missing_meta` of every directory), whatever else it holds, so
   the 0.5.0 and 0.6.0 cases keep their paths under a later version's rules.
   `UnsupportedVersionError`
   is raised by the version-taking accessors and by `migrate`, never by
   `validate`.
4. Schema, fixture and font accessors resolve package data independently of
   the current working directory.
5. Validation errors expose paths as tuples of object keys and array indices
   and render them as JSON pointers.
6. Every fixture and every rejection case is reproduced byte for byte by the
   standard writer.
7. The wheel and the sdist ship `docs/drawing.md`, the four 0.7.0 schema
   documents and the root `LICENSE`, byte for byte the repository's copies.
8. `migrate` rewrites a value of any supported version to the latest one
   (see "Versions and migration").

## Versions and migration

`SCHEMA_VERSION` is `"0.7.0"` and `SUPPORTED_VERSIONS` is `("0.5.0", "0.6.0",
"0.7.0")`, oldest first, the last one the latest. 0.6.0 changes the drawings a
version pins, not the manifest format; 0.7.0 adds the group and bundle files
and leaves the timeline file as it was. What proves the version handling:

- **One schema per version up to 0.6.0, the format unchanged.**
  `schema_documents(version)` is `("timeline",)` for 0.5.0 and 0.6.0 and
  `schema_path(version)` names `timeskeleton-<version>.schema.json`; each
  schema's `$id` contains `/<version>/` and its `meta.schema_version` constant
  is the version. With `$id`, the top-level `description` and that constant
  removed, the two parsed schemas are equal. Asking either version for its
  `group` document raises `ValueError` (`schema 0.6.0 has no 'group'
  document`).
- **The declared version selects the schema.** The schemas differ in their
  version constant, so a 0.5.0 value checked against the 0.6.0 schema fails at
  `meta.schema_version`. Every 0.5.0 fixture and every 0.6.0 fixture
  validating therefore proves that `validate` checks each value against the
  schema of the version it declares; every rejection case of either directory
  is rejected at its stored path, never at `meta.schema_version` unless that
  path is stored.
- **The 0.6.0 manifests are the 0.5.0 manifests.** Both directories hold the
  same 23 file names, and each 0.6.0 manifest and its 0.5.0 counterpart, both
  migrated to the latest version, are equal once both `meta.generator`
  members are removed (the generator names the timetoalign revision that
  emitted the fixtures, the one member a re-emission may change).
- **The 0.6.0 rejection cases are the 0.5.0 cases.** Both directories hold the
  same 55 file names, each pair with the same `path` and `reason`, and the
  two manifests are equal once both are migrated, for every case `migrate`
  accepts, the 0.6.0 one declaring 0.6.0; the two cases it refuses (`meta_schema_version_unknown`,
  `root_missing_meta`) are byte for byte the same in both directories.
- **The 0.7.0 timeline manifests hold the 0.6.0 manifests**, as above (the
  migration adds the flag): the 23 file names of 0.6.0 are those of 0.7.0
  without the six files 0.7.0 adds: `segment_line.json`,
  `segment_children.json`, `segment_pages.json`,
  `segment_pages_accolades.json` and `segment_pages_locked.json`, segment
  lines 0.6.0 cannot state, and `locked_root.json`, a root locked at
  construction; each pair equal once migrated and without
  `meta.generator`, except `corpus_score_ms3`: timetoalign now mints the ids
  of store-built children and keeps the store label as their name, so its
  children `notes` and `controls` are `clt_2` and `clt_3` named `notes` and
  `controls`. The pair differs, and is equal once the 0.6.0 children are
  renamed so.
- **The 0.7.0 rejection cases hold the 0.6.0 cases.** The 55 file names of
  the 0.6.0 directory are among the 100 of the 0.7.0 directory, each pair with
  the same `path` and `reason` (except two reasons: `root_missing_timeline`
  now reads that a file holds exactly one of timeline, group and bundle
  beside meta, and `statement_select_unknown_element` counts fourteen element
  types instead of ten), the two manifests equal once migrated (the
  0.7.0 one declaring 0.7.0), the two cases `migrate` refuses equal to the
  0.6.0 ones with `is_segment_line: false` on their timeline. The moved timeline
  document therefore rejects every 0.6.0 case at the same path.

`migrate(value)` returns a copy rewritten to `SCHEMA_VERSION` by an ordered
chain of steps, one per version after 0.5.0; 0.5.0 to 0.6.0 rewrites
`meta.schema_version` and nothing else; 0.6.0 to 0.7.0 rewrites it and writes
`is_segment_line: false` on every timeline (every 0.6.0 value is a timeline
file, and 0.6.0 knows no segment lines). It does not validate. What proves
it:

- **The pinned pairs.** `fixtures/migrations/0.5.0-to-0.6.0/before.json` is
  byte for byte `fixtures/0.5.0/bare.json` and
  `fixtures/migrations/0.6.0-to-0.7.0/before.json` byte for byte
  `fixtures/0.6.0/bare.json`; `dumps(migrate(before))` is byte for byte the
  `after.json` of the last pair, which differs from its `before.json` in the
  declared version and the root's `"is_segment_line": false`; the first
  pair's `after.json` differs from its `before.json` in the declared version
  only; the migrated value validates.
- **Only the declaration and the flag change.** For every 0.5.0 and every
  0.6.0 fixture, `migrate` gives its parsed value with the declaration
  `"0.7.0"` and `is_segment_line: false` added to every timeline, compared as
  text written by `dumps`.
- **The latest version is copied.** For every 0.7.0 fixture of every kind,
  `migrate` returns a value equal to its input that is not the input object.
- **The input is never changed.** After migrating a 0.5.0 and a 0.6.0 value,
  each input equals a fresh parse of its file, and changing the result's
  `meta` and `timeline` leaves the input unchanged (nothing is shared).
- **The chain reaches the latest version.** `bare.json` declaring each
  supported version migrates to a value declaring `SCHEMA_VERSION`, `"0.7.0"`.
- **Refusals.** A value declaring `"9.9.9"` or `"0.4.0"`, a value without
  `meta`, and a value whose `schema_version` is the number 5 raise
  `UnsupportedVersionError` with `version` `"9.9.9"`, `"0.4.0"`, `None` and
  `None`, and the message for `"9.9.9"` is exactly
  `unsupported schema_version '9.9.9'; this package supports 0.5.0, 0.6.0, 0.7.0`.

## File kinds and schema documents

From 0.7.0 on a file is a timeline file `{meta, timeline, graphical?}`, a
group file `{meta, timelines, group, graphical?}` or a bundle file `{meta,
timelines, bundle, graphical?}`, and the version has four schema documents:
`core` (the shared definitions), `timeline`, `group` and `bundle`. What proves
the layout and the dispatch:

- **Four documents, one version.** `SCHEMA_DOCUMENTS` and
  `schema_documents("0.7.0")` are `("core", "timeline", "group", "bundle")`;
  `schema_path("0.7.0", name)` is `schema/0.7.0/<name>.schema.json` and
  `schema_path("0.7.0")` the timeline document; each document's `$id` is
  `https://timetoalign.github.io/timeskeleton/0.7.0/<name>.schema.json`, so
  the file lies at its `$id`'s path below `schema/`. Every `$ref` of every
  document is either local (`#/$defs/<name>`, naming a definition of the same
  document) or relative to another document of the version
  (`<document>.schema.json#/$defs/<name>`, naming a definition of that
  document), and may continue with `/properties/<member>`, naming a member
  that definition declares; no reference is absolute. Definition names are
  unique across the four documents. `core` holds exactly `Coordinate`,
  `CoordinateNonnegative`, `Declaration`, `ElementType`, `Fraction`,
  `FractionNonnegative`, `FractionPositive`, `Graphical`, `Id`, `Meta`,
  `Number`, `NumberNonnegative`, `NumberPositive`, `NumberType`, `Paint`,
  `Selector`, `Statement` and `TimeUnit`: the graphical vocabulary is shared
  by the three file kinds, so the timeline document holds none of it.
- **The timeline definitions are 0.6.0's, moved, with three additions.** Rewriting
  every reference into `core` as a local one and every `{"$ref": Id, …}` as the
  inline id rule `{"type": "string", "pattern": …, …}` (the `children` keys'
  as `{"pattern": …}`, a key being a string) turns the union of the
  `core` and `timeline` definitions, without `Id` and `Meta`, and with the
  `is_segment_line` member removed from `TimelineManifest`'s `properties` and
  `required`, with `ElementType`'s last four values (`boundary`,
  `ancestor`, `group`, `card`) and its description reverted, and with the
  `Selector` member `inside` and the `Declaration` member `shadow` removed,
  into exactly 0.6.0's `$defs`; that member, those four element types and
  the two graphical members are the three additions ("Segment lines", "The
  graphical block"); the timeline document's root
  holds the members `meta` (a reference to `Meta`), `timeline` and
  `graphical` (a reference to `core`'s `Graphical`) as 0.6.0's does, and
  `Meta` is 0.6.0's `meta` with the constant `"0.7.0"` and the word "file" in
  its descriptions. Thirty-two `$ref`s name `Id`: the twenty-six `id` members
  of the timeline definitions, the `children` keys, a group's `id` and its
  `members` items, `MemberOrder` items, a bundle's `id`, and the keys of a
  bundle's `graphical.order`.
- **The group and bundle documents, literally.** The group file's members are
  `meta`, `timelines`, `group` and `graphical`, the first three required, no
  other admitted; `timelines` items are `timeline.schema.json#/$defs/TimelineManifest`.
  `Group` is closed over `id`, `name` (string or null), `meta` (object) and
  `members` (an array of distinct ids), all required. `GroupGraphical` is
  closed over `order`, a `MemberOrder` (an array of distinct ids), `styles`
  and `statements`, none required; `styles` and `statements` are exactly the
  references `core.schema.json#/$defs/Graphical/properties/styles` and
  `…/statements`, so they are `Graphical`'s members, never a copy. The bundle
  file's members are `meta`, `timelines`, `bundle` and `graphical`, the first
  three required; `Bundle` is closed over `id`, `name`, `meta`,
  `support_policy` (`omit`, `clamp` or `extrapolate`) and `groups` (items
  `group.schema.json#/$defs/Group`), all required; `BundleGraphical` is closed
  over `order`, an object whose keys are ids and whose values are
  `MemberOrder`s, and the same two references `styles` and `statements`. No
  member names claims: the shared cases
  `group_file_unknown_key` and `bundle_file_unknown_key` refuse a `claims`
  member at the file root, `bundle_unknown_key` one inside `bundle` (at
  `bundle`).
- **The kind decides the document.** `file_kind` returns `"timeline"`,
  `"group"` or `"bundle"` for a value holding exactly that one of the three
  members, and `None` for none, for two, and for a value that is no object.
  The test documents below validate, which they could not against another
  kind's document (each document admits only its own members). A 0.7.0 value
  with none of the three is rejected at the root with the message `exactly
  one of 'timeline', 'group' or 'bundle' is required; found none`, and one
  with `timeline` and `group` with `… found 'timeline', 'group'` (the shared
  case `file_kinds_several`). A value declaring `"9.9.9"` is rejected at
  `meta.schema_version` whether it holds a group or none of the three (its
  declaration is checked alone). A 0.6.0 value holding
  `timelines` and `group` instead of `timeline` is rejected at the root by the
  0.6.0 schema, not with the kind message: 0.6.0 knows timeline files only.

The tests build two valid documents from the 0.7.0 `bare` manifest (a
timeline of 8 quarters without name, children or maps):

- **the group document**: roots `piece` (with the child `second-half` at
  offset 4) and `recording`; the group `group_1`, name `"Second half"`,
  members `recording`, `second-half`; `graphical.order` `second-half`,
  `recording`;
- **the bundle document**: roots `annotations`, `page`, `performance`,
  `recording` (with the child `excerpt` at offset 2) and `score`; the bundle
  `bundle_1`, name `"Mixed"`, `support_policy` `omit`; groups `group_1`
  (members `performance`, `score`) and `group_2` (members `excerpt`, `page`);
  `graphical.order` `{group_1: [score, performance], group_2: [page,
  excerpt]}`. `annotations` is ungrouped, and `recording` is ungrouped while
  its child `excerpt` is a member.

The shared rejection cases are built from the same two documents, each with
one change.

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

## Identity

Every timeline, conversion map, region, break, jump and marker carries an
`id`; every `id` member and every `children` key matches
`^[^/\u0000-\u001f]+$` (non-empty, no `/`, no control character; spaces are
allowed). The schema cannot say that ids are unique across a manifest, nor
that a jump's `target` names a marker, so `identity_problems` checks both on
a schema-valid manifest and `validate` raises its first problem. What proves
it:

- **Identity order is stated.** A timeline's own id, then the ids of its
  conversion maps, regions, breaks, jumps and markers in array order, then its
  children's trees in code-point order of their keys. Each repeated id is one
  problem at its later occurrence, with the message
  `duplicate id '<id>', first at <pointer>`: with markers `m`, `m`, `bare` on
  the root `bare` and a child `c` holding a marker `m`, the three problems lie
  at `markers/1/id`, `markers/2/id` (first at `#/timeline/id`) and the
  child's `markers/0/id`, and `validate` reports the first. Two children
  keyed `ﬀ` and `😀` holding the same marker id report the `😀` child (code
  point order, which UTF-16 order would invert).
- **Targets stay within their timeline.** A jump targeting the root's marker
  `here` is accepted, a `null` target is accepted, `there` (a marker of the
  child only) is one problem at the root jump's `target`, and the child's
  jump targeting `here` is another (`'<target>' names no marker of this
  timeline`). Duplicates come before dangling targets.
- **Shared rejections**, one rule each: `id_duplicate_across_kinds` (a jump
  repeating a break's id), `id_with_slash`, `id_empty`, `id_control_character_tab`,
  `children_key_control_character_newline`, `jump_target_dangling` and
  `markers_object` (markers as an object keyed by name).
- **The schema states it literally** (the 0.6.0 schema; the 0.7.0 timeline
  document holds the same definitions, "File kinds and schema documents").
  `Region`, `Break`, `Jump` require `id`
  first; a region's `name` is a string or null; `Jump` holds `target` (string or null) instead of `target_name`;
  `Marker` is `{id, name, coordinate}` with a nullable `name`, closed; and
  `flow_control.markers` is an array of `Marker`. Twenty-six definitions carry
  an `id` member, every one with the pattern above. Every fixture has no
  identity problem.

## Segment lines

A segment line is a timeline containing only contiguous segments. From 0.7.0
on every timeline manifest, at every depth, carries the required boolean
`is_segment_line`, placed after `locked`, so `TimelineManifest` has fifteen
required members. A segment line's `class` is its segments' class, one of the
six; a nested segment line is one whose segments are segment lines
themselves. The schema cannot say that the segments are contiguous or alike,
so `identity_problems` checks every timeline whose `is_segment_line` is true,
after the duplicate ids and the jump targets, the tree in identity order
(a timeline, then its children by key). Its segments are visited in offset
order, ties by key in code-point order; for each segment:

- a `class` other than the segment line's, at the segment's
  `timeline/class`: `segment '<key>' of segment line '<id>' is no <class>`;
- an `is_segment_line` other than the first segment's, at the segment's
  `timeline/is_segment_line`: `segment '<key>' of segment line '<id>' differs
  from segment '<first key>' in is_segment_line`;
- an offset other than the end of the segment before it (0 for the first),
  at the segment's `offset`: `segment '<key>' of segment line '<id>' does not
  start at 0` or `… does not start where the one before it ends`;

and then, if the last segment does not end at the segment line's length (a
segment line without segments ends at 0), one problem at its `length`: `the
segments of segment line '<id>' do not end at its length`. A segment ends at
its offset plus its length; offsets, lengths and ends compare by exact value
(a float by its exact binary value), never through a float sum.

What proves it, with documents built from the 0.7.0 `bare` manifest (8
quarters, fraction coordinates):

- **Valid segment lines.** `bare` with `is_segment_line: true` and segments
  `a` (offset 0, length 3) and `b` (offset 3, length 5) has no problem; so has
  a nested segment line whose two segments are segment lines with two
  segments each; so has a segment line of length 0 without segments.
- **Each rule, one problem**, with the path and the message above: a segment
  of class `DiscreteLogicalTimeline`; the second segment a segment line while
  the first is not; segments starting at 1 (the first), and at 4 after one
  ending at 3 (a gap) and at 2 after one ending at 3 (an overlap), each at
  the offending `offset`; segments ending at 7 on a length of 8, and a
  segment line of length 8 without segments, at the `length`.
- **Offset order, not key order.** Segments keyed `z` (offset 0) and `a`
  (offset 3) are contiguous; with `a` at 4 the problem names `a`.
- **Exact values.** On a seconds axis (float coordinates) segments at 0.5
  (length 0.25) and 0.75 are contiguous, and segments at 0.1 (length 0.2) and
  0.3 are not (`0.1 + 0.2` is not exactly `0.3` in binary): the third
  segment's offset is reported, and the length, as the third segment's exact
  end misses it too.
- **Order and scope.** A document with a class problem, a flag problem, a gap
  and a short end yields them in that order, followed by the problems of the
  segments themselves (the offending segment, now a segment line without
  segments, does not end at its length); a segment line among the
  descendants is checked at its own path; a timeline with
  `is_segment_line: false` is never checked, whatever its children.
- **Shared rejections**: `segment_line_flag_missing` (at the timeline),
  `segment_line_flag_not_boolean`, `segment_line_segment_class`,
  `segment_line_segment_flag`, `segment_line_not_from_zero`,
  `segment_line_gap`, `segment_line_short_of_length`, and
  `group_root_segment_line_gap` (a segment line inside a group file's root,
  at `timelines/<i>/…`). Both validators report the same paths.
- **The fixture.** `segment_line.json`, emitted from timetoalign's
  `SegmentLine`, is a nested segment line of `ContinuousLogicalTimeline`
  segments in quarters, every coordinate a fraction (the library's default
  number type for quarters). Visited in identity order, its timelines are,
  as (id, name, `is_segment_line`, `locked`, absolute start, length):
  (`form`, `Form`, true, false, 0, 32), (`a`, `A`, true, true, 0, 8),
  (`a1`, null, false, true, 0, 8), (`b`, `B`, true, true, 8, 12), (`b1`,
  `b1`, false, true, 8, 6), (`b2`, `b2`, false, true, 14, 6), (`c`, `C`,
  true, true, 20, 12), (`c1`, null, false, true, 20, 12); every segment's
  offset in its line is its absolute start minus its line's, and the file
  has no problem. Every segment of `form` is a segment line, so the flag
  is one value per segment line; `a1` and `c1` have no name, so they draw
  no segment label.
- **Migration.** `migrate` from 0.6.0 writes `is_segment_line: false` on every
  timeline, the root and every descendant (the three levels of `nested`), and
  on nothing else.

## Identity in group and bundle files

The schema cannot say that ids are unique across the timelines of a file,
that a member names a timeline of the file, or that a display order is a
permutation of the members, so `identity_problems` checks them on a
schema-valid group or bundle file and `validate` raises its first problem.
The problems come in this order, each one problem per finding:

1. **Each root is its own scope.** The timeline-file rules apply to each root
   of `timelines` in array order, located under `timelines/<i>`: a jump
   target naming no marker of its timeline in root 1 is reported at
   `timelines/1/flow_control/jumps/0/target` (`timelines_root_jump_target_dangling`).
   Elements of different roots may share an id: a marker `m` in two roots is
   no problem.
2. **Part words are reserved.** In a group or bundle file an element that
   is no timeline (a conversion map, region, break, jump or marker) is
   addressed by its root's id and its own id joined by `/`, and its parts
   follow as `…/start`, `…/end`, `…/name` and `…/label`, and a timeline's
   card as `…/card`; so such an element may not carry one of those five
   words as its id, or `score/start` would name both. Visiting the roots in array order and each tree in identity
   order, each such id is one problem at that `id`, `id '<id>' is reserved
   in a group or bundle file`: a region `label` of root 1 at
   `timelines/1/regions/0/id` (`group_region_id_reserved`), and a region
   `card` of root 1 of a bundle file at the same path
   (`bundle_region_id_card`). Each of the five kinds is refused under each
   of the five words, in a group and in a bundle file; `starts` and `Start` are no part words. A timeline id
   may be one of the words (a timeline's parts are addressed by its own id),
   and a timeline file reserves none of them. The check follows the rules of
   every root (step 1), so a dangling target in root 1 comes before a
   reserved id in root 0.
3. **Timeline ids are unique across the file.** Visiting the roots in array
   order and each tree in identity order (a timeline, then its children by
   key), a timeline id equal to one of an earlier root is reported at its
   occurrence, `duplicate id '<id>', first at <pointer>`: a second root
   named `piece` at `timelines/1/id`, first at `#/timelines/0/id`
   (`timelines_id_duplicate_across_roots`), and a child `excerpt` of root 4
   repeating the child of root 3 at
   `timelines/4/children/excerpt/timeline/id` (`timelines_child_id_duplicate_across_roots`).
   A repetition within one root is that root's own problem (step 1) and is
   reported once.
4. **Group ids.** A group id equal to a timeline id is reported at the
   group's `id` with `duplicate id`, first at the timeline: `group/id`
   (`group_id_is_timeline_id`, `recording`) and `bundle/groups/1/id`
   (`bundle_group_id_is_timeline_id`, the descendant `excerpt`, first at
   `#/timelines/3/children/excerpt/timeline/id`); in a bundle, a group id
   equal to an earlier group's, first at that group
   (`bundle_group_id_duplicate`, at `bundle/groups/1/id`, first at
   `#/bundle/groups/0/id`).
5. **The bundle id.** In a bundle file, a bundle id equal to a timeline id
   (of a root or a descendant) or to a group id is one problem at
   `bundle/id`, `duplicate id '<id>', first at <pointer>`, the pointer naming
   the timeline, else the first group carrying that id:
   `bundle_id_is_timeline_id` (the descendant `excerpt`, first at
   `#/timelines/3/children/excerpt/timeline/id`) and `bundle_id_is_group_id`
   (`group_2`, first at `#/bundle/groups/1/id`). A bundle id equal to both a
   timeline id and a group id is one problem, first at the timeline (the
   group id repeating the timeline id is step 4's own problem).
6. **Members.** A member naming no timeline of the file is reported at the
   member, `'<id>' names no timeline of this file` (`group_member_dangling`
   at `group/members/0`; `bundle_member_dangling` at
   `bundle/groups/0/members/2`); in a bundle, a member already named by an
   earlier group, `duplicate member '<id>', first at <pointer>`
   (`bundle_member_in_two_groups`, `score` at `bundle/groups/1/members/2`,
   first at `#/bundle/groups/0/members/1`). A member nested in another
   member of the same group (its descendant at any depth) or containing one
   (its ancestor) is reported at the later of the two in array order: `member
   '<id>' lies inside member '<earlier id>' of the same group` or `member
   '<id>' contains member '<earlier id>' of the same group` (members share
   their start and end, but a child sits at its offset inside its parent, so
   both in one group would give two answers for one position). Only the first
   earlier member it nests with is named; a dangling member is not checked
   for nesting, a member of two groups is checked in each. Shared cases:
   `group_members_nested` (members `piece`, `recording`, `second-half`: at
   `group/members/2`, `member 'second-half' lies inside member 'piece' of the
   same group`) and `bundle_members_nested` (group `group_2` with members
   `excerpt`, `page`, `recording`: at `bundle/groups/1/members/2`, `member
   'recording' contains member 'excerpt' of the same group`). A child in one
   group and its root in another, or ungrouped, is no problem: the bundle
   document's `excerpt` (in `group_2`) with its root `recording` ungrouped,
   and with `recording` added to `group_1`, has no problem and validates.
7. **Every root of a group file contains a member.** A root containing none
   is reported at the root, `timeline '<id>' contains no member of the group`
   (`group_root_without_member`, `timelines/2`). A bundle's roots need none.
8. **Display orders are permutations.** In a group file, `graphical.order`;
   in a bundle file, each key of `graphical.order` in code-point order. A key
   naming no group is reported at the key, `'<key>' names no group of this
   bundle` (`bundle_order_unknown_group`); each entry that is not a member at
   the entry, `'<id>' is not a member of group '<group id>'`
   (`group_order_not_member`, `graphical/order/1`); then each member missing
   from the order at the order, `member '<id>' of group '<group id>' is
   missing` (`group_order_missing_member`, `bundle_order_missing_member`). A
   repeated entry is the schema's (`uniqueItems`, `group_order_repeated`). An
   absent `graphical`, an absent `order` and a bundle order without an entry
   for a group are no problem.

What proves it: the two test documents have no problem; each rule above is
one shared rejection case with exactly one problem, whose path both suites
assert, and a unit test states every message above literally; and one bundle
document carrying a finding of every step (a dangling target in root 0, a
region of root 0 whose id is the part word `end`, a
cross-root duplicate, a group id equal to a timeline id, a bundle id equal
to a group id, a dangling member, a member of two groups, an unknown order key, a stranger in an order and a
missing member) yields exactly the problems in the stated order, with their
paths and messages. A group id equal to a timeline id still names its group
for the display order, so it causes no further problem.

## The canonical order

The standard writer sorts the keys of every object by Unicode code point
(Python's `json.dumps(..., sort_keys=True)`), so object order needs no rule;
`children` in particular are written by key. Every array whose order carries
no meaning has one order: `conversion_maps` by id; `regions` by start, then
end, then id; flow-control `breaks` and `markers` by coordinate, then id;
`jumps` by from coordinate, then to coordinate, then id; in a group or bundle
file, `timelines` by id, a bundle's `groups` by id and every group's
`members`. Coordinates compare by exact numeric value, never by their JSON
spelling; strings by Unicode code point, never by UTF-16 code unit; ids are
unique, so no entries tie. Nothing else moves; in particular
`graphical.order` keeps its order. What proves it, asserted in both packages
with the same expected values:

- **It is the library's order.** Every fixture is written by timetoalign
  through the fixture script, which fails unless the library's own output
  equals the standard writer's, and every fixture is reproduced byte for byte
  by `dumps`.
- **Every tie, spelled out.** The `bare` fixture is extended with entries
  that tie at each level of every key, in an order that is not canonical, and
  the expected sequence of ids is stated literally: region bounds and break,
  jump and marker coordinates where numeric order and text order disagree
  (`[5, 8]` before `[2, 1]` and `[12, 1]`), regions tied on start and on
  start and end (`rd`, `rc`, `ra`, `rb`), breaks tied on coordinate (`kz`,
  `ka`, `kb`), jumps tied on both coordinates (`je`, `js`, `jd`, `jj`), and
  ids where code point order and UTF-16 order disagree (`"ﬀ"`, U+FB00, before
  `"😀"`, U+1F600, whose UTF-16 lead unit is 0xD83D: maps `B`, `B2`, `a2`,
  `ﬀ`, `😀`; markers `start`, `Coda`, `é`, `ﬀ!`, `😀!`). `canonical_order`
  leaves the children `z`, `m`, `b`, `a` as given, and the text `dumps`
  writes lists them `a`, `b`, `m`, `z` (inside `z`: `x`, `y`). The ordered
  result validates.
- **Keys sorted, literally.** A value with keys `b`, `😀`, `ﬀ`, `A` and a
  nested `z`, `10`, `2` is written as one literal text (`A` before `b`, `10`
  before `2` before `z`, `ﬀ` before `😀`) in both suites.
- **One canonical JSON text in both languages.** A literal value with nested
  objects and non-ASCII keys has one expected text in both suites, and the
  JavaScript text of every break and jump entry of every fixture equals the
  text Python's `json.dumps(entry, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False)` writes for the same file.
- **Group and bundle files.** The group document with its roots given as
  `recording`, `piece` and its members as `second-half`, `recording` is put in
  order `piece`, `recording` and `recording`, `second-half`, while
  `graphical.order` stays `second-half`, `recording`, and the manifests inside
  `timelines` are ordered as a timeline file's are (regions of `recording`
  given out of order come back sorted). The bundle document with its groups
  given as `group_2`, `group_1` and each group's members reversed comes back
  with `group_1`, `group_2` and sorted members; its `graphical.order` entries
  stay as given. Members `😀`, `ﬀ`, `b` are put in the order `b`, `ﬀ`, `😀`
  (code point order, which UTF-16 order would invert). A member that is no
  string (`5`) is refused (`cannot put members in canonical order`).
- **Only the file's arrays move.** `canonical_order` returns a copy and
  leaves its input unchanged; a value without a top-level `timeline`,
  `timelines`, `group` or `bundle` is copied as it is.

## The standard writer and lossless reading

Both packages export `dumps` (canonical order, then keys sorted by code
point, two-space indentation, a final newline, characters unescaped except `"`, `\` and control characters,
every float spelled as Python's `repr`, every integer without a decimal point)
and `canonical_order` / `canonicalOrder`. They must write the same value as
the same bytes. What proves it:

- **Every standard file round-trips.** Each of the 29 timeline, 9 group and
  9 bundle fixtures and the 100 rejection cases of the latest version (147
  files) is reproduced byte for byte by
  `dumps(json.loads(text))` in Python and by `dumps(parseJson(text))` in
  JavaScript. The JavaScript suite also reverses the keys of every object of
  every standard file, and the items of every array the canonical order sorts
  (fixtures only: a rejection case holds its manifest under `manifest`, which
  the order does not reach), and requires its `dumps` and Python's `dumps` to
  write the same bytes, equal to the file. `corpus_score_ms3` carries `→` and float-axis fixtures carry
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
  than written in some order (two regions without `start`).

## The fixture set

Fixtures are designed, not filtered: every entry of the fixture script's
builders emits exactly the files it builds. What proves the set:

- **The fixture set is stated literally.** The exact list of the 23 timeline
  file names of 0.6.0, and for 0.7.0 the same list with `locked_root.json`,
  `segment_children.json`, `segment_line.json`, `segment_pages.json`,
  `segment_pages_accolades.json` and `segment_pages_locked.json`;
  of the parangonar corpus the fixture script selects only
  `corpus_parangonar_parangonada__score_dlt_1` (a `DiscreteLogicalTimeline`
  with a `LinearMap`), by its id `score:dlt_1`. The group and bundle fixtures of 0.7.0 are
  emitted by the fixture script from timetoalign's `TimelineGroup.to_dict` and
  `AlignmentBundle.to_dict`, and stated literally: the groups
  `corpus_tilia`, `group_child_member`, `group_grandchild`,
  `group_number_types`, `group_parent_both`, `group_parent_exact`,
  `group_parent_right`, `group_parents_mixed`, `group_styled`; the bundles
  `bundle_mixed`, `bundle_shared_parent`, `bundle_ungrouped`, `corpus_ieee1599`, `corpus_listen_here`,
  `corpus_matchfile`, `corpus_mpm`, `corpus_parangonada`, `corpus_tilia`;
  `corpus_ieee1599` holds a nested segment line (an edition of pages of
  accolades).
  `fixture_paths("0.6.0", "group")` and `fixture_paths("0.6.0", "bundle")`
  are empty.

## The graphical block

The optional `graphical` block is the one of `docs/drawing.md` section 2:
`{"styles": {name: declaration}, "statements": [statement, ...]}`, both
optional; a statement `{"select", "set"}` whose `set` is a declaration or a
style name; the selector closed over `element` (the ten element types of
0.5.0 and 0.6.0; from 0.7.0 fourteen, the ten followed by `boundary`,
`ancestor`, `group` and `card`),
`ids` (a non-empty list of unique addresses), `domain`, `modality`, `class`
(the six timeline classes and the 21 conversion-map types the schema
defines), `within` and, from 0.7.0, `inside` (an element type); the
declaration closed over the eleven presentation properties `stroke`,
`stroke-width`, `stroke-dasharray`, `fill`, `opacity`, `font-size`, `rx`,
`display`, `side`, `content` and `max-width`, and from 0.7.0 also `shadow`
(a paint). What proves it:

- **The vocabulary is stated literally.** The members, enumerations,
  patterns and bounds of `Graphical`, `Statement`, `Selector`, `ElementType`,
  `Paint` and `Declaration`, the `class` enumeration as the timeline classes
  followed by every `type` constant of a conversion-map definition. The
  manifest's members are `meta`, `timeline` and `graphical`, the first two
  required, no other admitted.
- **0.7.0 adds four element types, `inside` and `shadow`.** The 0.7.0
  `ElementType` enumeration is 0.6.0's followed by `boundary`, `ancestor`,
  `group` and `card`; its `Selector` is 0.6.0's with the member `inside`
  (`{"$ref": "#/$defs/ElementType"}` and a description) added last, still
  closed; its `Declaration` is 0.6.0's with `shadow` (`{"$ref":
  "#/$defs/Paint"}`) added last. Each is accepted through one valid
  statement in the `graphical` block of `bare.json`: `{"select":
  {"element": "card"}, "set": {"rx": 5}}`, `{"select": {"inside":
  "ancestor"}, "set": {"opacity": 0.35}}` and `{"select": {"element":
  "card"}, "set": {"shadow": "#B8BEC8"}}`.
- **The defaults are a valid block.** The JSON block of `docs/drawing.md`
  section 4, read from the specification (the first `json` fence after the
  heading `## 4. Defaults`; three styles and 28 statements), validates as
  the `graphical` member of the 0.7.0 `bare.json`, so every default
  statement uses the vocabulary of the schema.
- **The styled fixtures.** `styled__score.json` and
  `styled__performance.json` are the only timeline files carrying a block,
  composed by the fixture script; their
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
- **Rejections.** Fourteen cases of each rejection directory, eight of them
  one change to `styled__score.json`, six one change to `bare.json`, with the path both validators report: an unknown
  selector member `kind` (the selector), the element type `segment` (the
  `element`), an empty `ids` list (the list), an unknown property `colour`
  (the `set`), a lower-case `stroke` (the `stroke`), the dash array `"3,3"`
  (the `stroke-dasharray`), `opacity` 1.5 (the `opacity`) and a `set` that is
  the number 5 (the `set`); plus a removed `projection` element and
  `show-projections` property, zero `max-width`, non-string `content`, an id
  holding a tab and a `children` key holding a newline. The 0.7.0 directory
  adds two, each one change to `styled__score.json`: a selector
  `{"inside": "segment"}`, refused at its `select/inside`
  (`statement_select_inside_unknown_element`), and a statement setting the
  lower-case `shadow` `#b8bec8` on the element `card`, refused at its
  `set/shadow` (`statement_set_shadow_lower_case`).
- **Group and bundle files (0.7.0).** A group file's and a bundle file's
  `graphical` holds `styles` and `statements` beside `order`, with the
  timeline file's vocabulary: the group document with the style `frame`
  `{"stroke": "#7F00FF"}` and the statements `{"select": {"element":
  "group"}, "set": "frame"}`, `{"select": {"element": "boundary"}, "set":
  {"stroke-width": 2}}` and `{"select": {"element": "ancestor", "ids":
  ["piece"]}, "set": {"opacity": 0.5}}` validates, and so does the bundle
  document with the same block beside its `order`; so the three new element
  types validate inside a group file's statement. An unknown member
  `arrangement` beside `order` is refused at `graphical` in either file
  (`group_graphical_unknown_key`); a group file's statement naming the
  element `segment` is refused at its `select/element`
  (`group_statement_select_unknown_element`), which shows that the shared
  rejection machinery reaches a group file's statements; an unknown
  property `colour` in a bundle file's named style is refused at the style,
  `graphical/styles/frame`. The 0.6.0 schema keeps its
  ten element types: a 0.6.0 statement naming `group` is refused at its
  `element`. `group_styled.json` is `group_number_types.json` (without
  `meta.generator`) plus exactly the `styles` `{"frame-highlight":
  {"stroke": "#7F00FF"}}` and the statements `{"select": {"element":
  "group"}, "set": "frame-highlight"}` and `{"select": {"element": "name",
  "ids": ["group_1/name"]}, "set": {"fill": "#7F00FF"}}` and `{"select":
  {"element": "card", "inside": "group"}, "set": {"shadow": "#C4B5FD", "rx":
  2}}`, its `order` unchanged.
- **Property bounds.** Exact validation tests accept `stroke-width` and `rx`
  at zero, `opacity` at both endpoints, positive `font-size` and `max-width`,
  `content` text and both forms of `stroke-dasharray`; they reject a negative
  width and radius, opacity outside either endpoint, zero font size and maximum
  width, non-text content and malformed dash text at the exact property path.
- **Names remain unrestricted.** A timeline name holding control characters
  validates; ids are covered under "Identity".

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
  `advances`, `ascender`, `descender`, `fallback` and `units_per_em`, in that
  (sorted) order, with `units_per_em`, `ascender`, `descender` and `fallback`
  2048, 1901, 483 (the `hhea` descender as a positive depth) and 1229 (the
  advance of glyph 0); `advances` holds 5918 code points, its keys sorted as
  strings, among them `"9833"` (♩) 966, `"48"` ("0") 1303
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

## Packaging

`docs/drawing.md` and the schema documents are part of the contract, so both
distributions carry them, and both carry the repository's MIT `LICENSE`.
The test builds the sdist and the wheel with `uv build` into a temporary
directory twice, the wheel once from the checkout (`--sdist --wheel`) and once
from the sdist (plain `uv build`, as the release does), and each time
requires `timeskeleton/docs/drawing.md` and
`timeskeleton/schema/0.7.0/<name>.schema.json` for the four documents in the
wheel and `src/timeskeleton/docs/drawing.md` and
`src/timeskeleton/schema/0.7.0/<name>.schema.json` in the sdist, each byte for
byte the repository's file; it also requires
`timeskeleton-<version>.dist-info/licenses/LICENSE` in the wheel and `LICENSE`
at the sdist root, each byte for byte the root `LICENSE` (the font's
`fonts/LICENSE` does not count).

## Generated artifacts

The package tests load the checked-in schema and fixtures that the build
bundles. JavaScript separately proves its generated TypeScript files do not
drift from a fresh generator run.

## Hermeticity

Tests obtain fixtures through package accessors, never relative paths. They use
no shared mutable input; the files a test writes (the font check's copy and
the built distributions) lie in its own temporary directory. Building the
distributions needs `uv`, and the network unless uv's cache already holds the
build backend.
