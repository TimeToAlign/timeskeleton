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

Version 0.7.0 has 43 manifests directly under `fixtures/0.7.0/`, 11 under
`groups/` and 9 under `bundles/`, 63 in all, each with its minimal twin, so
126 files. Beside them lie 105 rejection cases and 11 warning cases.

Every accepted fixture is written in the complete form, every key with a
default written with it, and has a **minimal twin** beside it,
`<name>.minimal.json`, the same manifest in the minimal form, as
timetoalign's `to_dict(minimal=True)` writes it. The two obey one law:
`minimal(fixture)` equals the twin, `complete(twin)` equals the fixture,
and the library reads both to equal objects. The manifests are emitted by
timetoalign through the catalogue and pipeline in `scripts/fixtures/`, with
`scripts/emit_fixtures.py` as its CLI; that pipeline is their only writer.
Regenerate them after a serialization change and review the diff. The CLI
refuses to replace the fixtures of a version whose tag
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

The package `scripts/fixtures/` holds the corpus: the builders in
`timelines.py`, `groups.py` and `bundles.py` (each builder's docstring
describes its case), the `graphical` blocks and the band-order manifests in
`graphical.py`, the ordered catalogue in `plan.py`, and the laws in
`verify.py`. A new case is appended to the catalogue within its directory.
The CLI writes each manifest and its twin with `timeskeleton.dumps` (object
keys sorted by code point, arrays in canonical order), reads both back,
validates them, checks the law above, and fails unless the manifest is
stable through the library: read by the class that holds its content
(`Timeline.from_dict` for one root and no group, `TimelineGroup.from_dict`
for one group, `AlignmentBundle.from_dict` otherwise) and written back with
`to_dict()` byte for byte, its arrays already in canonical order. A group's
display order in `graphical.order` is the library's own member order. The
`graphical` block the script composes for a manifest, its styles,
statements and band orders, is read back by the library, which keeps it as
written, and takes part in the round trip too: the library must write the
composed manifest back unchanged. Every timeline, measure map, conversion
map, region and flow-control element carries an ID; IDs the script does not give are
minted by timetoalign and depend on the construction order within the
builder, which is part of the fixture contract.

A catalogue case writes `<name>.json` in its directory. Several cases of
one name, such as the four of `conversion_maps`, write
`<name>__<slug>.json` each, where `<slug>` is the built object's ID with
every character outside `[A-Za-z0-9_-]` replaced by `_`. The script refuses
two IDs that would produce the same file name.

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
| `flow_control.json` | the flow marker `fine`, a repeat end taken twice to a named repeat start, and a dal segno to a named segno |
| `conversion_maps__*.json` | the conversion maps of one timeline per unit: `maps_quarters` every map type, a measure map read through its `MeasureRecordMap` and the three other measure views, a `CombinationMap` holding a measure view, and `TableMap`s of both kinds and the three extrapolations; `maps_ticks`, `maps_samples` and `maps_seconds` a `LinearMap` each; `maps_whole_notes` a measure map read through a `ChainMap` from whole notes |
| `bare.json` | one named timeline |
| `contiguous.json` | children that touch and overlap |
| `map.json` | conversion maps on a root and a child |
| `styled__score.json`, `styled__performance.json` | `graphical.statements` selecting elements by type, ID, class, domain, modality, and `within`, with a colour of its own for every drawn element and label of the score; the score's band order in `graphical.order` lays its markers band against its line above it and its conversion maps band against its line below it |
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
`locked` and `is_segment_line`, empty flow control is `[]`, and a
manifest without measure maps writes `measure_maps` as `[]`. Its minimal twin leaves all of these out. The children of these
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

Six manifests cover band orders and the bands of children (drawing
specification, section 6.4):

| File | Coverage |
| --- | --- |
| `map_child_band_order.json` | the timelines of `map`, with a band order for the child `phrase` alone that lays its conversion maps against its line below it |
| `map_root_band_order.json` | the timelines of `map`, with such a band order for the root `melody` and none for `phrase`, which follows the order of `melody` band by band |
| `styled_score_flow_inner.json` | `styled__score` with a band order whose flow control band lies nearer the line than its regions band |
| `joint_rows.json` | a root `piece` of 16 quarters whose children `b` and `d` each hold a child holding one more, so that each depth's two lines share a row and their children bands are laid out together, at two depths; `b` carries one map, `d1` and `d11` two each |
| `child_flow_control.json` | a root `piece` of 16 quarters whose child `verse` (8 at 4) holds a da capo al fine, the flow marker "Fine" at 4 and the jump origin "D.C. al Fine" at 8 back to 0, while the root holds no flow control |
| `child_jumps.json` | a root `piece` of 16 quarters whose child `verse` (8 at 4) holds the jump target `segno` at 2, the jump origin "Repeat" at 4, a repeat end taken twice back to the child's start, and the jump origin "D.S." at 8, a dal segno to `segno`, while the root holds no flow control |

