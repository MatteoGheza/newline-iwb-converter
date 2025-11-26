# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for iwb2pdf utility.
Build command: pyinstaller iwb2pdf.spec
"""

a = Analysis(
    ['src/newline_iwb_converter/iwb2pdf.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'reportlab',
        'svglib',
        'PIL',
        'lxml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='iwb2pdf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
