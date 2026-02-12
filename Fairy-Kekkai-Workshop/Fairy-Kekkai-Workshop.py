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
- 修复了字幕提取在检测路径时检测了错误临时文件夹路径的bug
- 优化视频框选手感

## 下载提示
- [Fairy-Kekkai-Workshop-v1.16.1-PaddleOCR-None-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.1/Fairy-Kekkai-Workshop-v1.16.1-PaddleOCR-None-Windows-x86_64-Setup.exe) (无OCR版本/可自由配置OCR)
- [Fairy-Kekkai-Workshop-v1.16.1-CPU-v1.4.0-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.1/Fairy-Kekkai-Workshop-v1.16.1-CPU-v1.4.0-Windows-x86_64-Setup.exe) (CPU版本)
- [Fairy-Kekkai-Workshop-v1.16.1-GPU-v1.4.0-CUDA-11.8-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.1/Fairy-Kekkai-Workshop-v1.16.1-GPU-v1.4.0-CUDA-11.8-Windows-x86_64-Setup.exe) (Nvidia 10 系列显卡)
- [Fairy-Kekkai-Workshop-v1.16.1-GPU-v1.4.0-CUDA-12.9-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.16.1/Fairy-Kekkai-Workshop-v1.16.1-GPU-v1.4.0-CUDA-12.9-Windows-x86_64-Setup.exe) (Nvidia 16 - 50 系列显卡)
- 迅雷链接：https://pan.xunlei.com/s/VOl2n0KP6LH3zXUqcYX1iYUAA1?pwd=yzim#

关于字幕提取的推荐参数(如果是整个画面提取把ssim拉到96以上)：
"""
