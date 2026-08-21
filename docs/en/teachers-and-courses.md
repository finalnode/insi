# Teachers and course authors

in:si courses use ordinary files. Scripts are Markdown, programming assignments
combine Markdown with declarative trainer definitions, and projects remain real
source folders. Courses can be edited locally, exported as ZIP archives or
published in repositories.

## Typical structure

```text
Skripte/
Aufgaben/
Trainer/
runtime.toml
*.insi-setup
```

The setup file records the course name, responsible person, optional school,
paths and repository. `runtime.toml` records the required Python version and
packages for a reproducible offline environment.

## Course studio

The course studio edits scripts and assignments in WYSIWYG or Markdown mode.
Only portable Markdown is stored. The annotation menu inserts known in:si
metadata, and the canonical validator reports problems with line numbers.

Difficulty, tags, staged hints, sources and requirements have dedicated form
fields and are composed back into the course files when saved.

## Trainer engines

`insi-trainer-v1` separates the platform from subject-specific evaluation.
`pykim` evaluates Python and the pixel world; `core` provides free-text,
matching and Parsons activities. Additional subject modules can register an
engine through the `insi.trainer_backends` entry point.

## Publication checklist

1. Validate the setup file and directory structure.
2. Record sources and licenses for all course material.
3. Pin reproducible, offline-available runtime requirements.
4. Test every runnable example and trainer in a clean environment.
5. Ensure exports contain no solutions, private keys or personal progress.
6. Document required network, file and external-program access.

The detailed trainer format currently lives in the German
[TRAINER_AUTOREN.md](../../TRAINER_AUTOREN.md); a complete English format
reference is planned as the authoring contract stabilizes.
