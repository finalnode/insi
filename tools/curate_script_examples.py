"""Entferne @button:run von Blöcken, die kein eigenständiges Programm sind."""

from insi.script_quality import annotated_script_blocks, run_headless


def main() -> None:
    invalid = [audit for audit in annotated_script_blocks() if not audit.runnable]
    for audit in annotated_script_blocks():
        if not audit.runnable or audit.kind == "pyxel":
            continue
        try:
            result = run_headless(audit)
        except Exception:
            invalid.append(audit)
            continue
        if result.returncode != 0:
            invalid.append(audit)
    by_path: dict[object, list[int]] = {}
    for audit in invalid:
        # @button:run steht höchstens einige Direktivenzeilen vor dem Code.
        by_path.setdefault(audit.path, []).append(audit.line)
    removed = 0
    for path, code_lines in by_path.items():
        lines = path.read_text(encoding="utf-8").splitlines()
        for code_line in sorted(code_lines, reverse=True):
            code_index = code_line - 2
            cursor = code_index - 1
            while cursor >= 0 and (
                lines[cursor].startswith("@button:") or not lines[cursor].strip()
            ):
                if lines[cursor].strip() == "@button:run":
                    del lines[cursor]
                    removed += 1
                    break
                cursor -= 1
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{removed} ungeeignete Ausführen-Markierungen entfernt.")


if __name__ == "__main__":
    main()
