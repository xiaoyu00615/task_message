# -*- mode: python ; coding: utf-8 -*-

# v1.0.1 版本打包配置

# 确保使用正确的工作目录
import os

# 添加必要的资源文件和隐藏导入
datas = [
    ('ui/*.py', 'ui'),
    ('core/*.py', 'core'),
    ('changelog', 'changelog'),
    ('explanation_manual', 'explanation_manual'),
    ('README.md', '.')
]

hiddenimports = [
    'PyQt5.QtWidgets',
    'PyQt5.QtCore', 
    'PyQt5.QtGui',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib',
    'numpy',
    'pandas',
    'datetime',
    'json',
    'os',
    'sys',
    'time'
]

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tasks_message',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None  # 可以根据需要添加图标
)
