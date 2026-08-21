# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

project = Path(SPEC).resolve().parents[2]
with (project / "pyproject.toml").open("rb") as source:
    app_version = str(tomllib.load(source)["project"]["version"])

datas = []
binaries = []
hiddenimports = []

for package in (
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
):
    datas += copy_metadata(package, recursive=True)

datas += collect_data_files("nicegui")
datas += collect_data_files("webview")
datas += collect_data_files("certifi")
pyxel_datas, pyxel_binaries, pyxel_hidden = collect_all("pyxel")
datas += pyxel_datas
binaries += pyxel_binaries
hiddenimports += pyxel_hidden
hiddenimports += collect_submodules("pykim.trainer.exercises")

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
hiddenimports += ["pykim.examples"]
hiddenimports += [
    "engineio.async_drivers.aiohttp",
    "engineio.async_drivers.asgi",
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "webview.platforms.cocoa",
    "nicegui.native.native_mode",
    "nicegui.elements.codemirror",
]

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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

app = BUNDLE(
    collection,
    name="insi.app",
    icon=str(project / "packaging" / "macos" / "assets" / "app-icon.icns"),
    bundle_identifier="de.simplicissima.insi",
    version=app_version,
    info_plist={
        "CFBundleDisplayName": "in:si",
        "CFBundleName": "insi",
        "CFBundleShortVersionString": app_version,
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.15",
    },
)
