# 0008. Publish both packages from one OIDC release workflow

Date: 2026-10-09

## Context

The Python and npm packages share one schema version and must be published
together without long-lived registry secrets.

## Considered options

- One tag and one workflow using OIDC trusted publishing.
- Two tags.
- Stored PyPI and npm tokens.
- release-please.
- Write release automation ourselves.

## Decision

Publish both packages from one version tag using GitHub Actions OIDC trusted
publishing. TimeToAlign maintainers retain a single review point, and the bus
factor is improved by avoiding personal tokens. Primary sources:
https://docs.pypi.org/trusted-publishers/, https://docs.npmjs.com/trusted-publishers,
and https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect.

## Consequences

The workflow has no token dependency and no packaged runtime size impact.
GitHub Actions and publisher actions carry their own licences and transitive
action dependencies. One release cadence keeps versions aligned; exiting to
separate tags costs process and version checks. Writing OIDC exchange logic
ourselves would add security-sensitive maintenance.

## Review date

2027-10-09.
