import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit


class DragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拖放文件夹示例")
        self.setGeometry(300, 300, 400, 300)
        # 创建文本框用于显示拖放的文件路径
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)
        # 启用拖放功能
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        # 检查是否包含 URL 数据（文件或文件夹）
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # 获取拖放的文件路径
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                self.text_edit.append(f"拖放的路径: {file}")
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DragDropWindow()
    window.show()
    sys.exit(app.exec())
