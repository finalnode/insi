"""Baue Wheelhouse und eigenständige in:si-macOS-App."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import os
import tempfile
from pathlib import Path


def apply_adhoc_signature(application: Path) -> None:
    """Entferne Finder-Metadaten und stelle eine prüfbare Ad-hoc-Signatur her."""

    subprocess.run(["xattr", "-cr", str(application)], check=True)
    command = [
        "codesign",
        "--force",
        "--deep",
        "--sign",
        "-",
        "--timestamp=none",
        str(application),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        subprocess.run(
            ["codesign", "--verify", "--deep", "--strict", str(application)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        diagnostic = f"{error.stdout or ''}\n{error.stderr or ''}"
        if "resource fork, Finder information, or similar detritus" not in diagnostic:
            raise
        # File Provider unter ~/Documents kann com.apple.provenance sofort nach
        # `xattr -cr` erneut setzen. Im privaten System-Tempordner lässt sich
        # derselbe Inhalt signieren; die Signatur wird danach zurückkopiert.
        with tempfile.TemporaryDirectory(prefix="insi-macos-sign-") as temporary:
            staged = Path(temporary) / application.name
            shutil.copytree(application, staged, symlinks=True)
            subprocess.run(["xattr", "-cr", str(staged)], check=True)
            staged_command = [*command[:-1], str(staged)]
            subprocess.run(staged_command, check=True)
            subprocess.run(
                ["codesign", "--verify", "--deep", "--strict", str(staged)],
                check=True,
            )
            shutil.rmtree(application)
            shutil.copytree(staged, application, symlinks=True)
        verification = subprocess.run(
            ["codesign", "--verify", "--deep", "--strict", str(application)],
            capture_output=True,
            text=True,
        )
        if verification.returncode:
            verification_diagnostic = (
                f"{verification.stdout or ''}\n{verification.stderr or ''}"
            )
            if "resource fork, Finder information, or similar detritus" not in (
                verification_diagnostic
            ):
                raise subprocess.CalledProcessError(
                    verification.returncode,
                    verification.args,
                    verification.stdout,
                    verification.stderr,
                )
            print(
                "Hinweis: Der synchronisierte Ausgabeordner hat erneut "
                "Finder-Metadaten gesetzt. Der lokale .app-Ordner ist deshalb "
                "nicht direkt verifizierbar; build_macos_dmg.py bereinigt und "
                "signiert den tatsächlichen DMG-Payload erneut."
            )
        return


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="in:si für macOS bauen")
    parser.add_argument("--skip-wheelhouse", action="store_true")
    parser.add_argument("--skip-clean", action="store_true")
    options = parser.parse_args(arguments)
    if platform.system() != "Darwin":
        raise SystemExit("Der macOS-App-Build muss unter macOS ausgeführt werden.")
    project = Path(__file__).resolve().parents[1]
    if os.environ.get("PYKIM_MACOS_BUILD_ENV") != "1":
        environment = project / "build" / "macos-venv"
        python = environment / "bin" / "python"
        if not python.is_file():
            subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(
            [
                str(python), "-m", "pip", "install",
                "git+https://github.com/finalnode/PyKIM.git@main",
            ],
            check=True,
        )
        subprocess.run(
            [str(python), "-m", "pip", "install", "-e", f"{project}[build]"],
            check=True,
        )
        child_environment = os.environ.copy()
        child_environment["PYKIM_MACOS_BUILD_ENV"] = "1"
        return subprocess.run(
            [str(python), str(Path(__file__).resolve()), *(__import__("sys").argv[1:])],
            cwd=project,
            env=child_environment,
        ).returncode
    if not options.skip_wheelhouse:
        subprocess.run(
            [sys.executable, str(project / "tools" / "build_wheelhouse.py")],
            cwd=project,
            check=True,
        )
    subprocess.run(
        [
            sys.executable,
            str(project / "tools" / "audit_runtime_licenses.py"),
            "--strict",
        ],
        cwd=project,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(project / "tools" / "build_macos_icon.py")],
        cwd=project,
        check=True,
    )
    if not options.skip_clean:
        for directory in (project / "build" / "macos", project / "dist" / "macos"):
            if directory.exists():
                shutil.rmtree(directory)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(project / "dist" / "macos"),
        "--workpath",
        str(project / "build" / "macos"),
    ]
    if not options.skip_clean:
        command.append("--clean")
    command.append(str(project / "packaging" / "macos" / "PyKIM.spec"))
    subprocess.run(command, cwd=project, check=True)
    application = project / "dist" / "macos" / "insi.app"
    if not application.is_dir():
        raise RuntimeError("PyInstaller hat keine macOS-App erzeugt.")
    apply_adhoc_signature(application)
    print(f"macOS-App erstellt: {application}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
