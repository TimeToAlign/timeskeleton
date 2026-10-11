# Fixtures

Every JSON file directly under `fixtures/0.5.0/` is a complete TimeSkeleton
manifest with one `{meta, timeline, graphical?}` object. The manifests are
emitted by timetoalign through `scripts/emit_fixtures.py`; that script is
their only writer. Regenerate them after a serialization change and review the
diff. Once tag `v0.5.0` exists, the script refuses to replace them.

The rejection cases under `fixtures/rejections/0.5.0/` are hand-authored.
Each changes one rule and records the path both validators must report. The
emission script does not touch them.

The [drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
pins how a manifest is drawn. A drawing is derived; these directories contain no drawing schema.

## Provenance

Each generated manifest records the timetoalign revision that produced it in
`meta.generator`:

```text
timetoalign <installed version> (<commit>)
```

To regenerate the manifests, run the script with an interpreter containing
the represented timetoalign revision:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C <timetoalign-checkout> rev-parse --short HEAD)"
```

The script writes each manifest with `timeskeleton.dumps` (object keys sorted
by code point, arrays in canonical order), reads it back, validates it, and
fails unless its timeline is stable through
`Timeline.from_dict(m).to_dict()`, compared with sorted keys and arrays as
they stand. A library whose array order differs from the canonical order
therefore fails the round trip. Every timeline, conversion map, region,
break, jump and marker carries an id; ids the script does not give are
minted by timetoalign and depend on the construction order in the script,
which is part of the fixture contract.

A builder that produces one top-level timeline uses `<builder>.json`. A
builder that produces several uses `<builder>__<slug>.json` for each
timeline, where `<slug>` is the timeline id with every character outside
`[A-Za-z0-9_-]` replaced by `_`. The script refuses two ids that would
produce the same file name.

## Manifest coverage

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

The corpus fixtures exercise public timetoalign loaders. A fixture is emitted
only when its structure (timeline classes, locks, conversion-map types,
region and flow-control counts, children, `graphical` block) differs from
every fixture emitted before it, and the synthetic fixtures are emitted
first, so no two fixtures pin the same combination:

| File or prefix | Loader input |
| --- | --- |
| `corpus_audio_audio.json` | an audio file |
| `corpus_midi_score_midi.json` | a score MIDI file |
| `corpus_score_ms3.json` | an ms3 score with measure-map and flow-control data |
| `corpus_supra_iiif.json` | an IIIF manifest |
| `corpus_parangonar_parangonada__score_dlt_1.json` | the discrete score timeline of a Parangonada alignment |

Every generated file carries the full timeline shape that timetoalign writes:
`name` is `null` when absent, placed children are locked, empty flow control
contains `breaks`, `jumps`, and `markers`, and absent measure maps and metric
hierarchies are `null`.

## Drawings

Each directory `fixtures/0.5.0/drawings/<name>/` pins one drawing of the
[drawing specification](https://github.com/TimeToAlign/timeskeleton/blob/main/docs/drawing.md)
with exactly three files:

- `inputs.json`, everything a drawing needs besides the manifest itself and
  the font, written with `dumps`:
  - `manifest`: the file name of the manifest in `fixtures/0.5.0/`;
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
for byte. Seven `figure.svg` files are derived by hand from the
specification alone and are never regenerated; `drawings/README.md` lists
them with their arithmetic. Every other figure, and every `inputs.json`, is
emitted by TimeLineEditor's writers with `pnpm emit-drawings --into
<timeskeleton checkout>` (run in its `app/packages/writers/`), which compares
the hand-derived SVGs with its own output instead of writing them.
Once tag `v0.5.0` exists, the script refuses to replace the drawings.

## Rejection coverage

The rejection cases cover the manifest root and metadata, timeline classes and
units, coordinate number forms and bounds, child offsets, conversion maps,
regions, flow control, measure maps, metric hierarchies, the
`graphical` block's selectors, declarations, and statement shapes, and the
identity rules `validate` checks beyond the schema: ids unique across a
manifest and jump targets naming a marker of their own timeline. Tests in
both packages load the same files and compare the reported path with the
case's expected path.

See the [main README](../README.md) for the schema API and canonical writer.
