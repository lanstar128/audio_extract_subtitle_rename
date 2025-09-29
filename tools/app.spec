# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 项目根目录
project_root = Path(SPECPATH).parent

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[str(project_root)],
    binaries=[
        # 包含FFmpeg二进制文件
        (str(project_root / 'bin' / 'ffmpeg.exe'), 'bin'),
        (str(project_root / 'bin' / 'ffprobe.exe'), 'bin'),
    ],
    datas=[
        # 包含配置文件
        (str(project_root / 'config'), 'config'),
        # 包含UI样式文件
        (str(project_root / 'ui'), 'ui'),
        # 包含资源文件
        (str(project_root / 'resources'), 'resources'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'rapidfuzz',
        'rapidfuzz.fuzz',
        'configparser',
        'pathlib',
        'dataclasses',
        'queue',
        'threading',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 添加images目录（如果存在）
if (project_root / 'images').exists():
    a.datas += [(str(project_root / 'images'), 'images')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='audio_subtitle_tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 关闭控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'resources' / 'images' / 'logo.ico') if (project_root / 'resources' / 'images' / 'logo.ico').exists() else None,
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='audio_subtitle_tools',
)
