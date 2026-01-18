import os
import sys

# 注意：此脚本用于打包 videocr/api.py 为独立的 exe
# 在整个项目目录下运行此脚本
# 输出目录为 videocr/dist

if sys.platform == "win32":
    args = [
        "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--mingw64",
        "--show-memory",
        "--show-progress",
        "--output-dir=Fairy-Kekkai-Workshop/app/service/CLI/videocr/dist",
        "Fairy-Kekkai-Workshop/app/service/CLI/videocr/api.py",
    ]

elif sys.platform == "darwin":
    args = [
        "python3 -m nuitka",
        "--standalone",
        "--show-memory",
        "--show-progress",
        "--assume-yes-for-download",
        "--output-dir=app/service/CLI/videocr/dist",
        "Fairy-Kekkai-Workshop/app/service/CLI/videocr/api.py",
    ]
else:
    args = [
        "pyinstaller",
        "--onefile",  # 生成单文件 exe
        "--distpath=app/service/CLI/videocr/dist",
        "Fairy-Kekkai-Workshop/app/service/CLI/videocr/api.py",
    ]

# 运行打包命令
os.system(" ".join(args))
