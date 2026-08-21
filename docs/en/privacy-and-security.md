# Privacy and security

in:si is offline-first and has no required central accounts. Personal data can
still exist locally: names or aliases, progress, source code, feedback and
exports may identify a learner and must be handled accordingly on managed
devices.

## Local data

Personal data normally stays in the selected course workspace. in:si does not
automatically upload progress or source code. Network access occurs for
deliberately initiated course installation, catalog or update checks, and when
building a runtime from packages that are not available locally.

The complete technical data inventory is available in German in
[DATENSCHUTZ.md](../../DATENSCHUTZ.md).

## Executing programs

Integrated course and learner code runs only after a sandbox self-test:

- Windows: AppContainer and Job Object;
- Linux: Bubblewrap and Wayland for graphical starts;
- macOS: a generated Seatbelt profile.

The runner limits network access, host files, process count, run time, CPU,
memory, output and newly written data where supported. No operating-system
sandbox is an absolute defence against unknown vulnerabilities.

External IDEs run outside these restrictions. Use courses from sources you can
evaluate. The full threat model and reporting process are in
[SECURITY.md](../../SECURITY.md).
