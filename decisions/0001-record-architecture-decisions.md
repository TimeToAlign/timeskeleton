# 0001. Record architecture decisions

Date: 2026-10-09

## Context

The schema and its two validation packages are intentionally small but serve
several language ecosystems. Their choices need a durable, reviewable record.

## Considered options

- Keep decisions only in source comments.
- Write an occasional narrative release note.
- Record concise MADR files here.
- Write the decision record format ourselves outside the repository.

## Decision

Use MADR-style files in `decisions/`, one numbered file per architectural
decision. The TimeToAlign maintainers own review; the bus factor is improved
because the reasoning lives beside the code. Sources: https://adr.github.io/madr/
and https://github.com/adr/madr/blob/main/LICENSE.

## Consequences

Each record states alternatives, maintenance burden, release cadence, licence,
size, transitive dependencies, exit cost, and a review date. This has no
runtime dependency or package-size cost; a replacement format can be adopted
by adding a conversion note.

## Review date

2027-10-09.
