# Fixtures

Fixtures are kept per schema version in `fixtures/<version>/`, for 0.5.0,
0.6.0 and 0.7.0, the current version; a version's drawings lie in its
`drawings/` directory, and the rejection cases of each version under
`fixtures/rejections/<version>/`.

The generated fixtures are complete TimeSkeleton files, one directory per
file kind:

- every JSON file directly under `fixtures/<version>/` is a timeline file
  `{meta, timeline, graphical?}`;
- every JSON file under `fixtures/<version>/groups/` is a group file `{meta,
  timelines, group, graphical}`;
- every JSON file under `fixtures/<version>/bundles/` is a bundle file
  `{meta, timelines, bundle, graphical}`.

Versions 0.5.0 and 0.6.0 have timeline files only. Version 0.7.0 has 29
timeline files, 9 group files and 9 bundle files, 46 drawings and 100
rejection cases. The files are emitted by
timetoalign through `scripts/emit_fixtures.py`; that script is their only
writer. Regenerate them after a serialization change and review the diff;
`--kinds` followed by one or more of `timeline`, `group` and `bundle`
regenerates those kinds alone. The script refuses to replace the fixtures of
a version whose tag `v<version>` exists, so a released version's fixtures
stay as released.

The rejection cases under `fixtures/rejections/<version>/` are
hand-authored. Each changes one rule and records the path both validators
must report. The emission script does not touch them.

