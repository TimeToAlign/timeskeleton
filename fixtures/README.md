# Fixtures

The fixtures of the current version, 0.7.0, are kept in `fixtures/0.7.0/`,
its drawings in `fixtures/0.7.0/drawings/`, its rejection cases under
`fixtures/rejections/0.7.0/` and its warning cases under
`fixtures/warnings/0.7.0/`. Older versions and their fixtures live in the
git history and in their released packages.

Every generated fixture is a TimeSkeleton manifest of the one shape
`{timeskeleton, timelines, …}`, and every manifest is an alignment bundle.
The directories sort the manifests by content only:

- directly under `fixtures/0.7.0/`, manifests of one root timeline and no
  group;
- under `groups/`, manifests holding one group;
- under `bundles/`, manifests of several groups, several ungrouped roots,
  or both.

Version 0.7.0 has 36 manifests directly under `fixtures/0.7.0/`, 10 under
`groups/` and 9 under `bundles/`, 55 in all, each with its minimal twin, so
110 files. Beside them lie 85 rejection cases and 11 warning cases.

Every accepted fixture is written in the complete form, every key with a
default written with it, and has a **minimal twin** beside it,
`<name>.minimal.json`, the same manifest in the minimal form, as
timetoalign's `to_dict(minimal=True)` writes it. The two obey one law:
`minimal(fixture)` equals the twin, `complete(twin)` equals the fixture,
and the library reads both to equal objects. The manifests are emitted by
timetoalign through `scripts/emit_fixtures.py`; that script is their only
writer. Regenerate them after a serialization change and review the diff.
The script refuses to replace the fixtures of a version whose tag
`v<version>` exists, so a released version's fixtures stay as released.

The rejection cases under `fixtures/rejections/<version>/` and the warning
cases under `fixtures/warnings/<version>/` are hand-authored. The emission
script does not touch them.

