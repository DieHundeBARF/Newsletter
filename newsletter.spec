# -*- mode: python -*-

block_cipher = None


a = Analysis(['newsletter.pyw'],
             pathex=['e:\\Newsletter'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

included_images = ['images/attachement.png', 'images/delete.png', 'images/footer.png', 'images/logo.png', 'images/mail.gif']
for image in included_images:
    a.datas += [(image, image, 'DATA')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='newsletter',
          icon='images/mail.ico',
          debug=False,
          strip=False,
          upx=True,
          console=False )
