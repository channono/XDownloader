# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['x3.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='XDownloader',  # 改为英文名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico'  # 如果你有图标文件的话
)

# macOS specific
app = BUNDLE(
    exe,
    name='XDownloader.app',  # 改为英文名
    icon='app.icns',  # macOS图标文件
    bundle_identifier='com.xdownloader.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True'
    },
)
