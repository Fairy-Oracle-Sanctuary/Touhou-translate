# coding:utf-8

from PySide6.QtCore import Signal

from ..components.base_task_interface import BaseTaskInterface
from ..components.videocr_card import OcrItemWidget
from ..service.ocr_service import OCRTask, OCRThread


class OcrTaskInterface(BaseTaskInterface):
    """提取字幕界面"""

    log_signal = Signal(str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(
            object_name="ocrTaskInterface",
            processing_text="提取中",
            task_type="提取",
            parent=parent,
        )

    def createTask(self, args):
        return OCRTask(args)

    def createTaskItem(self, task, parent):
        return OcrItemWidget(task, parent)

    def createTaskThread(self, task):
        return OCRThread(task)

    def getTaskPath(self, task):
        return task.video_path

    def onPrintOutput(self, task_id, message):
        """处理print输出并计算进度"""
        progress = self.parseOCRProgress(task_id, message)
        if progress is not None:
            self.onTaskProgress(task_id, progress)

    def parseOCRProgress(self, task_id, message):
        """解析OCR输出消息并计算进度"""
        # 这里保持原有的 parseOCRProgress 方法实现
        try:
            # Mapping frame {i + 1} of {progress_total}
            if "Mapping frame" in message:
                import re

                match = re.search(r"Mapping frame\s+(\d+)\s+of\s+(\d+)", message)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if current - 1 == 0:
                        self.log_signal.emit("正在处理视频帧中…", False, False)
                    else:
                        self.log_signal.emit(
                            f"正在处理视频帧 {current}/{total}", False, True
                        )
                    return 0

            # Step 1: Processing image {current} of {total}
            if "Step 1: Processing image" in message:
                import re

                match = re.search(r"Processing image\s+(\d+)\s+of\s+(\d+)", message)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = (current / total) * 50
                        if current - 1 == 0:
                            self.log_signal.emit("步骤1: 正在处理图像中…", False, False)
                        else:
                            self.log_signal.emit(
                                f"步骤1: 正在处理图像 {current}/{total}", False, True
                            )
                        return min(progress, 50)

            # Step 2: Performing OCR on image {current} of {total}
            elif "Step 2: Performing OCR on image" in message:
                import re

                match = re.search(
                    r"Performing OCR on image\s+(\d+)\s+of\s+(\d+)", message
                )
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = 50 + (current / total) * 50
                        self.log_signal.emit(
                            f"步骤2: 正在对图像进行OCR {current}/{total}", False, True
                        )
                        return min(progress, 100)

            elif "Advancing to frame" in message:
                import re

                match = re.search(r"Advancing to frame\s+(\d+)\s+of\s+(\d+)", message)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = (current / total) * 100
                        self.log_signal.emit(
                            f"正在提取处理视频帧 {current}/{total}", False, True
                        )

            elif "Starting PaddleOCR... This can take a while..." in message:
                self.log_signal.emit(
                    "正在启动PaddleOCR... 请耐心等待…\n ", False, False
                )

            elif "Generating subtitles..." in message:
                self.log_signal.emit("正在生成字幕文件...", False, False)

            elif "找到PaddleOCR路径:" in message:
                self.log_signal.emit(message, False, False)

            elif "找到模型路径:" in message:
                self.log_signal.emit(message, False, False)

            elif "找不到PaddleOCR路径:" in message:
                self.onTaskFinished(task_id, False, message)
                self.log_signal.emit(message, True, False)

            elif "无法找到PaddleOCR可执行文件:" in message:
                self.onTaskFinished(task_id, False, message)
                self.log_signal.emit(message, True, False)

            elif (
                "Error: PaddleOCR failed. See the log file for technical details:"
                in message
            ):
                self.onTaskFinished(task_id, False, message)
                self.log_signal.emit(message, True, False)

            return None

        except Exception as e:
            print(f"解析进度失败: {e}")
            return None

    def addOcrTask(self, args):
        self.addTask(args)

    def retryOcr(self, task_id):
        self.retryTask(task_id)
