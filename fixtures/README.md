# Golden fixtures

Every file under `fixtures/<schema version>/` is a complete TimeSkeleton
document emitted by timetoalign through `scripts/emit_fixtures.py`. The
script is the only writer of this directory: fixtures are never edited by
hand, and a change to the library's serialization is landed by regenerating
them and reviewing the diff.

## Provenance

The schema describes timetoalign's current trunk, which is ahead of the
version on PyPI. Each document records the exact revision it was produced
with in `meta.generator`:

```
timetoalign 1.2.0 (cc7c4e55)
```

that is, installed version 1.2.0 of timetoalign at commit `cc7c4e55`
(https://github.com/timetoalign/timetoalign). To regenerate, run the script
with an interpreter that has that revision (or a later one) installed:

```
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C <timetoalign checkout> rev-parse --short HEAD)"
```

The script writes the documents, reads them back, and fails unless every
timeline manifest is stable after `Timeline.from_dict(m).to_dict()`. Timeline ids are assigned by
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
