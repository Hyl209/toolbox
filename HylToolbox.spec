# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['hyl_toolbox.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('music/ncm_to_mp3.py', 'music'),
        ('mp4-mp3/converter.py', 'mp4-mp3'),
        ('mp4-mp3/config_store.py', 'mp4-mp3'),
        ('zipandpng/zipandpng.py', 'zipandpng'),
        ('image-convert/converter.py', 'image-convert'),
        ('pdf-tools/converter.py', 'pdf-tools'),
        ('logo.png', '.'),
    ],
    hiddenimports=['ncmdump'],
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
    name='格式转换工具',
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
    icon='logo.ico',
    onefile=True,
)
