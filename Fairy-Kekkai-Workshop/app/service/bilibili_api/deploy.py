import os
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
# upload_video.py路径
UPLOAD_VIDEO_PATH = Path(__file__).parent / "upload_video.py"
# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "dist" / "upload_video"
# bilibili_api 路径
BILIBILI_API_PATH = (
    Path(sys.executable).parent / "Lib" / "site-packages" / "bilibili_api"
)

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_pyinstaller():
    """使用pyinstaller打包upload_video.py为单个文件"""
    print("正在使用pyinstaller打包upload_video.py...")
    print(f"输入文件: {UPLOAD_VIDEO_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 构建pyinstaller命令
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        f"--distpath={OUTPUT_DIR}",
        "--name=upload-video",
        # 强制包含所有必要的模块
        "--hidden-import=bilibili_api",
        "--hidden-import=bilibili_api.clients",
        "--hidden-import=bilibili_api.clients.HTTPXClient",
        "--hidden-import=bilibili_api.clients.AioHTTPClient",
        "--hidden-import=bilibili_api.clients.CurlCFFIClient",
        "--hidden-import=bilibili_api.utils",
        "--hidden-import=bilibili_api.utils.network",
        "--hidden-import=bilibili_api.utils.sync",
        "--hidden-import=bilibili_api.exceptions",
        # 包含第三方HTTP库
        "--hidden-import=httpx",
        "--hidden-import=aiohttp",
        "--hidden-import=curl_cffi",
        # 包含所有子包
        "--collect-submodules=httpx",
        "--collect-submodules=aiohttp",
        "--collect-submodules=curl_cffi",
        # 包含数据文件
        "--add-data",
        f"{BILIBILI_API_PATH / 'data'}{os.pathsep}bilibili_api/data",
        # 使用 bilibili_api 自带的 PyInstaller hook
        "--additional-hooks-dir",
        str(BILIBILI_API_PATH / "_pyinstaller"),
        # 禁用优化，确保所有代码都被包含
        "--noupx",
        str(UPLOAD_VIDEO_PATH),
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
        print("\n错误: 未找到PyInstaller模块。请先安装: pip install pyinstaller")
        sys.exit(1)


def main():
    run_pyinstaller()


if __name__ == "__main__":
    main()

"""
D:/Touhou-project/projects/Fairy-Kekkai-Workshop/tools/upload-video.exe --video_path D:/Touhou-project/projects/世界因你而多彩第一季/11/熟肉_压制.mp4 --cover D:\Touhou-project\projects\世界因你而多彩第一季\11\封面.jpg --SESSDATA 888437e0%2C1785314511%2C687d1%2A12CjCVM84vp65xmbSkhWlHXxL17do_45MP6Di1XDE9JDl0tZ20G5PGNNcU4zjz69Ms71YSVjk0azJsSzFibGJaMG41YnhLdmI1NnFDbDNNdXE0dW5NcThjWTBnbmNvR3NhbkkxVXRITzZmZWNzdEMwZlJFcHJFLUdxcm9KMF9rZlJmanBRNUNqeGxBIIEC --BILI_JCT b2803146087156a253f42e7900a4ddae --BUVID3 0195C6E0-8C18-7E8F-044F-6324714AF8EE86683infoc --tid 1 --title 茶番剧 --desc touhou --tags ['东方'] --original False --source https://www.youtube.com/watch?v=XgZsv9zZMes --recreate False --delay_time 1769854920

D:/Touhou-project/projects/Fairy-Kekkai-Workshop/tools/upload-video.exe --video_path D:/Touhou-project/projects/世界因你而多彩第一季/15/熟肉_压制.mp4 --cover D:\Touhou-project\projects\世界因你而多彩第一季\15\封面.jpg --SESSDATA 8999a340%2C1785328471%2C6f044%2A12CjD6C0P6aoUb7LVPnihqkwcVt9bRZ-1vEYhG7f2kpoJqX_j4Nu6jJkFS4pKm0mKroq8SVktnV1BiQmxfc1g5cXJkSHFQZ1JGVnYtS2JxT0pGbnQ1bG1XWEZJcjV0R05mVmNjV3BGU1lDUDlXelJGZ1N5SDV5ZjZQci1fUktFOTRUUUd4cUJHeXVBIIEC --BILI_JCT adc52578109c5da1906beaac8c3aa705 --BUVID3 0195C6E0-8C18-7E8F-044F-6324714AF8EE86683infoc --tid 1 --title 茶番剧 --desc 111 --tags ['东方'] --original False --source https://www.youtube.com/watch?v=ObtusSmI35E --recreate False --delay_time 1770351600
"""