The [drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
pins how a manifest is drawn. A drawing is derived; these directories contain no drawing schema.

## Provenance

Each generated manifest records the timetoalign revision that produced it
in its free `meta` object, under `generator`:

```text
timetoalign <installed version> (<commit>)
```

To regenerate the files, run the script with an interpreter containing
the represented timetoalign revision:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C <timetoalign-checkout> rev-parse --short HEAD)"
```

The script writes each manifest and its twin with `timeskeleton.dumps`
(object keys sorted by code point, arrays in canonical order), reads both
back, validates them, checks the law above, and fails unless the manifest
is stable through the library: read by the class that holds its content
(`Timeline.from_dict` for one root and no group, `TimelineGroup.from_dict`
for one group, `AlignmentBundle.from_dict` otherwise) and written back with
`to_dict()`, compared with sorted keys and arrays as they stand. A library
whose array order differs from the canonical order therefore fails the
round trip. A group's `graphical.order` is the library's own member order
and takes part in the round trip; a single timeline's `graphical` block is
composed by the script and does not. Every timeline, conversion map,
region, break, jump and marker carries an id; ids the script does not give
are minted by timetoalign and depend on the construction order in the
script, which is part of the fixture contract.

A builder that produces one root timeline, group or bundle uses
`<builder>.json` in its directory. A builder that produces several uses
`<builder>__<slug>.json` for each, where `<slug>` is its id with every
character outside `[A-Za-z0-9_-]` replaced by `_`. The script refuses two ids
that would produce the same file name.

## Coverage of single timelines

The six axis fixtures cover every combination of continuous or discrete with
logical, physical, or graphical:

| File | Construction | Coverage |
| --- | --- | --- |
| `continuous_logical.json` | 12 quarters with children at `1/3` and `2` | fraction coordinates |
| `discrete_logical.json` | 480 ticks with two children | integer logical coordinates |
| `continuous_physical.json` | 12.5 seconds with children at 0.5 and 6.0 | float physical coordinates |
| `discrete_physical.json` | 44100 samples with two children | integer physical coordinates |
| `continuous_graphical.json` | 600.0 points with two children | float graphical coordinates |
| `discrete_graphical.json` | 1920 pixels with two children | integer graphical coordinates |

The structural fixtures add focused examples:

| File | Coverage |
| --- | --- |
| `with_region.json` | a named region |
| `nested.json` | three levels of timelines |
| `flow_control.json` | a break, a jump, and a named marker the jump targets |
| `conversion_maps__*.json` | every registered conversion-map class, grouped by source timeline |
| `bare.json` | one named timeline |
| `contiguous.json` | children that touch and overlap |
| `map.json` | conversion maps on a root and a child |
| `styled__score.json`, `styled__performance.json` | `graphical.statements` selecting elements by type, id, class, domain, modality, and `within`, with a colour of its own for every drawn element and label of the score |
| `locked_root.json` | a root of 16 quarters locked at construction, with a child `coda` of 4 quarters at 12 |
| `segment_line.json` | a nested segment line of quarters: `form` (32) of the segments `a` (8), `b` (12) and `c` (12), each a segment line itself, `b` of `b1` and `b2` (6 each) |
| `segment_pages.json` | an unlocked segment line `pages` of four pages of 1754 pixels |
| `segment_pages_locked.json` | the same segment line, locked once built |
| `segment_pages_accolades.json` | an unlocked segment line of four pages, each a segment line of four accolades of 400, 450, 452 and 452 pixels |
| `segment_children.json` | an unlocked root of 32 quarters whose three children are segment lines, two of them overlapping |

The corpus fixtures exercise public timetoalign loaders; the synthetic
fixtures are emitted first:

| File or prefix | Loader input |
| --- | --- |
| `corpus_audio_audio.json` | an audio file |
| `corpus_midi_score_midi.json` | a score MIDI file |
| `corpus_score_ms3.json` | an ms3 score with measure-map and flow-control data |
| `corpus_supra_iiif.json` | an IIIF manifest |
| `corpus_parangonar_parangonada__score_dlt_1.json` | the discrete score timeline of a Parangonada alignment |

Every generated manifest is in the complete form timetoalign writes:
`name` is `null` when absent, every timeline states `number_type`,
`locked` and `is_segment_line`, empty flow control contains `breaks`,
`jumps`, and `markers`, and absent measure maps and metric hierarchies are
`null`. Its minimal twin leaves all of these out. The children of these
fixtures are locked, as timetoalign embeds a child by default, except the
segments: a segment is never locked, its segment line's lock governs it, so
its `locked` is `false` and is left out of the minimal form. A segment line
that is a child, a segment or a group member is locked by default, and
its `locked: true` stays in the minimal form, since the table's default is
`false`. A manifest may equally hold an unlocked child that is
not a segment line, whose `locked` is `false` and is left out of the
minimal form.

Two more manifests cover the manifest's own keys:

| File | Coverage |
| --- | --- |
| `negative_offset.json` | a root carrying a negative `offset`, its origin on its unit's absolute axis |
| `named_without_id.json` | a manifest with a `name` and no `id` |

No fixture holds a child with a negative `offset`: the schema and the
validators accept one, but timetoalign, which emits the fixtures, does not
support it yet, and no rejection case refuses one.

Six manifests draw timelines of unknown length (`length: null`), one case
each:

| File | Coverage |
| --- | --- |
| `unknown_length.json` | a root of unknown length with content |
| `unknown_length_empty.json` | a root of unknown length without content |
| `unknown_length_locked.json` | a locked root of unknown length |
| `unknown_length_child.json` | a child of unknown length in a parent of known length |
| `groups/group_unknown_length.json` | a group with a member of unknown length |
| `unknown_length_segments.json` | a segment line whose last segment has an unknown length |

## Coverage of groups and bundles

Every builder writes its files; the constructed files are built first. The
conversion maps of the constructed groups and bundles are of five kinds,
each id minted and no name given: a map to ticks (`QuartersToTicks`, 480 per
quarter), a tempo map to seconds (a `ScalarMap` of half a second per
quarter), a map to samples (`SecondsToSamples`, 44100 per second), a map to
seconds (`SamplesToSeconds`, 44100 per second) and a map to points (a
`ScalarMap` of 3/4 of a point per pixel). A repeat is a jump labelled
"Repeat" back to an earlier coordinate (`repeat_end`, `first_n`,
`repeat_count` 1).

| Builder | Construction |
| --- | --- |
| `group_number_types` | a group of three timelines whose axes have different number types (quarters as fractions, seconds as floats, pixels as integers), in a display order that differs from their id order |
| `group_child_member` | a group of the second half of a score, a child of the score placed at its exact offset, with a whole recording |
| `group_styled` | the group of `group_number_types` with conversion maps, a region, a jump and styling: the score has a map to ticks, the region "Theme" from 0 to 8 and a repeat from 8 back to 0, the performance a map to samples and the page a map to points; its `styles` and `statements` give every group frame the style `frame-highlight` (a violet stroke), fill the group's title `group_1/name` violet, and give every card inside a frame a light violet `shadow` and a corner radius `rx` of 2 |
| `group_parent_right` | a child `first-half` (8 quarters at 0) of a piece of 16 quarters, with a whole recording; the piece runs on to the right of the member |
| `group_parent_both` | as above with the child `middle` (8 quarters at 4); the piece runs on to both sides |
| `group_parent_exact` | as above with the child `whole` (16 quarters at 0); the piece coincides with the member |
| `group_parents_mixed` | three child members of different parents (an exposition of 32 quarters at 16 in a locked sonata of 48; a take of 25.5 seconds at 30.0 in a session of 90.0 seconds, with a map to samples; a system of 600 pixels at 0 in a page of 1754) and the root `audio` of 1323000 samples, with a map to seconds |
| `group_grandchild` | a grandchild `theme` (8 quarters at 8 in a movement of 16 quarters at 16 in a score of 64) with a recording of 12.0 seconds |
| `bundle_mixed` | the bundle "Mixed" of two groups, a score with its performance and a page with an excerpt (a child of a recording); `annotations` is ungrouped, and the recording, which no group names, contains the member `excerpt` and is drawn only as its ancestor line. The score has a map to ticks, then a tempo map to seconds, and a repeat from 8 back to 0; the performance a map to samples; the page a map to points; the excerpt a map to seconds; the recording a map to seconds, kept in the manifest and not drawn; `annotations` the regions "Verse" from 0 to 4 and "Chorus" from 4 to 12, and no map |
| `bundle_shared_parent` | the bundle "Sonata" of two groups whose members are two children of one score (an exposition at 0 and a recapitulation at 20, 12 quarters each), each with a take; a page is ungrouped, and the score, which no group names, contains both members and is drawn only as an ancestor line of each. Both children are segment lines: the exposition, with a map to ticks, of the segments "First theme" and "Second theme" of 6 quarters, the second with a tempo map to seconds; the recapitulation, with no map, of the segment lines "First theme" and "Second theme" of 6 quarters, each of the segments "Phrase 1" and "Phrase 2" of 3 quarters, and only its "Second theme" has a map to ticks. The take `take_1` is a segment line, with a map to samples, of "First theme" (14.0 seconds) and "Second theme" (16.0 seconds); the take `take_2` and the page carry no map. The score has a map to ticks, the region "Development" from 12 to 20 and a repeat from 12 back to 0, kept in the manifest and not drawn. A segment's id begins with its segment line's (`exposition_first`, `recapitulation_second_1`) |
| `bundle_ungrouped` | the bundle "Sketches" of three ungrouped roots and no group: a score of 16 quarters with a map to ticks and a da capo al fine, the break "Fine" at 8 (`fine`, `after_dc_ds`) and the jump "D.C. al Fine" from 16 back to 0 (`da_capo_al_fine`, `after_first`, `repeat_count` 1); a recording with a map to seconds; and an unlocked segment line, with a map to points, of three pages of 1754 pixels that carry none |

The corpus builders, prefixed `corpus_`, write the groups and bundles that
public timetoalign loaders create from corpus specimens: the group of a
TiLiA export, and the bundles of a Parangonada alignment, a Matchfile, an
MPM performance, an IEEE 1599 document, a Listen Here! export and a TiLiA
export. No bundle fixture carries MatchClaims.

Conversion maps, regions and flow control are spread over the constructed
groups and bundles and the single-timeline fixture `styled__score` so that
each case below occurs in one of them at least.
`group_number_types`, `group_child_member`, the three `group_parent_*` and
`group_grandchild` hold none of them, and `group_unknown_length` holds only
a region. The segment lines of the single-timeline fixtures
(`segment_line`, `segment_pages`, `segment_pages_locked`,
`segment_pages_accolades`, `segment_children` and
`unknown_length_segments`) and their segments carry no conversion map;
among the constructed fixtures, segment lines with maps occur only in
`bundle_shared_parent` and `bundle_ungrouped`, and a segment that is not a
segment line carries a map only in `bundle_shared_parent`.

| Case | Timeline |
| --- | --- |
| a logical segment line with a map, the child of a timeline that is not a segment line, and a group member | `exposition` of `bundle_shared_parent` |
| a segment line whose segments are segment lines, the child of a timeline that is not a segment line | `recapitulation` of `bundle_shared_parent` |
| a segment line that is a segment of a segment line, with a map, beside one without | `recapitulation_second` and `recapitulation_first` of `bundle_shared_parent` |
| a map on a segment that is not a segment line, joining its segment line's stack after the line's own map | `exposition_second` of `bundle_shared_parent` |
| a physical segment line with a map, a root and a group member | `take_1` of `bundle_shared_parent` |
| a graphical segment line with a map, an unlocked ungrouped root | `pages` of `bundle_ungrouped` |
| a map stack of two maps on one timeline, and flow control on a group member | `score` of `bundle_mixed` |
| a map on a root member and on a child member of a group | `performance` and `excerpt` of `bundle_mixed`; `audio` and `take` of `group_parents_mixed` |
| a map on a pixel axis | `page` of `bundle_mixed` and of `group_styled`; `pages` of `bundle_ungrouped` |
| regions on an ungrouped root | `annotations` of `bundle_mixed` |
| a map, children, a region and flow control on one timeline | `score` of `styled__score` |
| a map, a region and flow control on a root that contains group members and is drawn only as an ancestor line of each, kept in the manifest and not drawn | `score` of `bundle_shared_parent` |
| a break and a jump together | `score` of `bundle_ungrouped` |
| a map, a region and flow control inside a styled frame | `score` of `group_styled` |

## Drawings

Each directory `fixtures/<version>/drawings/<name>/` pins one drawing of the
[drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
as it stands in that version, with exactly three files; the drawings of the
current version follow `docs/drawing.md` as it stands, and those of a
released version follow the specification tagged with it.

The drawings of 0.7.0 are every fixture in the complete form but the corpus
ones (`corpus_*`) at the default placement, and nineteen variants. The
drawing of a manifest directly under `fixtures/0.7.0/` is named as the file
(`nested`); that of a manifest under `groups/` or `bundles/` as the
directory's singular and the file (`group__group_child_member`,
`bundle__bundle_mixed`). The variants draw `nested` at the lengths 200, 400
and 800 (`nested__length-<L>`), the spacings 0.5, 1 and 2
(`nested__spacing-<v>`), both 800 and 2 (`nested__length-800-spacing-2`),
in a box 120 wider and 60 higher than its content (`nested__box`), at scale
2 (`nested__scale-2`) and with the band order `["flow", "regions",
"children"]` (`nested__order-flow-regions-children`); `map` with an
application layer that moves the child's map `ticks` below its line,
selecting it by its address `melody/ticks` (`map__child-map-below`);
`bundle_mixed` with the places `{group_2: {x: 40, y: 200, width: 700},
annotations: {x: -30, length: 300}}` (`bundle_mixed__places`) and with the
places `{group_1: {scale: 1.25}, performance: {width: 650, height: 120}}`
(`bundle_mixed__cards`); `bundle_ungrouped` with the place `{score: {x: -60,
y: -150, height: 120}}` (`bundle_ungrouped__places`), with the place
`{recording: {scale: 1.5}}` (`bundle_ungrouped__scale`) and with the place
`{recording: {spacing: 2}}` (`bundle_ungrouped__spacing`); and `styled__score`
with the band order `["flow", "regions", "children"]`
(`styled__score__bands-block`), with the
`bands` `{score: ["flow", "children", "regions"]}`
(`styled__score__bands-timeline`), and with both, its root's `bands`
`{score: ["regions", "children", "flow"]}` outranking that order
(`styled__score__bands-both`): 62 drawings in all. Each directory holds:

- `inputs.json`, everything a drawing needs besides the manifest itself and
  the font, written with `dumps`:
  - `manifest`: the path of the manifest relative to the same version's
    directory (`nested.json`, `groups/group_child_member.json`);
  - `placement`: `length`, `spacing`, `width`, `height`, `order`, `bands`
    and `places`, all seven always written, defaults included (400, 1,
    `null`, `null`, `["children", "regions", "flow"]`, `{}`, `{}`);
  - `scale`: the scale `z` at which the writers place the drawing;
  - `layers`: the statement lists an application supplies, lowest
    precedence first. The defaults and the manifest's own `graphical` block
    are not repeated here: the layers of the drawing are the defaults, then
    these (an empty list when there are none), then the manifest's
    `graphical`, which no layer outranks.
- `figure.svg`: the SVG of the drawing alone, placed at `(0, 0)` with the
  scale `z`;
- `figure.tex`: the TikZ of the same placement, a standalone document with
  the font directory `.`.

Two implementations that follow the specification write both figures byte
for byte. Twenty-two `figure.svg` files are derived by hand from the
specification alone and are never regenerated, the six figures of
timelines of unknown length, `bundle_ungrouped__places`,
`bundle_ungrouped__scale`, `bundle_ungrouped__spacing` and
`styled__score__bands-timeline` among them;
`drawings/README.md` lists them with their arithmetic. Every other figure, and every `inputs.json`, is emitted by
TimeLineEditor's writers with `pnpm emit-drawings --into <timeskeleton
checkout>` (run in its `app/packages/writers/`), which compares the
hand-derived SVGs with its own output instead of writing them. The script
refuses to replace the drawings of a version whose tag `v<version>`
exists.

## Rejection coverage

Each rejection case changes one rule of an accepted manifest and records
the path both validators must report; a rule inside a timeline is located
under the root that holds it, `/timelines/0/…`. The cases cover the version
marker (absent, or another version), the manifest's own members, timeline
units, own-axis values and their representation (such as an integer on a
fraction axis, or an integer on a float axis that no float equals
exactly), a child without an `offset`, a child whose unit is not its
parent's, a child whose `offset` lies beyond its parent's known length, a
child ending beyond it, conversion
maps, regions,
flow control, measure maps, metric hierarchies, the `graphical` block's
selectors, declarations, statement shapes and `order`, segment lines (a
non-boolean `is_segment_line`, a segment with another `is_segment_line`
value, a segment that leaves a gap or
does not start at 0, segments that fall short of a known length), and the
identity rules `validate` checks beyond the schema: ids unique within a
root's tree, timeline ids, group ids and the manifest's id unique together,
the part words `start`, `end`, `name`, `label` and `card` refused as an id,
in a manifest of one root as in any other, jump targets naming a marker of
their own timeline, members naming timelines of the manifest, a timeline a
member of at most one group, no member of a group lying inside another, and
display orders that are permutations of their group's members. Tests in
both packages load the same files and compare the reported path with the
case's expected path.

## Warning cases

An unknown key is never an error. Each of the 11 warning cases under
`fixtures/warnings/<version>/` holds a manifest carrying unknown keys
together with the list that `unknown_keys` and `unknownKeys` must return
for it: `{path, key}` entries, sorted by path and then by key.
`several_depths` places them at every depth of a manifest; each of the
others holds one or two keys its object does not declare, among them keys
that earlier versions defined, such as `support_policy` or a timeline's
`class`. Python's `warning_paths()` lists the cases. Both packages read the
same files and compare their lists with it.

See the [main README](../README.md) for the manifest shape, the schema API
and the canonical writer.
