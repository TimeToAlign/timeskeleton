# Fixtures

Every JSON file directly under `fixtures/<schema version>/` is a complete
TimeSkeleton file emitted by timetoalign through `scripts/emit_fixtures.py`:
an envelope up to 0.3.0, and from 0.4.0 on one timeline manifest. The script
is the only writer of those files: they are never edited by hand, and a change
to the library's serialization is landed by regenerating them and reviewing the
diff. Once the tag
`v<version>` exists, the script refuses to write into `fixtures/<version>/`:
a released version's fixtures are frozen, its geometry fixtures included.

For 0.3.0, `fixtures/0.3.0/geometry/` holds the geometry, SVG and TikZ fixtures of every
envelope; 0.4.0 has none. `fixtures/0.3.0/geometry-rejections/` holds the
geometries the geometry schema rejects; [`geometry/README.md`](0.3.0/geometry/README.md)
states their provenance.

The rejection cases under `fixtures/rejections/` and the migration pairs
under `fixtures/migrations/` are different: they are authored by hand, each
for the one rule or migration step it pins, and the script never touches
them.

## Provenance

The schema describes timetoalign's current trunk, which is ahead of the
version on PyPI. Each envelope records the exact revision it was produced
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

The script writes the envelopes with the standard writer, `dumps`, reads them
back, and fails unless every timeline manifest is stable, as JSON text, after
`Timeline.from_dict(m).to_dict()`; a library whose own order differs from the
canonical order therefore fails it. Timeline ids are assigned by
the library in construction order and therefore depend on the order of the
script, which is part of the fixture contract.

## Schema 0.1.0

Nine envelopes. Six cover the timeline classes, one per class, each with two
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
| `empty.json` | no timelines | the smallest valid envelope: an empty `timelines` map |
| `nested.json` | `ContinuousLogicalTimeline(length=16, unit="quarters")` with a child of length 8 at offset 4 that holds a child of length 2 at offset `Fraction(3, 2)` | three levels of nesting through the recursive `children` member |

Observed properties of the library's output that the fixtures pin: `name` is
`null` when no name was given; a child added to a parent is emitted with
`locked: true`; `flow_control` is emitted as `{"breaks": [], "jumps": [],
"markers": {}}`; `measure_map` and `metric_hierarchy` are `null` when absent.

## Schema 0.2.0

The nine synthetic envelopes are rebuilt at 0.2.0 from the same constructor
calls described above. The additional envelopes exercise the members that 0.2.0
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
| `empty.json` | synthetic empty envelope | minimum envelope |
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
envelopes, each with the path both validators must report and a reason. Both
packages consume them.

`fixtures/migrations/0.1.0-to-0.2.0/` holds a populated pair. `before.json` is
a 0.1.0 envelope in the shapes timetoalign wrote at 0.1.0: a tagged-measure
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
sixteen envelopes as `fixtures/0.2.0/`, built by the same constructors and
loaders, written by `dumps` in canonical order. Three of the sixteen 0.2.0
envelopes were not in canonical order (`conversion_maps.json`: timelines and
maps; `corpus_parangonar_parangonada.json`: timelines; `corpus_score_ms3.json`:
children and markers); migrated to 0.2.1 and written by `dumps`, every 0.2.0
envelope is byte-equal to its 0.2.1 counterpart, `meta.generator` aside.

`fixtures/rejections/0.2.1/` holds the 34 rejection cases of 0.2.0, each
change applied to the corresponding 0.2.1 envelope. A path into
`conversion_maps` follows the map to its canonical index, so three cases pin
another index than at 0.2.0.

`fixtures/migrations/0.2.0-to-0.2.1/` holds a pair. `before.json` is a 0.2.0
envelope written by timetoalign in insertion order, from a construction that
leaves every collection out of canonical order: two timelines (`score`,
`perf`), children tied on offset and nested children, conversion maps,
regions tied on start and on start and end, breaks tied on coordinate, jumps
tied on both coordinates, markers, and offsets and region bounds whose numeric
order and JSON-text order disagree (`[5, 8]` before `[2, 3]`). `after.json` is
the migrated envelope written by `dumps`; both packages reproduce it byte for
byte.

## Schema 0.3.0

