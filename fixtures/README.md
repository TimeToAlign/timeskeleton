# Fixtures

Every JSON file directly under `fixtures/0.4.0/` is a complete TimeSkeleton
manifest with one `{meta, timeline, graphical?}` object. The manifests are
emitted by timetoalign through `scripts/emit_fixtures.py`; that script is
their only writer. Regenerate them after a serialization change and review the
diff. Once tag `v0.4.0` exists, the script refuses to replace them.

The rejection cases under `fixtures/rejections/0.4.0/` are hand-authored.
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

The script writes each manifest with `timeskeleton.dumps`, reads it back, and
fails unless its timeline is stable through
`Timeline.from_dict(m).to_dict()`. A library whose order differs from the
canonical order therefore fails the round trip. Timeline and conversion-map
ids depend on the construction order in the script, which is part of the
fixture contract.

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
| `flow_control.json` | a break, a jump, and a named marker |
| `conversion_maps__*.json` | every registered conversion-map class, grouped by source timeline |
| `bare.json` | one named timeline |
| `contiguous.json` | children that touch and overlap |
| `map.json` | conversion maps on a root and a child |
| `styled__score.json`, `styled__perf.json` | `graphical.statements` selecting elements by type, id, domain, and `within` |

The corpus fixtures exercise public timetoalign loaders:

| File or prefix | Loader input |
| --- | --- |
| `corpus_audio_audio.json` | an audio file |
| `corpus_midi_score_midi.json` | a score MIDI file |
| `corpus_score_ms3.json` | an ms3 score with measure-map and flow-control data |
| `corpus_supra_iiif.json` | an IIIF manifest |
| `corpus_parangonar_parangonada__*.json` | the timelines of one Parangonada alignment |

Every generated file carries the full timeline shape that timetoalign writes:
`name` is `null` when absent, placed children are locked, empty flow control
contains `breaks`, `jumps`, and `markers`, and absent measure maps and metric
hierarchies are `null`.

## Rejection coverage

The rejection cases cover the manifest root and metadata, timeline classes and
units, coordinate number forms and bounds, child offsets, conversion maps,
regions, flow control, measure maps, metric hierarchies, and the
`graphical` block's selectors, declarations, and statement shapes. Tests in
both packages load the same files and compare the reported path with the
case's expected path.

See the [main README](../README.md) for the schema API and canonical writer.
