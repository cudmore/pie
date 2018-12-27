# -*- mode: python -*-

block_cipher = None


a = Analysis(['commander2.py'],
             pathex=['/Users/cudmore/Sites/pie/commander_app'],
             binaries=[],
             datas=[('templates', 'templates'), ('static', 'static'), ('config', 'config'), ('bin', 'bin')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='commander',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
