# ocr_service.py

import io
import sys

from PySide6.QtCore import QThread, QTimer, Signal

from .CLI.videocr.api import save_subtitles_to_file


class OCRTask:
    """OCR任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.status = "等待中"  # 等待中, 处理中, 已完成, 失败
        self.progress = 0
        self.error_message = ""
        self.video_path = args.get("video_path")
        self.file_path = args.get("file_path")

        OCRTask._id_counter += 1
        self.id = OCRTask._id_counter


class OCRThread(QThread):
    """OCR处理线程"""

    progress_signal = Signal(int, int, int)  # 进度百分比, 当前帧, 总帧数
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    log_signal = Signal(str)  # 日志信息
    print_signal = Signal(str)  # 新增：捕获print输出
    cancelled_signal = Signal()  # 新增：取消完成信号

    def __init__(self, task):
        super().__init__()
        self.task = task
        self.is_cancelled = False
        self.original_stdout = None
        self.print_capture = None
        self._cancellation_timer = None

    def run(self):
        """执行OCR处理"""
        self.task.status = "提取中"

        try:
            # 重定向标准输出
            self.original_stdout = sys.stdout
            self.print_capture = PrintCapture(self.print_signal)
            sys.stdout = self.print_capture

            ocr_params = self.task.args
            self.log_signal.emit("开始OCR处理...")

            # 检查是否已取消
            if self.is_cancelled:
                self.log_signal.emit("OCR处理已取消")
                return

            # 执行OCR处理
            save_subtitles_to_file(**ocr_params)

            # 再次检查是否已取消
            if self.is_cancelled:
                self.log_signal.emit("OCR处理已取消")
                return

            self.task.status = "已完成"
            self.task.progress = 100

            self.log_signal.emit("OCR处理完成")
            self.finished_signal.emit(True, "OCR处理完成")

        except Exception as e:
            # 如果是取消操作导致的异常，不记录为错误
            if self.is_cancelled:
                self.log_signal.emit("OCR处理已取消")
                return

            error_msg = f"OCR处理失败: {str(e)}"
            self.task.status = "失败"
            self.task.error_message = error_msg

            self.log_signal.emit(f"错误: {error_msg}")
            self.finished_signal.emit(False, error_msg)
        finally:
            # 恢复标准输出
            if self.original_stdout:
                sys.stdout = self.original_stdout

    def cancel(self):
        """取消OCR处理 - 异步非阻塞版本"""
        if not self.isRunning() or self.is_cancelled:
            return

        self.is_cancelled = True
        self.task.status = "已取消"

        # 立即发送取消日志，不等待线程结束
        self.log_signal.emit("正在取消OCR处理...")

        # 使用定时器异步检查线程状态，避免阻塞
        self._cancellation_timer = QTimer()
        self._cancellation_timer.timeout.connect(self._checkCancellationStatus)
        self._cancellation_timer.start(100)  # 每100ms检查一次

        # 设置超时保护，5秒后强制终止
        QTimer.singleShot(5000, self._forceTerminateIfNeeded)

    def _checkCancellationStatus(self):
        """检查取消状态"""
        if not self.isRunning():
            # 线程已结束
            self._cancellation_timer.stop()
            self.log_signal.emit("OCR处理已取消")
            self.cancelled_signal.emit()
        elif self.isFinished():
            # 线程已完成
            self._cancellation_timer.stop()
            self.cancelled_signal.emit()

    def _forceTerminateIfNeeded(self):
        """如果需要，强制终止线程"""
        if self.isRunning():
            self.log_signal.emit("强制终止OCR处理...")
            self.terminate()
            # 等待一小段时间让线程终止
            if self.wait(1000):
                self.log_signal.emit("OCR处理已强制终止")
                self.cancelled_signal.emit()
            else:
                self.log_signal.emit("警告: 线程终止可能未完成")
                self.cancelled_signal.emit()


class PrintCapture(io.TextIOBase):
    """捕获print输出的类"""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.buffer = ""

    def write(self, text):
        """重写write方法，发射信号"""
        if text.strip():  # 只发射非空文本
            self.signal.emit(text.strip())
        return len(text)
