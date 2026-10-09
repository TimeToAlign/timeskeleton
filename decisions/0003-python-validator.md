# 0003. Validate Python documents with jsonschema

Date: 2026-10-09

## Context

The Python package must validate draft 2020-12 documents and return useful
locations for invalid values.

## Considered options

- `jsonschema`.
- `fastjsonschema`.
- `check-jsonschema`.
- `jsonschema-rs`.
- Write the validator ourselves.

## Decision

Use `jsonschema` and `Draft202012Validator`. TimeToAlign maintainers benefit
from its public error paths and broad format support; its established project
reduces the bus factor. Primary sources: https://pypi.org/project/jsonschema/
and https://github.com/python-jsonschema/jsonschema/blob/main/COPYING.

## Consequences

`jsonschema` is a small runtime dependency with its documented transitive
dependencies and MIT licence. It is adequate for the expected low release
cadence and fixture-sized inputs. Replacing it later is isolated behind
`validate.py`; writing it ourselves would make schema conformance, security
updates, and exit testing the maintainers' responsibility.

## Review date

2027-10-09.
