from PySide6.QtGui import QIcon

from .base_task_card import BaseItemWidget
from .dialog import FFmpegProgressDialog, ReleaseProgressDialog, TranslateProgressDialog


class OcrItemWidget(BaseItemWidget):
    """OCR任务项组件"""

    def __init__(self, task, progressBar_type="common", task_type="提取", parent=None):
        super().__init__(task, progressBar_type, task_type, parent)


class TranslateItemWidget(BaseItemWidget):
    """翻译任务项组件"""

    def __init__(
        self,
        task,
        progressBar_type="determinate",
        task_type="翻译",
        ai_model=None,
        parent=None,
    ):
        super().__init__(task, progressBar_type, task_type, parent)
        self.ai_model = ai_model
        self.setImage(ai_model)
        self.clicked.connect(self.handleClick)

    def setImage(self, ai_model):
        """设置图标"""
        self.imageLabel.setImage(
            QIcon(f":/app/images/icons/{ai_model}.svg").pixmap(32, 32)
        )

    def handleClick(self):
        """处理点击事件"""
        dialog = TranslateProgressDialog(task=self.task, parent=self.parent().parent())
        dialog.exec()


class FFmpegItemWidget(BaseItemWidget):
    """压制任务项组件"""

    def __init__(self, task, progressBar_type="common", task_type="压制", parent=None):
        super().__init__(task, progressBar_type, task_type, parent)
        self.clicked.connect(self.handleClick)

    def handleClick(self):
        """处理点击事件"""
        dialog = FFmpegProgressDialog(task=self.task, parent=self.parent().parent())
        dialog.exec()


class ReleaseItemWidget(BaseItemWidget):
    """B站上传任务项组件"""

    def __init__(self, task, progressBar_type="common", task_type="上传", parent=None):
        super().__init__(task, progressBar_type, task_type, parent)
        self.setImage()
        self.clicked.connect(self.handleClick)

    def setImage(self):
        """设置图标"""
        self.imageLabel.setImage(QIcon(":/app/images/logo/bilibili.svg").pixmap(32, 32))

    def handleClick(self):
        """处理点击事件"""
        dialog = ReleaseProgressDialog(task=self.task, parent=self.parent().parent())
        dialog.exec()
