# Golden fixtures

Every file under `fixtures/<schema version>/` is a complete TimeSkeleton
document emitted by timetoalign through `scripts/emit_fixtures.py`. The
script is the only writer of those directories: golden fixtures are never
edited by hand, and a change to the library's serialization is landed by
regenerating them and reviewing the diff. Once the tag `v<version>` exists,
the script refuses to write into `fixtures/<version>/`: a released version's
fixtures are frozen.

The rejection cases under `fixtures/rejections/` and the migration pairs
under `fixtures/migrations/` are different: they are authored by hand, each
for the one rule or migration step it pins, and the script never touches
them.

## Provenance

The schema describes timetoalign's current trunk, which is ahead of the
version on PyPI. Each document records the exact revision it was produced
with in `meta.generator`:

```
timetoalign <installed version> (<commit>)
```

that is, the installed version of timetoalign and the commit of
https://github.com/timetoalign/timetoalign it was built from. To regenerate, run the script
with an interpreter that has that revision (or a later one) installed:

```
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C <timetoalign checkout> rev-parse --short HEAD)"
```

The script writes the documents with the standard writer, `dumps`, reads them
back, and fails unless every timeline manifest is stable, as JSON text, after
`Timeline.from_dict(m).to_dict()`; a library whose own order differs from the
canonical order therefore fails it. Timeline ids are assigned by
the library in construction order and therefore depend on the order of the
script, which is part of the fixture contract.

## Schema 0.1.0

Nine documents. Six cover the timeline classes, one per class, each with two
children at offsets represented as an exact `Fraction` pair or a JSON float.
Each coordinate records its unit and number type alongside that selected value
representation.

| File | Built from | Proves |
|---|---|---|
| `continuous_logical.json` | `ContinuousLogicalTimeline(length=12, unit="quarters")`; children of lengths 4 and 3 at offsets `Fraction(1, 3)` and `2` | a `fraction` axis: every coordinate has a `[numerator, denominator]` value, including the non-integer offset `[1, 3]` |
| `discrete_logical.json` | `DiscreteLogicalTimeline(length=Fraction(480), unit="ticks")`; children `Fraction(120)` and `Fraction(96)` at offsets `Fraction(3)` and `Fraction(7)` | an `int` axis with JSON integer values |
| `continuous_physical.json` | `ContinuousPhysicalTimeline(length=12.5, unit="seconds")`; children 4.25 and 3.0 at offsets 0.5 and 6.0 | a `float` axis with JSON number values |
| `discrete_physical.json` | `DiscretePhysicalTimeline(length=Fraction(44100), unit="samples")`; children `Fraction(11025)` and `Fraction(2205)` at offsets `Fraction(100)` and `Fraction(20000)` | an `int` axis with JSON integer values in the physical domain |
| `continuous_graphical.json` | `ContinuousGraphicalTimeline(length=600.0, unit="points")`; children 200.0 and 150.0 at offsets 10.0 and 300.0 | a `float` axis in the graphical domain |
| `discrete_graphical.json` | `DiscreteGraphicalTimeline(length=Fraction(1920), unit="pixels")`; children `Fraction(640)` and `Fraction(480)` at offsets `Fraction(16)` and `Fraction(1000)` | an `int` axis with JSON integer values in the graphical domain |
| `with_region.json` | the `continuous_logical` construction plus `create_region("theme", 2, 6)` | a populated `regions` array; its items are opaque objects in 0.1.0 |
| `empty.json` | no timelines | the smallest valid document: an empty `timelines` map |
| `nested.json` | `ContinuousLogicalTimeline(length=16, unit="quarters")` with a child of length 8 at offset 4 that holds a child of length 2 at offset `Fraction(3, 2)` | three levels of nesting through the recursive `children` member |

Observed properties of the library's output that the fixtures pin: `name` is
`null` when no name was given; a child added to a parent is emitted with
`locked: true`; `flow_control` is emitted as `{"breaks": [], "jumps": [],
"markers": {}}`; `measure_map` and `metric_hierarchy` are `null` when absent.

## Schema 0.2.0

The nine synthetic documents are rebuilt at 0.2.0 from the same constructor
calls described above. The additional documents exercise the members that 0.2.0
specifies. No library loader produces a `ContinuousGraphicalTimeline`, so the
synthetic `continuous_graphical.json` remains its coverage.