## Coverage of groups and bundles

Every builder writes its files; the constructed files are built first. The
conversion maps of the constructed groups and bundles are of five kinds,
each a `LinearMap`, each ID minted and no name given: a map to ticks (480
per quarter), a tempo map to seconds (half a second per quarter), a map to
samples (44100 per second), a map to seconds (1/44100 of a second per
sample) and a map to points (3/4 of a point per pixel). A repeat is a jump
origin labelled "Repeat" back to an earlier coordinate (`repeat_end`,
`repeat_count` 1).

| Builder | Construction |
| --- | --- |
| `group_number_types` | a group of three timelines whose axes have different number types (quarters as fractions, seconds as floats, pixels as integers), in a display order that differs from their ID order |
| `group_child_member` | a group of the second half of a score, a child of the score placed at its exact offset, with a whole recording |
| `group_styled` | the group of `group_number_types` with conversion maps, a region, a jump origin and styling: the score has a map to ticks, the region "Theme" from 0 to 8 and a repeat from 8 back to 0, the performance a map to samples and the page a map to points; its `styles` and `statements` give every group frame the style `frame-highlight` (a violet stroke), fill the group's title `group_1/name` violet, and give every card inside a frame a light violet `shadow` and a corner radius `rx` of 2 |
| `group_parent_right` | a child `first-half` (8 quarters at 0) of a piece of 16 quarters, with a whole recording; the piece runs on to the right of the member |
| `group_parent_both` | as above with the child `middle` (8 quarters at 4); the piece runs on to both sides |
| `group_parent_exact` | as above with the child `whole` (16 quarters at 0); the piece coincides with the member |
| `group_parents_mixed` | three child members of different parents (an exposition of 32 quarters at 16 in a locked sonata of 48; a take of 25.5 seconds at 30.0 in a session of 90.0 seconds, with a map to samples; a system of 600 pixels at 0 in a page of 1754) and the root `audio` of 1323000 samples, with a map to seconds |
| `group_grandchild` | a grandchild `theme` (8 quarters at 8 in a movement of 16 quarters at 16 in a score of 64) with a recording of 12.0 seconds |
| `bundle_mixed` | the bundle "Mixed" of two groups, a score with its performance and a page with an excerpt (a child of a recording); `annotations` is ungrouped, and the recording, which no group names, contains the member `excerpt` and is drawn only as its ancestor line. The score has a map to ticks, then a tempo map to seconds, and a repeat from 8 back to 0; the performance a map to samples; the page a map to points; the excerpt a map to seconds; the recording a map to seconds, kept in the manifest and not drawn; `annotations` the regions "Verse" from 0 to 4 and "Chorus" from 4 to 12, and no map |
| `bundle_shared_parent` | the bundle "Sonata" of two groups whose members are two children of one score (an exposition at 0 and a recapitulation at 20, 12 quarters each), each with a take; a page is ungrouped, and the score, which no group names, contains both members and is drawn only as an ancestor line of each. Both children are segment lines: the exposition, with a map to ticks, of the segments "First theme" and "Second theme" of 6 quarters, the second with a tempo map to seconds; the recapitulation, with no map, of the segment lines "First theme" and "Second theme" of 6 quarters, each of the segments "Phrase 1" and "Phrase 2" of 3 quarters, and only its "Second theme" has a map to ticks. The take `take_1` is a segment line, with a map to samples, of "First theme" (14.0 seconds) and "Second theme" (16.0 seconds); the take `take_2` and the page carry no map. The score has a map to ticks, the region "Development" from 12 to 20 and a repeat from 12 back to 0, kept in the manifest and not drawn. A segment's ID begins with its segment line's (`exposition_first`, `recapitulation_second_1`) |
| `bundle_ungrouped` | the bundle "Sketches" of three ungrouped roots and no group: a score of 16 quarters with a map to ticks and a da capo al fine, the flow marker "Fine" at 8 (`fine`) and the jump origin "D.C. al Fine" at 16 back to 0 (`da_capo_al_fine`); a recording with a map to seconds; and an unlocked segment line, with a map to points, of three pages of 1754 pixels that carry none |
| `group_measure_map` | the group "Edition" of a score of 16 quarters and its MIDI rendering of 7680 ticks, both reading one entry of `measure_maps`, four bars of 4/4: the score through its `MeasureRecordMap`, the rendering through a `ChainMap` of the `LinearMap` `ppq` to quarters (480 ticks per quarter) and its `MeasureRecordMap` |