0.3.0 keeps every definition of 0.2.1 and adds the optional `graphical`
block of style rules (see the [README](../README.md#drawing-a-manifest)).
`fixtures/0.3.0/` holds the sixteen envelopes of 0.2.1, each byte-equal to
its 0.2.1 counterpart but for the declared version and `meta.generator`,
and four envelopes built to draw one element each, written by the same
script from public constructors:

| File | Built from | Proves |
|---|---|---|
| `bare.json` | `ContinuousLogicalTimeline(length=8, unit="quarters")` named `Bare` | the smallest drawing: one line, its wedges and labels, the frame |
| `contiguous.json` | a root of 8 quarters with children of lengths 3, 5 and 2 at offsets 0, 3 and 1 | first-fit packing: a child starting where another ends shares its row, an overlapping one moves out |
| `map.json` | a root of 8 quarters carrying a `ScalarMap`, with a child of 4 at offset 2 carrying a `QuartersToTicks` map | the map band beyond the children, two maps in conflict |
| `styled.json` | a score (8 quarters, two children, a map, a region, a jump) and a performance (10.0 seconds, one child), plus a `graphical` block written in the script (`GRAPHICAL`): rules of the envelope and of the `score`, `b` and `perf` containers | every rank of the cascade, per-property fall-through to an outer container, a tie, the filter, projected coordinates, length labels, a float frame |

`styled.json` is the only envelope carrying a `graphical` block; its
manifests are the library's, the block is the script's.

`fixtures/rejections/0.3.0/` holds 45 cases: the 34 of 0.2.1 declaring
0.3.0, and eleven one-change cases of the `graphical` block, each made on
`styled.json` (an unknown member of the block, a timeline container that is
no list, a rule without `set`, an empty `set`, an unknown property, an
unknown element type, a selector with `kind` or with `timeline`, which are
no selector members, an empty `ids` list, a lower-case colour, an unknown
side).

`fixtures/migrations/0.2.1-to-0.3.0/` holds a pair. `before.json` is the
`after.json` of the 0.2.0 to 0.2.1 pair; `after.json` is the same text with
the declared version changed to 0.3.0, since the block is additive.

`fixtures/0.3.0/geometry/<name>/` holds, for each of the twenty envelopes,
its geometry (`geometry.json`, written by `dumps`), its SVG (`figure.svg`)
and its TikZ figure (`figure.tex`, a standalone LuaLaTeX source file), written
with the writers' default options. The geometry of `bare`, `contiguous`,
`nested`, `map`, `with_region`, `flow_control` and `styled` is derived by
hand from the geometry specification as tagged at `v0.3.0`
([`docs/geometry.md`](https://github.com/timetoalign/timeskeleton/blob/v0.3.0/docs/geometry.md)),
with the arithmetic written out in [`geometry/README.md`](0.3.0/geometry/README.md);
the other geometries and every figure are written by the TimeLineEditor's
`app/packages/writers/scripts/emit-geometry.ts`, which refuses to run unless
its layout reproduces the seven hand-derived files byte for byte, and, like
`emit_fixtures.py`, once the tag `v<version>` exists.
These files are a frozen record of the 0.3.0 drawing and do not constrain the current specification.
`fixtures/0.3.0/geometry-rejections/` holds six hand-authored cases, each one
change to `bare/geometry.json` with the path both validators report.

## Schema 0.4.0

0.4.0 holds exactly one timeline manifest per file. An editor places many
timelines on a canvas, each with its own manifest; a manifest is what the
library serializes for one object and knows nothing about where or how often it
is placed. The earlier envelope conflated that placement concern with the
manifest.

`fixtures/0.4.0/` contains one file for each top-level timeline emitted by
every 0.3.0 builder except `empty`. A builder with one timeline keeps its file
name. A builder with several timelines emits `<builder>__<slug>.json`, where
`<slug>` is the timeline id with each character outside `[A-Za-z0-9_-]`
replaced by `_`. This produces 34 manifests. The styled score and performance
each retain the four manifest-level rules, while `graphical.timelines` keeps
only containers in that root's subtree.

`fixtures/rejections/0.4.0/` contains the 45 earlier one-change cases rebased
onto their corresponding single manifests, plus the required-root case
`root_missing_timeline` and `meta_generator_not_string`. Each case stores the
invalid value under `manifest`; tests also accept the frozen earlier key when
reading released cases. Every case declares `"0.4.0"` except two:
`meta_schema_version_unknown` declares the unknown version `"9.9.9"` and is
rejected at `meta.schema_version`, and `root_missing_meta` has no `meta` to
declare a version and is rejected at the root.

`fixtures/migrations/0.3.0-to-0.4.0/` pins migration of a one-root envelope,
including preservation of manifest-level styles and removal of a graphical
container outside the root's subtree. `fixtures/migrations/split/0.3.0/` pins
division of `styled.json`: `before.json` is the published envelope and
`after/perf.json` and `after/score.json` are the two envelopes returned by
`split`, in id order. Migrating each returned envelope produces its 0.4.0
manifest.
