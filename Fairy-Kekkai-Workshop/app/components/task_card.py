from .base_task_card import BaseItemWidget


class OcrItemWidget(BaseItemWidget):
    """OCR任务项组件"""

    def __init__(self, task, progressBar_type="common", task_type="提取", parent=None):
        super().__init__(task, progressBar_type, task_type, parent)


class TranslateItemWidget(BaseItemWidget):
    """翻译任务项组件"""

    def __init__(
        self, task, progressBar_type="determinate", task_type="翻译", parent=None
    ):
        super().__init__(task, progressBar_type, task_type, parent)


class FFmpegItemWidget(BaseItemWidget):
    """压制任务项组件"""

    def __init__(self, task, progressBar_type="common", task_type="压制", parent=None):
        super().__init__(task, progressBar_type, task_type, parent)
