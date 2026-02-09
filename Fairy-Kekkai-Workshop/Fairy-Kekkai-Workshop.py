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
- AI设置页面新增测试配置是否正常的按钮，能快速确认配置参数是否正确
- 同步了最新的VideOCR (https://github.com/timminator/VideOCR)
- 字幕提取功能现在预处理步骤（映射）和步骤 1 是多线程的（例如，在 6 核 5600x 上性能最多可提高 7 倍）
- 修复了字幕提取ssim参数未能传递的BUG
- 优化了翻译功能，glm模型现用OpenAI接口调用

## 下载提示
- [Fairy-Kekkai-Workshop-v1.15.0-PaddleOCR-None-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.15.0/Fairy-Kekkai-Workshop-v1.15.0-PaddleOCR-None-Windows-x86_64-Setup.exe) (无OCR版本/可自由配置OCR)
- [Fairy-Kekkai-Workshop-v1.15.0-CPU-v1.3.2-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.15.0/Fairy-Kekkai-Workshop-v1.15.0-CPU-v1.3.2-Windows-x86_64-Setup.exe) (CPU版本)
- [Fairy-Kekkai-Workshop-v1.15.0-GPU-v1.3.2-CUDA-11.8-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.15.0/Fairy-Kekkai-Workshop-v1.15.0-GPU-v1.3.2-CUDA-11.8-Windows-x86_64-Setup.exe) (Nvidia 10 系列显卡)
- [Fairy-Kekkai-Workshop-v1.15.0-GPU-v1.3.2-CUDA-12.9-Windows-x86_64-Setup.exe](https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases/download/v1.15.0/Fairy-Kekkai-Workshop-v1.15.0-GPU-v1.3.2-CUDA-12.9-Windows-x86_64-Setup.exe) (Nvidia 16 - 50 系列显卡)
- 迅雷链接：https://pan.xunlei.com/s/VOl2n0KP6LH3zXUqcYX1iYUAA1?pwd=yzim#

此次版本更新意在修复bug以及潜在bug，版本号提升为1.15是为了同步videocr的更新
"""
