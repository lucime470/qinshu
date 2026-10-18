# -*- mode: python ; coding: utf-8 -*-
"""禽枢单文件 exe 打包配置。

用法（仓库根目录）：
    python build/build_exe.py
等价于：
    pyinstaller --clean --noconfirm build/qinshu.spec

要点：
    - 入口是 app.py，输出 dist/qinshu.exe（onefile）。
    - webapp/templates、webapp/static 与 data/rules 必须一起打包，
      否则解包后页面或规则表会缺。
    - 课例库不进 exe。运行时会写到 exe 旁边的 storage/qinshu.db。
"""

import sys
from pathlib import Path

_SPEC_DIR = Path(SPECPATH).resolve()
_ROOT = _SPEC_DIR.parent

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PyInstaller.utils.hooks import collect_submodules  # noqa: E402

hiddenimports = (
    collect_submodules("core")
    + collect_submodules("webapp")
    + collect_submodules("storage")
)

datas = [
    (str(_ROOT / "webapp" / "templates"), "webapp/templates"),
    (str(_ROOT / "webapp" / "static"), "webapp/static"),
    (str(_ROOT / "data" / "rules"), "data/rules"),
    (str(_ROOT / "storage" / "schema.sql"), "storage"),
]

a = Analysis(
    [str(_ROOT / "app.py")],
    pathex=[str(_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="qinshu",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
