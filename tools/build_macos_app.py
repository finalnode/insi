"""Baue Wheelhouse und eigenständige in:si-macOS-App."""

from __future__ import annotations

import platform
import shutil
import subprocess
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
    if platform.system() != "Darwin":
        raise SystemExit("Der macOS-App-Build muss unter macOS ausgeführt werden.")
    if __package__:
        from .build_desktop_app import main as build_desktop
    else:
        from build_desktop_app import main as build_desktop
    return build_desktop(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