The corpus builders, prefixed `corpus_`, write the groups and bundles that
public timetoalign loaders create from corpus specimens: the group of a
TiLiA export, and the bundles of a Parangonada alignment, a Matchfile, an
MPM performance, an IEEE 1599 document, a Listen Here! export and a TiLiA
export. No bundle fixture carries MatchClaims.

Conversion maps, regions and flow control are spread over the constructed
groups and bundles and the single-timeline fixtures `styled__score`,
`unknown_length_child`, `unknown_length_segments`, `child_flow_control`
and `child_jumps`
so that each case below occurs in one of them at least.
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
| a flow marker and a jump origin together | `score` of `bundle_ungrouped` |
| a map, a region and flow control inside a styled frame | `score` of `group_styled` |
| a region on a child | `movement` of `unknown_length_child` |
| regions on segments without a line of their own, joining their segment line's regions band | `a` and `c` of `unknown_length_segments` |
| a flow marker and a jump origin on a child, its root holding none | `verse` of `child_flow_control` |
| a jump target, a repeat end with a repeat count and a targeted dal segno on a child, its root holding none | `verse` of `child_jumps` |
| a measure map shared by two timelines, one reading it through a `ChainMap` from ticks | `score` and `midi` of `group_measure_map` |

The defaults hide the markers, regions and flow control bands of every
timeline held by a band, every timeline of a member drawing but its root
(drawing specification, section 4). So a child's regions or flow control,
or a segment's, is drawn in a figure only where a statement of the manifest
or an application layer displays its band: the drawings
`unknown_length_child__regions-shown`,
`unknown_length_segments__regions-shown` and
`child_flow_control__flow-shown` add such a layer (Drawings, below).

## Drawings

Each directory `fixtures/<version>/drawings/<name>/` pins one drawing of the
[drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
as it stands in that version, with exactly three files; the drawings of the
current version follow `docs/drawing.md` as it stands, and those of a
released version follow the specification tagged with it.

The drawings of 0.7.0 are every fixture in the complete form but the corpus
ones (`corpus_*`) at the default placement, and eighteen variants. The
drawing of a manifest directly under `fixtures/0.7.0/` is named as the file
(`nested`); that of a manifest under `groups/` or `bundles/` as the
directory's singular and the file (`group__group_child_member`,
`bundle__bundle_mixed`). The variants draw `nested` at the lengths 200, 400
and 800 (`nested__length-<L>`), with the card spacings 0 and 8 of its one card
(`nested__card-spacing-<S>`), with both the length 800 and the card spacing
8 (`nested__length-800-card-spacing-8`), in a box 120 wider and 60 higher than its content (`nested__box`) and at
scale 2 (`nested__scale-2`); `bundle_mixed` with the places `{group_2: {x:
40, y: 200, width: 700}, annotations: {x: -30, length: 300}}`
(`bundle_mixed__places`) and with the places `{group_1: {scale: 1.25},
performance: {width: 650, height: 120}}` (`bundle_mixed__cards`), with
the frame spacing `{group_1: {spacing: 16}}`, the gap between the frame's
two cards (`bundle_mixed__frame-spacing-16`), and with the card spacing
`{score: {spacing: 8}}` of a member card, which deepens the arc of
`score`'s jump origin (`bundle_mixed__member-card-spacing-8`);
`bundle_ungrouped` with the place `{score: {x: -60, y: -150, height: 120}}`
(`bundle_ungrouped__places`), with the place `{recording: {scale: 1.5}}`
(`bundle_ungrouped__scale`) and with the box's spacing 24 and the card
spacing `{score: {spacing: 8}}`, which deepens `score`'s flow control band
(`bundle_ungrouped__spacing`); and three manifests with an application
layer of one statement that sets `display` to `inline` on bands the
defaults hide: `unknown_length_child` on the band `movement/regions_1`
(`unknown_length_child__regions-shown`), `unknown_length_segments` on every
regions band, `{"element": "band", "class": "regions"}`
(`unknown_length_segments__regions-shown`), and `child_flow_control` on the
band `verse/flow_control_1` (`child_flow_control__flow-shown`): 66 drawings
in all. No variant sets a band order: band orders are the manifests' own,
in their `graphical.order` (`styled__score`, `styled_score_flow_inner`,
`map_child_band_order`, `map_root_band_order`). Each directory holds:

