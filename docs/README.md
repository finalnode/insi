# in:si documentation

The documentation is deliberately stored as portable Markdown and is included
in desktop distributions. It can be read offline without a documentation
website or user account.

The living [draft release notes for 0.8](release-notes-0.8.md) describe the
current `0.8.0.dev0` state on `main`. Stable downloads remain at
version 0.7.1 until that work has passed its release checks.
The [0.8 scope-cut protocol](v0.8-abschlussprotokoll.md) records the completed
scope, current evidence and remaining release gates.

## Current verification

Commit `a91a614` passed the [Python 3.11–3.13 and UI tests](https://github.com/finalnode/insi/actions/runs/34683048752)
and [all four desktop builds](https://github.com/finalnode/insi/actions/runs/34683048695).
Windows required a retry after a PyInstaller/AppContainer startup failure.
Recent changes defer PyKIM checker loading, avoid repeated trainer-engine
discovery and check the selected Python runtime before searching alternatives.

Before releasing 0.8, real school devices, migration from existing 0.7 data and
removable-drive recovery still need manual verification. This is a development
build, not a published 0.8 release.

## Deutsch

- [Erste Schritte](de/erste-schritte.md)
- [Lehrkräfte und Kursautoren](de/lehrkraefte-und-kurse.md)
- [Datenschutz und Sicherheit](de/datenschutz-und-sicherheit.md)

## English

- [Getting started](en/getting-started.md)
- [Teachers and course authors](en/teachers-and-courses.md)
- [Privacy and security](en/privacy-and-security.md)
