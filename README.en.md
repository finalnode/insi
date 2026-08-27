# in:si

[![Desktop builds](https://github.com/finalnode/insi/actions/workflows/build-desktop.yml/badge.svg?branch=main)](https://github.com/finalnode/insi/actions/workflows/build-desktop.yml)
[![Latest release](https://img.shields.io/github/v/release/finalnode/insi?label=Download)](https://github.com/finalnode/insi/releases/latest)
[![License: AGPL-3.0+](https://img.shields.io/badge/License-AGPL--3.0%2B-blue.svg)](LICENSE)

**Language:** [Deutsch](README.md) · English

**This development branch builds in:si 0.8.0.dev0.** It is not a published
release yet. **in:si 0.7.1** remains the current stable release of the local
desktop learning environment for modular computer science courses. The app combines course
installation, learning texts, interactive assignments, automated feedback,
progress, projects and authoring tools in one application that remains largely
offline after setup.
The current work is available on
[`develop/v0.8`](https://github.com/finalnode/insi/tree/develop/v0.8); `main`
remains on the 0.7 state until the new version passes its release checks.

The name **in:si** stands for **informatica simplicissima**: computer science
should be made as accessible as possible without hiding real languages, files
and tools behind a simplified learning interface. Its educational principle is:
**Simplify as much as necessary, abstract as little as possible.**

> **Project status: alpha.** Interfaces and local formats may still change.
> Desktop builds are not production-signed. The macOS build is ad-hoc signed
> but not notarized.

> **Current build evidence:** Commit `d038417` of `develop/v0.8` built
> successfully for Windows, Linux and both macOS architectures. Windows
> AppContainer and real window launch, Linux Bubblewrap/Wayland and both macOS
> Seatbelt checks passed. Each platform also rebuilt a fresh course runtime
> exclusively from its packaged offline wheelhouse. Verification on real school
> devices remains required.

> **0.8.0.dev0 development state:** `develop/v0.8` now includes versioned data
> migration, visible project snapshots, local data control, faster startup
> paths and a more focused test structure. The current check reports 480
> passed tests, one platform-related skip and four additional passing E2E
> tests. See the
> [draft 0.8 release notes](docs/release-notes-0.8.md) for progress and release
> blockers. The [0.8 scope-cut protocol](docs/v0.8-abschlussprotokoll.md)
> separates completed scope from outstanding release evidence.

## Why in:si exists

Introductory programming classes often split their work across an LMS, PDFs,
an editor, an IDE, test scripts and several storage locations. Those tools are
normal for experienced developers, but their organizational overhead can hide
the actual learning goal.

Fully hosted learning platforms reduce that fragmentation but commonly require
accounts, permanent connectivity and vendor-specific editors or formats. in:si
chooses a local, file-based middle ground:

- learners get one place to read, try, solve, test and build projects;
- teachers distribute ordinary Markdown, Python, YAML and project files;
- published course material and personal work remain separate;
- real languages, libraries and IDEs stay visible and replaceable;
- central learning workflows continue without an internet connection.

The current sample course teaches Python through the independent
[PyKIM](https://github.com/finalnode/PyKIM) subject module. The platform is
designed for more subject engines, but PyKIM is currently the only complete
integration.

## What in:si is — and is not

in:si is a local learning workspace, course reader, assignment runner and
course-authoring environment. It is not a learning management system, cloud
service, classroom surveillance tool, grade book or replacement for a full
IDE. It deliberately has no required user accounts, telemetry or central
learner database.

The built-in editor should make the first steps easier. Learners can later open
the same files in Thonny, VS Code or another IDE without converting them to a
proprietary format.

## Current capabilities

- install, select and update local or repository-based courses;
- read structured scripts and copy or run selected examples;
- solve code, free-text, matching and Parsons-style assignments;
- run automated trainers through a subject-neutral engine contract;
- keep progress, projects and notes in the selected course workspace;
- save automatic or named project states and restore them without discarding
  the current working state;
- edit course texts in WYSIWYG or Markdown mode while storing plain Markdown;
- create and validate course packages and portable ZIP archives;
- use controlled, fail-closed execution on Windows, macOS and Linux;
- open learner files in external IDEs when integrated execution is unavailable;
- inspect privacy, source and license information directly in the app.

## Installation and development

Python 3.11 or newer is required for a source installation:

```bash
git clone https://github.com/finalnode/insi.git
cd insi
python -m venv venv
source venv/bin/activate
python -m pip install -e .
insi
```

On Windows activate the environment with:

```powershell
venv\Scripts\activate
```

The visible `venv` directory name also avoids inherited Finder hidden flags on
macOS with Python 3.14, which can otherwise disable the `.pth` file of an
editable installation.

The desktop packages for `0.7.1` are built automatically from the corresponding
version tag and published in the official GitHub release:

| Operating system | Architecture | Download |
|---|---|---|
| Windows | x86_64 | **[Download ZIP](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-windows-x86_64.zip)** |
| Linux | x86_64 | **[Download TAR.GZ](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-linux-x86_64.tar.gz)** |
| macOS | Apple Silicon (`arm64`) | **[Download DMG](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-macos-arm64.dmg)** |
| macOS | Intel (`x86_64`) | **[Download DMG](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-macos-x86_64.dmg)** |

All releases remain available on the
[GitHub Releases page](https://github.com/finalnode/insi/releases).

## Security and offline operation

Course and learner programs are potentially untrusted code. Integrated starts
are therefore enabled only after the operating-system sandbox passes an actual
self-test. Windows uses an AppContainer and Job Object, Linux uses Bubblewrap,
and macOS uses a generated Seatbelt profile. If the required isolation is not
available, in:si refuses the integrated start and offers the external IDE as an
explicitly unrestricted alternative.

The security model, permanent limits and reporting process are documented in
[SECURITY.md](SECURITY.md). Local storage, network destinations, exports and
deletion paths are listed in [DATENSCHUTZ.md](DATENSCHUTZ.md) in German.

## Current limitations

- The TOAST UI toolbar still needs final layout verification at narrow window
  widths; the previously observed WYSIWYG freeze is fixed.
- The real-device school matrix for Windows, macOS and Linux is not complete.
- Desktop packages are not production-signed or notarized.
- The 0.7-to-0.8 migration and visible snapshot restoration are implemented on
  the development branch but still require release and platform verification.
- Local multi-user profiles belong to a later milestone.
- Setup, course, trainer and data formats do not receive a 1.x stability promise
  before version 1.0.

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for detailed impact and workarounds and
[ROADMAP.md](ROADMAP.md) for the milestones through 1.3.

## Documentation

The documentation is stored as ordinary Markdown and shipped with desktop
packages:

- [Getting started](docs/en/getting-started.md)
- [Teachers and course authors](docs/en/teachers-and-courses.md)
- [Privacy and security](docs/en/privacy-and-security.md)
- [German documentation](docs/de/erste-schritte.md)

A hosted documentation site is optional; no hosted service is required to read
or use the documentation.

## License

in:si is licensed under the
[GNU Affero General Public License v3 or later](LICENSE)
(`AGPL-3.0-or-later`) starting with version 0.7. Commercial use remains
permitted. Modified distributions must provide corresponding source, and users
interacting with a modified network version must be offered its corresponding
source as required by the license.

Previously published MIT versions remain under MIT. PyKIM, external courses and
bundled third-party components retain their own licenses. See
[LICENSING.md](LICENSING.md) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
