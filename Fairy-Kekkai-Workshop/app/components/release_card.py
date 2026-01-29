from PySide6.QtGui import QIcon

from .base_task_card import BaseItemWidget


class ReleaseItemWidget(BaseItemWidget):
    """B站上传任务项组件"""

    def __init__(self, task, progressBar_type="common", task_type="上传", parent=None):
        super().__init__(task, progressBar_type, task_type, parent)
        self.setImage()

    def setImage(self):
        """设置图标"""
        self.imageLabel.setImage(
            QIcon(":/app/images/logo/bilibili.svg").pixmap(32, 32)
        )
