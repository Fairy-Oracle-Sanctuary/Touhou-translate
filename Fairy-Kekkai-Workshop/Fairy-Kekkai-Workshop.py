from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont)
from qfluentwidgets import FluentIcon as FIF
from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication
from PySide6.QtCore import Qt, QUrl, QSharedMemory
from PySide6.QtGui import QIcon, QDesktopServices
import sys


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
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName("Fairy-Kekkai-Workshop")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Fairy-Kekkai")
    
    # 创建并显示主窗口
    from app.view.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     w = MainWindow()
#     w.show()
#     app.exec()


# Fairy-Kekkai-Workshop
# pip install --upgrade yt-dlp