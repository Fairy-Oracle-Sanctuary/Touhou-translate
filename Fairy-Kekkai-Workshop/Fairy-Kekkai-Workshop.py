"""
以下文件中的代码用到了仓库(https://github.com/zhiyiYo/Fluent-M3U8)中的源码
Fairy-Kekkai-Workshop/app/view/setting_interface.py
Fairy-Kekkai-Workshop/app/service/version_service.py
Fairy-Kekkai-Workshop/app/common/setting.py
Fairy-Kekkai-Workshop/app/common/logger.py
Fairy-Kekkai-Workshop/app/components/sample_card.py
Fairy-Kekkai-Workshop/deploy.py
"""

import os
import sys

from app.common.config import cfg
from app.common.setting import TEAM, VERSION
from app.view.main_window import MainWindow
from PySide6.QtCore import QSharedMemory
from PySide6.QtWidgets import QApplication


def is_app_running():
    """检查应用程序是否已经在运行"""
    # 使用共享内存或系统信号量来确保单例
    app_id = "Fairy-Kekkai-Workshop"
    shared_memory = QSharedMemory(app_id)

    if shared_memory.attach():
        # 已经有一个实例在运行
        return True
    else:
        # 这是第一个实例
        shared_memory.create(1)
        return False


def main():
    # 检查是否已经有实例在运行
    if is_app_running():
        # 可以尝试激活已运行的实例
        print("应用程序已经在运行中")
        return 1

    # 界面缩放
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName("Fairy-Kekkai-Workshop")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(TEAM)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行应用程序
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

# Fairy-Kekkai-Workshop

"""
## 更新日志
- 集成了最新的 PaddleOCR 3.4 版本，该版本将支持语言扩展至 110 种，并提高了拉丁字母、西里尔字母、阿拉伯字母等的识别准确率。
- 自定义api功能会在只有主机:端口且无 path 时追加 /v1
- 字幕提取视频框选支持了从视频范围外向内拖动，当鼠标进入视频范围时自动开始框选
- 字幕提取视频框选支持了对坐标值进行修改的功能

## 下载提示
- [Fairy-Kekkai-Workshop-v1.16.0-PaddleOCR-None-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.0/Fairy-Kekkai-Workshop-v1.16.0-PaddleOCR-None-Windows-x86_64-Setup.exe) (无OCR版本/可自由配置OCR)
- [Fairy-Kekkai-Workshop-v1.16.0-CPU-v1.4.0-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.0/Fairy-Kekkai-Workshop-v1.16.0-CPU-v1.4.0-Windows-x86_64-Setup.exe) (CPU版本)
- [Fairy-Kekkai-Workshop-v1.16.0-GPU-v1.4.0-CUDA-11.8-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.0/Fairy-Kekkai-Workshop-v1.16.0-GPU-v1.4.0-CUDA-11.8-Windows-x86_64-Setup.exe) (Nvidia 10 系列显卡)
- [Fairy-Kekkai-Workshop-v1.16.0-GPU-v1.4.0-CUDA-12.9-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.0/Fairy-Kekkai-Workshop-v1.16.0-GPU-v1.4.0-CUDA-12.9-Windows-x86_64-Setup.exe) (Nvidia 16 - 50 系列显卡)
- 迅雷链接：https://pan.xunlei.com/s/VOl2n0KP6LH3zXUqcYX1iYUAA1?pwd=yzim#

此次版本更新后PaddleOCR版本变更为1.4.0，如果您需要用字幕功能请不要下载 `PaddleOCR-None` 版本，安装完后可以删除先前的PaddleOCR-v1.3.2程序

关于字幕提取的推荐参数：
"""
