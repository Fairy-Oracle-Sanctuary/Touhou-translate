# widgets/system_tray.py
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from qfluentwidgets import Action, SystemTrayMenu

from ..resource import resource_rc  # noqa: F401


class SystemTray(QSystemTrayIcon):
    def __init__(self, main_window, parent=None):
        super().__init__(parent=parent)
        self.main_window = main_window
        self.setup_tray()

    def setup_tray(self):
        """设置系统托盘"""
        # 设置托盘图标（可以使用应用图标）
        self.setIcon(self.main_window.windowIcon())

        # 创建托盘菜单
        self.menu = SystemTrayMenu()

        # 添加菜单项
        self.menu.addActions(
            [
                Action(
                    self.tr("显示/隐藏界面"), triggered=lambda: self.on_tray_activated()
                ),
                Action(
                    self.tr("退出"),
                    triggered=QApplication.instance().exit,
                    # triggered=lambda: print("a")
                ),
            ]
        )
        self.setContextMenu(self.menu)

        # 显示托盘图标
        self.show()

    def on_tray_activated(self):
        """托盘图标被激活时的处理"""
        # 显示/隐藏主窗口
        if self.main_window.isVisible():
            self.hide_main_window()
        else:
            self.show_main_window()

    def show_main_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.activateWindow()  # 激活窗口到前台
        self.main_window.raise_()  # 窗口置顶

    def hide_main_window(self):
        """隐藏主窗口到托盘"""
        self.main_window.hide()
        self.showMessage(
            "Fairy-Kekkai-Workshop",
            "程序已最小化到系统托盘",
            QIcon(":/app/images/logo.png"),
            1500,
        )

    def quit_application(self):
        """退出应用程序"""
        # 设置真正退出标志
        self.main_window._really_quit = True
        # 退出应用程序
        QApplication.instance().exit