- `inputs.json`, everything a drawing needs besides the manifest itself and
  the font, written with `dumps`:
  - `manifest`: the path of the manifest relative to the same version's
    directory (`nested.json`, `groups/group_child_member.json`);
  - `placement`: `length`, `spacing`, `width`, `height` and `places`, all
    five always written, defaults included (400, 8, `null`, `null`, `{}`);
    `spacing` is the box's, the gap between its items at their default
    `y`, and a place's `spacing` the gap between that frame's cards or that
    card's rows and bands (drawing specification, section 8.6);
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
for byte. Twenty-eight `figure.svg` files are derived by hand from the
specification alone and are never regenerated, among them every drawing of
a timeline of unknown length, the three variants of `bundle_ungrouped`, the
three variants that display a band the defaults hide, the band orders of
`styled_score_flow_inner`, `map_child_band_order` and
`map_root_band_order`, and `joint_rows`; `drawings/README.md` lists them
with their arithmetic. Every other figure, and every `inputs.json`, is
emitted by TimeLineEditor's writers with `pnpm emit-drawings --into
<timeskeleton checkout>` (run in its `app/packages/writers/`), which
compares the hand-derived SVGs with its own output instead of writing them.
The script refuses to replace the drawings of a version whose tag
`v<version>` exists.

## Rejection coverage

Each rejection case breaks one rule of an accepted manifest and records the
`path` and the `code` both validators must report, and a `reason`. A rule
inside a timeline is located under the root that holds it, `/timelines/0/…`.
Tests in both packages load the same files and compare the error's path and
code with the case's. The cases cover every code:

| Code | Rule | Cases |
| --- | --- | --- |
| `not_a_manifest` | the value is an object holding `timeskeleton` | `root_missing_marker` |
| `finite_number` | every number is finite | `infinite_length`, `nan_offset` |
| `schema` | the schema document | 54 cases named after the member they break: units and number types, lengths and offsets (a Fraction member with a fractional part, `length_fraction_member_not_integral`, among them), IDs, conversion maps, flow control, measure maps, groups, `graphical` selectors, declarations and `order` |
| `representation` | an own-axis value can be read as its axis's number type, however it is spelled | `length_int_on_fraction_axis`, `length_fraction_on_int_axis`, `length_float_on_int_axis`, `float_axis_int_not_exact`, `region_start_float_on_fraction_axis`, `child_offset_fraction_on_float_axis` |
| `duplicate_id` | IDs unique within a root's tree, a map another map holds included; timeline, group and measure-map IDs unique together | `id_duplicate_across_kinds`, `nested_map_id_duplicate`, `timelines_id_duplicate_across_roots`, `timelines_child_id_duplicate_across_roots`, `group_id_duplicate`, `group_id_is_timeline_id`, `group_id_is_descendant_id`, `measure_map_id_is_timeline_id` |
| `dangling_target` | a jump origin's target names a jump target of its own timeline, a measure view's `measure_map` an entry of `measure_maps` | `jump_target_flow_marker`, `timelines_root_jump_target_dangling`, `measure_view_dangling` |
| `conversion_map` | a `TableMap`'s x and y values agree in length and its x values increase strictly; a `PiecewiseMap` has one map fewer than breaks, and its breaks increase strictly | `table_map_lengths_differ`, `table_map_x_not_increasing`, `piecewise_map_maps_count`, `piecewise_map_breaks_not_increasing` |
| `child_unit` | a child has its parent's unit | `child_unit_differs` |
| `child_offset` | a child starts within its parent's known length | `child_offset_beyond_parent` |
| `child_end` | a child ends within its parent's known length | `child_end_beyond_parent` |
| `segment_line` | segments run contiguously from 0 to the line's length, with one `is_segment_line` value | `segment_line_not_from_zero`, `segment_line_gap`, `segment_line_gap_in_later_root`, `segment_line_short_of_length`, `segment_line_segment_flag` |
| `reserved_id` | the part words and the band IDs are no ID, nor the ID of a map another map holds | `part_word_timeline_id`, `part_word_region_card`, `part_word_region_label`, `part_word_one_root`, `band_id_region`, `nested_map_id_reserved` |
| `manifest_id` | the manifest's ID is no timeline, group or measure-map ID | `manifest_id_is_group_id`, `manifest_id_is_descendant_id`, `manifest_id_is_measure_map_id` |
| `group_member` | a member names a timeline, lies in one group, and neither contains nor lies inside another member of its group | `member_dangling`, `member_in_two_groups`, `members_contain_member`, `members_inside_member` |
| `order_key` | a key of `graphical.order` names a group or a timeline | `order_unknown_group` |
| `display_order` | a group's display order is a permutation of its members | `group_order_not_member`, `order_missing_member` |
| `band_order` | a band order is a permutation of its timeline's ID and five bands | `band_order_unknown_entry`, `band_order_missing_band` |

`version_unknown` names another version; its `code` is `null` and its
`"error": "UnsupportedVersionError"` names the error both packages raise
instead. JSON has no non-finite number, so the two `finite_number` cases hold
a finite placeholder at their path and name in `non_finite` (`"Infinity"` or
`"NaN"`) the value a test puts there before validating; Python's
`timeskeleton.rejection_case` reads a case with that value in place.

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
