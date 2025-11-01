import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from qfluentwidgets import Action, FluentIcon, RoundMenu, Theme, setTheme


class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)  # 启用鼠标跟踪
        layout = QVBoxLayout(self)
        label = QLabel("在此区域右键点击任意位置调出菜单")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def contextMenuEvent(self, event):
        # 创建 RoundMenu
        menu = RoundMenu(parent=self)

        # 添加菜单项
        menu.addAction(Action(FluentIcon.HOME, "主页"))
        menu.addAction(Action(FluentIcon.SEARCH, "搜索"))
        menu.addAction(Action(FluentIcon.CHAT, "聊天"))
        menu.addSeparator()
        menu.addAction(Action(FluentIcon.SETTING, "设置"))
        menu.addAction(Action(FluentIcon.HEART, "收藏"))

        # 连接菜单项信号
        for action in menu.actions():
            action.triggered.connect(
                lambda checked, a=action: print(f"选择了: {a.text()}")
            )

        # 在鼠标位置显示菜单
        menu.exec(event.globalPos())
        event.accept()  # 表示已处理该事件


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("右键随地调出 RoundMenu")
        self.resize(500, 400)

        setTheme(Theme.AUTO)  # 自动主题

        # 设置中央组件
        central_widget = CustomWidget()
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
