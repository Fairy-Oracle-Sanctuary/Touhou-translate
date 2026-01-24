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
- 更新了主页面
- 新增了对PaddleOCR自定义temp文件夹的支持
- 新增了输出更多PaddleOCR运行时的细节
- 新增点击项目卡片查看项目进度
- 新增压制视频时点击任务卡片查看压制进度
- 新增AI翻译时点击任务卡片查看翻译进度
- 新增了AI的设置:
    - temperature(温度)
    - prompt(提示词模板)
- 新增了ai接口:
    - 腾讯混元
    - Gemini 3 Flash
    - 书生
    - GLM-4.5-FLASH
    - Spark-Lite
    - 百度ERNIE-Speed-128K
- 优化了项目打开时的性能
- 优化了提取字幕、翻译、压制界面的布局
- 修复了主页面更新按钮点击时会检查两次更新的BUG
- 修复了一些小BUG
"""