The migration pairs under `fixtures/migrations/` are hand-authored too
(section [Migrations](#migrations)).

The [drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
pins how a timeline manifest is drawn. A drawing is derived; these directories contain no drawing schema.

## Provenance

Each generated file records the timetoalign revision that produced it in
`meta.generator`:

```text
timetoalign <installed version> (<commit>)
```

To regenerate the files, run the script with an interpreter containing
the represented timetoalign revision:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C <timetoalign-checkout> rev-parse --short HEAD)"
```

The script writes each file with `timeskeleton.dumps` (object keys sorted
by code point, arrays in canonical order), reads it back, validates it, and
fails unless its content is stable through the library: a timeline file's
`timeline` through `Timeline.from_dict(m).to_dict()`, a group file without
its `meta` through `TimelineGroup.from_dict(m).to_dict()`, and a bundle file
without its `meta` through `AlignmentBundle.from_dict(m).to_dict()`, each
compared with sorted keys and arrays as they stand. A library whose array
order differs from the canonical order therefore fails the round trip. A
group's or bundle's `graphical.order` is the library's own member order and
takes part in the round trip; a timeline file's `graphical` block is composed
by the script and does not. Every timeline, conversion map, region,
break, jump and marker carries an id; ids the script does not give are
minted by timetoalign and depend on the construction order in the script,
which is part of the fixture contract.

A builder that produces one top-level timeline, group or bundle uses
`<builder>.json` in its kind's directory. A builder that produces several
uses `<builder>__<slug>.json` for each, where `<slug>` is its id with every
character outside `[A-Za-z0-9_-]` replaced by `_`. The script refuses two ids
that would produce the same file name.

## Timeline file coverage

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

Every generated file carries the full timeline shape that timetoalign writes:
`name` is `null` when absent, placed children, segments included, are
locked, empty flow control contains `breaks`, `jumps`, and `markers`, absent
measure maps and metric hierarchies are `null`, and from 0.7.0 on every
timeline states `is_segment_line`.

## Group and bundle file coverage

Every builder writes its files; the constructed files are built first:

| Builder | Construction |
| --- | --- |
| `group_number_types` | a group of three timelines whose axes have different number types (quarters as fractions, seconds as floats, pixels as integers), in a display order that differs from their id order |
| `group_child_member` | a group of the second half of a score, a child of the score placed at its exact offset, with a whole recording |
| `group_styled` | the group of `group_number_types` with `styles` and `statements`: every group frame takes the style `frame-highlight` (a violet stroke), the group's title `group_1/name` is filled violet, and every card inside a frame has a light violet `shadow` and a corner radius `rx` of 2 |
| `group_parent_right` | a child `first-half` (8 quarters at 0) of a piece of 16 quarters, with a whole recording; the piece runs on to the right of the member |
| `group_parent_both` | as above with the child `middle` (8 quarters at 4); the piece runs on to both sides |
| `group_parent_exact` | as above with the child `whole` (16 quarters at 0); the piece coincides with the member |
| `group_parents_mixed` | three child members of different parents (an exposition of 32 quarters at 16 in a locked sonata of 48, a take of 25.5 seconds at 30.0 in a session of 90.0 seconds, a system of 600 pixels at 0 in a page of 1754) and the root `audio` of 1323000 samples |
| `group_grandchild` | a grandchild `theme` (8 quarters at 8 in a movement of 16 quarters at 16 in a score of 64) with a recording of 12.0 seconds |
| `bundle_mixed` | a bundle of two groups, a score with its performance and a page with an excerpt of a recording (a child of the recording, whose root joins the bundle ungrouped), and one more ungrouped timeline |
| `bundle_shared_parent` | a bundle of two groups whose members are two children of one score (an exposition at 0 and a recapitulation at 20, 12 quarters each), each with a take; the score and a page are ungrouped |
| `bundle_ungrouped` | a bundle of three ungrouped roots and no group: a score, a recording and a segment line of three pages |

The corpus builders, prefixed `corpus_`, write the groups and bundles that
public timetoalign loaders create from corpus specimens: the group of a
TiLiA export, and the bundles of a Parangonada alignment, a Matchfile, an
MPM performance, an IEEE 1599 document, a Listen Here! export and a TiLiA
export. No bundle fixture carries MatchClaims.

## Drawings

Each directory `fixtures/<version>/drawings/<name>/` pins one drawing of the
[drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
as it stands in that version, with exactly three files; the drawings of the
current version follow `docs/drawing.md` as it stands, and those of a
released version follow the specification tagged with it.

The 46 drawings of 0.7.0 are every fixture of every kind but the corpus
ones (`corpus_*`) at the default placement, 35 in all, and eleven
variants. A timeline file's drawing is named as the file (`nested`), a
group or bundle file's as its directory's kind and the file
(`group__group_child_member`, `bundle__bundle_mixed`). The variants draw
`nested` at the lengths 200, 400 and 800 (`nested__length-<L>`), the
spacings 0.5, 1 and 2 (`nested__spacing-<v>`), both 800 and 2
(`nested__length-800-spacing-2`), in a box 120 wider and 60 higher than its
content (`nested__box`), at scale 2 (`nested__scale-2`) and with the band
order `["flow", "regions", "children"]`
(`nested__order-flow-regions-children`), and `map` with an application
layer that moves the child's map `ticks` below its line
(`map__child-map-below`). Each directory holds:

- `inputs.json`, everything a drawing needs besides the manifest itself and
  the font, written with `dumps`:
  - `manifest`: the path of the manifest relative to the same version's
    directory (`nested.json`, `groups/group_child_member.json`);
  - `placement`: `length`, `spacing`, `width`, `height` and `order`, all
    five always written, defaults included (400, 1, `null`, `null`,
    `["children", "regions", "flow"]`);
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
for byte. Some `figure.svg` files are derived by hand from the
specification alone and are never regenerated: twelve in 0.7.0, seven in
0.5.0 and in 0.6.0. Each version's `drawings/README.md` lists them with
their arithmetic. Every other figure, and every `inputs.json`, is
emitted by TimeLineEditor's writers with `pnpm emit-drawings --into
<timeskeleton checkout>` (run in its `app/packages/writers/`), which compares
the hand-derived SVGs with its own output instead of writing them.
The script refuses to replace the drawings of a version whose tag
`v<version>` exists.

## Rejection coverage

The rejection cases cover the file root and metadata, timeline classes and
units, coordinate number forms and bounds, child offsets, conversion maps,
regions, flow control, measure maps, metric hierarchies, the `graphical`
block's selectors, declarations, and statement shapes, and the identity rules
`validate` checks beyond the schema: ids unique across a manifest and jump
targets naming a marker of their own timeline. From 0.7.0 on they also cover
segment lines (a missing or non-boolean `is_segment_line`, a segment of
another class or another `is_segment_line` value, a segment that leaves a gap
or does not start at 0, segments that fall short of the segment line's
length), the file kinds (none or several of `timeline`, `group` and `bundle`),
the group and bundle file shapes and their `graphical` block (its `order`,
its statements, an unknown member), the selector member `inside` and the
property `shadow`, and the identity rules of group and bundle files: each
root its own scope, the part words `start`, `end`, `name`, `label` and
`card` refused as the id of a map, region, break, jump or marker, timeline
ids unique across the file, group ids distinct from timeline ids and from
each other, the bundle id distinct from every timeline and group id, members
naming timelines of the file, a timeline a member of at most one group, no
member of a group lying inside another, every root of a group file
containing a member, and display orders that are permutations of their
group's members. Tests in both packages load the same files and compare the reported
path with the case's expected path.

## Migrations

Each directory `fixtures/migrations/<from>-to-<to>/` pins one migration step
with two files: `before.json`, a file of version `<from>`, and
`after.json`, the standard text (`dumps`) of `migrate` applied to it. Both
packages migrate `before.json` and compare the result with `after.json` byte
for byte. In `0.5.0-to-0.6.0`, `before.json` is `fixtures/0.5.0/bare.json`,
and `after.json` differs from it only in `meta.schema_version`. In
`0.6.0-to-0.7.0`, `before.json` is `fixtures/0.6.0/bare.json`, and
`after.json` differs from it in `meta.schema_version` and in the timeline's
`is_segment_line: false`.

See the [main README](../README.md) for the file kinds, the schema API and the canonical writer.
