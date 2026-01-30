import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
# videocr_cli.py路径
VIDEOCR_CLI_PATH = Path(__file__).parent / "upload_video.py"
# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "dist" / "upload_video"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_nuitka():
    """使用nuitka打包upload_video.py为单个文件"""
    print("正在使用nuitka打包upload_video.py...")
    print(f"输入文件: {VIDEOCR_CLI_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 构建nuitka命令
    args = [
        sys.executable,  # 使用当前Python解释器
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",  # 打包为单个文件
        "--output-dir={}".format(OUTPUT_DIR),
        "--output-filename=videocr-cli",
        "--include-module=bilibili_api",  # videocr需要的模块
        "--mingw64",  # 使用mingw64编译器
        "--show-memory",
        "--show-progress",
        str(VIDEOCR_CLI_PATH),
    ]

    # 执行命令
    try:
        subprocess.run(args, check=True)
        print("\n打包完成！")
        print(f"可执行文件路径: {OUTPUT_DIR / 'upload-video.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n错误: 未找到nuitka模块。请先安装: pip install nuitka")
        sys.exit(1)


def run_pyinstaller():
    """使用pyinstaller打包videocr_cli.py为单个文件"""
    print("正在使用pyinstaller打包videocr_cli.py...")
    print(f"输入文件: {VIDEOCR_CLI_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 构建pyinstaller命令
    args = [
        sys.executable,  # 使用当前Python解释器
        "-m",
        "PyInstaller",
        "--onefile",  # 打包为单个文件
        "--name=videocr-cli",
        "--distpath={}".format(OUTPUT_DIR),
        "--workpath={}".format(OUTPUT_DIR / "build"),
        "--specpath={}".format(OUTPUT_DIR),
        "--icon=Fairy-Kekkai-Workshop/app/resource/images/logo.ico",
        str(VIDEOCR_CLI_PATH),
    ]

    # 执行命令
    try:
        subprocess.run(args, check=True)
        print("\n打包完成！")
        print(f"可执行文件路径: {OUTPUT_DIR / 'videocr-cli.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n错误: 未找到pyinstaller模块。请先安装: pip install pyinstaller")
        sys.exit(1)


def main():
    run_nuitka()


if __name__ == "__main__":
    main()
