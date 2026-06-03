# coding:utf-8

from PySide6.QtCore import Signal

from ..components.base_task_interface import BaseTaskInterface
from ..components.task_card import OcrItemWidget
from ..service.ocr_service import OCRProcess, OCRTask


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

    def createTaskItem(self, task: OCRTask, parent):
        return OcrItemWidget(task, parent)

    def createTaskThread(self, task: OCRTask):
        return OCRProcess(task)

    def getTaskPath(self, task: OCRTask):
        return task.input_file

    def onPrintLog(self, task_id, message, is_error, is_flush):
        """处理日志输出"""
        self.log_signal.emit(message, is_error, is_flush)

    def onPrintOutput(self, task_id, message):
        """处理print输出并计算进度"""
        progress = self.parseOCRProgress(task_id, message)
        if progress is not None:
            self.onTaskProgress(task_id, progress)

    def parseOCRProgress(self, task_id, message):
        """解析OCR输出消息并计算进度"""
        try:
            import re

            # Step 1/3: Processing video... Current: HH:MM:SS / HH:MM:SS
            if "Step 1/3" in message:
                match = re.search(
                    r"Current:\s+(\d+:\d+:\d+)\s+/\s+(\d+:\d+:\d+)", message
                )
                if match:
                    current_time_str = match.group(1)
                    total_time_str = match.group(2)

                    def time_to_seconds(time_str):
                        parts = time_str.split(":")
                        if len(parts) == 3:
                            h, m, s = parts
                            return int(h) * 3600 + int(m) * 60 + int(s)
                        elif len(parts) == 2:
                            m, s = parts
                            return int(m) * 60 + int(s)
                        return 0

                    current_seconds = time_to_seconds(current_time_str)
                    total_seconds = time_to_seconds(total_time_str)

                    if total_seconds > 0:
                        progress = (current_seconds / total_seconds) * 33
                        if current_seconds == 0:
                            self.log_signal.emit(
                                "步骤1/3: 正在处理视频帧…", False, False
                            )
                        else:
                            self.log_signal.emit(
                                f"步骤1/3: 正在处理视频帧… {current_time_str} / {total_time_str}",
                                False,
                                True,
                            )
                        return min(progress, 33)

            # Step 2/3: Performing Text-Detection on image X of Y
            elif "Step 2/3" in message and "Text-Detection" in message:
                match = re.search(
                    r"Performing Text-Detection on image\s+(\d+)\s+of\s+(\d+)", message
                )
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = 33 + (current / total) * 20
                        self.log_signal.emit(
                            f"步骤2/3: 正在进行文本检测 {current}/{total}", False, True
                        )
                        return min(progress, 53)

            # Step 2/3: Analyzing frame X of Y
            elif "Analyzing frame" in message:
                match = re.search(r"Analyzing frame\s+(\d+)\s+of\s+(\d+)", message)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = 53 + ((current - 1) / total) * 13
                        self.log_signal.emit(
                            f"步骤2/3: 正在分析检测帧 {current}/{total}", False, True
                        )
                        return min(progress, 66)

            # Text-Detection pass start
            elif (
                "Running Text-Detection-Only pass" in message
                or "Starting PaddleOCR..." in message
            ):
                self.log_signal.emit(message, False, False)
                return 33

            # Filtered out redundant frames
            elif "Filtered out" in message and "redundant frame" in message:
                self.log_signal.emit(message, False, False)
                return 66

            # Step 3/3: Performing OCR on image X of Y
            elif "Step 3/3" in message and "Performing OCR" in message:
                match = re.search(
                    r"Performing OCR on image\s+(\d+)\s+of\s+(\d+)", message
                )
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = 66 + (current / total) * 34
                        self.log_signal.emit(
                            f"步骤3/3: 正在对图像进行OCR识别 {current}/{total}",
                            False,
                            True,
                        )
                        return min(progress, 100)

            # Generating subtitles...
            elif "Generating subtitles..." in message:
                self.log_signal.emit("正在生成字幕文件...", False, False)

            # 找到PaddleOCR路径
            elif "找到PaddleOCR路径:" in message:
                self.log_signal.emit(message, False, False)

            # 找到模型路径
            elif "找到模型路径:" in message:
                message = message.split(" ")
                self.log_signal.emit(
                    message[0]
                    + "\n"
                    + message[1]
                    + "\n"
                    + message[2]
                    + "\n"
                    + message[3],
                    False,
                    False,
                )

            # 找不到PaddleOCR路径
            elif "找不到PaddleOCR路径:" in message:
                self.onTaskFinished(task_id, False, message)
                self.log_signal.emit(message, True, False)

            # 无法找到PaddleOCR可执行文件
            elif "无法找到PaddleOCR可执行文件:" in message:
                self.onTaskFinished(task_id, False, message)
                self.log_signal.emit(message, True, False)

            # PaddleOCR failed
            elif (
                "Error: PaddleOCR failed. See the log file for technical details:"
                in message
            ):
                self.onTaskFinished(task_id, False, message)
                self.log_signal.emit(message, True, False)

            # 默认输出未匹配的日志消息（调试用）
            else:
                self.log_signal.emit(message, False, False)

            return None

        except Exception as e:
            print(f"解析进度失败: {e}")
            return None

    def addOcrTask(self, args):
        self.addTask(args)

    def retryOcr(self, task_id):
        self.retryTask(task_id)