| File | Built from | Proves |
|---|---|---|
| `continuous_graphical.json` | synthetic timeline constructor | continuous graphical timeline |
| `continuous_logical.json` | synthetic timeline constructor | continuous logical timeline |
| `continuous_physical.json` | synthetic timeline constructor | continuous physical timeline |
| `discrete_graphical.json` | synthetic timeline constructor | discrete graphical timeline |
| `discrete_logical.json` | synthetic timeline constructor | discrete logical timeline |
| `discrete_physical.json` | synthetic timeline constructor | discrete physical timeline |
| `empty.json` | synthetic empty document | minimum document |
| `nested.json` | synthetic nested timelines | recursive children |
| `with_region.json` | synthetic timeline and `create_region` | region serialization |
| `conversion_maps.json` | public map constructors and `add_conversion_map` | all registered conversion-map classes |
| `flow_control.json` | public flow-control methods | breaks, jumps, and markers |
| `corpus_audio_audio.json` | `AudioLoader` on `audio/` | continuous physical timeline |
| `corpus_midi_score_midi.json` | MIDI loader on `midi/` | discrete logical timeline |
| `corpus_parangonar_parangonada.json` | Parangonada loader on `parangonar/` | discrete physical timeline |
| `corpus_score_ms3.json` | `Ms3Loader` on `score/` (`out_of_the_flow_experience-flow_only`) | flow control and 14 compressed Measure Map rows representing 15 measures, with successors in `next` as row IDs; the anacrusis (count 1) and the second constituent of the split bar 9 (count 14) carry `offset_within_measure` (`[3, 1]` and `[2, 1]`, from the table's `mc_offset` of 3/4 and 1/2 whole notes); count 7, where the piece ends, has `next: []`; the acceptance check expands the rows through the library to verify the count |
| `corpus_supra_iiif.json` | IIIF manifest loader on `supra/` | discrete graphical timeline |

`fixtures/rejections/0.2.0/` contains 34 complete one-mutation invalid
documents, each with the path both validators must report and a reason. Both
packages consume them.

`fixtures/migrations/0.1.0-to-0.2.0/` holds a populated pair. `before.json` is
a 0.1.0 document in the shapes timetoalign wrote at 0.1.0: a tagged-measure
measure map of four measures (an anacrusis as a `MeasureConstituent` at offset
3, and a repeat whose last bar names the successors `["m2", "m4"]`), a
`MetricalPositionMap` with its redundant `maps` and `names`, a `LinearMap`,
and a region. `after.json` is the result of the migration, serialized with
two-space indentation and a final newline: four compressed rows whose
successors are row IDs (`["2", "4"]`) and whose first row carries
`offset_within_measure: [3, 1]`, and the position map as `meter_map` plus
`beat_map_id`, every other member unchanged. Both packages must reproduce it
byte for byte.

## Schema 0.2.1

0.2.1 keeps the definitions of 0.2.0 and fixes the canonical order in which
writers emit every collection whose order carries no meaning (see the
[README](../README.md#canonical-order)). `fixtures/0.2.1/` holds the same
sixteen documents as `fixtures/0.2.0/`, built by the same constructors and
loaders, written by `dumps` in canonical order. Three of the sixteen 0.2.0
documents were not in canonical order (`conversion_maps.json`: timelines and
maps; `corpus_parangonar_parangonada.json`: timelines; `corpus_score_ms3.json`:
children and markers); migrated to 0.2.1 and written by `dumps`, every 0.2.0
document is byte-equal to its 0.2.1 counterpart, `meta.generator` aside.

`fixtures/rejections/0.2.1/` holds the 34 rejection cases of 0.2.0, each
change applied to the corresponding 0.2.1 document. A path into
`conversion_maps` follows the map to its canonical index, so three cases pin
another index than at 0.2.0.

`fixtures/migrations/0.2.0-to-0.2.1/` holds a pair. `before.json` is a 0.2.0
document written by timetoalign in insertion order, from a construction that
leaves every collection out of canonical order: two timelines (`score`,
`perf`), children tied on offset and nested children, conversion maps,
regions tied on start and on start and end, breaks tied on coordinate, jumps
tied on both coordinates, markers, and offsets and region bounds whose numeric
order and JSON-text order disagree (`[5, 8]` before `[2, 3]`). `after.json` is
the migrated document written by `dumps`; both packages reproduce it byte for
byte.
