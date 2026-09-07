# -*- mode: python ; coding: utf-8 -*-

import platform
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

project = Path(SPEC).resolve().parents[2]
system = platform.system()

datas = []
binaries = []
hiddenimports = []

metadata_packages = [
    "insi",
    "PyKIM",
    "nicegui",
    "pywebview",
    "pyxel",
    "certifi",
    "cryptography",
    "packaging",
    "PyYAML",
    "Send2Trash",
]
if system == "Windows":
    metadata_packages.append("pythonnet")
elif system == "Linux":
    metadata_packages.append("PyGObject")
for package in metadata_packages:
    datas += copy_metadata(package, recursive=True)

datas += collect_data_files("nicegui")
datas += collect_data_files("webview")
datas += collect_data_files("certifi")
pyxel_datas, pyxel_binaries, pyxel_hidden = collect_all("pyxel")
datas += pyxel_datas
binaries += pyxel_binaries
hiddenimports += pyxel_hidden
hiddenimports += collect_submodules("pykim.trainer.exercises")
hiddenimports += [
    "engineio.async_drivers.aiohttp",
    "engineio.async_drivers.asgi",
    "nicegui.elements.codemirror",
    "nicegui.native.native_mode",
    "insi.windows_sandbox_helper",
    "pykim.examples",
    "uvicorn.lifespan.on",
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
]
if system == "Windows":
    hiddenimports += ["webview.platforms.winforms"]
elif system == "Linux":
    hiddenimports += ["webview.platforms.gtk"]

datas += collect_data_files("pykim", include_py_files=False)
datas += collect_data_files("insi", include_py_files=False)
datas += collect_data_files("pykim.examples", include_py_files=True)
datas.append((
    str(project / "packaging" / "macos" / "assets" / "app-icon-master.png"),
    "insi/assets",
))
datas.append((str(project / "THIRD_PARTY_NOTICES.md"), "licenses"))
datas.append((str(project / "LICENSE"), "licenses"))
datas.append((str(project / "LICENSING.md"), "licenses"))
datas.append((str(project / "DATENSCHUTZ.md"), "documentation"))
datas.append((str(project / "README.md"), "documentation"))
datas.append((str(project / "README.en.md"), "documentation"))
datas.append((str(project / "SECURITY.md"), "documentation"))
datas.append((str(project / "KNOWN_ISSUES.md"), "documentation"))
datas.append((str(project / "ROADMAP.md"), "documentation"))
datas.append((str(project / "docs"), "documentation/docs"))

wheelhouse = project / "dist" / "wheelhouse"
if wheelhouse.is_dir():
    datas.append((str(wheelhouse), "wheels"))

analysis = Analysis(
    [str(project / "packaging" / "app_entry.py")],
    pathex=[str(project / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter.test", "unittest.test"],
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data)
icon = str(project / "packaging" / "macos" / "assets" / "app-icon-master.png")

if system == "Windows":
    # Nur ein echtes Onefile-Paket erreicht den Python-Einstieg zuverlässig,
    # wenn der sichtbare Starter direkt auf einer langsamen SMB-Freigabe liegt.
    # Der Konsolen-Bootloader schreibt frühe Fehler auf die geerbten Pipes,
    # statt in einem AppContainer einen unsichtbaren MessageBox-Dialog zu öffnen.
    # Bei einem normalen Desktop-Start wird sein eigenes Konsolenfenster sofort
    # verborgen; CREATE_NO_WINDOW des Brokers verhindert es dort vollständig.
    executable = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        name="insi",
        icon=icon,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=True,
        hide_console="hide-early",
    )
else:
    executable = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name="insi",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
    )
    python_runner = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name="insi-python",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=True,
    )
    collection = COLLECT(
        executable,
        python_runner,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        strip=False,
        upx=False,
        name="insi",
    )
