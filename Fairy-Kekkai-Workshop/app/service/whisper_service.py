# coding:utf-8
import os
from datetime import datetime

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger


def get_whisper_cli_path():
    """获取 WhisperNetCLI.exe 路径，优先使用用户自定义路径"""
    custom_path = cfg.get(cfg.whisperCliPath)
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # 默认路径: tools/Whisper/WhisperNetCLI.exe
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "tools",
        "Whisper",
        "WhisperNetCLI.exe",
    )


class WhisperTask:
    """Whisper转录任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.input_file = args["video_path"]
        self.output_file = args["output_path"]
        self.model_file = args.get("model", "")
        self.language = args.get("language", "")
        self.format = args.get("format", "srt")
        self.gpu = args.get("gpu", "")
        self.status = "等待中"  # 等待中, 转录中, 已完成, 失败
        self.progress = 0
        self.error_message = ""

        WhisperTask._id_counter += 1
        self.id = WhisperTask._id_counter


class WhisperProcess(QObject):
    """Whisper转录进程"""

    progress_signal = Signal(int, str, str)  # 进度百分比, 速度, 状态信息
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    cancelled_signal = Signal()  # 取消完成信号

    def __init__(self, task):
        super().__init__()
        self.logger = Logger("WhisperProcess", "whisper")
        self.task = task
        self.is_cancelled = False
        self.process = None
        self.output_lines = []  # 存储输出用于错误诊断
        self._cancellation_timer = None

    def build_whisper_command(self):
        """构建 Whisper 命令"""
        # 获取 WhisperNetCLI.exe 路径
        cli_path = get_whisper_cli_path()

        cmd = [cli_path]
        cmd.extend(["--video_path", self.task.input_file])
        cmd.extend(["--output", self.task.output_file])
        cmd.extend(["--model", self.task.model_file])
        # 仅当指定了具体语言时才传 --language；"auto"/空 时让 Whisper 自动检测
        if self.task.language and self.task.language != "auto":
            cmd.extend(["--language", self.task.language])
        cmd.extend(["--format", self.task.format])

        # 只有当 GPU 不是"自动检测"且不为空时才添加 GPU 参数
        if self.task.gpu and self.task.gpu != "自动检测":
            cmd.extend(["--gpu", self.task.gpu])

        return cmd

    def start(self):
        self.task.status = "识别中"
        self.task.start_time = datetime.now()

        try:
            # 获取 WhisperNetCLI.exe 路径
            cli_path = get_whisper_cli_path()

            if not os.path.exists(cli_path):
                self.finished_signal.emit(False, f"WhisperNetCLI.exe不存在: {cli_path}")
                return

            # 检查模型文件
            if not os.path.exists(self.task.model_file):
                self.finished_signal.emit(
                    False, f"模型文件不存在: {self.task.model_file}"
                )
                return

            # 确保输出目录存在
            output_dir = os.path.dirname(self.task.output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # 构建命令
            cmd = self.build_whisper_command()
            try:
                print(f"执行Whisper命令: {' '.join(cmd)}")
            except UnicodeEncodeError:
                pass

            # 创建QProcess
            self.process = QProcess()

            # 连接信号
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.errorOccurred.connect(self.handle_error)

            # 设置程序和工作目录
            self.process.setProgram(cli_path)
            self.process.setArguments(cmd[1:])  # 去掉程序路径本身

            # 启动进程
            self.process.start()

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"语音转录失败: {str(e)}"
                if self.output_lines:
                    error_msg += "\n输出日志:\n" + "\n".join(self.output_lines[-10:])

                self.task.status = "失败"
                self.task.error_message = error_msg
                self.task.end_time = datetime.now()
                self.finished_signal.emit(False, error_msg)
                event_bus.whisper_finished_signal.emit(False, error_msg)

    def handle_stdout(self):
        """处理标准输出"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        )
        event_bus.whisper_update_signal.emit(str(self.task.id), data.replace("\n", "-"))
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)
            self.logger.info(f"Whisper输出: {line}")

            if self.is_cancelled:
                return

            # 解析进度信息
            if line.startswith("PROGRESS:"):
                try:
                    progress = int(line.split(":")[1])
                    self.task.progress = progress
                    self.progress_signal.emit(progress, f"{progress}%", "转录中")
                    self.logger.info(f"进度更新: {progress}%")
                except (ValueError, IndexError):
                    pass
            elif "转录完成" in line:
                self.task.progress = 100
                self.progress_signal.emit(100, "完成", "转录完成")

    def handle_stderr(self):
        """处理标准错误输出"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        )
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)

            # 错误输出可能包含有用信息
            if "错误" in line:
                self.logger.error(f"Whisper错误: {line}")

    def handle_finished(self, exit_code, exit_status):
        """进程完成处理"""
        if self.is_cancelled:
            self.task.status = "已取消"
            self.finished_signal.emit(False, "转录已取消")
            self.cancelled_signal.emit()
            self.logger.info(f"转录已取消 -{self.task.input_file}-")
        elif exit_code == 0:
            self.task.status = "已完成"
            self.task.progress = 100
            self.task.end_time = datetime.now()
            self.logger.info(f"转录完成 -{self.task.input_file}-")

            # 检查输出文件是否存在
            if os.path.exists(self.task.output_file):
                file_size = os.path.getsize(self.task.output_file) / 1024  # KB
                success_msg = f"转录完成 - 文件大小: {file_size:.2f}KB"
            else:
                success_msg = "转录完成"

            self.finished_signal.emit(True, success_msg)
            event_bus.whisper_finished_signal.emit(True, str(self.task.output_file))
        else:
            error_message = f"转录失败，错误码: {exit_code}"

            # 添加最后几行输出作为调试信息
            if self.output_lines:
                last_lines = "\n".join(self.output_lines[-5:])
                error_message += f"\n最后输出:\n{last_lines}"

            self.task.status = "失败"
            self.task.error_message = error_message
            self.task.end_time = datetime.now()
            self.finished_signal.emit(False, error_message)
            event_bus.whisper_finished_signal.emit(False, error_message)

    def handle_error(self, error):
        """处理进程错误"""
        if self.is_cancelled:
            return

        error_map = {
            QProcess.ProcessError.FailedToStart: "进程启动失败",
            QProcess.ProcessError.Crashed: "进程崩溃",
            QProcess.ProcessError.Timedout: "进程超时",
            QProcess.ProcessError.WriteError: "写入错误",
            QProcess.ProcessError.ReadError: "读取错误",
            QProcess.ProcessError.UnknownError: "未知错误",
        }

        error_msg = error_map.get(error, f"进程错误: {error}")
        self.finished_signal.emit(False, error_msg)

    def cancel(self):
        """取消转录"""
        if self.is_cancelled:
            return

        self.is_cancelled = True

        try:
            print("正在取消语音转录...")
        except UnicodeEncodeError:
            pass

        if self.process and self.process.state() == QProcess.Running:
            # 先尝试优雅地终止
            self.process.terminate()

            # 使用定时器异步检查进程状态，避免阻塞
            self._cancellation_timer = QTimer()
            self._cancellation_timer.timeout.connect(self._checkCancellationStatus)
            self._cancellation_timer.start(100)  # 每100ms检查一次

            # 设置超时保护，5秒后强制终止
            QTimer.singleShot(5000, self._forceTerminateIfNeeded)
        else:
            # 如果没有进程在运行，直接发送取消完成信号
            self.cancelled_signal.emit()

    def _checkCancellationStatus(self):
        """检查取消状态"""
        if not self.process or self.process.state() != QProcess.Running:
            # 进程已结束
            if self._cancellation_timer:
                self._cancellation_timer.stop()
            self.cancelled_signal.emit()

    def _forceTerminateIfNeeded(self):
        """如果需要，强制终止进程"""
        if self.process and self.process.state() == QProcess.Running:
            try:
                print("强制终止转录进程...")
            except UnicodeEncodeError:
                pass
            self.process.kill()
            # 等待一小段时间让进程终止
            if self.process.waitForFinished(1000):
                try:
                    print("转录进程已强制终止")
                except UnicodeEncodeError:
                    pass
                self.cancelled_signal.emit()
            else:
                try:
                    print("警告: 进程终止可能未完成")
                except UnicodeEncodeError:
                    pass
                self.cancelled_signal.emit()
