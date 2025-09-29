import os
import sys
from app.common.setting import VERSION

if sys.platform == "win32":
    args = [
        'nuitka',
        '--standalone',
        '--windows-disable-console',
        '--plugin-enable=pyside6' ,
        '--include-qt-plugins=sensible,sqldrivers',
        '--assume-yes-for-downloads',
        # '--msvc=latest',              # Use MSVC
        '--mingw64',                    # Use MinGW
        '--show-memory' ,
        '--show-progress' ,
        '--windows-icon-from-ico=Fairy-Kekkai-Workshop/app/resource/images/logo.ico',
        # '--windows-company-name="Shokokawaii Inc."',
        # '--windows-product-name=Fluent-M3U8',
        f'--windows-file-version={VERSION}',
        f'--windows-product-version={VERSION}',
        '--windows-file-description="Fairy Kekkai Workshop"',
        '--output-dir=Fairy-Kekkai-Workshop/dist',
        'Fairy-Kekkai-Workshop/Fairy-Kekkai-Workshop.py',
    ]
elif sys.platform == "darwin":
    args = [
        'python3 -m nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--include-qt-plugins=sensible,sqldrivers',
        '--show-memory',
        '--show-progress',
        "--macos-create-app-bundle",
        "--assume-yes-for-download",
        "--macos-disable-console",
        f"--macos-app-version={VERSION}",
        "--macos-app-name=Fairy Kekkai Workshop",
        "--macos-app-icon=Fairy-Kekkai-Workshop/app/resource/images/logo.ico",
        "--copyright=baby2016",
        '--output-dir=Fairy-Kekkai-Workshop/dist',
        'Fairy-Kekkai-Workshop/Fairy-Kekkai-Workshop.py',
    ]
else:
    args = [
        'pyinstaller',
        '-w',
        'Fairy-Kekkai-Workshop.py',
    ]


os.system(' '.join(args))

