import os
import sys

from app.common.setting import PADDLEOCR_VERSION, VERSION

if sys.platform == "win32":
    args = [
        "nuitka",
        "--standalone",
        "--windows-uac-admin",
        "--windows-disable-console",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=sensible,sqldrivers",
        "--assume-yes-for-downloads",
        "--mingw64",
        "--show-memory",
        "--show-progress",
        "--windows-icon-from-ico=Fairy-Kekkai-Workshop/app/resource/images/logo.ico",
        f"--windows-file-version={VERSION}",
        f"--windows-product-version={VERSION}",
        '--windows-file-description="Fairy Kekkai Workshop"',
        "--output-dir=Fairy-Kekkai-Workshop/dist",
        # tools/
        "--include-data-files=Fairy-Kekkai-Workshop/tools/yt-dlp.exe=tools/yt-dlp.exe",
        "--include-data-files=Fairy-Kekkai-Workshop/tools/ffmpeg.exe=tools/ffmpeg.exe",
        "--include-data-dir=Fairy-Kekkai-Workshop/tools/PaddleOCR.PP-OCRv5.support.files=tools/PaddleOCR.PP-OCRv5.support.files",
        f"--include-data-dir=Fairy-Kekkai-Workshop/tools/PaddleOCR-{PADDLEOCR_VERSION}=tools/PaddleOCR-{PADDLEOCR_VERSION}",
        "Fairy-Kekkai-Workshop/Fairy-Kekkai-Workshop.py",
    ]

elif sys.platform == "darwin":
    args = [
        "python3 -m nuitka",
        "--standalone",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=sensible,sqldrivers",
        "--show-memory",
        "--show-progress",
        "--macos-create-app-bundle",
        "--assume-yes-for-download",
        "--macos-disable-console",
        f"--macos-app-version={VERSION}",
        "--macos-app-name=Fairy Kekkai Workshop",
        "--macos-app-icon=Fairy-Kekkai-Workshop/app/resource/images/logo.ico",
        "--copyright=baby2016",
        "--output-dir=Fairy-Kekkai-Workshop/dist",
        "Fairy-Kekkai-Workshop/Fairy-Kekkai-Workshop.py",
    ]
else:
    args = [
        "pyinstaller",
        "-w",
        "Fairy-Kekkai-Workshop.py",
    ]


os.system(" ".join(args))
print("打包完成！")
