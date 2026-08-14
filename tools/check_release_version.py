"""Prüfe den Release-Tag gegen die in:si-Versionsquellen."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def source_version(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"Keine __version__ in {path} gefunden.")


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PyKIM-Releaseversion prüfen")
    parser.add_argument("tag", help="Git-Tag, beispielsweise v0.5.2")
    options = parser.parse_args(arguments)
    project = Path(__file__).resolve().parents[1]
    with (project / "pyproject.toml").open("rb") as source:
        metadata_version = str(tomllib.load(source)["project"]["version"])
    runtime_version = source_version(project / "src" / "insi" / "__init__.py")
    tag_version = options.tag.removeprefix("v")
    if len({metadata_version, runtime_version, tag_version}) != 1:
        raise SystemExit(
            "Versionskonflikt: "
            f"Tag={tag_version}, Metadaten={metadata_version}, "
            f"insi.__version__={runtime_version}"
        )
    print(f"Releaseversion {tag_version} ist konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
