# Security Policy

## Reporting a vulnerability

**Do not open a public issue for security problems.** Report privately via GitHub Security Advisories:
**[Report a vulnerability](https://github.com/meaningfy-ws/rdf-fingerprinter/security/advisories/new)**.

We follow **coordinated disclosure**: we triage the private report, develop and release a fix, request
a CVE where warranted, and publish the advisory once a fixed release is available. Please give us a
reasonable window to remediate before any public disclosure.

We aim to acknowledge a report within a few working days.

## Supported versions

Security fixes land on the latest released line. Older lines are supported at maintainers' discretion.

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ |
| < 1.0   | ❌ |

## Handling fixed releases

A vulnerable release already published is **yanked** (kept installable for existing pins, hidden from
new resolves) and superseded by a patched release — it is never deleted, which would break downstream
pinned installs.
